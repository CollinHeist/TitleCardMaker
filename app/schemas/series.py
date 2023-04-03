from typing import Any, Literal, Optional, Union
from pathlib import Path

from pydantic import constr, Field, root_validator, validator

from app.schemas.base import Base, UNSPECIFIED, validate_argument_lists_to_dict
from app.schemas.font import TitleCase#, UpdateSeriesFont
from app.schemas.preferences import EpisodeDataSource, ImageSourceToggle, Style

# Match absolute ranges (1-10), season numbers (1), episode ranges (s1e1-s1e10)
SeasonTitleRange = constr(regex=r'^(\d+-\d+)|(\d+)|(s\d+e\d+-s\d+e\d+)$')

class SortedImageSourceToggle(ImageSourceToggle):
    priority: int


#TODO Add validation for filename format string

"""
Base classes
"""
class BaseConfig(Base):
    name: Optional[str] = Field(..., min_length=1)
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

class BaseTemplate(BaseConfig):
    name: str = Field(..., min_length=1, title='Template name')
    hide_season_text: bool = Field(default=False)
    hide_episode_text: bool = Field(default=False)

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
    match_titles: bool = Field(default=True)
    
    hide_season_text: Optional[bool] = Field(default=None)
    hide_episode_text: Optional[bool] = Field(default=None)
    font_id: Optional[int] = Field(
        default=None,
        title='Font ID',
        description='ID of the Font applied to this series',
    )
    font_color: Optional[str] = Field(default=None)
    font_title_case: Optional[TitleCase] = Field(default=None)
    font_size: Optional[float] = Field(default=None)
    font_kerning: Optional[float] = Field(default=None)
    font_stroke_width: Optional[float] = Field(default=None)
    font_interline_spacing: Optional[int] = Field(default=None)
    font_vertical_shift: Optional[int] = Field(default=None)
    font_delete_missing: Optional[bool] = Field(default=None)

    emby_library_name: Optional[str] = Field(
        default=None,
        min_length=1, 
        title='Emby library name',
        description='Library within Emby with this series',
    )
    jellyfin_library_name: Optional[str] = Field(
        default=None,
        min_length=1, 
        title='Jellyfin library name',
        description='Library within Jellyfin with this series',
    )
    plex_library_name: Optional[str] = Field(
        default=None,
        min_length=1, 
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
    directory: Optional[str] = Field(
        default=None,
        title='Card directory',
        description='Top-level directory for all title cards of this series'
    )

class BaseUpdate(Base):
    name: Optional[str] = Field(default=UNSPECIFIED, min_length=1)
    font_id: Optional[int] = Field(default=UNSPECIFIED)
    sync_specials: Optional[bool] = Field(default=UNSPECIFIED)
    skip_localized_images: Optional[bool] = Field(default=UNSPECIFIED)
    filename_format: Optional[str] = Field(default=UNSPECIFIED)
    episode_data_source: Optional[EpisodeDataSource] = Field(default=UNSPECIFIED)
    translations: Optional[dict[str, str]] = Field(default=UNSPECIFIED)
    card_type: Optional[str] = Field(default=UNSPECIFIED)
    hide_season_text: Optional[bool] = Field(default=UNSPECIFIED)
    season_title_ranges: Optional[list[SeasonTitleRange]] = Field(default=UNSPECIFIED)
    season_title_values: Optional[list[str]] = Field(default=UNSPECIFIED)
    hide_episode_text: Optional[bool] = Field(default=UNSPECIFIED)
    unwatched_style: Optional[Style] = Field(default=UNSPECIFIED)
    watched_style: Optional[Style] = Field(default=UNSPECIFIED)
    episode_text_format: Optional[str] = Field(default=UNSPECIFIED)
    extra_keys: Optional[list[str]] = Field(default=UNSPECIFIED)
    extra_values: Optional[list[Any]] = Field(default=UNSPECIFIED)

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('season_title_ranges', 'season_title_values',
               'extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @root_validator
    def delete_unspecified_args(cls, values):
        delete_keys = [key for key, value in values.items() if value == UNSPECIFIED]
        for key in delete_keys:
            del values[key]

        return values

    @root_validator
    def validate_paired_lists(cls, values):
        # Season title ranges
        values = validate_argument_lists_to_dict(
            values, 'season titles',
            'season_title_ranges', 'season_title_values',
            output_key='season_titles'
        )
        # Extras
        return validate_argument_lists_to_dict(
            values, 'extras',
            'extra_keys', 'extra_values',
            output_key='extras',
        )

"""
Creation classes
"""
class NewTemplate(BaseTemplate):
    name: str = Field(..., min_length=1, title='Template name')
    season_title_ranges: list[SeasonTitleRange] = Field(default=[])
    season_title_values: list[str] = Field(default=[])
    extra_keys: list[str] = Field(default=[])
    extra_values: list[str] = Field(default=[])

    @validator('season_title_ranges', 'season_title_values',
               'extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @root_validator
    def validate_paired_lists(cls, values):
        # Season title ranges
        values = validate_argument_lists_to_dict(
            values, 'season titles',
            'season_title_ranges', 'season_title_values',
            output_key='season_titles'
        )
        # Extras
        return validate_argument_lists_to_dict(
            values, 'extras',
            'extra_keys', 'extra_values',
            output_key='extras',
        )

class NewSeries(BaseSeries):
    font_replacements_in: Optional[list[str]] = Field(default=None)
    font_replacements_out: Optional[list[str]] = Field(default=None)
    season_title_ranges: Optional[list[SeasonTitleRange]] = Field(default=None)
    season_title_values: Optional[list[str]] = Field(default=None)
    extra_keys: Optional[list[str]] = Field(default=None)
    extra_values: Optional[list[Any]] = Field(default=None)

    @validator('font_replacements_in', 'font_replacements_out',
               'season_title_ranges', 'season_title_values',
               'extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @root_validator
    def validate_paired_lists(cls, values):
        # Season title ranges
        values = validate_argument_lists_to_dict(
            values, 'season titles',
            'season_title_ranges', 'season_title_values',
            output_key='season_titles'
        )
        # Extras
        values = validate_argument_lists_to_dict(
            values, 'extras',
            'extra_keys', 'extra_values',
            output_key='extras',
        )
        # Character replacements
        return validate_argument_lists_to_dict(
            values, 'character replacements',
            'font_replacements_in', 'font_replacements_out',
            output_key='font_replacements'
        )

"""
Update classes
"""
class UpdateTemplate(BaseUpdate):
    name: str = Field(default=UNSPECIFIED, min_length=1)
    font_id: Optional[int] = Field(default=UNSPECIFIED)
    sync_specials: bool = Field(default=UNSPECIFIED)
    skip_localized_images: Optional[bool] = Field(default=UNSPECIFIED)
    filename_format: Optional[str] = Field(default=UNSPECIFIED)
    episode_data_source: Optional[EpisodeDataSource] = Field(default=UNSPECIFIED)
    translations: dict[str, str] = Field(default=UNSPECIFIED)
    card_type: Optional[str] = Field(default=UNSPECIFIED)
    hide_season_text: bool = Field(default=UNSPECIFIED)
    season_title_ranges: list[SeasonTitleRange] = Field(default=UNSPECIFIED)
    season_title_values: list[str] = Field(default=UNSPECIFIED)
    hide_episode_text: bool = Field(default=UNSPECIFIED)
    unwatched_style: Optional[Style] = Field(default=UNSPECIFIED)
    watched_style: Optional[Style] = Field(default=UNSPECIFIED)
    episode_text_format: Optional[str] = Field(default=UNSPECIFIED)
    extra_keys: list[str] = Field(default=UNSPECIFIED)
    extra_values: list[Any] = Field(default=UNSPECIFIED)

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('season_title_ranges', 'season_title_values',
               'extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        # Filter out empty strings - all arguments can accept empty lists
        return [val for val in ([v] if isinstance(v, str) else v) if val != '']

    @root_validator
    def delete_unspecified_args(cls, values):
        delete_keys = [key for key, value in values.items() if value == UNSPECIFIED]
        for key in delete_keys:
            del values[key]

        return values

    @root_validator
    def validate_paired_lists(cls, values):
        # Season title ranges
        values = validate_argument_lists_to_dict(
            values, 'season titles',
            'season_title_ranges', 'season_title_values',
            output_key='season_titles'
        )
        # Extras
        return validate_argument_lists_to_dict(
            values, 'extras',
            'extra_keys', 'extra_values',
            output_key='extras',
        )

class UpdateSeries(BaseUpdate):
    name: str = Field(default=UNSPECIFIED, min_length=1)
    year: int = Field(default=UNSPECIFIED, ge=1900)

    template_id: Optional[int] = Field(default=UNSPECIFIED)
    font_id: Optional[int] = Field(default=UNSPECIFIED)
    sync_specials: Optional[bool] = Field(default=UNSPECIFIED)
    skip_localized_images: Optional[bool] = Field(default=UNSPECIFIED)
    filename_format: Optional[str] = Field(default=UNSPECIFIED)
    episode_data_source: Optional[EpisodeDataSource] = Field(default=UNSPECIFIED)
    match_titles: bool = Field(default=UNSPECIFIED)
    translations: Optional[dict[str, str]] = Field(default=UNSPECIFIED)
    card_type: Optional[str] = Field(default=UNSPECIFIED)
    hide_season_text: Optional[bool] = Field(default=UNSPECIFIED)
    season_title_ranges: Optional[list[SeasonTitleRange]] = Field(default=UNSPECIFIED)
    season_title_values: Optional[list[str]] = Field(default=UNSPECIFIED)
    hide_episode_text: Optional[bool] = Field(default=UNSPECIFIED)
    unwatched_style: Optional[Style] = Field(default=UNSPECIFIED)
    watched_style: Optional[Style] = Field(default=UNSPECIFIED)
    episode_text_format: Optional[str] = Field(default=UNSPECIFIED)
    extra_keys: Optional[list[str]] = Field(default=UNSPECIFIED)
    extra_values: Optional[list[Any]] = Field(default=UNSPECIFIED)

    font_color: Optional[str] = Field(default=UNSPECIFIED)
    font_title_case: Optional[TitleCase] = Field(default=UNSPECIFIED)
    font_size: Optional[float] = Field(default=UNSPECIFIED)
    font_kerning: Optional[float] = Field(default=UNSPECIFIED)
    font_stroke_width: Optional[float] = Field(default=UNSPECIFIED)
    font_interline_spacing: Optional[int] = Field(default=UNSPECIFIED)
    font_vertical_shift: Optional[int] = Field(default=UNSPECIFIED)
    font_replacements_in: Optional[list[str]] = Field(default=UNSPECIFIED)
    font_replacements_out: Optional[list[str]] = Field(default=UNSPECIFIED)
    font_delete_missing: Optional[bool] = Field(default=UNSPECIFIED)

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
    directory: Optional[str] = Field(default=UNSPECIFIED)

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @root_validator
    def delete_unspecified_args(cls, values):
        delete_keys = [key for key, value in values.items() if value == UNSPECIFIED]
        for key in delete_keys:
            del values[key]

        return values

    @validator('font_replacements_in', 'font_replacements_out',
               'season_title_ranges', 'season_title_values',
               'extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @root_validator
    def validate_paired_lists(cls, values):
        # Season title ranges
        values = validate_argument_lists_to_dict(
            values, 'season titles',
            'season_title_ranges', 'season_title_values',
            output_key='season_titles'
        )
        # Extras
        values = validate_argument_lists_to_dict(
            values, 'extras',
            'extra_keys', 'extra_values',
            output_key='extras',
        )
        # Character replacements
        return validate_argument_lists_to_dict(
            values, 'character replacements',
            'font_replacements_in', 'font_replacements_out',
            output_key='font_replacements'
        )

"""
Return classes
"""
class Template(BaseTemplate):
    id: int
    season_titles: Optional[dict[str, str]]
    extras: Optional[dict[str, str]]

class Series(BaseSeries):
    id: int
    full_name: str
    poster_path: Optional[str]
    poster_url: str
    font_color: Optional[str]
    font_title_case: Optional[TitleCase]
    font_size: Optional[float]
    font_kerning: Optional[float]
    font_stroke_width: Optional[float]
    font_interline_spacing: Optional[int]
    font_vertical_shift: Optional[int]
    font_replacements: Optional[dict[str, str]]
    font_delete_missing: Optional[bool]
    season_titles: Optional[dict[str, str]]
    extras: Optional[dict[str, Any]]