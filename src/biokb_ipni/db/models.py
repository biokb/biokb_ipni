"""Module defining the database models for the biokb_ipni application."""

from datetime import date as date_type
from typing import Any, Optional

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from biokb_ipni.constants import PROJECT_NAME


class Base(DeclarativeBase):
    _prefix = PROJECT_NAME + "_"


class Location(Base):
    """Location model representing geographical locations in the database.

    Attributes:
        id (int): Primary key identifier for the location.
        locality (Optional[str]): Locality description of the location.
        latitude (Optional[float]): Latitude coordinate of the location.
        longitude (Optional[float]): Longitude coordinate of the location.
    """

    __tablename__ = Base._prefix + "location"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    locality: Mapped[Optional[str]] = mapped_column(
        Text, comment="Locality description of the location"
    )
    latitude: Mapped[Optional[float]] = mapped_column(
        comment="Latitude coordinate of the location"
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        comment="Longitude coordinate of the location"
    )
    type_materials: Mapped[list["TypeMaterial"]] = relationship(
        back_populates="location"
    )


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
        remarks (Optional[str]): Additional remarks about the name.
        reference_id (Optional[str]): Foreign key to the associated reference.
        family_id (Optional[int]): Foreign key to the family.
        tax_id (Optional[int]): NCBI Taxon ID associated with the name.
        family (Family): Relationship to the associated family.
        reference (Reference): Relationship to the associated reference.
        type_materials (list[TypeMaterial]): Relationship to associated type materials.
        primary_relations (list[NameRelation]): Relationships where this name is the primary name.
        related_relations (list[NameRelation]): Relationships where this name is the related name.
    """

    __tablename__ = Base._prefix + "name"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, comment="Primary key identifier for the name"
    )

    rank: Mapped[str] = mapped_column(
        String(255), comment="Taxonomic rank of the name", index=True
    )
    scientific_name: Mapped[str] = mapped_column(
        String(255), index=True, comment="The scientific name"
    )
    authorship: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Authorship information for the name"
    )
    status: Mapped[str] = mapped_column(
        String(255), comment="Status of the name (e.g., accepted, synonym)", index=True
    )
    published_in_year: Mapped[Optional[int]] = mapped_column(
        comment="Year the name was published"
    )
    published_in_page: Mapped[Optional[int]] = mapped_column(
        comment="Page number where the name was published"
    )
    remarks: Mapped[Optional[str]] = mapped_column(
        Text, comment="Additional remarks about the name"
    )

    # foreign keys
    reference_id: Mapped[Optional[str]] = mapped_column(
        String(length=255).with_variant(
            VARCHAR(255, collation="utf8mb4_bin"), "mysql", "mariadb"
        ),
        ForeignKey(Base._prefix + "reference.id"),
        comment="Foreign key to the associated reference",
    )
    family_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Base._prefix + "family.id", comment="Foreign key to the family"),
        comment="Foreign key to the family",
    )
    tax_id: Mapped[Optional[int]] = mapped_column(
        comment="NCBI Taxon ID associated with the name"
    )

    # relationships
    family: Mapped["Family"] = relationship(back_populates="names")
    reference: Mapped["Reference"] = relationship(back_populates="names")
    type_materials: Mapped[list["TypeMaterial"]] = relationship(back_populates="name")

    primary_relations: Mapped[list["NameRelation"]] = relationship(
        back_populates="name",
        foreign_keys="NameRelation.name_id",
    )

    related_relations: Mapped[list["NameRelation"]] = relationship(
        back_populates="related_name",
        foreign_keys="NameRelation.related_name_id",
    )

    @property
    def family_name(self) -> str:
        """Get the family name associated with this name."""
        return self.family.family if self.family else ""

    def __repr__(self) -> str:
        return f"<Name:id={self.id!r}, scientific_name={self.scientific_name!r}>"


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
        names (list[Name]): Relationship to associated names.
    """

    __tablename__ = Base._prefix + "reference"

    id: Mapped[str] = mapped_column(
        String(length=255).with_variant(
            VARCHAR(255, collation="utf8mb4_bin"), "mysql", "mariadb"
        ),
        primary_key=True,
        comment="Primary key identifier for the reference",
    )

    doi: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Digital Object Identifier for the reference"
    )
    alternative_id: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Alternative identifier for the reference"
    )
    citation: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Citation string for the reference"
    )
    title: Mapped[str] = mapped_column(Text, comment="Title of the reference")
    author: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Author(s) of the reference"
    )
    issued: Mapped[Optional[str]] = mapped_column(
        Text, comment="Publication date of the reference"
    )
    volume: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Volume number of the reference"
    )
    issue: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Issue number of the reference"
    )
    page: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Page numbers of the reference"
    )
    issn: Mapped[Optional[str]] = mapped_column(
        String(255), comment="ISSN of the reference"
    )
    isbn: Mapped[Optional[str]] = mapped_column(
        String(255), comment="ISBN of the reference"
    )
    link: Mapped[Optional[str]] = mapped_column(
        String(255), comment="URL link to the reference"
    )
    remarks: Mapped[Optional[str]] = mapped_column(
        Text, comment="Additional remarks about the reference"
    )

    @property
    def names_short(self) -> list[dict[str, str]]:
        """Get a list of dicts with name and ID."""
        return [
            {"id": name.id, "scientific_name": name.scientific_name}
            for name in self.names
        ]

    @property
    def name_ids(self) -> list[str]:
        """Get a list of associated name IDs."""
        return [name.id for name in self.names]

    # relationships
    names: Mapped[list[Name]] = relationship(back_populates="reference")

    def __repr__(self) -> str:
        return f"<Reference:id={self.id!r}, title={self.title!r}>"


