from datetime import date as date_type
from typing import Optional

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ipni.constants import PROJECT_NAME

# TODO: Analyse if datatypes are OK


class Base(DeclarativeBase):
    _prefix = PROJECT_NAME + "_"


class Name(Base):
    __tablename__ = Base._prefix + "name"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)

    rank: Mapped[str] = mapped_column(String(255))
    scientific_name: Mapped[str] = mapped_column(String(255))
    authorship: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(255))
    published_in_year: Mapped[Optional[int]]
    published_in_page: Mapped[Optional[int]]
    link: Mapped[str] = mapped_column(String(255), unique=True)
    remarks: Mapped[Optional[str]] = mapped_column(String(255))

    # foreign keys
    reference_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey(Base._prefix + "reference.id")
    )
    # relationships
    taxon: Mapped["Taxon"] = relationship(back_populates="name")
    reference: Mapped["Reference"] = relationship(back_populates="names")
    type_materials: Mapped[list["TypeMaterial"]] = relationship(back_populates="name")

    # name_relations: Mapped[list["NameRelation"]] = relationship(
    #     foreign_keys="name_relation.id", back_populates="name"
    # )


class Reference(Base):
    __tablename__ = Base._prefix + "reference"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)

    doi: Mapped[Optional[str]] = mapped_column(String(255))
    alternative_id: Mapped[Optional[str]] = mapped_column(String(255))
    citation: Mapped[Optional[str]] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[Optional[str]] = mapped_column(String(255))
    issued: Mapped[Optional[str]] = mapped_column(String(255))
    volume: Mapped[Optional[str]] = mapped_column(String(255))
    issue: Mapped[Optional[str]] = mapped_column(String(255))
    page: Mapped[Optional[str]] = mapped_column(String(255))
    issn: Mapped[Optional[str]] = mapped_column(String(255))
    isbn: Mapped[Optional[str]] = mapped_column(String(255))
    link: Mapped[Optional[str]] = mapped_column(String(255))
    remarks: Mapped[Optional[str]] = mapped_column(String(255))

    # relationships
    names: Mapped[list[Name]] = relationship(back_populates="reference")


class Taxon(Base):
    __tablename__ = Base._prefix + "taxon"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)

    provisional: Mapped[bool]
    status: Mapped[Optional[str]] = mapped_column(String(255))
    family: Mapped[str] = mapped_column(String(255))
    link: Mapped[Optional[str]] = mapped_column(String(255))

    # foreign keys
    name_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey(Base._prefix + "name.id")
    )

    # relationships
    name: Mapped[Name] = relationship(back_populates="taxon")


class NameRelation(Base):
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
    __tablename__ = Base._prefix + "type_material"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    citation: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[Optional[str]] = mapped_column(String(255))
    institution_code: Mapped[Optional[str]] = mapped_column(String(255))
    catalog_number: Mapped[Optional[str]] = mapped_column(String(255))
    collector: Mapped[Optional[str]] = mapped_column(String(255))
    date: Mapped[Optional[date_type]] = mapped_column(Date)
    locality: Mapped[Optional[str]] = mapped_column(String(255))
    latitude: Mapped[Optional[float]]
    longitude: Mapped[Optional[float]]
    remarks: Mapped[Optional[str]] = mapped_column(String(255))

    # foreign keys
    name_id: Mapped[str] = mapped_column(
        String(255), ForeignKey(Base._prefix + "name.id"), nullable=False
    )

    # relationships
    name: Mapped[Name] = relationship(back_populates="type_materials")
