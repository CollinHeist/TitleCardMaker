from pathlib import Path
from typing import Any

from json import dumps, loads
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy import PickleType

from app.database.session import Base
from app.dependencies import get_preferences
from modules.CleanPath import CleanPath

ASSET_DIRECTORY = Path(__file__).parent.parent / 'assets'

class Series(Base):
    __tablename__ = 'series'

    # Required arguments
    id = Column(Integer, primary_key=True)
    name = Column(String)
    year = Column(Integer)
    poster_path = Column(String, default=str(ASSET_DIRECTORY/'placeholder.jpg'))
    poster_url = Column(String, default='/assets/placeholder.jpg')

    # Series config arguments
    directory = Column(String, default=None)
    emby_library_name = Column(String, default=None)
    jellyfin_library_name = Column(String, default=None)
    plex_library_name = Column(String, default=None)
    filename_format = Column(String, default=None)
    episode_data_source = Column(String, default=None)
    sync_specials = Column(Boolean, default=None)
    skip_localized_images = Column(Boolean, default=None)
    translations = Column(MutableList.as_mutable(PickleType), default=None)
    match_titles = Column(Boolean, default=True)

    # Database arguments
    emby_id = Column(Integer, default=None)
    imdb_id = Column(String, default=None)
    jellyfin_id = Column(String, default=None)
    sonarr_id = Column(String, default=None)
    tmdb_id = Column(Integer, default=None)
    tvdb_id = Column(Integer, default=None)
    tvrage_id = Column(Integer, default=None)

    # Font arguments
    font_id = Column(Integer, ForeignKey('font.id'))
    font_color = Column(String, default=None)
    font_title_case = Column(String, default=None)
    font_size = Column(Float, default=None)
    font_kerning = Column(Float, default=None)
    font_stroke_width = Column(Float, default=None)
    font_interline_spacing = Column(Integer, default=None)
    font_vertical_shift = Column(Integer, default=None)
    font_delete_missing = Column(Boolean, default=None)
    font_replacements = Column(MutableDict.as_mutable(PickleType), default=None)

    # Card arguments
    template_id = Column(Integer, ForeignKey('template.id'))
    card_type = Column(String, default=None)
    hide_season_text = Column(Boolean, default=None)
    season_titles = Column(MutableDict.as_mutable(PickleType), default=None)
    hide_episode_text = Column(Boolean, default=None)
    episode_text_format = Column(String, default=None)
    unwatched_style = Column(String, default=None)
    watched_style = Column(String, default=None)
    extras = Column(MutableDict.as_mutable(PickleType), default=None)

    @hybrid_property
    def full_name(self) -> str:
        return f'{self.name} ({self.year})'

    @hybrid_property
    def path_safe_name(self) -> str:
        return CleanPath.sanitize_name(self.full_name)