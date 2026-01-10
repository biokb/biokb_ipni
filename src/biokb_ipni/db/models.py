"""Module defining the database models for the biokb_ipni application."""

from datetime import date as date_type
from typing import Optional

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from biokb_ipni.constants import PROJECT_NAME


class Base(DeclarativeBase):
    _prefix = PROJECT_NAME + "_"


class Name(Base):
    """Name model representing a scientific name in the database.

    Attributes:
        id (str): Primary key identifier for the name.
        rank (str): Taxonomic rank of the name.
        scientific_name (str): The scientific name.
        authorship (Optional[str]): Authorship information for the name.
        status (str): Status of the name (e.g., accepted, synonym).
        published_in_year (Optional[int]): Year the name was published.
        published_in_page (Optional[int]): Page number where the name was published.
        link (str): Unique link associated with the name.
        remarks (Optional[str]): Additional remarks about the name.
        reference_id (Optional[str]): Foreign key to the associated reference.
        taxon (Taxon): Relationship to the associated taxon.
        reference (Reference): Relationship to the associated reference.
        type_materials (list[TypeMaterial]): Relationship to associated type materials.
    """

    __tablename__ = Base._prefix + "name"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)

    rank: Mapped[str] = mapped_column(String(255))
    scientific_name: Mapped[str] = mapped_column(String(255), index=True)
    authorship: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(255))
    published_in_year: Mapped[Optional[int]]
    published_in_page: Mapped[Optional[int]]
    link: Mapped[str] = mapped_column(String(255), unique=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # foreign keys
    reference_id: Mapped[Optional[str]] = mapped_column(
        String(length=255).with_variant(
            VARCHAR(255, collation="utf8mb4_bin"), "mysql", "mariadb"
        ),
        ForeignKey(Base._prefix + "reference.id"),
    )
    # relationships
    taxon: Mapped["Taxon"] = relationship(back_populates="name")
    reference: Mapped["Reference"] = relationship(back_populates="names")
    type_materials: Mapped[list["TypeMaterial"]] = relationship(back_populates="name")

    # name_relations: Mapped[list["NameRelation"]] = relationship(
    #     foreign_keys="name_relation.id", back_populates="name"
    # )


class Reference(Base):
    """Reference model representing bibliographic references in the database.

    Attributes:
        id (str): Primary key identifier for the reference.
        doi (Optional[str]): Digital Object Identifier for the reference.
        alternative_id (Optional[str]): Alternative identifier for the reference.
        citation (Optional[str]): Citation string for the reference.
        title (str): Title of the reference.
        author (Optional[str]): Author(s) of the reference.
        issued (Optional[str]): Publication date of the reference.
        volume (Optional[str]): Volume number of the reference.
        issue (Optional[str]): Issue number of the reference.
        page (Optional[str]): Page numbers of the reference.
        issn (Optional[str]): ISSN of the reference.
        isbn (Optional[str]): ISBN of the reference.
        link (Optional[str]): URL link to the reference.
        remarks (Optional[str]): Additional remarks about the reference.
        names (list[Name]): Relationship to associated names."""

    __tablename__ = Base._prefix + "reference"

    id: Mapped[str] = mapped_column(
        String(length=255).with_variant(
            VARCHAR(255, collation="utf8mb4_bin"), "mysql", "mariadb"
        ),
        primary_key=True,
    )

    doi: Mapped[Optional[str]] = mapped_column(String(255))
    alternative_id: Mapped[Optional[str]] = mapped_column(String(255))
    citation: Mapped[Optional[str]] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(Text)
    author: Mapped[Optional[str]] = mapped_column(String(255))
    issued: Mapped[Optional[str]] = mapped_column(Text)
    volume: Mapped[Optional[str]] = mapped_column(String(255))
    issue: Mapped[Optional[str]] = mapped_column(String(255))
    page: Mapped[Optional[str]] = mapped_column(String(255))
    issn: Mapped[Optional[str]] = mapped_column(String(255))
    isbn: Mapped[Optional[str]] = mapped_column(String(255))
    link: Mapped[Optional[str]] = mapped_column(String(255))
    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # relationships
    names: Mapped[list[Name]] = relationship(back_populates="reference")


class Taxon(Base):
    """Taxon model representing taxonomic information in the database.

    Attributes:
        id (str): Primary key identifier for the taxon.
        provisional (bool): Indicates if the taxon is provisional.
        status (Optional[str]): Status of the taxon.
        family (Optional[str]): Family to which the taxon belongs.
        link (Optional[str]): URL link associated with the taxon.
        name_id (Optional[str]): Foreign key to the associated name.
        name (Name): Relationship to the associated name.
    """

    __tablename__ = Base._prefix + "taxon"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)

    provisional: Mapped[bool]
    status: Mapped[Optional[str]] = mapped_column(String(255))
    family: Mapped[Optional[str]] = mapped_column(String(255))
    link: Mapped[Optional[str]] = mapped_column(String(255))

    # foreign keys
    name_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey(Base._prefix + "name.id")
    )

    # relationships
    name: Mapped[Name] = relationship(back_populates="taxon")


class NameRelation(Base):
    """NameRelation model representing relationships between names in the database.

    Attributes:
        id (int): Primary key identifier for the name relation.
        type (str): Type of relationship between the names.
        related_name_id (Optional[str]): Foreign key to the related name.
        name_id (Optional[str]): Foreign key to the primary name.
        related_name (Name): Relationship to the related name.
        name (Name): Relationship to the primary name.
    """

    __tablename__ = Base._prefix + "name_relation"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    type: Mapped[str] = mapped_column(String(255))

    # foreign keys
    related_name_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey(Base._prefix + "name.id")
    )
    name_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey(Base._prefix + "name.id")
    )
    # relationships
    related_name: Mapped[Name] = relationship(foreign_keys=[related_name_id])
    name: Mapped[Name] = relationship(foreign_keys=[name_id])


class TypeMaterial(Base):
    """TypeMaterial model representing type material information in the database.

    Attributes:
        id (int): Primary key identifier for the type material.
        citation (Optional[str]): Citation for the type material.
        status (Optional[str]): Status of the type material.
        institution_code (Optional[str]): Institution code where the type material is held.
        catalog_number (Optional[str]): Catalog number of the type material.
        collector (Optional[str]): Collector of the type material.
        date (Optional[date_type]): Date of collection of the type material.
        locality (Optional[str]): Locality information of the type material.
        latitude (Optional[float]): Latitude coordinate of the collection site.
        longitude (Optional[float]): Longitude coordinate of the collection site.
        remarks (Optional[str]): Additional remarks about the type material.
        name_id (str): Foreign key to the associated name.
        name (Name): Relationship to the associated name.
    """

    __tablename__ = Base._prefix + "type_material"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    citation: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[Optional[str]] = mapped_column(String(255))
    institution_code: Mapped[Optional[str]] = mapped_column(String(255))
    catalog_number: Mapped[Optional[str]] = mapped_column(String(255))
    collector: Mapped[Optional[str]] = mapped_column(String(255))
    date: Mapped[Optional[date_type]] = mapped_column(Date)
    locality: Mapped[Optional[str]] = mapped_column(Text)
    latitude: Mapped[Optional[float]]
    longitude: Mapped[Optional[float]]
    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # foreign keys
    name_id: Mapped[str] = mapped_column(
        String(255), ForeignKey(Base._prefix + "name.id"), nullable=False
    )

    # relationships
    name: Mapped[Name] = relationship(back_populates="type_materials")
