import logging
import os.path
import re
import shutil
from typing import List, Optional, TypeVar

from rdflib import RDF, XSD, Graph, Literal, Namespace, URIRef
from sqlalchemy import Engine, and_, create_engine, or_, select, text
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from biokb_ipni import constants
from biokb_ipni.constants import BASIC_NODE_LABEL, EXPORT_FOLDER
from biokb_ipni.db import models
from biokb_ipni.rdf import namespaces

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# Type variable for SQLAlchemy model classes
BaseModels = TypeVar("BaseModels", bound=models.Base)


def get_namespace(model_name: str) -> Namespace:
    """Generate an RDF namespace for a given SQLAlchemy model class.

    Args:
        model: SQLAlchemy model class to generate namespace for.

    Returns:
        RDF Namespace object with URI based on the model's class name.
    """
    return Namespace(f"{namespaces.BASE_URI}/{model_name}#")


def get_empty_graph() -> Graph:
    graph = Graph()
    # Bind generic ontology namespaces
    graph.bind(prefix="rel", namespace=namespaces.REL_NS)
    graph.bind(prefix="xs", namespace=XSD)
    graph.bind(prefix="n", namespace=namespaces.NODE_NS)
    graph.bind(prefix="ncbi", namespace=namespaces.NCBI_TAXON_NS)
    graph.bind(prefix="a", namespace=namespaces.NAME_NS)
    graph.bind(prefix="f", namespace=namespaces.FAMILY_NS)

    return graph


