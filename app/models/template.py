from pathlib import Path
from typing import Any

from json import dumps, loads
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy import PickleType

from app.database.session import Base

class Template(Base):
    __tablename__ = 'template'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    filename_format = Column(String, default=None)
    episode_data_source = Column(String, default=None)
    image_source_priority = Column(MutableList.as_mutable(PickleType), default=None)
    sync_specials = Column(Boolean, default=None)
    skip_localized_images = Column(Boolean, default=None)
    translations = Column(MutableList.as_mutable(PickleType), default=[])

    font_id = Column(Integer, ForeignKey('font.id'))
    card_type = Column(String, default=None)
    hide_season_text = Column(Boolean, default=None)
    season_titles = Column(MutableDict.as_mutable(PickleType), default={})
    hide_episode_text = Column(Boolean, default=None)
    episode_text_format = Column(String, default=None)
    unwatched_style = Column(String, default=None)
    watched_style = Column(String, default=None)
    extras = Column(MutableDict.as_mutable(PickleType), default={})

    @hybrid_property
    def card_properties(self) -> dict[str, Any]:
        return {
            'template_id': self.id,
            'template_name': self.name,
            'filename_format': self.filename_format,
            'font_id': self.font_id,
            'card_type': self.card_type,
            'hide_season_text': self.hide_season_text,
            'season_titles': self.season_titles,
            'hide_episode_text': self.hide_episode_text,
            'episode_text_format': self.episode_text_format,
            'unwatched_style': self.unwatched_style,
            'watched_style': self.watched_style,
            'extras': self.extras,
        }