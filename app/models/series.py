from pathlib import Path
from re import sub as re_sub, IGNORECASE
from typing import Any

from sqlalchemy import (
    Boolean, Column, Float, ForeignKey, Integer, String, JSON, func
)

from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.dependencies import get_preferences
from app.models.template import SeriesTemplates

from modules.CleanPath import CleanPath
from modules.SeriesInfo import SeriesInfo

INTERNAL_ASSET_DIRECTORY = Path(__file__).parent.parent / 'assets'


def regex_replace(pattern, replacement, string):
    """Perform a Regex replacement with the given arguments"""

    return re_sub(pattern, replacement, string, IGNORECASE)


# pylint: disable=no-self-argument,comparison-with-callable
class Series(Base):
    """
    SQL Table that defines a Series. This contains any Series-level
    customizations, as well as relational objects to a linked Font, or
    Sync; as well as any Cards, Loaded assets, Episodes, or Templates.
    """

    __tablename__ = 'series'

    # Referencial arguments
    id = Column(Integer, primary_key=True)
    font_id = Column(Integer, ForeignKey('font.id'))
    font = relationship('Font', back_populates='series')
    sync_id = Column(Integer, ForeignKey('sync.id'), default=None)
    sync = relationship('Sync', back_populates='series')
    cards = relationship('Card', back_populates='series')
    loaded = relationship('Loaded', back_populates='series')
    episodes = relationship('Episode', back_populates='series')
    templates = relationship(
        'Template',
        secondary=SeriesTemplates.__table__,
        back_populates='series'
    )

    # Required arguments
    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    monitored = Column(Boolean, default=True, nullable=False)
    poster_file = Column(
        String,
        default=str(INTERNAL_ASSET_DIRECTORY/'placeholder.jpg')
    )
    poster_url = Column(String, default='/internal_assets/placeholder.jpg')

    # Series config arguments
    directory = Column(String, default=None)
    emby_library_name = Column(String, default=None)
    jellyfin_library_name = Column(String, default=None)
    plex_library_name = Column(String, default=None)
    card_filename_format = Column(String, default=None)
    episode_data_source = Column(String, default=None)
    sync_specials = Column(Boolean, default=None)
    skip_localized_images = Column(Boolean, default=None)
    translations = Column(MutableList.as_mutable(JSON), default=None)
    match_titles = Column(Boolean, default=True, nullable=False)

    # Database arguments
    emby_id = Column(Integer, default=None)
    imdb_id = Column(String, default=None)
    jellyfin_id = Column(String, default=None)
    sonarr_id = Column(String, default=None)
    tmdb_id = Column(Integer, default=None)
    tvdb_id = Column(Integer, default=None)
    tvrage_id = Column(Integer, default=None)

    # Font arguments
    font_color = Column(String, default=None)
    font_title_case = Column(String, default=None)
    font_size = Column(Float, default=None)
    font_kerning = Column(Float, default=None)
    font_stroke_width = Column(Float, default=None)
    font_interline_spacing = Column(Integer, default=None)
    font_interword_spacing = Column(Integer, default=None)
    font_vertical_shift = Column(Integer, default=None)

    # Card arguments
    card_type = Column(String, default=None)
    hide_season_text = Column(Boolean, default=None)
    season_titles = Column(MutableDict.as_mutable(JSON), default=None)
    hide_episode_text = Column(Boolean, default=None)
    episode_text_format = Column(String, default=None)
    unwatched_style = Column(String, default=None)
    watched_style = Column(String, default=None)
    extras = Column(MutableDict.as_mutable(JSON), default=None)


    # Columns from relationships
    @hybrid_property
    def episode_ids(self) -> list[int]:
        """
        ID's of any Episodes associated with this Series (rather than
        the ORM objects themselves).

        Returns:
            List of ID's for associated Episodes.
        """

        return [episode.id for episode in self.episodes]


    @hybrid_property
    def template_ids(self) -> list[int]:
        """
        ID's of any Templates associated with this Series (rather than
        the ORM objects themselves).

        Returns:
            List of ID's for associated Templates.
        """

        return [template.id for template in self.templates]


    @hybrid_property
    def full_name(self) -> str:
        """The full name of this Series formatted as Name (Year)"""

        return f'{self.name} ({self.year})'


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
    def sort_name(cls: 'Series'):
        """Class-expression of `sort_name` property."""

        return func.regex_replace(r'^(a|an|the)(\s)', '', func.lower(cls.name))


    @hybrid_property
    def small_poster_url(self) -> str:
        """URI to the small poster URL of this Series."""

        return f'/assets/{self.id}/poster-750.jpg'


    @hybrid_property
    def number_of_seasons(self) -> int:
        """Number of unique seasons in this Series' linked Episodes."""

        return len(set(episode.season_number for episode in self.episodes))


    @hybrid_property
    def episode_count(self) -> int:
        """Number of Episodes linked to this Series."""

        return len(self.episodes)


    @hybrid_property
    def card_count(self) -> int:
        """Number of Title Cards linked to this Series."""

        return len(self.cards)


    @hybrid_property
    def path_safe_name(self) -> str:
        """Name of this Series to be utilized in Path operations"""

        return str(CleanPath.sanitize_name(self.full_name))


    @hybrid_property
    def card_directory(self) -> Path:
        """Path-safe Card subdirectory for this Series."""

        if self.directory is None:
            directory = self.path_safe_name
        else:
            directory = self.directory

        return CleanPath(get_preferences().card_directory) / directory


    @hybrid_property
    def source_directory(self) -> str:
        """Path-safe source subdirectory for this Series."""

        return str(CleanPath(get_preferences().source_directory) / self.path_safe_name)


    @hybrid_property
    def log_str(self) -> str:
        """
        Loggable string that defines this object (i.e. `__repr__`).
        """

        return f'Series[{self.id}] "{self.full_name}"'


    @hybrid_property
    def card_properties(self) -> dict[str, Any]:
        """
        Properties to utilize and merge in Title Card creation.

        Returns:
            Dictionary of properties.
        """

        return {
            'series_name': self.name,
            'series_full_name': self.full_name,
            'year': self.year,
            'card_filename_format': self.card_filename_format,
            'font_color': self.font_color,
            'font_title_case': self.font_title_case,
            'font_size': self.font_size,
            'font_kerning': self.font_kerning,
            'font_stroke_width': self.font_stroke_width,
            'font_interline_spacing': self.font_interline_spacing,
            'font_interword_spacing': self.font_interword_spacing,
            'font_vertical_shift': self.font_vertical_shift,
            'directory': self.directory,
            'card_type': self.card_type,
            'hide_season_text': self.hide_season_text,
            'season_titles': self.season_titles,
            'hide_episode_text': self.hide_episode_text,
            'episode_text_format': self.episode_text_format,
            'unwatched_style': self.unwatched_style,
            'watched_style': self.watched_style,
            'extras': self.extras,
            'series_emby_id': self.emby_id,
            'series_imdb_id': self.imdb_id,
            'series_jellyfin_id': self.jellyfin_id,
            'series_sonarr_id': self.sonarr_id,
            'series_tmdb_id': self.tmdb_id,
            'series_tvdb_id': self.tvdb_id,
            'series_tvrage_id': self.tvrage_id,
        }

    @hybrid_property
    def export_properties(self) -> dict[str, Any]:
        """
        Properties to export in Blueprints.

        Returns:
            Dictionary of the properties that can be used in an
            UpdateSeries model to modify this object.
        """

        if self.season_titles is None:
            st_ranges, st_values = None, None
        else:
            st_ranges = list(self.season_titles.keys())
            st_values = list(self.season_titles.values())

        if self.extras is None:
            ex_keys, ex_values = None, None
        else:
            ex_keys = list(self.extras.keys())
            ex_values = list(self.extras.values())

        return {
            'font_color': self.font_color,
            'font_title_case': self.font_title_case,
            'font_size': self.font_size,
            'font_kerning': self.font_kerning,
            'font_stroke_width': self.font_stroke_width,
            'font_interline_spacing': self.font_interline_spacing,
            'font_interword_spacing': self.font_interword_spacing,
            'font_vertical_shift': self.font_vertical_shift,
            'card_type': self.card_type,
            'hide_season_text': self.hide_season_text,
            'season_title_ranges': st_ranges,
            'season_title_values': st_values,
            'hide_episode_text': self.hide_episode_text,
            'episode_text_format': self.episode_text_format,
            'extra_keys': ex_keys,
            'extra_values': ex_values,
            'translations': self.translations,
        }


    @hybrid_property
    def image_source_properties(self) -> dict[str, Any]:
        """
        Properties to use in image source setting evaluations.

        Returns:
            Dictionary of properties.
        """

        return {
            'skip_localized_images': self.skip_localized_images,
        }


    @hybrid_property
    def as_series_info(self) -> SeriesInfo:
        """
        Represent this Series as a SeriesInfo object, including any
        database ID's.
        """

        return SeriesInfo(
            name=self.name,
            year=self.year,
            emby_id=self.emby_id,
            imdb_id=self.imdb_id,
            jellyfin_id=self.jellyfin_id,
            sonarr_id=self.sonarr_id,
            tmdb_id=self.tmdb_id,
            tvdb_id=self.tvdb_id,
            tvrage_id=self.tvrage_id,
        )


    @hybrid_method
    def comes_before(self, name: str) -> bool:
        """
        Whether the given name comes before this Series.

        Returns:
            True if the given `name` comes before this Series'
            alphabetically. False otherwise
        """

        return self.sort_name < name

    @comes_before.expression
    def comes_before(cls, name: str) -> bool:
        """Class expression of the `comes_before()` method."""

        return cls.sort_name < name


    @hybrid_method
    def comes_after(self, name: str) -> bool:
        """
        Whether the given name comes after this Series.

        Returns:
            True if the given `name` comes after this Series'
            alphabetically. False otherwise.
        """

        return self.sort_name > name

    @comes_after.expression # pylint: disable=no-self-argument
    def comes_after(cls, name: str) -> bool:
        """Class expression of the `comes_after()` method."""

        return cls.sort_name > name


    @hybrid_method
    def get_logo_file(self, source_base: str) -> Path:
        """
        Get the logo file for this series.

        Args:
            source_base: Base source directory.

        Returns:
            Path to the logo file that corresponds to this series' under
            the given base source directory.
        """

        return Path(source_base) / self.path_safe_name / 'logo.png'


    @hybrid_method
    def get_series_backdrop(self, source_base: str) -> Path:
        """
        Get the backdrop file for this series.

        Args:
            source_base: Base source directory.

        Returns:
            Path to the backdrop file that corresponds to this series'
            under the given base source directory.
        """

        return Path(source_base) / self.path_safe_name / 'backdrop.jpg'
