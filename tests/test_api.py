import os
from typing import Generator

from sqlalchemy.orm.session import Session

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from biokb_ipni.api.main import app, get_db
from biokb_ipni.db.manager import DbManager

# Create a new test database engine (SQLite in-memory for testing)
test_engine = create_engine("sqlite:///tests/db/test.db")
TestSessionLocal = sessionmaker(bind=test_engine)


# Dependency override to use test database
def override_get_db() -> Generator[Session, None, None]:
    db: Session = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the override to the FastAPI dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client_with_data() -> TestClient:
    # Create tables in the test database
    path_data_folder = os.path.join("tests", "data")
    dm = DbManager(engine=test_engine, path_data_folder=path_data_folder)
    dm.recreate_db()
    dm.import_data()
    return TestClient(app)


def test_server(client_with_data: TestClient) -> None:
    response = client_with_data.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Running!"}


class TestName:

    def test_get_name(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/name/1-1")
        assert response.status_code == 200
        data = response.json()
        expected = {
            "rank": "spec.",
            "scientific_name": "scientificName_1",
            "authorship": "authorship_1",
            "status": "status_1",
            "published_in_year": 2001,
            "published_in_page": 1,
            "link": "https://test.link/1",
            "remarks": "remarks_1",
            "reference_id": "referenceID_1",
            "id": "1-1",
        }
        assert data == expected

    def test_list_names(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/names/")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_list_names_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/names/?limit=10")
        assert response.status_code == 200
        assert len(response.json()) == 4

    def test_list_names_offset(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/names/?offset=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_names_offset_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/names/?offset=2&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        expected = {
            "id": "3-1",
            "rank": "spec.",
            "scientific_name": "scientificName_3",
            "authorship": "authorship_3",
            "status": "status_3",
            "published_in_year": 2003,
            "published_in_page": 3,
            "link": "https://test.link/3",
            "remarks": "remarks_3",
            "reference_id": "referenceID_3",
        }
        assert data[0] == expected


class TestNameRelation:

    def test_name_relation(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/name_relation/1")
        assert response.status_code == 200
        data = response.json()
        expected = {
            "id": 1,
            "name_id": "1-1",
            "related_name_id": "2-1",
            "type": "type_1",
        }
        assert data == expected

    def test_list_name_relations(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/name_relations/")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_name_relations_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/name_relations/?limit=4")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_name_relations_offset(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/name_relations/?offset=1")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_name_relation_offset_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/name_relations/?offset=1&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        expected = {
            "id": 2,
            "name_id": "1-1",
            "related_name_id": "3-1",
            "type": "type_1",
        }
        assert data[0] == expected


class TestReference:

    def test_get_reference(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/reference/1-1$v1")
        assert response.status_code == 200
        data = response.json()
        print(data)
        expected = {
            "doi": "doi_1",
            "alternative_id": "alternative_id_1",
            "citation": "citation_1",
            "title": "title_1",
            "author": "author_1",
            "issued": "issued_1",
            "volume": "volume_1",
            "issue": "issue_1",
            "page": "page_1",
            "issn": "issn_1",
            "isbn": "isbn_1",
            "link": "link_1",
            "remarks": "remarks_1",
            "id": "1-1$v1",
        }
        assert data == expected

    def test_list_references(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/references/")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_list_reference_limit(self, client_with_data: TestClient):
        response = client_with_data.get("/references/?limit=10")
        assert response.status_code == 200
        assert len(response.json()) == 4

    def test_list_references_offset(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/references/?offset=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_names_offset_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/references/?offset=2&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        expected = {
            "doi": "doi_3",
            "alternative_id": "alternative_id_3",
            "citation": "citation_3",
            "title": "title_3",
            "author": "author_3",
            "issued": "issued_3",
            "volume": "volume_3",
            "issue": "issue_3",
            "page": "page_3",
            "issn": "issn_3",
            "isbn": "isbn_3",
            "link": "link_3",
            "remarks": "remarks_3",
            "id": "3-1$v3",
        }
        assert data[0] == expected


class TestTaxon:

    def test_get_taxon(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/taxon/1-1")
        assert response.status_code == 200
        data = response.json()
        expected = {
            "provisional": True,
            "status": "status_1",
            "family": "family_1",
            "link": "http://link_1.test",
            "name_id": "1-1",
            "id": "1-1",
        }
        assert data == expected

    def test_list_taxons(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/taxons/")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_list_taxons_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/taxons/?limit=10")
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_list_taxons_offset(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/taxons/?offset=2")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_list_taxons_offset_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/taxons/?offset=2&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        expected = {
            "provisional": True,
            "status": "status_3",
            "family": "family_3",
            "link": "http://link_3.test",
            "name_id": "3-1",
            "id": "3-1",
        }
        assert data[0] == expected


class TestTypeMaterial:

    def test_get_type_material(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/type_material/1")
        assert response.status_code == 200
        data = response.json()
        expected = {
            "citation": "citation_1",
            "status": "status_1",
            "institution_code": "institution_code_1",
            "catalog_number": "catalog_number_1",
            "collector": "collector_1",
            "date": "1970-01-01",
            "locality": "locality_1",
            "latitude": 1.1,
            "longitude": 1.1,
            "remarks": "remarks_1",
            "name_id": "1-1",
            "id": 1,
        }
        assert data == expected

    def test_list_type_materials(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/type_materials/")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_list_type_materials_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/type_materials/?limit=4")
        assert response.status_code == 200
        assert len(response.json()) == 4

    def test_list_names_offset(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/type_materials/?offset=2")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_list_type_materials_offset_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/type_materials/?offset=2&limit=1")
        assert response.status_code == 200
        data = response.json()
        print(data)
        assert len(data) == 1
        expected = {
            "citation": "citation_3",
            "status": "status_3",
            "institution_code": "institution_code_3",
            "catalog_number": "catalog_number_3",
            "collector": "collector_3",
            "date": "1970-01-03",
            "locality": "locality_3",
            "latitude": 3.3,
            "longitude": 3.3,
            "remarks": "remarks_3",
            "name_id": "1-1",
            "id": 3,
        }
        assert data[0] == expected