class Family(Base):
    """Family model representing family information in the database.

    Attributes:
        id (str): Primary key identifier for the family.
        family_name (str): Name of the family.
        tax_id (Optional[int]): NCBI Taxon ID associated with the family.
        names (list[Name]): Relationship to associated names.
    """

    __tablename__ = Base._prefix + "family"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, comment="Primary key identifier for the family"
    )
    family: Mapped[str] = mapped_column(String(255), comment="Name of the family")
    tax_id: Mapped[Optional[int]] = mapped_column(
        comment="NCBI Taxon ID associated with the family"
    )

    # relationships
    names: Mapped[list[Name]] = relationship(back_populates="family")

    @property
    def names_short(self) -> list[dict[str, str]]:
        """Get a list of dicts with name and ID."""
        return [
            {"id": name.id, "scientific_name": name.scientific_name}
            for name in self.names
        ]

    @property
    def name_ids(self) -> list[str]:
        """Get a list of associated name IDs."""
        return [name.id for name in self.names]

    def __repr__(self) -> str:
        return f"<Family:id={self.id!r}, family={self.family!r}>"


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

    type: Mapped[str] = mapped_column(
        String(255), comment="Type of relationship between the names", index=True
    )

    # foreign keys
    related_name_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey(Base._prefix + "name.id", comment="Foreign key to the related name"),
    )
    name_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey(Base._prefix + "name.id", comment="Foreign key to the primary name"),
    )
    # relationships
    name: Mapped[Name] = relationship(
        back_populates="primary_relations",
        foreign_keys=[name_id],
    )

    related_name: Mapped[Name] = relationship(
        back_populates="related_relations",
        foreign_keys=[related_name_id],
    )

    def __repr__(self) -> str:
        return f"<NameRelation:id={self.id!r}, type={self.type!r}, name_id={self.name_id!r}, related_name_id={self.related_name_id!r}>"


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
        remarks (Optional[str]): Additional remarks about the type material.
        name_id (str): Foreign key to the associated name.
        location_id (Optional[int]): Foreign key to the location.
        name (Name): Relationship to the associated name.
        location (Optional[Location]): Relationship to the location.

    """

    __tablename__ = Base._prefix + "type_material"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    citation: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Citation for the type material"
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Status of the type material"
    )
    institution_code: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Institution code where the type material is held"
    )
    catalog_number: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Catalog number of the type material"
    )
    collector: Mapped[Optional[str]] = mapped_column(
        String(255), comment="Collector of the type material"
    )
    date: Mapped[Optional[date_type]] = mapped_column(
        Date, comment="Date of collection of the type material"
    )
    remarks: Mapped[Optional[str]] = mapped_column(
        Text, comment="Additional remarks about the type material"
    )
    # foreign keys
    name_id: Mapped[str] = mapped_column(
        String(255), ForeignKey(Base._prefix + "name.id"), nullable=False
    )
    location_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Base._prefix + "location.id"), comment="Foreign key to the location"
    )

    # relationships
    name: Mapped[Name] = relationship(back_populates="type_materials")
    location: Mapped[Optional[Location]] = relationship(back_populates="type_materials")

    def __repr__(self) -> str:
        return f"<TypeMaterial:id={self.id!r}, status={self.status!r}, institution_code={self.institution_code!r}>"
