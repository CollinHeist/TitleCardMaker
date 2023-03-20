from pathlib import Path

from json import dumps, loads
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType

from app.database.session import Base

BASE_PATH = Path('/mnt/user/Media/TitleCardMaker/')

def default_directory(context) -> str:
    params = context.get_current_parameters()
    return str(BASE_PATH / 'cards' / f'{params["name"]} ({params["year"]})')

class Series(Base):
    __tablename__ = 'series'

    # Required arguments
    id = Column(Integer, primary_key=True)
    name = Column(String)
    year = Column(Integer)
    poster_path = Column(String, default=str(BASE_PATH / 'app' / 'assets' / 'placeholder.jpg'))
    poster_url = Column(String, default='/assets/placeholder.jpg')

    # Optional SERIES arguments
    emby_library_name = Column(String, default=None)
    jellyfin_library_name = Column(String, default=None)
    plex_library_name = Column(String, default=None)
    filename_format = Column(String, default='{full_name} - S{season:02}E{episode:02}')
    episode_data_source = Column(String, default='Sonarr')
    image_source_priority = Column(MutableList.as_mutable(PickleType), default=['TMDb', 'Plex', 'Emby'])
    sync_specials = Column(Boolean, default=False)
    skip_localized_images = Column(Boolean, default=False)
    translations = Column(MutableList.as_mutable(PickleType), default=[])
    match_titles = Column(Boolean, default=True)

    # Database arguments
    emby_id = Column(Integer, default=None)
    imdb_id = Column(String, default=None)
    jellyfin_id = Column(String, default=None)
    sonarr_id = Column(String, default=None)
    tmdb_id = Column(Integer, default=None)
    tvdb_id = Column(Integer, default=None)
    tvrage_id = Column(Integer, default=None)

    # Optional CARD argument
    font_id = Column(Integer, ForeignKey('font.id'))
    template_id = Column(Integer, ForeignKey('template.id'))
    directory = Column(String, default=default_directory)
    card_type = Column(String, default='standard')
    hide_seasons = Column(Boolean, default=False)
    season_titles = Column(MutableList.as_mutable(PickleType), default=[])
    hide_episode_text = Column(Boolean, default=False)
    episode_text_format = Column(String, default='Episode {episode_number}')
    unwatched_style = Column(String, default='unique')
    watched_style = Column(String, default='unique')
    extras = Column(MutableList.as_mutable(PickleType), default=[])

    @hybrid_property
    def full_name(self) -> str:
        return f'{self.name} ({self.year})'