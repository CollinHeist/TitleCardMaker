from typing import Literal, Optional, Union
from pathlib import Path

from app.schemas.base import Base
from app.schemas.preferences import EpisodeDataSource, ImageSourceToggle, Style

class SortedImageSourceToggle(ImageSourceToggle):
    priority: int


class SeasonTitle(Base):
    range: str
    title: str


class Template(Base):
    id: int
    name: str

    card_type: Optional[str]
    font_id: Optional[int]
    unwatched_style: Optional[Style]
    watched_style: Optional[Style]

    hide_seasons: bool
    season_titles: Optional[dict[str, str]]
    hide_episode_text: bool
    episode_text_format: Optional[str]

    sync_specials: Optional[bool]
    skip_localized_images: Optional[bool]
    filename_format: Optional[str]
    episode_data_source: Optional[EpisodeDataSource]
    # image_source_priority: Optional[list[str]]
    translations: Optional[list[dict[str, str]]]

    extras: Optional[dict[str, str]]
    

class Series(Base):
    id: int
    name: str
    year: int
    full_name: str
    poster_path: str
    poster_url: str
    emby_library_name: Optional[str]
    jellyfin_library_name: Optional[str]
    plex_library_name: Optional[str]
    directory: str

    template_id: Optional[int]
    font_id: Optional[int]

    emby_id: Optional[int]
    imdb_id: Optional[str]
    jellyfin_id: Optional[str]
    sonarr_id: Optional[str]
    tmdb_id: Optional[int]
    tvdb_id: Optional[int]
    tvrage_id: Optional[int]
        
    unwatched_style: Style
    watched_style: Style

    card_type: str
    hide_seasons: bool
    # season_titles: list[SeasonTitle]
    season_titles: dict[str, str]
    hide_episode_text: bool
    episode_text_format: str

    sync_specials: bool
    skip_localized_images: bool
    filename_format: str
    episode_data_source: EpisodeDataSource
    # image_source_priority: list[str]
    translations: list[dict[str, str]]

    extras: dict[str, str]