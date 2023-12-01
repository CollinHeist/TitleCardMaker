# pylint: disable=no-self-argument
from re import sub as re_sub, IGNORECASE

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, relationship
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
class BlueprintSeries(BlueprintBase):
    """
    SQL table for all Series directly tied to a Blueprint.
    """

    __tablename__ = 'series'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False) # Same as clean_name
    year = Column(Integer, nullable=False)
    path_name = Column(String, nullable=False)

    # Database arguments
    imdb_id = Column(String, default=None)
    tmdb_id = Column(Integer, default=None)
    tvdb_id = Column(Integer, default=None)

    blueprints = relationship('Blueprint', back_populates='series')


    @hybrid_property
    def sort_name(self) -> str:
        """
        The sort-friendly name of this Series.

        Returns:
            Sortable name. This is lowercase with any prefix a/an/the
            removed.
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
    """
    SQL table for all Blueprints.    
    """

    __tablename__ = 'blueprints'

    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey('series.id'))
    blueprint_number = Column(Integer, nullable=False)

    creator = Column(String, nullable=False)
    created = Column(DateTime, nullable=False, default=func.now)
    json = Column(String, nullable=False)

    series: Mapped[BlueprintSeries] = relationship(
        'BlueprintSeries',
        back_populates='blueprints'
    )


    @property
    def blueprint(self) -> ImportBlueprint:
        """
        Attribute of the actual Blueprint (i.e. configurable options)
        for this object.

        Returns:
            The Pydantic model creation of this object's raw blueprint
            JSON.
        """

        return ImportBlueprint.parse_raw(self.json)


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
