import logging
import os
import re
import secrets
from contextlib import asynccontextmanager
from difflib import SequenceMatcher
from typing import Annotated, AsyncGenerator, List

import jellyfish
import Levenshtein
import uvicorn
from fastapi import Body, Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import Engine, create_engine, or_, select
from sqlalchemy.orm import Session

# from database import SessionLocal
from sqlalchemy.sql import text

from biokb_ipni.api import schemas
from biokb_ipni.api.query_tools import SASearchResults, build_dynamic_query
from biokb_ipni.api.tags import Tag
from biokb_ipni.constants import (
    DB_DEFAULT_CONNECTION_STR,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
    ZIPPED_TTLS_PATH,
)
from biokb_ipni.db import manager, models
from biokb_ipni.rdf.neo4j_importer import Neo4jImporter
from biokb_ipni.rdf.turtle import TurtleCreator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

USERNAME = os.environ.get("API_USERNAME", "admin")
PASSWORD = os.environ.get("API_PASSWORD", "admin")


def get_engine() -> Engine:
    conn_url = os.environ.get("CONNECTION_STR", DB_DEFAULT_CONNECTION_STR)
    engine: Engine = create_engine(conn_url)
    return engine


def get_session():
    engine: Engine = get_engine()
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize app resources on startup and cleanup on shutdown."""
    engine = get_engine()
    manager.DbManager(engine)
    yield
    # Clean up resources if needed
    pass


app = FastAPI(
    title="IPNI Data API",
    description="RestfulAPI for IPNI-based data. <br><br>Reference: https://www.ipni.org/",
    version="0.1.0",
    lifespan=lifespan,
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


###############################################################################
# Database Management
###############################################################################
@app.post(
    path="/import_data/",
    response_model=dict[str, int],
    tags=[Tag.DB_MANAGE],
)
async def import_data(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    force_download: bool = Query(
        False,
        description=(
            "Whether to re-download data files even if they already exist,"
            " ensuring the newest version."
        ),
    ),
    keep_files: bool = Query(
        True,
        description=(
            "Whether to keep the downloaded files"
            " after importing them into the database."
        ),
    ),
) -> dict[str, int]:
    """Download data (if not exists) and load in database.

    Can take up to 15 minutes to complete.
    """
    try:
        dbm = manager.DbManager()
        result = dbm.import_data(force_download=force_download, keep_files=keep_files)
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing data. {e}",
        ) from e
    return result


@app.get("/export_ttls/", tags=[Tag.DB_MANAGE])
async def get_report(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    force_create: bool = Query(
        False,
        description="Whether to re-generate the TTL files even if they already exist.",
    ),
) -> FileResponse:

    file_path = ZIPPED_TTLS_PATH
    if not os.path.exists(file_path) or force_create:
        try:
            TurtleCreator().create_ttls()
        except Exception as e:
            logger.error(f"Error generating TTL files: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generating TTL files. Data already imported?",
            ) from e
    return FileResponse(
        path=file_path, filename="coconut_ttls.zip", media_type="application/zip"
    )


@app.get("/import_neo4j/", tags=[Tag.DB_MANAGE])
async def import_neo4j(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    uri: str | None = Query(
        NEO4J_URI,
        description="The Neo4j URI. If not provided, "
        "the default from environment variable is used.",
    ),
    user: str | None = Query(
        NEO4J_USER,
        description="The Neo4j user. If not provided,"
        " the default from environment variable is used.",
    ),
    password: str | None = Query(
        NEO4J_PASSWORD,
        description="The Neo4j password. If not provided,"
        " the default from environment variable is used.",
    ),
) -> dict[str, str]:
    """Import RDF turtle files in Neo4j."""
    try:
        if not os.path.exists(ZIPPED_TTLS_PATH):
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail=(
                    "Zipped TTL files not found. Please "
                    "generate them first using /export_ttls/ endpoint."
                ),
            )
        importer = Neo4jImporter(neo4j_uri=uri, neo4j_user=user, neo4j_pwd=password)
        importer.import_ttls()
    except Exception as e:
        logger.error(f"Error importing data into Neo4j: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing data into Neo4j: {e}",
        ) from e
    return {"status": "Neo4j import completed successfully."}


###############################################################################
# Name
###############################################################################
@app.get("/name/{name_id}", response_model=schemas.Name, tags=[Tag.NAME])
async def get_name(
    name_id: str, session: Session = Depends(get_session)
) -> models.Name | None:
    obj = session.get(models.Name, name_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Name with id={name_id} not found.",
        )
    return obj


@app.get(
    "/names/find_similar",
    response_model=list[schemas.NameSearchResult],
    tags=[Tag.NAME],
)
async def names_find_similar(
    session: Session = Depends(get_session),
    search_for_name: str = Query(
        ..., description="Name to search for", example="acHila meliflium"
    ),
):
    """Fuzzy search for similar names using LEVENSHTEIN algorithm."""
    search_for_name = re.sub(r"\s+", " ", search_for_name.strip())
    name_splitted = [x.strip() for x in search_for_name.split(" ")]

    stmt = select(models.Name.scientific_name, models.Name.id).select_from(models.Name)

    # First, check for exact match
    # If an exact match is found, return it immediately.
    exact_results = session.execute(
        stmt.where(models.Name.scientific_name == search_for_name)
    ).all()
    if exact_results:
        return_values = []
        for exact_result in exact_results:
            return_values.append(
                schemas.NameSearchResult(
                    calculate_with="exact",
                    scientific_name=exact_result.scientific_name,
                    similarity=1.0,
                    ipni_id=exact_result.id,
                )
            )
        return return_values

    # If no exact match, use phonetic similarity with Metaphone algorithm
    # Metaphone is better than soundex for non-English names including Latin scientific names
    # Also try Jaro-Winkler which works well for scientific names with shared prefixes
    name_metaphone = jellyfish.metaphone(search_for_name)
    first_letter = search_for_name[0].upper()

    # Get names that start with same letter to reduce the dataset for phonetic comparison
    candidate_stmt = (
        select(models.Name.scientific_name, models.Name.id)
        .select_from(models.Name)
        .where(models.Name.scientific_name.like(f"{first_letter}%"))
    )

    candidates = session.execute(candidate_stmt).all()

    # Filter candidates by Metaphone similarity and Jaro-Winkler
    phonetic_matches = []
    for candidate in candidates:
        candidate_metaphone = jellyfish.metaphone(candidate.scientific_name)

        # Check if metaphone codes match
        metaphone_match = name_metaphone == candidate_metaphone

        # Also check Jaro-Winkler similarity for scientific names (good for genus/species prefixes)
        jaro_similarity = jellyfish.jaro_winkler_similarity(
            search_for_name.lower(), candidate.scientific_name.lower()
        )

        if metaphone_match or jaro_similarity > 0.8:
            # Calculate combined similarity score
            sequence_ratio = SequenceMatcher(
                None, search_for_name.lower(), candidate.scientific_name.lower()
            ).ratio()
            final_similarity = max(jaro_similarity, sequence_ratio)

            if final_similarity > 0.5:
                phonetic_matches.append(
                    schemas.NameSearchResult(
                        calculate_with="metaphone_jaro",
                        scientific_name=candidate.scientific_name,
                        ipni_id=candidate.id,
                        similarity=round(final_similarity, 2),
                    )
                )

    if phonetic_matches:
        return sorted(phonetic_matches, key=lambda x: x.similarity, reverse=True)[:30]

    results = []
    ratios = []
    # If no phonetic matches, fall back to pattern-based search with Levenshtein distance

    if len(name_splitted) < 2:
        search_str = f"{search_for_name}%"
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
        ratio = SequenceMatcher(None, search_for_name, result.scientific_name).ratio()
        if ratio > 0.3:  # Threshold for similarity
            ratios.append(
                schemas.NameSearchResult(
                    calculate_with="pattern_match",
                    scientific_name=result.scientific_name,
                    ipni_id=result.id,
                    similarity=round(ratio, 2),
                )
            )
    if ratios:
        return sorted(ratios, key=lambda x: x.similarity, reverse=True)

    # if no results Levenshtein
    if not ratios:
        stmt4 = stmt.where(
            or_(
                models.Name.scientific_name.like(f"{search_for_name[0]}%"),
                models.Name.scientific_name.like(f"%{search_for_name[-4:]}"),
            )
        )
        results = session.execute(stmt4).all()

        for result in results:
            ratio = Levenshtein.ratio(search_for_name, result.scientific_name)
            if ratio > 0.3:
                ratios.append(
                    schemas.NameSearchResult(
                        calculate_with="levenshtein",
                        scientific_name=result.scientific_name,
                        ipni_id=result.id,
                        similarity=round(ratio, 2),  # Convert to percentage
                    )
                )
        if ratios:
            return sorted(ratios, key=lambda x: x.similarity, reverse=True)[:3]

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Name '{search_for_name}' not found.",
        )


@app.get("/name_ranks/", tags=[Tag.NAME])
async def name_ranks(
    session: Session = Depends(get_session),
) -> List[str]:
    """Get all distinct ranks in names."""
    ranks = session.query(models.Name.rank).group_by(models.Name.rank).all()
    return [r[0] for r in ranks if r[0] is not None]


@app.get("/name_status/", tags=[Tag.NAME])
async def name_statuses(
    session: Session = Depends(get_session),
) -> List[str]:
    """Get all distinct status in names."""
    statuses = session.query(models.Name.status).group_by(models.Name.status).all()
    return [s[0] for s in statuses if s[0] is not None]


@app.get("/names/search/", response_model=List[schemas.Name], tags=[Tag.NAME])
async def search_names(
    search: schemas.NameSearch = Depends(schemas.NameSearch),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:

    return build_dynamic_query(
        search_obj=search, model_cls=models.Name, session=session
    )


###############################################################################
# Reference
###############################################################################
@app.get("/reference/{ref_id}", response_model=schemas.Reference, tags=[Tag.REFERENCE])
async def get_reference(
    ref_id: str, session: Session = Depends(get_session)
) -> models.Reference | None:
    obj = session.get(models.Reference, ref_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference with id={id} not found.",
        )
    return obj


@app.get(
    "/references/search/",
    response_model=schemas.ReferenceSearchResult,
    tags=[Tag.REFERENCE],
)
async def search_references(
    search: schemas.ReferenceSearch = Depends(schemas.ReferenceSearch),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.Reference,
        session=session,
    )


# ###############################################################################
# Family
# ###############################################################################
@app.get("/family/{id}", response_model=schemas.Family, tags=[Tag.FAMILY])
async def get_family(
    id: str, session: Session = Depends(get_session)
) -> models.Family | None:
    obj = session.get(models.Family, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Family with id={id} not found.",
        )
    return obj


@app.get("/families/", response_model=List[schemas.Family], tags=[Tag.FAMILY])
async def family_families(
    session: Session = Depends(get_session),
) -> List[models.Family]:
    """Get all distinct families."""
    return session.query(models.Family).all()


@app.get(
    "/families/search/", response_model=schemas.FamilySearchResult, tags=[Tag.FAMILY]
)
async def search_families(
    search: schemas.FamilySearch = Depends(schemas.FamilySearch),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.Family,
        session=session,
    )


# ###############################################################################
# # NameRelation
# ###############################################################################
@app.get(
    "/name_relation/{id}",
    response_model=schemas.NameRelation,
    tags=[Tag.NAME_RELATION],
)
async def get_name_relation(
    id: str, session: Session = Depends(get_session)
) -> models.NameRelation | None:
    obj = session.get(models.NameRelation, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Name Relation with id={id} not found.",
        )
    return obj


@app.get("/name_relation_types/", tags=[Tag.NAME_RELATION])
async def name_relation_types(
    session: Session = Depends(get_session),
) -> List[str]:
    """Get all distinct types in name relations."""
    types = (
        session.query(models.NameRelation.type).group_by(models.NameRelation.type).all()
    )
    return [t[0] for t in types if t[0] is not None]


@app.get(
    "/name_relations/search/",
    response_model=schemas.NameRelationSearchResult,
    tags=[Tag.NAME_RELATION],
)
async def search_name_relations(
    search: schemas.NameRelationSearch = Depends(schemas.NameRelationSearch),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.NameRelation,
        session=session,
    )


###############################################################################
# TypeMaterial
###############################################################################
@app.get(
    "/type_material/{id}",
    response_model=schemas.TypeMaterial,
    tags=[Tag.TYPE_MATERIAL],
)
async def get_type_material(
    id: int, session: Session = Depends(get_session)
) -> models.TypeMaterial | None:
    obj = session.get(models.TypeMaterial, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Type material with id={id} not found.",
        )
    return obj


@app.get(
    "/type_materials/search/",
    response_model=schemas.TypeMaterialSearchResult,
    tags=[Tag.TYPE_MATERIAL],
)
async def search_type_materials(
    search: schemas.TypeMaterialSearch = Depends(schemas.TypeMaterialSearch),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.TypeMaterial,
        session=session,
    )


###############################################################################
# Location
###############################################################################


@app.get(
    "/location/{id}",
    response_model=schemas.Location,
    tags=[Tag.LOCATION],
)
async def get_location(
    id: int, session: Session = Depends(get_session)
) -> models.Location | None:
    obj = session.get(models.Location, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id={id} not found.",
        )
    return obj


@app.get(
    "/locations/search/",
    response_model=schemas.LocationSearchResult,
    tags=[Tag.LOCATION],
)
async def search_locations(
    search: schemas.LocationSearch = Depends(schemas.LocationSearch),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.Location,
        session=session,
    )
