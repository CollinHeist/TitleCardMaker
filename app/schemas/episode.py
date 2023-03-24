from typing import Literal, Optional, Union

from pydantic import Field

from app.schemas.base import Base

class BaseEpisode(Base):
    season_number: int
    episode_number: int
    absolute_number: Optional[int] = Field(
        default=None,
        title='Absolute episode number',
        description='Absolute episode ordering of the episode',
    )
    title: str = Field(..., min_length=1)
    emby_id: Optional[int] = Field(default=None, title='Emby server ID')
    imdb_id: Optional[str] = Field(default=None, title='IMDb database ID')
    jellyfin_id: Optional[str] = Field(default=None, title='Jellyfin server ID')
    tmdb_id: Optional[int] = Field(default=None, title='TMDb database ID')
    tvdb_id: Optional[int] = Field(default=None, title='TVDb database ID')
    tvrage_id: Optional[int] = Field(default=None, title='TVRage database ID')
    
class NewEpisode(BaseEpisode):
    ...

class UpdateEpisode(Base):
    title: Optional[str] = Field(default=None)

class Episode(BaseEpisode):
    id: int
    series_id: int
    source_path: str
    card_path: str