from re import sub as re_sub, IGNORECASE

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.database.session import BlueprintBase
from app.schemas.series import NewSeries
from modules.SeriesInfo import SeriesInfo


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
    name = Column(String, nullable=False)
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
        """Class-expression of `sort_name` property."""

        return func.regex_replace(r'^(a|an|the)(\s)', '', func.lower(cls.name))


    @hybrid_property
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


    @hybrid_property
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

    series: Mapped[BlueprintSeries] = relationship('BlueprintSeries', back_populates='blueprints')