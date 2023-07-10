from pathlib import Path
from typing import Any

from sqlalchemy import (
    Boolean, Column, DateTime, Integer, Float, ForeignKey, String, JSON
)
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.models.template import EpisodeTemplates
from app.schemas.preferences import Style

from modules.EpisodeInfo2 import EpisodeInfo

class Episode(Base):
    __tablename__ = 'episode'

    # Referencial arguments
    id = Column(Integer, primary_key=True, index=True)
    font_id = Column(Integer, ForeignKey('font.id'))
    font = relationship('Font', back_populates='episodes')
    series_id = Column(Integer, ForeignKey('series.id'))
    series = relationship('Series', back_populates='episodes')
    card = relationship('Card', back_populates='episode')
    loaded = relationship('Loaded', back_populates='episode')
    templates = relationship(
        'Template',
        secondary=EpisodeTemplates.__table__,
        back_populates='episodes'
    )
    
    source_file = Column(String, default=None)
    card_file = Column(String, default=None)
    watched = Column(Boolean, default=None)

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
    font_vertical_shift = Column(Integer, default=None)

    emby_id = Column(Integer, default=None)
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

    # Relationship column properties
    @hybrid_property
    def template_ids(self) -> list[int]:
        return [template.id for template in self.templates]


    @hybrid_property
    def index_str(self) -> str:
        return f'S{self.season_number:02}E{self.episode_number:02}'


    @hybrid_property
    def log_str(self) -> str:
        return f'Episode[{self.id}] {self.as_episode_info}'


    @hybrid_property
    def card_properties(self) -> dict[str, Any]:
        return {
            'source_file': self.source_file,
            'card_file': self.card_file,
            'watched': self.watched,
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
        return {
            'card_type': self.card_type,
            'match_title': self.match_title,
            'hide_season_text': self.hide_season_text,
            'season_text': self.season_text,
            'hide_episode_text': self.hide_episode_text,
            'episode_text': self.episode_text,
            'unwatched_style': self.unwatched_style,
            'watched_style': self.watched_style,
            'font_id': self.font_id,
            'font_color': self.font_color,
            'font_size': self.font_size,
            'font_kerning': self.font_kerning,
            'font_stroke_width': self.font_stroke_width,
            'font_interline_spacing': self.font_interline_spacing,
            'font_vertical_shift': self.font_vertical_shift,
            'extras': self.extras,
        }


    @hybrid_property
    def as_episode_info(self) -> EpisodeInfo:
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
    def get_source_file(self,
            source_directory: str,
            series_directory: str,
            style: Style
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
        if (source_file := self.source_file) is None:
            if 'art' in style:
                source_file = 'backdrop.jpg'
            else:
                source_file = f's{self.season_number}e{self.episode_number}.jpg'

        # Return full path for this source base and Series
        return (Path(source_directory) / series_directory / source_file).resolve()