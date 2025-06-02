import logging
import os
import shutil
from codecs import ignore_errors
from typing import Any

import pandas as pd
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from biokb_ipni.constants import (
    DB_DEFAULT_CONNECTION_STR,
    DEFAULT_PATH_UNZIPPED_DATA_FOLDER,
    TsvFileName,
)
from biokb_ipni.db.models import (
    Base,
    Name,
    NameRelation,
    Reference,
    Taxon,
    TypeMaterial,
)
from biokb_ipni.tools import (
    download_and_unzip,
    get_cleaned_and_standardized_dataframe,
    parse_date,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

file_table_map: dict[str, Any] = {
    TsvFileName.REFERENCE: Reference,
    TsvFileName.NAME: Name,
    TsvFileName.TAXON: Taxon,
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
        path_data_folder: str | None = None,
        force_download=False,
    ):
        """
        Initialize the DbManager with a database engine and path to the data files.

        If path_to_zip_file == None, latest version IPNI will be downloaded.

        Args:
            engine: SQLAlchemy database engine instance.
            path_to_zip_file (str): Path to the directory containing TSV files (unzipped).
        """
        if isinstance(engine, Engine):
            self.engine = engine
        else:
            self.engine = create_engine(DB_DEFAULT_CONNECTION_STR)
        self.Session = sessionmaker(bind=self.engine)
        self.path_data_folder = path_data_folder
        self.force_download = force_download

    def create_db(self):
        """Create all tables in the database."""
        Base.metadata.create_all(self.engine)

    def drop_db(self):
        """Drop all tables from the database."""
        Base.metadata.drop_all(self.engine)

    def recreate_db(self):
        """Recreate the database by dropping and creating all tables."""
        self.drop_db()
        self.create_db()
        logger.info("Database recreated.")

    def import_data(self) -> dict[str, int]:
        self.create_db()
        imported = {}
        if not self.path_data_folder:
            self.path_data_folder = download_and_unzip(self.force_download)

        self.recreate_db()

        for tsv_file, model in file_table_map.items():
            logger.info(f"Start import into {model.__tablename__}")
            number_of_imported_rows = self.import_model_data(tsv_file, model)
            if not number_of_imported_rows is None:
                imported[model.__tablename__] = number_of_imported_rows

        if self.path_data_folder == DEFAULT_PATH_UNZIPPED_DATA_FOLDER:
            shutil.rmtree(DEFAULT_PATH_UNZIPPED_DATA_FOLDER)

        logger.info("Data imported: %s", imported)
        return imported

    def import_model_data(self, tsv_file: str, model) -> int | None:
        """
        Imports data from a TSV file into the specified database model.
        Reads a TSV file, optionally processes the data based on the model type,
        cleans and standardizes the DataFrame, and appends the data to the corresponding
        database table.
        Args:
            tsv_file (str): The name of the TSV file to import.
            model: The SQLAlchemy model class representing the target database table.
        Returns:
            int | None: The number of rows inserted into the database, or None if the operation fails.
        Raises:
            FileNotFoundError: If the data folder is not set or does not exist.
        """

        if self.path_data_folder:
            file_path = os.path.join(self.path_data_folder, tsv_file)

            df = pd.read_csv(file_path, sep="\t", low_memory=False)
            if model == TypeMaterial:
                df.drop(columns=["col:ID"], inplace=True)
                df["col:remarks"] = df["col:remarks"].replace(float("nan"), None)
                df["col:date"] = df["col:date"].map(parse_date)  # type: ignore

            df = get_cleaned_and_standardized_dataframe(df)

            if model == NameRelation:
                # For NameRelation, we need to ensure that the related_name_id and name_id
                # have a corresponding entry in the Name table.
                df_name_id = pd.read_csv(
                    os.path.join(self.path_data_folder, TsvFileName.NAME),
                    sep="\t",
                    usecols=["col:ID"],
                ).rename(columns={"col:ID": "name_id"})
                df = df[
                    df.related_name_id.isin(df_name_id.name_id)
                    & df.name_id.isin(df_name_id.name_id)
                ]

            return df.to_sql(
                model.__tablename__,
                self.engine,
                if_exists="append",
                index=False,
            )
        else:
            raise FileNotFoundError(
                "No import folder exists. Init with `auto_load_data=True` or set `path_data_folder`"
            )
