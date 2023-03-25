from typing import Literal, Optional, Union
from pathlib import Path

from pydantic import conint, Field, validator

from app.schemas.base import Base, UNSPECIFIED
from app.schemas.preferences import EpisodeDataSource, ImageSourceToggle, Style

class SortedImageSourceToggle(ImageSourceToggle):
    priority: int


class BaseConfig(Base):
    font_id: Optional[int] = Field(
        default=None,
        title='Font ID',
        description='ID of the Font to apply',
    )
    sync_specials: Optional[bool] = Field(
        default=None,
        title='Sync specials toggle',
        description='Whether to sync specials of this series'
    )
    skip_localized_images: Optional[bool] = Field(default=None)
    filename_format: Optional[str] = Field(default=None)
    episode_data_source: Optional[EpisodeDataSource] = Field(default=None)
    translations: Optional[dict[str, str]] = Field(default=None)
    card_type: Optional[str] = Field(
        default=None,
        title='Title card type',
        description='Type of title cards to create',
    )
    hide_season_text: Optional[bool] = Field(default=False)
    hide_episode_text: Optional[bool] = Field(default=None)
    unwatched_style: Optional[Style] = Field(
        default=None,
        title='Unwatched episode style',
        description='How to style unwatched episodes of this series',
    )
    watched_style: Optional[Style] = Field(
        default=None,
        title='Watched episode style',
        description='How to style watched episodes of this series',
    )
    episode_text_format: Optional[str] = Field(default=None)

class BaseSeries(BaseConfig):
    name: str = Field(..., min_length=1, title='Series name')
    year: int = Field(
        ...,
        ge=1900,
        title='Series year',
        description='Year the series first aired'
    )
    template_id: Optional[int] = Field(
        default=None,
        title='Template ID',
        description='ID of the Template applied to this series',
    )
    emby_library_name: Optional[str] = Field(
        default=None,
        title='Emby library name',
        description='Library within Emby with this series',
    )
    jellyfin_library_name: Optional[str] = Field(
        default=None,
        title='Jellyfin library name',
        description='Library within Jellyfin with this series',
    )
    plex_library_name: Optional[str] = Field(
        default=None,
        title='Plex library name',
        description='Library within Plex with this series',
    )
    emby_id: Optional[int] = Field(default=None, title='Emby server ID')
    imdb_id: Optional[str] = Field(default=None, title='IMDb database ID')
    jellyfin_id: Optional[str] = Field(default=None, title='Jellyfin server ID')
    sonarr_id: Optional[str] = Field(default=None, title='Sonarr server ID')
    tmdb_id: Optional[int] = Field(default=None, title='TMDb database ID')
    tvdb_id: Optional[int] = Field(default=None, title='TVDb database ID')
    tvrage_id: Optional[int] = Field(default=None, title='TVRage database ID')
    directory: str = Field(
        default=None,
        title='Card directory',
        description='Top-level directory for all title cards of this series'
    )

class BaseTemplate(BaseConfig):
    name: str = Field(..., min_length=1, title='Template name')

class NewSeries(BaseSeries):
    season_title_ranges: Optional[list[str]] = Field(default=[])
    season_title_values: Optional[list[str]] = Field(default=[])
    extra_keys: Optional[list[str]] = Field(default=[])
    extra_values: Optional[list[str]] = Field(default=[])

    @validator('season_title_ranges', 'season_title_values', 'extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

class NewTemplate(BaseTemplate):
    season_title_ranges: Optional[list[str]] = Field(default=None)
    season_title_values: Optional[list[str]] = Field(default=None)
    extra_keys: Optional[list[str]] = Field(default=None)
    extra_values: Optional[list[str]] = Field(default=None)

    @validator('season_title_ranges', 'season_title_values', 'extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

class UpdateBase(Base):
    font_id: Optional[int] = Field(default=UNSPECIFIED)
    sync_specials: Optional[bool] = Field(default=UNSPECIFIED)
    skip_localized_images: Optional[bool] = Field(default=UNSPECIFIED)
    filename_format: Optional[str] = Field(default=UNSPECIFIED)
    episode_data_source: Optional[EpisodeDataSource] = Field(default=UNSPECIFIED)
    translations: Optional[dict[str, str]] = Field(default=UNSPECIFIED)
    card_type: Optional[str] = Field(default=UNSPECIFIED)
    hide_season_text: Optional[bool] = Field(default=UNSPECIFIED)
    season_title_ranges: Optional[list[str]] = Field(default=UNSPECIFIED)
    season_title_values: Optional[list[str]] = Field(default=UNSPECIFIED)
    hide_episode_text: Optional[bool] = Field(default=UNSPECIFIED)
    unwatched_style: Optional[Style] = Field(default=UNSPECIFIED)
    watched_style: Optional[Style] = Field(default=UNSPECIFIED)
    episode_text_format: Optional[str] = Field(default=UNSPECIFIED)
    extra_keys: Optional[list[str]] = Field(default=UNSPECIFIED)
    extra_values: Optional[list[str]] = Field(default=UNSPECIFIED)

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('season_title_ranges', 'season_title_values', 'extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

class UpdateSeries(UpdateBase):
    name: Optional[str] = Field(default=UNSPECIFIED, min_length=1)
    year: Optional[int] = Field(default=UNSPECIFIED, ge=1900)
    template_id: Optional[int] = Field(default=UNSPECIFIED)
    emby_library_name: Optional[str] = Field(default=UNSPECIFIED)
    jellyfin_library_name: Optional[str] = Field(default=UNSPECIFIED)
    plex_library_name: Optional[str] = Field(default=UNSPECIFIED)
    emby_id: Optional[int] = Field(default=UNSPECIFIED)
    imdb_id: Optional[str] = Field(default=UNSPECIFIED)
    jellyfin_id: Optional[str] = Field(default=UNSPECIFIED)
    sonarr_id: Optional[str] = Field(default=UNSPECIFIED)
    tmdb_id: Optional[int] = Field(default=UNSPECIFIED)
    tvdb_id: Optional[int] = Field(default=UNSPECIFIED)
    tvrage_id: Optional[int] = Field(default=UNSPECIFIED)
    directory: str = Field(default=UNSPECIFIED)

class UpdateTemplate(UpdateBase):
    name: Optional[str] = Field(default=UNSPECIFIED, min_length=1)

class Series(BaseSeries):
    id: int
    full_name: str
    poster_path: str
    poster_url: str
    season_titles: dict[str, str]
    extras: dict[str, str]

class Template(BaseTemplate):
    id: int
    season_titles: Optional[dict[str, str]]
    extras: Optional[dict[str, str]]