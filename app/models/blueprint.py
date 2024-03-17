# pylint: disable=no-self-argument
from datetime import datetime
from re import sub as re_sub, IGNORECASE
from typing import Optional

from sqlalchemy import Column, ForeignKey, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.database.session import BlueprintBase
from app.schemas.blueprint import ImportBlueprint
from app.schemas.series import NewSeries
from modules.SeriesInfo2 import SeriesInfo


def regex_replace(pattern, replacement, string):
    """Perform a Regex replacement with the given arguments"""

    return re_sub(pattern, replacement, string, IGNORECASE)


"""
The following SQL tables should not be a part of the primary SQL Base
Metadata. These tables should be part of a Blueprint SQL Metadata; as
these are only defined in the Blueprints SQL table.
"""
association_table = Table(
    'association_table',
    BlueprintBase.metadata,
    Column('blueprint_id', ForeignKey('blueprints.id'), primary_key=True),
    Column('set_id', ForeignKey('sets.id'), primary_key=True),
)

class BlueprintSeries(BlueprintBase):
    """
    SQL table for all Series directly tied to a Blueprint.
    """

    __tablename__ = 'series'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    year: Mapped[int]
    path_name: Mapped[str]
    imdb_id: Mapped[Optional[str]]
    tmdb_id: Mapped[Optional[int]]
    tvdb_id: Mapped[Optional[int]]
    blueprints: Mapped['Blueprint'] = relationship(back_populates='series')


    @hybrid_property
    def sort_name(self) -> str:
        """
        The sort-friendly name of this Series. This is lowercase with
        any prefix a/an/the removed.
        """

        return regex_replace(r'^(a|an|the)(\s)', '', self.name.lower())

    @sort_name.expression
    def sort_name(cls: 'BlueprintSeries'):
        """Class-expression of the `sort_name` property."""

        return func.regex_replace(r'^(a|an|the)(\s)', '', func.lower(cls.name))


    @hybrid_property
    def letter(self) -> str:
        """Letter subfolder for this Series."""

        return self.sort_name[0].upper()

    @letter.expression
    def letter(cls: 'BlueprintSeries'):
        """Class expression of the `letter` property."""

        return func.upper(cls.sort_name[0])


    @property
    def as_series_info(self) -> SeriesInfo:
        """
        Represent this Series as a SeriesInfo object, including any
        database ID's.
        """

        return SeriesInfo(
            name=self.name,
            year=self.year,
            imdb_id=self.imdb_id,
            tmdb_id=self.tmdb_id,
            tvdb_id=self.tvdb_id,
        )


    @property
    def as_new_series(self) -> NewSeries:
        """
        Get the `NewSeries` Pydantic model equivalent of this object.
        """

        return NewSeries(
            name=self.name,
            year=self.year,
            imdb_id=self.imdb_id,
            tmdb_id=self.tmdb_id,
            tvdb_id=self.tvdb_id,
        )


class Blueprint(BlueprintBase):
    """SQL table for all Blueprints."""

    __tablename__ = 'blueprints'

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(ForeignKey('series.id'))
    blueprint_number: Mapped[int]

    creator: Mapped[str]
    created: Mapped[datetime] = mapped_column(default=func.now)
    json: Mapped[str]

    series: Mapped[BlueprintSeries] = relationship(
        'BlueprintSeries',
        back_populates='blueprints'
    )
    sets: Mapped[list['BlueprintSet']] = relationship(
        secondary=association_table, back_populates='blueprints'
    )


    @property
    def blueprint(self) -> ImportBlueprint:
        """
        Attribute of the actual Blueprint (i.e. configurable options)
        for this object.
        """

        return ImportBlueprint.parse_raw(self.json)


    @property
    def set_ids(self) -> list[int]:
        """IDs of all Sets associated with this Blueprint"""

        return [bp_set.id for bp_set in self.sets]


    def get_folder(self, blueprint_repo_url: str) -> str:
        """
        Get the repo-URL subfolder associated with this Blueprint.

        Args:
            blueprint_repo_url: Base URL of the Blueprints repository.

        Returns:
            URL associated with this Blueprint.
        """

        return (
            f'{blueprint_repo_url}/{self.series.letter}/{self.series.path_name}'
            f'/{self.blueprint_number}'
        )


class BlueprintSet(BlueprintBase):
    """SQL table for all Sets of Blueprints."""

    __tablename__ = 'sets'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    blueprints: Mapped[list[Blueprint]] = relationship(
        secondary=association_table, back_populates='sets',
    )
