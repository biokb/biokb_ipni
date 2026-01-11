# schemas.py
from datetime import date as date_type
from typing import Annotated, Literal, Optional
from unittest.mock import Base

from neo4j import Query
from pydantic import BaseModel, ConfigDict, Field


class OffsetLimit(BaseModel):
    limit: Annotated[int, Field(le=100)] = 10
    offset: int = 0


class CountOffsetLimit(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int


# -------------------------------------------------------------------
# Location Schemas
# -------------------------------------------------------------------
class LocationBase(BaseModel):
    locality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Location(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class LocationSearch(OffsetLimit):
    """Fields for searching location records."""

    id: Optional[int] = None
    locality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationSearchResult(CountOffsetLimit):
    results: list[Location]


# -------------------------------------------------------------------
# Name Schemas
# -------------------------------------------------------------------
class NameBase(BaseModel):
    """Shared fields for reading and creating Name records."""

    rank: str
    scientific_name: str
    authorship: Optional[str] = None
    status: Optional[str]
    published_in_year: Optional[int]
    published_in_page: Optional[int]
    remarks: Optional[str]
    reference_id: Optional[str] = None


class Name(NameBase):
    """Fields returned when reading a Name record from the DB."""

    model_config = ConfigDict(from_attributes=True)

    id: str


class NameSearch(OffsetLimit):
    """Fields for search."""

    id: Optional[str] = None
    rank: Optional[str] = None
    scientific_name: Optional[str] = None
    authorship: Optional[str] = None
    status: Optional[str] = None
    published_in_year: Optional[int] = None
    published_in_page: Optional[int] = None
    remarks: Optional[str] = None
    reference_id: Optional[str] = None


class NameSearchResult(BaseModel):
    calculate_with: Literal["exact", "levenshtein", "metaphone_jaro", "pattern_match"]
    scientific_name: str
    ipni_id: str
    similarity: float = Field(le=1.0)


# -------------------------------------------------------------------
# Name Detail
# -------------------------------------------------------------------
class NameDetail(BaseModel):
    """
    A custom schema to return extended metadata for a given name ID,
    including scientific name, reference title, family name, and
    collector/locality from TypeMaterial.
    """

    name_id: str
    scientific_name: str
    reference_title: Optional[str] = None
    family_name: Optional[str] = None
    collector: Optional[str] = None
    locality: Optional[str] = None


# -------------------------------------------------------------------
# Reference Schemas
# -------------------------------------------------------------------
class ReferenceBase(BaseModel):
    doi: Optional[str] = None
    alternative_id: Optional[str] = None
    citation: Optional[str] = None
    author: Optional[str] = None
    issued: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    page: Optional[str] = None
    issn: Optional[str] = None
    isbn: Optional[str] = None
    link: Optional[str] = None
    remarks: Optional[str] = None


class ReferenceCreate(ReferenceBase):
    id: str
    title: str


class Reference(ReferenceBase):
    id: str
    title: str
    name_ids: list[str]

    model_config = ConfigDict(from_attributes=True)


class ReferenceSearch(ReferenceBase, OffsetLimit):
    """Fields for searching references."""

    id: Optional[str] = None
    title: Optional[str] = None


class ReferenceSearchResult(CountOffsetLimit):
    results: list[Reference]


# -------------------------------------------------------------------
# Family Schemas
# -------------------------------------------------------------------
class FamilyBase(BaseModel):
    family: str
    tax_id: Optional[int] = None


class Family(FamilyBase):
    id: str

    # model_config = ConfigDict(from_attributes=True)


class FamilySearch(OffsetLimit):
    """Fields for searching family records."""

    id: Optional[str] = None
    family: Optional[str] = None
    tax_id: Optional[int] = None


class FamilySearchResult(CountOffsetLimit):
    results: list[Family]


# -------------------------------------------------------------------
# NameRelation Schemas
# -------------------------------------------------------------------
class NameRelationBase(BaseModel):

    type: str
    related_name_id: Optional[str] = None
    name_id: Optional[str] = None


class NameRelationCreate(NameRelationBase):
    pass


class NameRelation(NameRelationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class NameRelationSearch(OffsetLimit):
    """Fields for searching name relations."""

    id: Optional[int] = None
    type: Optional[str] = None
    related_name_id: Optional[str] = None
    name_id: Optional[str] = None


class NameRelationSearchResult(OffsetLimit):
    results: list[NameRelation]


# -------------------------------------------------------------------
# TypeMaterial Schemas
# -------------------------------------------------------------------
class TypeMaterialBase(BaseModel):
    citation: Optional[str] = None
    status: Optional[str] = None
    institution_code: Optional[str] = None
    catalog_number: Optional[str] = None
    collector: Optional[str] = None
    date: Optional[date_type] = None
    remarks: Optional[str] = None
    name_id: str


class TypeMaterial(TypeMaterialBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: Optional[int] = None


class TypeMaterialSearch(OffsetLimit):
    """Fields for searching type material records."""

    id: Optional[int] = None
    citation: Optional[str] = None
    status: Optional[str] = None
    institution_code: Optional[str] = None
    catalog_number: Optional[str] = None
    collector: Optional[str] = None
    date: Optional[date_type] = None
    locality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    remarks: Optional[str] = None
    name_id: Optional[str] = None


class TypeMaterialSearchResult(OffsetLimit):
    results: list[TypeMaterial]
