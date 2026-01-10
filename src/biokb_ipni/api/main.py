# main.py
import logging
import os
import re
import secrets
from datetime import date, datetime
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Annotated, List, Optional, Union, get_args, get_origin

import Levenshtein
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy import and_, create_engine, not_, or_, select
from sqlalchemy.orm import Session

# from database import SessionLocal
from sqlalchemy.sql import text

from biokb_ipni.api import schemas
from biokb_ipni.api.tags import Tag
from biokb_ipni.constants import DB_DEFAULT_CONNECTION_STR
from biokb_ipni.db import models
from biokb_ipni.db.manager import DbManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

USERNAME = os.environ.get("API_USERNAME", "admin")
PASSWORD = os.environ.get("API_PASSWORD", "admin")

# 1) Configure Database
SQLALCHEMY_DATABASE_URL = os.getenv("CONNECTION_STR", DB_DEFAULT_CONNECTION_STR)

engine = create_engine(SQLALCHEMY_DATABASE_URL)


def get_db():
    dbm = DbManager(engine=engine)
    session = dbm.Session()
    try:
        yield session
    finally:
        session.close()


# 3) Create FastAPI App
app = FastAPI(
    title="IPNI Data API",
    description="RestfulAPI for IPNI-based data. <br><br>Reference: https://www.ipni.org/",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    uvicorn.run(
        app="biokb_ipni.api.main:app",
        host=host,
        port=port,
        log_level="warning",
    )


def verify_credentials(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    is_correct_username = secrets.compare_digest(credentials.username, USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


def build_dynamic_query(
    search_obj: BaseModel,
    model_cls,
    db: Session,
    limit: Optional[int] = None,  # default limit for pagination
    offset: Optional[int] = None,  # default offset for pagination
):
    """
    Build and execute a SQLAlchemy 2.0-style SELECT based on the non-None
    attributes of a Pydantic model instance.  The operator is inferred from
    each field's *declared* type, not the runtime value.
    """
    filters = []

    # Only the attributes the client actually supplied (`exclude_none`)
    payload = search_obj.model_dump(exclude_none=True)

    for field_name, value in payload.items():

        # Skip if the SQLAlchemy model has no matching column / hybrid attr
        if not hasattr(model_cls, field_name):
            continue
        column = getattr(model_cls, field_name)

        # ↓ The type you wrote in the Pydantic model definition
        declared_type = search_obj.__pydantic_fields__[field_name].annotation
        # Handle Optional types (e.g., Optional[str] or Union[str, None])
        if get_origin(declared_type) is Union:
            args = [arg for arg in get_args(declared_type) if arg is not type(None)]
            if args:
                declared_type = args[0]
        origin = get_origin(declared_type) or declared_type

        # STRING ......................................................................
        if origin is str:
            logger.info("used string filter")
            filters.append(column.like(value) if ("%" in value) else column == value)

        # NUMBERS .....................................................................
        elif origin in (int, float, Decimal):
            filters.append(column == value)

        # BOOLEANS ....................................................................
        elif origin is bool:
            filters.append(column.is_(value))

        # DATE / DATETIME – supports equality or simple closed range ...................
        elif origin in (date, datetime):
            if isinstance(value, (list, tuple)) and len(value) == 2:
                filters.append(column.between(value[0], value[1]))
            else:
                filters.append(column == value)

        # FALLBACK .....................................................................
        else:
            logger.warning(
                f"Unsupported type for field '{field_name}': {declared_type}. "
                "Using equality operator as fallback."
            )
            filters.append(column == value)

    stmt = select(model_cls).where(*filters)
    if limit is not None:
        stmt = stmt.limit(limit)
    if offset is not None:
        stmt = stmt.offset(offset)

    logger.info(stmt.compile(compile_kwargs={"literal_binds": True}))

    return db.execute(stmt).scalars().all()


###############################################################################
# Manage
###############################################################################
@app.get("/", tags=["Manage"])
def check_status() -> dict:
    return {"msg": "Running!"}


@app.get("/import_data/", tags=["Manage"])
def import_data(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    session: Session = Depends(get_db),
):
    return DbManager(engine=engine).import_data()


###############################################################################
# Name
###############################################################################
@app.get("/name/{name_id}", response_model=schemas.Name, tags=[Tag.NAME])
def get_name(name_id: str, session: Session = Depends(get_db)) -> models.Name | None:
    obj = session.get(models.Name, name_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Name with id={name_id} not found.",
        )
    return obj


@app.get("/names/find_similar", tags=[Tag.NAME])
def names_find_similar(
    session: Session = Depends(get_db),
    name: str = Query(..., description="Name to search for"),
):
    """Fuzzy search for similar names using LEVENSHTEIN algorithm."""
    name = re.sub(r"\s+", " ", name.strip())
    name_splitted = [x.strip() for x in name.split(" ")]

    stmt = select(models.Name.scientific_name, models.Name.id).select_from(models.Name)

    # First, check for exact match
    # If an exact match is found, return it immediately.
    exact_results = session.execute(
        stmt.where(models.Name.scientific_name == name)
    ).all()
    if exact_results:
        return_values = []
        for exact_result in exact_results:
            return_values.append(
                {
                    "calculate_with": "exact",
                    "scientific_name": exact_result.scientific_name,
                    "ipni_id": exact_result.id,
                    "similarity": 1.0,  # Exact match
                }
            )
        return return_values

    # If no exact match, check for soundex match
    # This is a phonetic algorithm for indexing names by sound, as pronounced in English.
    stmt2 = stmt.where(text(f"SOUNDEX(scientific_name) = SOUNDEX('{name}')"))
    results = session.execute(stmt2).all()

    ratios = []
    if not results:
        # If no exact or soundex match, use Levenshtein distance

        if len(name_splitted) < 2:
            search_str = f"{name}%"
        else:
            search_str = f"{name_splitted[0]}% {name_splitted[1]}%"
        stmt3 = (
            select(models.Name.scientific_name, models.Name.id)
            .select_from(models.Name)
            .where(models.Name.scientific_name.like(search_str))
        )
        results = session.execute(stmt3).all()

        # check for similarity

        for result in results:

            ratio = SequenceMatcher(None, name, result.scientific_name).ratio()
            if ratio > 0.3:  # Threshold for similarity
                ratios.append(
                    {
                        "calculate_with": "soundex",
                        "scientific_name": result.scientific_name,
                        "ipni_id": result.id,
                        "similarity": round(ratio, 2),  # Convert to percentage
                    }
                )
        if ratios:
            return sorted(ratios, key=lambda x: x["similarity"], reverse=True)

    # if no results Levenshtein
    if not ratios:
        stmt4 = stmt.where(
            or_(
                models.Name.scientific_name.like(f"{name[0]}%"),
                models.Name.scientific_name.like(f"%{name[-4:]}"),
            )
        )
        results = session.execute(stmt4).all()

        for result in results:
            ratio = Levenshtein.ratio(name, result.scientific_name)
            if ratio > 0.3:
                ratios.append(
                    {
                        "calculate_with": "levenshtein",
                        "scientific_name": result.scientific_name,
                        "ipni_id": result.id,
                        "similarity": round(ratio, 2),  # Convert to percentage
                    }
                )
        if ratios:
            return sorted(ratios, key=lambda x: x["similarity"], reverse=True)[:3]

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Name '{name}' not found.",
        )


@app.get("/names/", response_model=List[schemas.Name], tags=[Tag.NAME])
def list_names(
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 3,
    session: Session = Depends(get_db),
) -> List[models.Name]:
    return session.query(models.Name).offset(offset).limit(limit).all()


@app.get("/name_ranks/", tags=[Tag.NAME])
def name_ranks(
    session: Session = Depends(get_db),
) -> List[str]:
    """Get all distinct ranks in names."""
    ranks = session.query(models.Name.rank).group_by(models.Name.rank).all()
    return [r[0] for r in ranks if r[0] is not None]


@app.get("/name_statuses/", tags=[Tag.NAME])
def name_statuses(
    session: Session = Depends(get_db),
) -> List[str]:
    """Get all distinct statuses in names."""
    statuses = session.query(models.Name.status).group_by(models.Name.status).all()
    return [s[0] for s in statuses if s[0] is not None]


@app.get("/names/search/", response_model=List[schemas.Name], tags=[Tag.NAME])
def search_names(
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 3,
    search: schemas.NameSearch = Depends(schemas.NameSearch),
    session: Session = Depends(get_db),
):
    return build_dynamic_query(
        search_obj=search, model_cls=models.Name, db=session, limit=limit, offset=offset
    )


###############################################################################
# Reference
###############################################################################
@app.get("/reference/{ref_id}", response_model=schemas.Reference, tags=[Tag.REFERENCE])
def get_reference(
    ref_id: str, session: Session = Depends(get_db)
) -> models.Reference | None:
    obj = session.get(models.Reference, ref_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference with id={id} not found.",
        )
    return obj


@app.get("/references/", response_model=List[schemas.Reference], tags=[Tag.REFERENCE])
def list_references(
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 3,
    session: Session = Depends(get_db),
) -> List[models.Reference]:
    return session.query(models.Reference).offset(offset).limit(limit).all()


@app.get(
    "/references/search/", response_model=List[schemas.Reference], tags=[Tag.REFERENCE]
)
def search_references(
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 3,
    search: schemas.ReferenceSearch = Depends(schemas.ReferenceSearch),
    session: Session = Depends(get_db),
):
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.Reference,
        db=session,
        limit=limit,
        offset=offset,
    )


# ###############################################################################
# # Taxon
# ###############################################################################
@app.get("/taxon/{id}", response_model=schemas.Taxon, tags=[Tag.TAXON])
def get_taxon(id: str, session: Session = Depends(get_db)) -> models.Taxon | None:
    obj = session.get(models.Taxon, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Taxon with id={id} not found.",
        )
    return obj


@app.get("/taxons/", response_model=List[schemas.Taxon], tags=[Tag.TAXON])
def list_taxons(
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 3,
    session: Session = Depends(get_db),
) -> List[models.Taxon]:
    return session.query(models.Taxon).offset(offset).limit(limit).all()


@app.get("/taxon_families/", tags=[Tag.TAXON])
def taxon_families(
    session: Session = Depends(get_db),
) -> List[str]:
    """Get all distinct families in taxa."""
    families = session.query(models.Taxon.family).group_by(models.Taxon.family).all()
    return [f[0] for f in families if f[0] is not None]


@app.get("/taxons/search/", response_model=List[schemas.Taxon], tags=[Tag.TAXON])
def search_taxons(
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 3,
    search: schemas.TaxonSearch = Depends(schemas.TaxonSearch),
    session: Session = Depends(get_db),
):
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.Taxon,
        db=session,
        limit=limit,
        offset=offset,
    )


