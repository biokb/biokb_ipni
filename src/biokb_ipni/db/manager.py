import logging
import os
import shutil
import sqlite3
import urllib.request
import zipfile
from typing import Any, Optional

import pandas as pd
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from biokb_ipni.constants import (
    DATA_FOLDER,
    DB_DEFAULT_CONNECTION_STR,
    DOWNLOAD_URL,
    PATH_TO_TAXTREE_ZIP_FILE,
    PATH_TO_ZIP_FILE,
    RANKED_LINEAGE_COLUMNS,
    RANKED_LINEAGE_DTYPES,
    TAXTREE_DATA_FOLDER,
    TAXTREE_DOWNLOAD_URL,
    TsvFileName,
)
from biokb_ipni.db.models import (
    Base,
    Family,
    Name,
    NameRelation,
    Reference,
    TypeMaterial,
    Location,
)
from biokb_ipni.tools import get_cleaned_and_standardized_dataframe, parse_date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(
    dbapi_connection: sqlite3.Connection, _connection_record: object
) -> None:
    """Enable foreign key constraint for SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


file_table_map: dict[str, Any] = {
    TsvFileName.REFERENCE: Reference,
    TsvFileName.NAME: Name,
    TsvFileName.TAXON: Family,
    TsvFileName.TYPE_MATERIAL: TypeMaterial,
    TsvFileName.NAMES_RELATION: NameRelation,
}


class DbManager:
    """
    Manages database operations, including creating, dropping, and importing data from TSV files.
    """

    def __init__(
        self,
        engine: Engine | None = None,
        path_to_zip_file: str | None = None,
        force_download=False,
    ):
        """Initialize the DbManager with a database engine.

        Args:
            engine (Engine | None): SQLAlchemy engine. If None, a default SQLite engine is created.
            path_to_zip_file (str | None): Path to the zip file containing data. If None, uses default path.
            force_download (bool): Whether to force download the data.
        """
        if isinstance(engine, Engine):
            self.engine = engine
        else:
            self.engine = create_engine(DB_DEFAULT_CONNECTION_STR)
        self.Session = sessionmaker(bind=self.engine)
        self.path_to_zip_file = path_to_zip_file or PATH_TO_ZIP_FILE
        self.force_download = force_download

    @property
    def session(self) -> Session:
        """Get a new SQLAlchemy session.

        Returns:
            Session: SQLAlchemy session
        """
        return self.Session()

    def _set_path_to_zip_file(self, path_to_zip_file: str) -> None:
        """Set the path to the zip file. Mainly for testing purposes.

        Args:
            path_to_zip_file (str): Path to the zip file.
        """
        self.path_to_zip_file = path_to_zip_file

    def recreate_db(self) -> None:
        """Recreate the database by dropping and creating all tables."""
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        logger.info("Database recreated.")

    def import_data(
        self, force_download: bool = False, keep_files: bool = False
    ) -> dict[str, int]:
        """Import all data in database.
        Args:
            force_download (bool, optional): If True, will force download the data, even if
                files already exist. If False, it will skip the downloading part if files
                already exist locally. Defaults to False.
            keep_files (bool, optional): If True, downloaded files are kept after import.
                Defaults to False.
        Returns:
            Dict[str, int]: table=key and number of inserted=value
        """
        self.recreate_db()
        imported = {}

        if force_download or not os.path.exists(PATH_TO_TAXTREE_ZIP_FILE):
            os.makedirs(TAXTREE_DATA_FOLDER, exist_ok=True)
            urllib.request.urlretrieve(TAXTREE_DOWNLOAD_URL, PATH_TO_TAXTREE_ZIP_FILE)

        # NCBI Taxonomy
        # =============================================================================
        logger.info("Loading NCBI Taxonomy data for mapping families and names")
        with zipfile.ZipFile(PATH_TO_TAXTREE_ZIP_FILE, "r") as z:
            with z.open("rankedlineage.dmp") as f:
                df = pd.read_csv(
                    f,
                    sep=r"\t\|\t|\t\|$",
                    header=None,
                    usecols=[0, 1, 7],
                    names=RANKED_LINEAGE_COLUMNS,
                    engine="python",
                    index_col=False,
                    dtype=RANKED_LINEAGE_DTYPES,
                )
                df_tax = df[df["phylum"] == "Streptophyta"][["tax_id", "tax_name"]]
                df = None  # free memory

        # IPNI
        # =============================================================================

        if force_download or not os.path.exists(self.path_to_zip_file):
            os.makedirs(DATA_FOLDER, exist_ok=True)
            urllib.request.urlretrieve(DOWNLOAD_URL, self.path_to_zip_file)
            logger.info(f"{DOWNLOAD_URL} downloaded to {self.path_to_zip_file}")

        # -----------------------------------------------------------------------------
        # Reference
        # -----------------------------------------------------------------------------
        logger.info("Importing references")
        df_reference = self.get_dataframe(TsvFileName.REFERENCE, Reference)
        df_reference.to_sql(
            Reference.__tablename__, self.engine, if_exists="append", index=False
        )
        imported[Reference.__tablename__] = len(df_reference)
        df_reference = None  # free memory

        # -----------------------------------------------------------------------------
        # Family
        # -----------------------------------------------------------------------------
        logger.info("Importing families")
        with zipfile.ZipFile(self.path_to_zip_file, "r") as z:
            with z.open("Taxon.tsv") as f:
                df_nameid_family = (
                    pd.read_csv(
                        f,
                        sep="\t",
                        usecols=["col:family", "col:nameID"],
                    )
                    .dropna()
                    .drop_duplicates()
                    .rename(columns={"col:family": "family", "col:nameID": "id"})
                )
                # df_nameid_family: columns = family, id (foreign key to Name)

        # create a DataFrame for Family table
        # 1. get unique families
        # 2. map to NCBI tax_id
        # 3. insert into Family table
        df_family = df_nameid_family[["family"]].dropna().drop_duplicates()
        df_family = (
            df_family.merge(df_tax, left_on="family", right_on="tax_name", how="left")[
                ["family", "tax_id"]
            ]
            .reset_index(drop=True)
            .rename_axis("id")
            .rename(index=lambda i: i + 1)
        )
        df_family.to_sql(
            Family.__tablename__, self.engine, if_exists="append", index=True
        )
        imported[Family.__tablename__] = len(df_family)
        # -----------------------------------------------------------------------------
        # Name
        # -----------------------------------------------------------------------------
        logger.info("Importing names")
        df_family["family_id"] = df_family.index  # add foreign key for merging
        df_name_family = df_nameid_family.merge(
            df_family,
            how="inner",
            on="family",
        )[
            ["id", "family_id"]
        ]  # foreign key to Name (id) and Family (family_id)
        df_nameid_family = None  # free memory
        df_family = None  # free memory

        # -----------------------------------------------------------------------------
        # link is removed from Name model, because it is redundant (https://ipni.org/n/{id})
        df_name = self.get_dataframe(TsvFileName.NAME, Name).drop(columns=["link"])
        df_name = df_name.merge(
            df_name_family,
            how="left",
            on="id",
        )
        df_name_family = None  # free memory
        df_name = df_name.merge(
            df_tax, left_on="scientific_name", right_on="tax_name", how="left"
        ).drop(columns=["tax_name"])
        df_name["family_id"] = df_name["family_id"].astype("Int64")  # allow nulls
        df_name["tax_id"] = df_name["tax_id"].astype("Int64")  # allow nulls
        df_name.to_sql(Name.__tablename__, self.engine, if_exists="append", index=False)
        imported[Name.__tablename__] = len(df_name)
        df_name = None  # free memory

        # -----------------------------------------------------------------------------
        # TypeMaterial
        # -----------------------------------------------------------------------------
        logger.info("Importing type materials")
        df_type_material = self.get_dataframe(TsvFileName.TYPE_MATERIAL, TypeMaterial)
        df_location = (
            df_type_material[["locality", "latitude", "longitude"]]
            .drop_duplicates()
            .reset_index(drop=True)
            .rename_axis("id")
            .rename(index=lambda i: i + 1)
        )
        df_location.to_sql(
            Location.__tablename__, self.engine, if_exists="append", index=True
        )
        df_location["location_id"] = df_location.index  # add location_id for merging
        df_type_material = df_type_material.merge(
            df_location,
            how="left",
            on=["locality", "latitude", "longitude"],
        ).drop(
            columns=["locality", "latitude", "longitude"]
        )  # drop columns after merging
        df_location = None  # free memory
        df_type_material.to_sql(
            TypeMaterial.__tablename__, self.engine, if_exists="append", index=False
        )
        imported[TypeMaterial.__tablename__] = len(df_type_material)
        df_type_material = None  # free memory
        # -----------------------------------------------------------------------------
        # NameRelation
        # -----------------------------------------------------------------------------
        logger.info("Importing name relations")
        df_name_relation = self.get_dataframe(TsvFileName.NAMES_RELATION, NameRelation)
        df_name_relation.to_sql(
            NameRelation.__tablename__, self.engine, if_exists="append", index=False
        )
        imported[NameRelation.__tablename__] = len(df_name_relation)
        df_name_relation = None  # free memory

        if not keep_files:
            shutil.rmtree(self.path_to_zip_file)

        return imported

    def get_dataframe(self, tsv_file: str, model) -> pd.DataFrame:
        with zipfile.ZipFile(self.path_to_zip_file, "r") as z:
            with z.open(tsv_file) as f:
                df: pd.DataFrame = pd.read_csv(
                    f,
                    sep="\t",
                    low_memory=False,
                )
        if model == TypeMaterial:
            df.drop(columns=["col:ID"], inplace=True)
            df["col:remarks"] = df["col:remarks"].replace(float("nan"), None)
            df["col:date"] = df["col:date"].map(parse_date)  # type: ignore

        df = get_cleaned_and_standardized_dataframe(df)

        if model == NameRelation:
            # For NameRelation, we need to ensure that the related_name_id and name_id
            # have a corresponding entry in the Name table.
            with zipfile.ZipFile(self.path_to_zip_file, "r") as z:
                with z.open(TsvFileName.NAME) as f:
                    df_name_id = pd.read_csv(
                        f,
                        sep="\t",
                        usecols=["col:ID"],
                    ).rename(columns={"col:ID": "name_id"})
            df = df[
                df.related_name_id.isin(df_name_id.name_id)
                & df.name_id.isin(df_name_id.name_id)
            ]
        if not df.empty:
            return df
        else:
            raise ValueError(f"No data found in {tsv_file}")


def import_data(
    engine: Optional[Engine] = None,
    force_download: bool = False,
    keep_files: bool = False,
) -> dict[str, int]:
    """Import all data in database.

    Args:
        engine (Optional[Engine]): SQLAlchemy engine. Defaults to None.
        force_download (bool, optional): If True, will force download the data, even if
            files already exist. If False, it will skip the downloading part if files
            already exist locally. Defaults to False.
        keep_files (bool, optional): If True, downloaded files are kept after import.
            Defaults to False.

    Returns:
        Dict[str, int]: table=key and number of inserted=value
    """
    db_manager = DbManager(engine)
    return db_manager.import_data(force_download=force_download, keep_files=keep_files)


def get_session(engine: Optional[Engine] = None) -> Session:
    """Get a new SQLAlchemy session.

    Returns:
        Session: SQLAlchemy session
    """
    db_manager = DbManager(engine)
    return db_manager.session
