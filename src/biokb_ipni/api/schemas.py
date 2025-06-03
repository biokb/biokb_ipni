# schemas.py
from datetime import date as date_type
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


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
    link: Optional[str]
    remarks: Optional[str]
    reference_id: Optional[str] = None


class Name(NameBase):
    """Fields returned when reading a Name record from the DB."""

    model_config = ConfigDict(from_attributes=True)

    id: str


class NameSearch(BaseModel):
    """Fields for search."""

    id: Optional[str] = None
    rank: Optional[str] = None
    scientific_name: Optional[str] = None
    authorship: Optional[str] = None
    status: Optional[str] = None
    published_in_year: Optional[int] = None
    published_in_page: Optional[int] = None
    link: Optional[str] = None
    remarks: Optional[str] = None
    reference_id: Optional[str] = None


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
    title: str
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


class Reference(ReferenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


class ReferenceSearch(BaseModel):
    """Fields for searching references."""

    id: Optional[str] = None
    doi: Optional[str] = None
    alternative_id: Optional[str] = None
    citation: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    issued: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    page: Optional[str] = None
    issn: Optional[str] = None
    isbn: Optional[str] = None
    link: Optional[str] = None
    remarks: Optional[str] = None


# -------------------------------------------------------------------
# Taxon Schemas
# -------------------------------------------------------------------
class TaxonBase(BaseModel):
    provisional: bool
    status: Optional[str] = None
    family: str
    link: Optional[str] = None
    name_id: Optional[str] = None


class TaxonCreate(TaxonBase):
    id: str


class Taxon(TaxonBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


class TaxonSearch(BaseModel):
    """Fields for searching taxon records."""

    id: Optional[str] = None
    provisional: Optional[bool] = None
    status: Optional[str] = None
    family: Optional[str] = None
    link: Optional[str] = None
    name_id: Optional[str] = None


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


class NameRelationSearch(BaseModel):
    """Fields for searching name relations."""

    id: Optional[int] = None
    type: Optional[str] = None
    related_name_id: Optional[str] = None
    name_id: Optional[str] = None


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
    locality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    remarks: Optional[str] = None
    name_id: str


class TypeMaterialCreate(TypeMaterialBase):
    pass


class TypeMaterial(TypeMaterialBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class TypeMaterialSearch(BaseModel):
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
