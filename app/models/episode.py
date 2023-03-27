from sqlalchemy import Boolean, Column, Integer, Float, ForeignKey, String
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy import PickleType

from app.database.session import Base

def default_source(context) -> str:
    params = context.get_current_parameters()
    return f's{params["season_number"]}e{params["episode_number"]}.jpg'

def default_card(context) -> str:
    params = context.get_current_parameters()
    return f'card-s{params["season_number"]}e{params["episode_number"]}.jpg'

class Episode(Base):
    __tablename__ = 'episode'

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey('series.id'))
    template_id = Column(Integer, ForeignKey('template.id'))

    source_file_path = Column(String, default=default_source)
    card_file_path = Column(String, default=default_card)

    season_number = Column(Integer, nullable=False)
    episode_number = Column(Integer, nullable=False)
    absolute_number = Column(Integer, default=None)

    title = Column(String, nullable=False)
    match_title = Column(Boolean, default=None)

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