class TurtleCreator:
    """Factory class for generating RDF Turtle files from IPNI database."""

    pass

    def __init__(
        self,
        engine: Engine | None = None,
    ):
        self.__ttls_folder = EXPORT_FOLDER
        connection_str = os.getenv(
            "CONNECTION_STR", constants.DB_DEFAULT_CONNECTION_STR
        )
        self.__engine = engine if engine else create_engine(str(connection_str))
        self.Session = sessionmaker(bind=self.__engine)

    def _set_ttls_folder(self, export_to_folder: str) -> None:
        """Sets the export folder path.

        This is mainly for testing purposes.
        """
        self.__ttls_folder = export_to_folder

    def create_ttls(self) -> str:
        """Generate RDF Turtle files from the database.
        Returns:
            Path to the zip file containing all generated Turtle files.
        """
        logging.info("Starting turtle file generation process.")
        os.makedirs(self.__ttls_folder, exist_ok=True)
        self._create_families()
        self._create_locations()
        self._create_name_relations()
        self._create_names()

        # Package everything into a zip file
        path_to_zip_file: str = self._create_zip_from_all_ttls()
        logging.info(f"Turtle files successfully packaged in {path_to_zip_file}")
        return path_to_zip_file

    def _create_families(self) -> None:
        logging.info("Creating RDF families turtle file.")

        graph = get_empty_graph()

        with self.Session() as session:
            # Query all families
            families: List[models.Family] = session.query(models.Family).all()

            for family in tqdm(families, desc="Creating families triples"):
                family_entity: URIRef = namespaces.FAMILY_NS[str(family.id)]
                # Add type declarations
                graph.add(
                    triple=(
                        family_entity,
                        RDF.type,
                        namespaces.NODE_NS[models.Family.__name__],
                    )
                )
                graph.add(
                    triple=(
                        family_entity,
                        RDF.type,
                        namespaces.NODE_NS[BASIC_NODE_LABEL],
                    )
                )
                graph.add(
                    triple=(
                        family_entity,
                        namespaces.REL_NS["name"],
                        Literal(family.family, datatype=XSD.string),
                    )
                )
        ttl_path = os.path.join(
            self.__ttls_folder, f"{models.Family.__tablename__}.ttl"
        )
        graph.serialize(ttl_path, format="turtle")
        del graph

    def _create_locations(self) -> None:
        # using type_material to extract locations
        logging.info("Creating RDF location turtle file.")
        graph = get_empty_graph()
        with self.Session() as session:
            locations = (
                session.query(models.Location)
                .where(
                    or_(
                        models.Location.locality.is_not(None),
                        and_(
                            models.Location.latitude.is_not(None),
                            models.Location.longitude.is_not(None),
                        ),
                    )
                )
                .all()
            )

            # Query all type_materials
            for location in locations:
                location_entity: URIRef = namespaces.LOCATION_NS[str(location.id)]

                # Add type declarations
                graph.add(
                    triple=(
                        location_entity,
                        RDF.type,
                        namespaces.NODE_NS["Location"],
                    )
                )
                graph.add(
                    triple=(
                        location_entity,
                        RDF.type,
                        namespaces.NODE_NS[BASIC_NODE_LABEL],
                    )
                )
                if location.locality:
                    graph.add(
                        triple=(
                            location_entity,
                            namespaces.REL_NS["locality"],
                            Literal(location.locality, datatype=XSD.string),
                        )
                    )
                if location.latitude and location.longitude:
                    graph.add(
                        triple=(
                            location_entity,
                            namespaces.REL_NS["latitude"],
                            Literal(location.latitude, datatype=XSD.float),
                        )
                    )
                    graph.add(
                        triple=(
                            location_entity,
                            namespaces.REL_NS["longitude"],
                            Literal(location.longitude, datatype=XSD.float),
                        )
                    )

            stmt = (
                select(models.TypeMaterial.name_id, models.TypeMaterial.location_id)
                .select_from(models.TypeMaterial)
                .join(models.Location)
                .where(
                    or_(
                        models.Location.locality.is_not(None),
                        and_(
                            models.Location.latitude.is_not(None),
                            models.Location.longitude.is_not(None),
                        ),
                    )
                )
            )
            for name_id, location_id in session.execute(stmt).all():
                name_entity: URIRef = namespaces.NAME_NS[str(name_id)]
                location_entity: URIRef = namespaces.LOCATION_NS[str(location_id)]
                graph.add(
                    triple=(
                        name_entity,
                        namespaces.REL_NS["HAS_LOCATION"],
                        location_entity,
                    )
                )

        ttl_path = os.path.join(self.__ttls_folder, f"ipni_location.ttl")
        graph.serialize(ttl_path, format="turtle")
        del graph

    def _create_name_relations(self) -> None:
        logging.info("Creating name relations file.")

        graph = get_empty_graph()

        with self.Session() as session:
            # Query all name relations
            name_relations: List[models.NameRelation] = session.query(
                models.NameRelation
            ).all()

            for relation in tqdm(name_relations, desc="Creating name relation triples"):
                subject_entity: URIRef = namespaces.NAME_NS[
                    str(relation.related_name_id)
                ]
                object_entity: URIRef = namespaces.NAME_NS[str(relation.name_id)]

                if re.search(r"^[A-Z_]+$", relation.type):
                    relation_name_suffix = relation.type
                else:
                    relation_name_suffix = (
                        re.sub(r"([A-Z])", r"_\1", relation.type).strip("_").upper()
                    )
                graph.add(
                    triple=(
                        subject_entity,
                        namespaces.REL_NS[f"HAS_{relation_name_suffix}"],
                        object_entity,
                    )
                )
        ttl_path = os.path.join(
            self.__ttls_folder, f"{models.NameRelation.__tablename__}.ttl"
        )
        graph.serialize(ttl_path, format="turtle")
        del graph

    def _create_names(self) -> None:
        logging.info("Creating RDF names turtle file.")

        with self.__engine.connect() as conn:
            # Query all names
            result = conn.execution_options(stream_results=True).execute(
                text(f"SELECT * FROM {models.Name.__tablename__}")
            )
            file_counter = 0
            while True:
                names = result.fetchmany(100_000)
                if not names:
                    break

                file_counter += 1
                graph = get_empty_graph()
                for name in names:

                    name_entity: URIRef = namespaces.NAME_NS[str(name.id)]
                    # Add type declarations
                    graph.add(
                        triple=(
                            name_entity,
                            RDF.type,
                            namespaces.NODE_NS[models.Name.__name__],
                        )
                    )
                    graph.add(
                        triple=(
                            name_entity,
                            RDF.type,
                            namespaces.NODE_NS[BASIC_NODE_LABEL],
                        )
                    )
                    graph.add(
                        triple=(
                            name_entity,
                            namespaces.REL_NS["name"],
                            Literal(name.scientific_name, datatype=XSD.string),
                        )
                    )
                    if name.tax_id:
                        graph.add(
                            triple=(
                                name_entity,
                                namespaces.REL_NS["SAME_AS"],
                                namespaces.NCBI_TAXON_NS[str(name.tax_id)],
                            )
                        )
                    graph.add(
                        triple=(
                            name_entity,
                            namespaces.REL_NS["rank"],
                            Literal(name.rank, datatype=XSD.string),
                        )
                    )
                    # add relation to family
                    if name.family_id:
                        graph.add(
                            triple=(
                                name_entity,
                                namespaces.REL_NS["HAS_FAMILY"],
                                namespaces.FAMILY_NS[str(name.family_id)],
                            )
                        )

                ttl_path = os.path.join(
                    self.__ttls_folder,
                    f"{models.Name.__tablename__}_{file_counter}.ttl",
                )
                graph.serialize(ttl_path, format="turtle")
                del graph

    def _create_zip_from_all_ttls(self) -> str:
        """Package all generated turtle files into a single zip archive.

        Creates a zip file containing all .ttl files in the export folder,
        then removes the temporary turtle files directory to clean up.

        Returns:
            Path to the created zip file.
        """
        logger.info("Packaging turtle files into zip archive.")

        # Create zip archive from all turtle files
        path_to_zip_file = shutil.make_archive(
            base_name=self.__ttls_folder, format="zip", root_dir=self.__ttls_folder
        )

        # Clean up temporary turtle files directory
        shutil.rmtree(self.__ttls_folder)

        return path_to_zip_file


def create_ttls(
    engine: Optional[Engine] = None,
    export_to_folder: Optional[str] = None,
) -> str:
    """Create all turtle files.

    If engine=None tries to get the settings from environment else uses the default engine.

    If export_to_folder is provided, turtle files are exported to this folder. Otherwise,
    the default export folder (~/.biokb/ipni/data) is used.

    Args:
        engine (Engine | None, optional): SQLAlchemy engine. Defaults to None.
        export_to_folder (str | None, optional): Folder to export ttl files.
            Defaults to None.

    Returns:
        str: path zipped file with ttls.
    """
    ttl_creator = TurtleCreator(engine=engine)
    if export_to_folder:
        ttl_creator._set_ttls_folder(export_to_folder)
    return ttl_creator.create_ttls()
