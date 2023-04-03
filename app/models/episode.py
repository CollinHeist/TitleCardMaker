from typing import Any

from sqlalchemy import Boolean, Column, Integer, Float, ForeignKey, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy import PickleType

from app.database.session import Base
from app.dependencies import get_preferences
from modules.CleanPath import CleanPath

class Episode(Base):
    __tablename__ = 'episode'

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey('series.id'))
    template_id = Column(Integer, ForeignKey('template.id'))

    source_file = Column(String, default=None)
    card_file = Column(String, default=None)
    watched = Column(Boolean, default=None)

    season_number = Column(Integer, nullable=False)
    episode_number = Column(Integer, nullable=False)
    absolute_number = Column(Integer, default=None)

    title = Column(String, nullable=False)
    match_title = Column(Boolean, default=None)
    auto_split_title = Column(Boolean, default=True, nullable=False)

    hide_season_text = Column(Boolean, default=None)
    season_text = Column(String, default=None)
    hide_episode_text = Column(Boolean, default=None)
    episode_text = Column(String, default=None)
    unwatched_style = Column(String, default=None)
    watched_style = Column(String, default=None)

    font_id = Column(Integer, ForeignKey('font.id'))
    font_color = Column(String, default=None)
    font_title_case = Column(String, default=None)
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

    extras = Column(MutableDict.as_mutable(PickleType), default=None)

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
            'title': self.title,
            'match_title': self.match_title,
            'auto_split_title': self.auto_split_title,
            'hide_season_text': self.hide_season_text,
            'season_text': self.season_text,
            'hide_episode_text': self.hide_episode_text,
            'episode_text': self.episode_text,
            'unwatched_style': self.unwatched_style,
            'watched_style': self.watched_style,
            'font_id': self.font_id,
            'font_color': self.font_color,
            'font_title_case': self.font_title_case,
            'font_size': self.font_size,
            'font_kerning': self.font_kerning,
            'font_stroke_width': self.font_stroke_width,
            'font_interline_spacing': self.font_interline_spacing,
            'font_vertical_shift': self.font_vertical_shift,
            'extras': self.extras,
        }