# ###############################################################################
# # NameRelation
# ###############################################################################
@app.get(
    "/name_relation/{id}",
    response_model=schemas.NameRelation,
    tags=[Tag.NAME_RELATION],
)
def get_name_relation(
    id: str, session: Session = Depends(get_db)
) -> models.NameRelation | None:
    obj = session.get(models.NameRelation, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Name Relation with id={id} not found.",
        )
    return obj


@app.get(
    "/name_relations/",
    response_model=List[schemas.NameRelation],
    tags=[Tag.NAME_RELATION],
)
def list_name_relations(
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 3,
    session: Session = Depends(get_db),
) -> List[models.NameRelation]:
    return session.query(models.NameRelation).offset(offset).limit(limit).all()


@app.get("/name_relation_types/", tags=[Tag.NAME_RELATION])
def name_relation_types(
    session: Session = Depends(get_db),
) -> List[str]:
    """Get all distinct types in name relations."""
    types = (
        session.query(models.NameRelation.type).group_by(models.NameRelation.type).all()
    )
    return [t[0] for t in types if t[0] is not None]


@app.get(
    "/name_relations/search/",
    response_model=List[schemas.NameRelation],
    tags=[Tag.NAME_RELATION],
)
def search_name_relations(
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 3,
    search: schemas.NameRelationSearch = Depends(schemas.NameRelationSearch),
    session: Session = Depends(get_db),
):
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.NameRelation,
        db=session,
        limit=limit,
        offset=offset,
    )


# ###############################################################################
# # TypeMaterial
# ###############################################################################
@app.get(
    "/type_material/{id}",
    response_model=schemas.TypeMaterial,
    tags=[Tag.TYPE_MATERIAL],
)
def get_type_material(
    id: int, session: Session = Depends(get_db)
) -> models.TypeMaterial | None:
    obj = session.get(models.TypeMaterial, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Type material with id={id} not found.",
        )
    return obj


@app.get(
    "/type_materials/",
    response_model=List[schemas.TypeMaterial],
    tags=[Tag.TYPE_MATERIAL],
)
def list_type_materials(
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 3,
    session: Session = Depends(get_db),
) -> List[models.TypeMaterial]:
    return session.query(models.TypeMaterial).offset(offset).limit(limit).all()


@app.get(
    "/type_materials/search/",
    response_model=List[schemas.TypeMaterial],
    tags=[Tag.TYPE_MATERIAL],
)
def search_type_materials(
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 3,
    search: schemas.TypeMaterialSearch = Depends(schemas.TypeMaterialSearch),
    session: Session = Depends(get_db),
):
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.TypeMaterial,
        db=session,
        limit=limit,
        offset=offset,
    )
