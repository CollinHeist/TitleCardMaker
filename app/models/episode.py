from logging import Logger
from pathlib import Path
from typing import Any, Optional, Union

from sqlalchemy import (
    Boolean, Column, DateTime, Integer, Float, ForeignKey, String, JSON
)
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, object_session, relationship

from app.database.session import Base
from app.models.template import EpisodeTemplates, Template
from app.schemas.preferences import Style

from modules.Debug import log
from modules.EpisodeDataSource2 import WatchedStatus
from modules.EpisodeInfo2 import EpisodeInfo
from modules.Debug import log


class Episode(Base):
    """
    SQL Table that defines an Episode. This contains any Episode-level
    customizations, as well as relational objects to the parent Series,
    as well as any linked Font, Cards, Loaded records, or Templates.
    """

    __tablename__ = 'episode'

    # Referencial arguments
    id = Column(Integer, primary_key=True, index=True)
    font_id = Column(Integer, ForeignKey('font.id'))
    series_id = Column(Integer, ForeignKey('series.id'))

    cards = relationship(
        'Card',
        back_populates='episode',
        cascade='all, delete-orphan'
    )
    font: Mapped['Font'] = relationship('Font', back_populates='episodes')
    series: Mapped['Series'] = relationship('Series', back_populates='episodes')
    loaded = relationship(
        'Loaded',
        back_populates='episode',
        cascade='all, delete-orphan'
    )
    _templates: Mapped[list[EpisodeTemplates]] = relationship(
        EpisodeTemplates,
        back_populates='episode',
        order_by=EpisodeTemplates.order,
        cascade='all, delete-orphan',
    )
    templates: AssociationProxy[list[Template]] = association_proxy(
        '_templates', 'template',
        creator=lambda st: st,
    )

    source_file = Column(String, default=None)
    card_file = Column(String, default=None)
    watched_statuses: dict[int, dict[str, bool]] = Column(
        MutableDict.as_mutable(JSON),
        default={},
        nullable=False
    )

    season_number = Column(Integer, nullable=False)
    episode_number = Column(Integer, nullable=False)
    absolute_number = Column(Integer, default=None)

    title = Column(String, nullable=False)
    match_title = Column(Boolean, default=None)
    auto_split_title = Column(Boolean, default=True, nullable=False)

    card_type = Column(String, default=None)
    hide_season_text = Column(Boolean, default=None)
    season_text = Column(String, default=None)
    hide_episode_text = Column(Boolean, default=None)
    episode_text = Column(String, default=None)
    unwatched_style = Column(String, default=None)
    watched_style = Column(String, default=None)

    font_color = Column(String, default=None)
    font_size = Column(Float, default=None)
    font_kerning = Column(Float, default=None)
    font_stroke_width = Column(Float, default=None)
    font_interline_spacing = Column(Integer, default=None)
    font_interword_spacing = Column(Integer, default=None)
    font_vertical_shift = Column(Integer, default=None)

    emby_id = Column(String, default=None)
    imdb_id = Column(String, default=None)
    jellyfin_id = Column(String, default=None)
    tmdb_id = Column(Integer, default=None)
    tvdb_id = Column(Integer, default=None)
    tvrage_id = Column(Integer, default=None)
    airdate = Column(DateTime, default=None)

    extras = Column(MutableDict.as_mutable(JSON), default=None)
    translations = Column(MutableDict.as_mutable(JSON), default={})

    image_source_attempts = Column(
        MutableDict.as_mutable(JSON),
        default={'Emby': 0, 'Jellyfin': 0, 'Plex': 0, 'TMDb': 0}
    )


    @hybrid_method
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


    # Relationship column properties
    @hybrid_property
    def template_ids(self) -> list[int]:
        """
        ID's of any Templates associated with this Episode (rather than
        the ORM objects themselves).

        Returns:
            List of ID's for associated Templates.
        """

        return [template.id for template in self.templates]


    @hybrid_property
    def index_str(self) -> str:
        """
        Index string as sXeY for this Episode.
        """

        return f'S{self.season_number:02}E{self.episode_number:02}'


    @hybrid_property
    def log_str(self) -> str:
        """
        Loggable string that defines this object (i.e. `__repr__`).
        """

        return f'Episode[{self.id}] {self.as_episode_info}'


    @hybrid_property
    def card_properties(self) -> dict[str, Any]:
        """
        Properties to utilize and merge in Title Card creation.

        Returns:
            Dictionary of properties.
        """

        return {
            'source_file': self.source_file,
            'card_file': self.card_file,
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
            **self.as_episode_info.characteristics,
        }


    @hybrid_property
    def export_properties(self) -> dict[str, Any]:
        """
        Properties to export in Blueprints.

        Returns:
            Dictionary of the properties that can be used in an
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
            'auto_split_title': False if not self.auto_split_title else None,
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


    @hybrid_property
    def as_episode_info(self) -> EpisodeInfo:
        """
        The EpisodeInfo representation of this Episode.

        Returns:
            EpisodeInfo created with this Episode's data - e.g. title,
            indices, database ID's, and airdate.
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


    @hybrid_method
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

        info: EpisodeInfo = self.as_episode_info
        info.copy_ids(other)

        changed = False
        for id_type, id_ in info.ids.items():
            if id_ and getattr(self, id_type) != id_:
                log.debug(f'{self.log_str}.{id_type} | {getattr(self, id_type)} -> {id_}')
                setattr(self, id_type, id_)
                changed = True

        return changed


    @hybrid_method
    def get_source_file(self,
            source_directory: Union[str, Path],
            style: Style,
        ) -> Path:
        """
        Get the source file for this Episode based on the given
        attributes.

        Args:
            source_directory: Root Source directory for all Series.
            series_directory: Series source directory for this specific
                Series.
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
        return (
            Path(source_directory) / self.series.path_safe_name / source_name
        ).resolve()
    

    @hybrid_property
    def watch_status_bools(self) -> list[bool]:
        """
        _summary_

        Returns:
            _description_
        """

        return [
            status
            for _, interface in self.watched_statuses.items()
            for _, status in interface.values()
        ]


    @hybrid_property
    def watched_statuses_flat(self) -> dict[str, bool]:
        """
        _summary_

        Returns:
            _description_
        """

        statuses = {}
        for _, interface in self.watched_statuses.items():
            for library_name, status in interface.items():
                statuses[library_name] = status

        return statuses


    @hybrid_method
    def get_watched_status(self,
            interface_id: int,
            library_name: str,
        ) -> Optional[bool]:
        """
        
        """

        return self.watched_statuses.get(interface_id, {}).get(library_name)


    @hybrid_method
    def add_watched_status(self, status: WatchedStatus, /) -> bool:
        """
        
        """

        # No watched status, skip
        if not status.has_status:
            return False

        # If this interface has existing mappings
        iid, lib = status.interface_id, status.library_name
        if iid in self.watched_statuses:
            # If this library has existing mappings, update and return diff
            if lib in self.watched_statuses[iid]:
                current = self.watched_statuses[iid][lib]
                self.watched_statuses[iid][lib] = status.status
                return current != status.status

            # Library has no mappings, add
            self.watched_statuses[iid][lib] = status.status
            return True

        # Interface has no mappings, add
        self.watched_statuses[iid] = {lib: status.status}
        return True
