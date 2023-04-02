from sqlalchemy import Boolean, Column, Float, Integer, String, ForeignKey
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import PickleType

from app.database.session import Base

class Card(Base):
    __tablename__ = 'card'

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey('series.id'))
    episode_id = Column(Integer, ForeignKey('episode.id'))

    source_file = Column(String, nullable=False)
    card_file = Column(String, nullable=False)
    filesize = Column(Integer)

    card_type = Column(String, nullable=False)
    title_text = Column(String, nullable=False)
    season_text = Column(String, nullable=False)
    hide_season_text = Column(Boolean, nullable=False)
    episode_text = Column(String, nullable=False)
    hide_episode_text = Column(Boolean, nullable=False)

    font_file = Column(String, nullable=False)
    font_color = Column(String, nullable=False)
    font_size = Column(Float, nullable=False)
    font_kerning = Column(Float, nullable=False)
    font_stroke_width = Column(Float, nullable=False)
    font_interline_spacing = Column(Integer, nullable=False)
    font_vertical_shift = Column(Integer, nullable=False)
    
    blur = Column(Boolean, nullable=False)
    grayscale = Column(Boolean, nullable=False)

    extras = Column(MutableDict.as_mutable(PickleType), default={}, nullable=False)

    season_number = Column(Integer, default=0, nullable=False)
    episode_number = Column(Integer, default=0, nullable=False)
    absolute_number = Column(Integer, default=0)