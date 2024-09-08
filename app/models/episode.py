from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING, TypedDict

from sqlalchemy import Column, ForeignKey, String, JSON
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from app.dependencies import get_preferences
from app.database.session import Base
from app.models.template import EpisodeTemplates, Template
from app.schemas.connection import ServerName
from app.schemas.preferences import Style

from modules.Debug import log
from modules.EpisodeDataSource2 import WatchedStatus
from modules.EpisodeInfo2 import EpisodeInfo

if TYPE_CHECKING:
    from app.models.card import Card
    from app.models.font import Font
    from app.models.loaded import Loaded
    from app.models.series import Series


class Library(TypedDict): # pylint: disable=missing-class-docstring
    interface: ServerName
    interface_id: int
    name: str


class Episode(Base):
    """
    SQL Table that defines an Episode. This contains any Episode-level
    customizations, as well as relational objects to the parent Series,
    as well as any linked Font, Cards, Loaded records, or Templates.
    """

    __tablename__ = 'episode'

    # Referencial arguments
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    font_id: Mapped[Optional[int]] = mapped_column(ForeignKey('font.id'))
    series_id: Mapped[int] = mapped_column(ForeignKey('series.id'))

    cards: Mapped[list['Card']] = relationship(
        back_populates='episode',
        cascade='all,delete-orphan'
    )
    font: Mapped['Font'] = relationship(back_populates='episodes')
    series: Mapped['Series'] = relationship(back_populates='episodes')
    loaded: Mapped[list['Loaded']] = relationship(
        back_populates='episode',
        cascade='all,delete-orphan'
    )
    _templates: Mapped[list[EpisodeTemplates]] = relationship(
        EpisodeTemplates,
        back_populates='episode',
        cascade='all, delete-orphan',
        order_by=EpisodeTemplates.order,
    )
    templates: AssociationProxy[list[Template]] = association_proxy(
        '_templates', 'template',
        creator=lambda st: st,
    )

    source_file: Mapped[Optional[str]]
    card_file: Mapped[Optional[str]]
    watched_statuses: dict[str, bool] = Column(
        MutableDict.as_mutable(JSON),
        default={},
        nullable=False
    )

    season_number: Mapped[int]
    episode_number: Mapped[int]
    absolute_number: Mapped[Optional[int]]

    title: Mapped[str]
    match_title: Mapped[Optional[bool]]
    auto_split_title: Mapped[Optional[bool]] = mapped_column(default=None)

    card_type: Mapped[Optional[str]]
    hide_season_text: Mapped[Optional[bool]]
    season_text: Mapped[Optional[str]]
    hide_episode_text: Mapped[Optional[bool]]
    episode_text: Mapped[Optional[str]]
    unwatched_style: Mapped[Optional[Style]] = mapped_column(String, default=None)
    watched_style: Mapped[Optional[Style]] = mapped_column(String, default=None)

    font_color: Mapped[Optional[str]]
    font_size: Mapped[Optional[float]]
    font_kerning: Mapped[Optional[float]]
    font_stroke_width: Mapped[Optional[float]]
    font_interline_spacing: Mapped[Optional[int]]
    font_interword_spacing: Mapped[Optional[int]]
    font_vertical_shift: Mapped[Optional[int]]

    emby_id: Mapped[str]
    imdb_id: Mapped[Optional[str]]
    jellyfin_id: Mapped[str]
    tmdb_id: Mapped[Optional[int]]
    tvdb_id: Mapped[Optional[int]]
    tvrage_id: Mapped[Optional[int]]
    airdate: Mapped[Optional[datetime]]

    translations: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default={}
    )
    extras: Mapped[Optional[dict[str, Any]]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=None
    )


    def assign_templates(self,
            templates: list[Template],
            *,
            log: Logger = log,
        ) -> None:
        """
        Assign the given Templates to this Episode. This updates the
        association table for Episode:Template relationships as needed.

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
            existing = object_session(template).query(EpisodeTemplates)\
                .filter_by(episode_id=self.id,
                           template_id=template.id,
                           order=index)\
                .first()
            if existing:
                self.templates.append(existing)
            else:
                self.templates.append(EpisodeTemplates(
                    episode_id=self.id,
                    template_id=template.id,
                    order=index,
                ))

        log.debug(f'Episode[{self.id}].template_ids = {[t.id for t in templates]}')


    @property
    def template_ids(self) -> list[int]:
        """
        ID's of any Templates associated with this Episode (rather than
        the ORM objects themselves).
        """

        return [template.id for template in self.templates]


    @property
    def index_str(self) -> str:
        """Index string as sXXeYY for this Episode."""

        return f'S{self.season_number:02}E{self.episode_number:02}'


    def __repr__(self) -> str:
        return (
            f'{self.series.full_name} '
            f'S{self.season_number:02}E{self.episode_number:02}'
        )


    def get_card_properties(self, library: Optional[Library]) -> dict[str, Any]:
        """Properties to utilize and merge in Title Card creation."""

        eps = [(
            episode.season_number,
            episode.episode_number,
            episode.absolute_number
        ) for episode in self.series.episodes]
        # season_episode_count is the number of episodes in the season
        season_episode_count = len([e for e in eps if e[0]==self.season_number])
        # season_episode_max is the maximum episode number in the season
        season_episode_max =max(e[1] for e in eps if e[0] == self.season_number)
        # season_absolute_max is the maximum absolute number in the season
        season_absolute_max = max(
            (e[2] for e in eps
             if e[0] == self.season_number and e[2] is not None),
            default=0,
        )
        # series_episode_count is the total number of episodes in the series
        series_episode_count = len(eps)
        # series_episode_max is the maximum episode number in the series
        series_episode_max = max(e[1] for e in eps)
        # series_absolute_max is the maximum absolute number in the series
        series_absolute_max = max(
            (e[2] for e in eps if e[2] is not None),
            default=0,
        )

        # Add watched status
        watched = None
        if library:
            watched = self.get_watched_status(
                library['interface_id'], library['name']
            )

        return {
            'source_file': self.source_file,
            'card_file': self.card_file,
            'watched': watched,
            'title': self.translations.get('preferred_title', self.title),
            'match_title': self.match_title,
            'auto_split_title': self.auto_split_title,
            'card_type': self.card_type,
            'hide_season_text': self.hide_season_text,
            'season_text': self.season_text,
            'hide_episode_text': self.hide_episode_text,
            'episode_text': self.episode_text,
            'unwatched_style': self.unwatched_style,
            'watched_style': self.watched_style,
            'font_color': self.font_color,
            'font_size': self.font_size,
            'font_kerning': self.font_kerning,
            'font_stroke_width': self.font_stroke_width,
            'font_interline_spacing': self.font_interline_spacing,
            'font_interword_spacing': self.font_interword_spacing,
            'font_vertical_shift': self.font_vertical_shift,
            'extras': self.extras,
            'episode_emby_id': self.emby_id,
            'episode_imdb_id': self.imdb_id,
            'episode_jellyfin_id': self.jellyfin_id,
            'episode_tmdb_id': self.tmdb_id,
            'episode_tvdb_id': self.tvdb_id,
            'episode_tvrage_id': self.tvrage_id,
            'season_episode_count': season_episode_count,
            'season_episode_max': season_episode_max,
            'season_absolute_max': season_absolute_max,
            'series_episode_count': series_episode_count,
            'series_episode_max': series_episode_max,
            'series_absolute_max': series_absolute_max,
            **self.as_episode_info.characteristics, # pylint: disable=no-member
        }


    @property
    def export_properties(self) -> dict[str, Any]:
        """
        Properties to export in Blueprints that can be used in an
        UpdateEpisode model to modify this object.
        """

        if self.extras is None:
            ex_keys, ex_values = None, None
        else:
            ex_keys = list(self.extras.keys())
            ex_values = list(self.extras.values())

        return {
            'card_type': self.card_type,
            'match_title': self.match_title,
            'auto_split_title': self.auto_split_title,
            'hide_season_text': self.hide_season_text,
            'season_text': self.season_text,
            'hide_episode_text': self.hide_episode_text,
            'episode_text': self.episode_text,
            'font_id': self.font_id,
            'font_color': self.font_color,
            'font_size': self.font_size,
            'font_kerning': self.font_kerning,
            'font_stroke_width': self.font_stroke_width,
            'font_interline_spacing': self.font_interline_spacing,
            'font_interword_spacing': self.font_interword_spacing,
            'font_vertical_shift': self.font_vertical_shift,
            'extra_keys': ex_keys,
            'extra_values': ex_values,
        }


    @property
    def as_episode_info(self) -> EpisodeInfo:
        """
        The EpisodeInfo representation of this Episode created with this
        Episode's data - e.g. title, indices, database IDs, and airdate.
        """

        return EpisodeInfo(
            title=self.title,
            season_number=self.season_number,
            episode_number=self.episode_number,
            absolute_number=self.absolute_number,
            emby_id=self.emby_id,
            imdb_id=self.imdb_id,
            jellyfin_id=self.jellyfin_id,
            tmdb_id=self.tmdb_id,
            tvdb_id=self.tvdb_id,
            tvrage_id=self.tvrage_id,
            airdate=self.airdate,
        )


    def update_from_info(self, other: EpisodeInfo, log: Logger = log) -> bool:
        """
        Update this Episodes' database IDs from the given EpisodeInfo.

        >>> e = Episode(..., imdb_id='tt1234', emby_id='0:9876')
        >>> ei = EpisodeInfo(..., emby_id='1:456', tmdb_id=50,
                                  imdb_id='tt990')
        >>> e.update_from_info(ei)
        >>> e.imdb_id, e.emby_id, s.tmdb_id
        ('tt1234', '0:9876,1:456', 50)

        Args:
            other: Other set of info to merge into this.
            log: Logger for all log messages.

        Returns:
            Whether this object was changed.
        """

        info = self.as_episode_info
        info.copy_ids(other, log=log)

        changed = False
        for id_type, id_ in info.ids.items():
            if id_ and getattr(self, id_type) != id_:
                log.debug(f'{self}.{id_type} | {getattr(self, id_type)} -> {id_}')
                setattr(self, id_type, id_)
                changed = True

        return changed


    def remove_interface_ids(self, interface_id: int, /) -> bool:
        """
        Remove any database IDs associated with the given interface /
        Connection ID. This can update the `emby_id` and `jellyfin_id`
        attributes.

        Args:
            interface_id: ID of the interface whose IDs are being
                removed.

        Returns:
            Whether any ID attributes of this Episode were modified.
        """

        # Get EpisodeInfo representation
        episode_info: EpisodeInfo = self.as_episode_info

        # Delete from each InterfaceID
        changed = False
        if episode_info.emby_id.delete_interface_id(interface_id):
            self.emby_id = str(episode_info.emby_id)
            changed = True
        if episode_info.jellyfin_id.delete_interface_id(interface_id):
            self.jellyfin_id = str(episode_info.jellyfin_id)
            changed = True

        return changed


    def has_source_file(self, style: Style = 'unique') -> bool:
        """Whether this Episode's Source File exists."""

        return self.get_source_file(style).exists()


    def get_source_file(self, style: Style) -> Path:
        """
        Get the source file for this Episode based on the given
        attributes.

        Args:
            style: Effective Style for this episode.

        Returns:
            Fully resolved Path to the source file for this Episode.
        """

        # No manually specified source, use default based on style
        if (source_name := self.source_file) is None:
            if 'art' in style:
                source_name = 'backdrop.jpg'
            else:
                source_name = f's{self.season_number}e{self.episode_number}.jpg'

        # Return full path for this source base and Series
        return (get_preferences().source_directory \
            / self.series.path_safe_name \
            / source_name
        ).resolve()


    @property
    def watched_statuses_flat(self) -> dict[str, bool]:
        """
        Get a mapping of library names to watched statuses for this
        Episode. This is the flattened dictionary for each library name.

        >>> ep.watched_statuses = {'1:TV': True, '2:Anime': False}
        >>> ep.watched_statuses_flat
        {'TV': True, 'Anime': False}
        """

        return {
            key.split(':', maxsplit=1): watched
            for key, watched in self.watched_statuses
        }


    def get_watched_status(self,
            interface_id: int,
            library_name: str,
        ) -> Optional[bool]:
        """
        Get this Episode's watched status for the given library.

        Args:
            interface_id: ID of the interface associated with the
                library.
            library_name: Name of the library whose status to query.

        Returns:
            Whether this Episode has been watched within the given
            library. If there is no defined watched status, None is
            returned.
        """

        return self.watched_statuses.get(f'{interface_id}:{library_name}')


    def add_watched_status(self, status: WatchedStatus, /) -> bool:
        """
        Add the given WatchedStatus to this Episode's watched statuses.

        Args:
            status: The WatchedStatus to update this object with.

        Returns:
            Whether this Episode's watched status was modified.
        """

        # No watched status, skip
        if not status.has_status:
            return False

        # Watched status defined, update existing mapping
        if (key := status.db_key) in self.watched_statuses:
            current = self.watched_statuses.get(key)
            self.watched_statuses[key] = status.status
            return current != status.status

        # Interface has no mappings, add
        self.watched_statuses[key] = status.status
        return True


    def reset_card_config(self) -> None:
        """
        Reset this Episode to a "default" un-customized state. This only
        affects Card-related properties.
        """

        self.font_id = None
        self.templates = []
        self.card_type = None
        self.hide_season_text = None
        self.season_text = None
        self.hide_episode_text = None
        self.episode_text = None
        self.font_color = None
        self.font_size = None
        self.font_kerning = None
        self.font_stroke_width = None
        self.font_interline_spacing = None
        self.font_interword_spacing = None
        self.font_vertical_shift = None
        self.extras = {}
