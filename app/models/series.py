from logging import Logger
from pathlib import Path
from re import sub as regex_replace, IGNORECASE
from typing import (
    Any, Iterator, Literal, Optional, TypedDict, Union, TYPE_CHECKING
)

from sqlalchemy import ColumnElement, ForeignKey, JSON, func
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship
from thefuzz.fuzz import partial_token_sort_ratio as partial_ratio

from app.database.session import Base
from app.dependencies import get_preferences
from app.models.template import SeriesTemplates, Template
from app.schemas.connection import ServerName
from modules.CleanPath import CleanPath
from modules.Debug import log
from modules.SeriesInfo2 import SeriesInfo

if TYPE_CHECKING:
    from app.models.card import Card
    from app.models.connection import Connection
    from app.models.episode import Episode
    from app.models.font import Font
    from app.models.loaded import Loaded
    from app.models.sync import Sync

# Return type of the library iterator
class Library(TypedDict): # pylint: disable=missing-class-docstring
    interface: ServerName
    interface_id: int
    name: str

INTERNAL_ASSET_DIRECTORY = Path(__file__).parent.parent / 'assets'


# pylint: disable=no-self-argument,comparison-with-callable
class Series(Base):
    """
    SQL Table that defines a Series. This contains any Series-level
    customizations, as well as relational objects to a linked Font, or
    Sync; as well as any Cards, Loaded assets, Episodes, or Templates.
    """

    __tablename__ = 'series'

    # Referencial arguments
    id: Mapped[int] = mapped_column(primary_key=True)
    data_source_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('connection.id'),
        default=None
    )
    font_id: Mapped[Optional[int]] = mapped_column(ForeignKey('font.id'), default=None)
    sync_id: Mapped[Optional[int]] = mapped_column(ForeignKey('sync.id'), default=None)

    cards: Mapped[list['Card']] = relationship(
        back_populates='series',
        cascade='all,delete-orphan',
    )
    data_source: Mapped['Connection'] = relationship(back_populates='series',)
    font: Mapped['Font'] = relationship(back_populates='series')
    sync: Mapped['Sync'] = relationship(back_populates='series')
    loaded: Mapped[list['Loaded']] = relationship(
        back_populates='series',
        cascade='all,delete-orphan',
    )
    episodes: Mapped[list['Episode']] = relationship(
        back_populates='series',
        cascade='all,delete-orphan',
    )
    _templates: Mapped[list[SeriesTemplates]] = relationship(
        SeriesTemplates,
        back_populates='series',
        order_by=SeriesTemplates.order,
        cascade='all, delete-orphan',
    )
    templates: AssociationProxy[list[Template]] = association_proxy(
        '_templates', 'template',
        creator=lambda st: st,
    )

    # Required arguments
    name: Mapped[str]
    year: Mapped[int]
    monitored: Mapped[bool]
    poster_file: Mapped[str] = mapped_column(
        default=str(INTERNAL_ASSET_DIRECTORY/'placeholder.jpg')
    )
    poster_url: Mapped[str] = mapped_column(default='/internal_assets/placeholder.jpg')

    # Series config arguments
    directory: Mapped[Optional[str]]
    libraries: Mapped[list[Library]] = mapped_column(
        MutableList.as_mutable(JSON),
        default=[]
    )
    card_filename_format: Mapped[Optional[str]]
    sync_specials: Mapped[Optional[bool]]
    skip_localized_images: Mapped[Optional[bool]]
    translations: Mapped[Optional[list[dict[str, str]]]] = mapped_column(
        MutableList.as_mutable(JSON),
        default=None
    )
    match_titles: Mapped[bool] = mapped_column(default=True)

    # Database arguments
    emby_id: Mapped[Optional[str]]
    imdb_id: Mapped[Optional[str]]
    jellyfin_id: Mapped[Optional[str]]
    sonarr_id: Mapped[Optional[str]]
    tmdb_id: Mapped[Optional[int]]
    tvdb_id: Mapped[Optional[int]]
    tvrage_id: Mapped[Optional[int]]

    # Font arguments
    font_color: Mapped[Optional[str]]
    font_title_case: Mapped[Optional[str]]
    font_size: Mapped[Optional[float]]
    font_kerning: Mapped[Optional[float]]
    font_stroke_width: Mapped[Optional[float]]
    font_interline_spacing: Mapped[Optional[int]]
    font_interword_spacing: Mapped[Optional[int]]
    font_vertical_shift: Mapped[Optional[int]]

    # Card arguments
    card_type: Mapped[Optional[str]]
    hide_season_text: Mapped[Optional[bool]]
    season_titles: Mapped[Optional[dict[str, str]]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=None
    )
    hide_episode_text: Mapped[Optional[bool]]
    episode_text_format: Mapped[Optional[str]]
    unwatched_style: Mapped[Optional[str]]
    watched_style: Mapped[Optional[str]]
    extras: Mapped[Optional[dict[str, str]]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=None
    )


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'Series[{self.id}] {self.full_name}'


    # Columns from relationships
    @property
    def episode_ids(self) -> list[int]:
        """
        ID's of any Episodes associated with this Series (rather than
        the ORM objects themselves).

        Returns:
            List of ID's for associated Episodes.
        """

        return [episode.id for episode in self.episodes]


    def assign_templates(self,
            templates: list[Template],
            *,
            log: Logger = log,
        ) -> None:
        """
        Assign the given Templates to this Series. This updates the
        association table for Series:Template relationships as needed.

        Args:
            templates: List of Templates to assign to this object. The
                provided order is used for the creation of the
                association table objects so that order is preserved
                within the relationship.
            log: Logger for all log messages.
        """

        # Reset existing assocations
        self.templates = []
        for index, template in enumerate(templates):
            existing = object_session(template).query(SeriesTemplates)\
                .filter_by(series_id=self.id,
                           template_id=template.id,
                           order=index)\
                .first()
            if existing:
                self.templates.append(existing)
            else:
                self.templates.append(SeriesTemplates(
                    series_id=self.id,
                    template_id=template.id,
                    order=index,
                ))

        log.debug(f'Series[{self.id}].template_ids = {[t.id for t in templates]}')


    @property
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


    @full_name.expression
    def full_name(cls: 'Series') -> ColumnElement[str]:
        """Class-expression of `full_name` property."""

        return cls.name + '(' + cls.year + ')'


    @hybrid_property
    def sort_name(self) -> str:
        """
        The sort-friendly name of this Series.

        Returns:
            Sortable name. This is lowercase with any prefix a/an/the
            removed.
        """

        return regex_replace(
            r'^(a|an|the)(\s)', '', self.name.lower(), flags=IGNORECASE
        )

    @sort_name.expression
    def sort_name(cls: 'Series') -> ColumnElement[str]:
        """Class-expression of `sort_name` property."""

        return func.regex_replace(r'^(a|an|the)(\s)', '', func.lower(cls.name))


    @hybrid_method
    def diff_ratio(self, other: str) -> int:
        """
        Return the ratio of the most similar substring as a number
        between 0 and 100 but sorting the token before comparing.

        Args:
            other: String to compare against this Series' name.

        Returns:
            Difference ratio of the given string and this name. 0 being
            no match, 100 being perfect match.
        """

        return partial_ratio(self.name.lower(), other.lower())


    @diff_ratio.expression
    def diff_ratio(cls: 'Series', other: str) -> ColumnElement[int]:
        """Class expression of `diff_ratio` property."""

        return func.partial_ratio(func.lower(cls.name), other.lower())


    @hybrid_method
    def fuzzy_matches(self, other: str, threshold: int = 85) -> bool:
        """
        Determine whether the given name's fuzzy Levenshtein Distance
        exceeds the given match threshold.

        Args:
            other: Name being fuzzy-matched against.
            threshold: Requirement for a match. 0-100, 0 being all text
                matches; 100 being perfect match.

        Returns:
            True if the fuzzy match quantity of this Series' name and
            the given `other` name exceed the given threshold.
        """

        return partial_ratio(self.name.lower(), other.lower()) >= threshold

    @fuzzy_matches.expression
    def fuzzy_matches(
            cls: 'Series',
            other: str,
            threshold: int = 85,
        ) -> ColumnElement[bool]:
        """Class-expression of the `fuzzy_matches` method."""

        return func.partial_ratio(
            func.lower(cls.name), other.lower()
        ) >= threshold


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
    def comes_before(cls, name: str) -> ColumnElement[bool]:
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
    def comes_after(cls, name: str) -> ColumnElement[bool]:
        """Class expression of the `comes_after()` method."""

        return cls.sort_name > name


    @property
    def small_poster_url(self) -> str:
        """URI to the small poster URL of this Series."""

        return f'/assets/{self.id}/poster-750.jpg'


    @property
    def number_of_seasons(self) -> int:
        """Number of unique seasons in this Series' linked Episodes."""

        return len(set(episode.season_number for episode in self.episodes))


    @property
    def episode_count(self) -> int:
        """Number of Episodes linked to this Series."""

        return len(self.episodes)


    @property
    def card_count(self) -> int:
        """Number of Title Cards linked to this Series."""

        return len(self.cards)


    @property
    def path_safe_name(self) -> str:
        """Name of this Series to be utilized in Path operations"""

        return str(CleanPath.sanitize_name(self.full_name))[:254]


    @property
    def card_directory(self) -> Path:
        """Path-safe Card subdirectory for this Series."""

        if self.directory is None:
            directory = self.path_safe_name
        else:
            directory = self.directory

        return CleanPath(get_preferences().card_directory) / directory


    @property
    def source_directory(self) -> str:
        """Path-safe source subdirectory for this Series."""

        return str(
            CleanPath(get_preferences().source_directory) / self.path_safe_name
        )


    @property
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

    @property
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

        match_titles = None if self.match_titles else self.match_titles

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
            'skip_localized_images': self.skip_localized_images,
            'match_titles': match_titles,
        }


    @property
    def image_source_properties(self) -> dict[str, Any]:
        """
        Properties to use in image source setting evaluations.

        Returns:
            Dictionary of properties.
        """

        return {
            'skip_localized_images': self.skip_localized_images,
        }


    @property
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
            match_titles=self.match_titles,
        )


    def update_from_series_info(self, other: SeriesInfo) -> bool:
        """
        Update this Series' database IDs from the given SeriesInfo.

        >>> s = Series(..., imdb_id='tt1234', sonarr_id='0:9876')
        >>> si = SeriesInfo(..., sonarr_id='1:456', tmdb_id=50,
                                 imdb_id='tt990')
        >>> s.update_from_series_info(si)
        >>> s.imdb_id, s.sonarr_id, s.tmdb_id
        ('tt1234', '0:9876,1:456', 50)

        Args:
            other: Other set of Series info to merge into this.

        Returns:
            Whether this object was changed.
        """

        info = self.as_series_info
        info.copy_ids(other)

        changed = False
        for id_type, id_ in info.ids.items():
            if id_ and getattr(self, id_type) != id_:
                setattr(self, id_type, id_)
                changed = True

        return changed


    def remove_interface_ids(self, interface_id: int) -> bool:
        """
        Remove any database IDs associated with the given interface /
        Connection ID. This can update the `emby_id`, `jellyfin_id`, and
        the `sonarr_id` attributes.

        Args:
            interface_id: ID of the interface whose IDs are being
                removed.

        Returns:
            Whether any ID attributes of this Episode were modified.
        """

        # Get SeriesInfo representation
        series_info: SeriesInfo = self.as_series_info

        # Delete from each InterfaceID
        changed = False
        if series_info.emby_id.delete_interface_id(interface_id):
            self.emby_id = str(series_info.emby_id)
            changed = True
        if series_info.jellyfin_id.delete_interface_id(interface_id):
            self.jellyfin_id = str(series_info.jellyfin_id)
            changed = True
        if series_info.sonarr_id.delete_interface_id(interface_id):
            self.sonarr_id = str(series_info.sonarr_id)
            changed = True

        return changed


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


    def get_libraries(self,
            interface: Union[int, Literal['Emby', 'Jellyfin', 'Plex']],
        ) -> Iterator[tuple[int, str]]:
        """
        Iterate over this Series' libraries of the given server type or
        interface ID.

        >>> s = Series(...)
        >>> s.libraries = [
            {'interface': 'Emby', 'interface_id': 0, 'name': 'TV'},
            {'interface': 'Plex', 'interface_id': 0, 'name': 'TV'},
            {'interface': 'Plex', 'interface_id': 1, 'name': 'Anime'},
        ]
        >>> list(s.get_libraries('Plex'))
        [(0, 'TV'), (1, 'Anime')]
        >>> list(s.get_libraries(1))
        [(1, 'Anime')]

        Args:
            interface: Interface type or ID whose libraries to yield.

        Yields:
            Tuple of the interface ID and library name.
        """

        for library in self.libraries:
            if ((isinstance(interface, int)
                    and library['interface_id'] == interface)
                or (isinstance(interface, str)
                    and library['interface'] == interface)):
                yield library['interface_id'], library['name']
