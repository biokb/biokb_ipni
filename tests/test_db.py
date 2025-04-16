import pandas as pd
import pytest
from sqlalchemy import create_engine

from ipni.db import models
from ipni.db.manager import DbManager


@pytest.fixture
def db_manager() -> DbManager:
    """
    Creates a temporary SQLite database for testing, creates all tables,
    and imports data from tests/data.
    """
    engine = create_engine(f"sqlite://")  # in memory
    db_manager = DbManager(engine=engine, path_data_folder="tests/data")
    return db_manager


class TestDbManager:
    def test_create_db(self, db_manager: DbManager):
        db_manager.create_db()
        tables = models.Base.metadata.tables.keys()
        print(tables)
        assert set(tables) == {
            "ipni_name",
            "ipni_reference",
            "ipni_taxon",
            "ipni_name_relation",
            "ipni_type_material",
        }

    def test_import_data(self, db_manager: DbManager):
        db_manager.import_data()
        with db_manager.Session() as session:
            assert session.query(models.Name).count() == 4
            assert session.query(models.NameRelation).count() == 2
            assert session.query(models.Reference).count() == 4
            assert session.query(models.Taxon).count() == 5
            assert session.query(models.TypeMaterial).count() == 6
