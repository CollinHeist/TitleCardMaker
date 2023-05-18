from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Integer, Float, ForeignKey, String, JSON
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import relationship

from app.database.session import Base
from modules.EpisodeInfo2 import EpisodeInfo

class Episode(Base):
    __tablename__ = 'episode'

    # Referencial arguments
    id = Column(Integer, primary_key=True, index=True)
    font_id = Column(Integer, ForeignKey('font.id'))
    series_id = Column(Integer, ForeignKey('series.id'))
    template_id = Column(Integer, ForeignKey('template.id'))
    card = relationship('Card', back_populates='episode')
    font = relationship('Font', back_populates='episodes')
    series = relationship('Series', back_populates='episodes')
    templates = relationship('Template', back_populates='episodes')

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

    extras = Column(JSON, default=None)
    translations = Column(JSON, default={})

    image_source_attempts = Column(
        JSON,
        default={'Emby': 0, 'Jellyfin': 0, 'Plex': 0, 'TMDb': 0}
    )


    @hybrid_property
    def log_str(self) -> str:
        return f'Episode[{self.id}] {self.as_episode_info}'


    @hybrid_property
    def card_properties(self) -> dict[str, Any]:
        return {
            'episode_id': self.id,
            'template_id': self.template_id,
            'source_file': self.source_file,
            'card_file': self.card_file,
            'watched': self.watched,
            'season_number': self.season_number,
            'episode_number': self.episode_number,
            'absolute_number': self.absolute_number,
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
            series_directory: str) -> Path:

        if self.source_file is None:
            filename = f's{self.season_number}e{self.episode_number}.jpg'
            return Path(source_directory) / series_directory / filename

        return Path(source_directory) / series_directory / self.source_file