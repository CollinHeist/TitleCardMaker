# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Any, Literal, Optional

from pydantic import constr, Field, root_validator, validator  # pylint: disable=no-name-in-module

from app.models.template import OPERATIONS, ARGUMENT_KEYS
from app.schemas.base import (
    Base, UpdateBase, UNSPECIFIED, validate_argument_lists_to_dict
)
from app.schemas.font import TitleCase
from app.schemas.ids import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.schemas.preferences import EpisodeDataSource, Style, LanguageCode

# Match absolute ranges (1-10), season numbers (1), episode ranges (s1e1-s1e10)
SeasonTitleRange = constr(regex=r'^(\d+-\d+)|^(\d+)|^(s\d+e\d+-s\d+e\d+)$')
DictKey = constr(regex=r'^[a-zA-Z]+[^ -]*$', min_length=1)

"""
Base classes
"""
FilterOperation = Literal[tuple(OPERATIONS.keys())]
FilterArgument = Literal[tuple(ARGUMENT_KEYS)]

class Condition(Base):
    argument: FilterArgument
    operation: FilterOperation
    reference: str

class Translation(Base):
    language_code: LanguageCode
    data_key: DictKey

class BaseConfig(Base):
    font_id: Optional[int] = None
    sync_specials: Optional[bool] = None
    skip_localized_images: Optional[bool] = None
    card_filename_format: Optional[str] = None
    episode_data_source: Optional[EpisodeDataSource] = None
    card_type: Optional[str] = None
    unwatched_style: Optional[Style] = None
    watched_style: Optional[Style] = None
    hide_season_text: Optional[bool] = None
    hide_episode_text: Optional[bool] = None
    episode_text_format: Optional[str] = None

class BaseTemplate(BaseConfig):
    name: str = Field(..., min_length=1, title='Template name')
    filters: list[Condition] = []
    translations: Optional[list[Translation]] = None

class BaseSeries(BaseConfig):
    name: str = Field(..., min_length=1, title='Series name')
    year: int = Field(
        ...,
        ge=1900,
        title='Series year',
        description='Year the series first aired'
    )
    monitored: bool = True
    template_ids: Optional[list[int]] = None
    match_titles: bool = True
    translations: Optional[list[Translation]] = None

    font_color: Optional[str] = None
    font_title_case: Optional[TitleCase] = None
    font_size: Optional[float] = None
    font_kerning: Optional[float] = None
    font_stroke_width: Optional[float] = None
    font_interline_spacing: Optional[int] = None
    font_vertical_shift: Optional[int] = None

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
    emby_id: EmbyID = None
    imdb_id: IMDbID = None
    jellyfin_id: JellyfinID = None
    sonarr_id: SonarrID = None
    tmdb_id: TMDbID = None
    tvdb_id: TVDbID = None
    tvrage_id: TVRageID = None
    directory: Optional[str] = None

class BaseUpdate(UpdateBase):
    name: Optional[str] = Field(default=UNSPECIFIED, min_length=1)
    monitored: bool = UNSPECIFIED
    font_id: Optional[int] = UNSPECIFIED
    sync_specials: Optional[bool] = UNSPECIFIED
    skip_localized_images: Optional[bool] = UNSPECIFIED
    card_filename_format: Optional[str] = UNSPECIFIED
    episode_data_source: Optional[EpisodeDataSource] = UNSPECIFIED
    translations: Optional[list[Translation]] = UNSPECIFIED
    card_type: Optional[str] = UNSPECIFIED
    hide_season_text: Optional[bool] = UNSPECIFIED
    season_title_ranges: Optional[list[SeasonTitleRange]] = UNSPECIFIED
    season_title_values: Optional[list[str]] = UNSPECIFIED
    hide_episode_text: Optional[bool] = UNSPECIFIED
    unwatched_style: Optional[Style] = UNSPECIFIED
    watched_style: Optional[Style] = UNSPECIFIED
    episode_text_format: Optional[str] = UNSPECIFIED
    extra_keys: Optional[list[DictKey]] = UNSPECIFIED
    extra_values: Optional[list[Any]] = UNSPECIFIED

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

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

"""
Creation classes
"""
class NewTemplate(BaseTemplate):
    name: str = Field(..., min_length=1, title='Template name')
    season_title_ranges: list[SeasonTitleRange] = []
    season_title_values: list[str] = []
    extra_keys: list[str] = []
    extra_values: list[Any] = []

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
    season_title_ranges: Optional[list[SeasonTitleRange]] = None
    season_title_values: Optional[list[str]] = None
    extra_keys: Optional[list[str]] = None
    extra_values: Optional[list[Any]] = None

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

"""
Update classes
"""
class UpdateTemplate(BaseUpdate):
    name: str = Field(default=UNSPECIFIED, min_length=1)
    filters: list[Condition] = UNSPECIFIED
    season_title_ranges: list[SeasonTitleRange] = UNSPECIFIED
    season_title_values: list[str] = UNSPECIFIED
    extra_keys: list[DictKey] = UNSPECIFIED
    extra_values: list[Any] = UNSPECIFIED

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('translations',
               'season_title_ranges', 'season_title_values',
               'extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        # Filter out empty strings - all arguments can accept empty lists
        return [val for val in ([v] if isinstance(v, str) else v) if val != '']

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

    template_ids: Optional[list[int]] = UNSPECIFIED
    font_id: Optional[int] = UNSPECIFIED
    sync_specials: Optional[bool] = UNSPECIFIED
    skip_localized_images: Optional[bool] = UNSPECIFIED
    card_filename_format: Optional[str] = UNSPECIFIED
    episode_data_source: Optional[EpisodeDataSource] = UNSPECIFIED
    match_titles: bool = UNSPECIFIED
    translations: Optional[list[Translation]] = UNSPECIFIED
    card_type: Optional[str] = UNSPECIFIED
    hide_season_text: Optional[bool] = UNSPECIFIED
    season_title_ranges: Optional[list[SeasonTitleRange]] = UNSPECIFIED
    season_title_values: Optional[list[str]] = UNSPECIFIED
    hide_episode_text: Optional[bool] = UNSPECIFIED
    unwatched_style: Optional[Style] = UNSPECIFIED
    watched_style: Optional[Style] = UNSPECIFIED
    episode_text_format: Optional[str] = UNSPECIFIED
    extra_keys: Optional[list[DictKey]] = UNSPECIFIED
    extra_values: Optional[list[Any]] = UNSPECIFIED

    font_color: Optional[str] = UNSPECIFIED
    font_title_case: Optional[TitleCase] = UNSPECIFIED
    font_size: Optional[float] = UNSPECIFIED
    font_kerning: Optional[float] = UNSPECIFIED
    font_stroke_width: Optional[float] = UNSPECIFIED
    font_interline_spacing: Optional[int] = UNSPECIFIED
    font_vertical_shift: Optional[int] = UNSPECIFIED

    emby_library_name: Optional[str] = UNSPECIFIED
    jellyfin_library_name: Optional[str] = UNSPECIFIED
    plex_library_name: Optional[str] = UNSPECIFIED
    emby_id: EmbyID = UNSPECIFIED
    imdb_id: IMDbID = UNSPECIFIED
    jellyfin_id: JellyfinID = UNSPECIFIED
    sonarr_id: SonarrID = UNSPECIFIED
    tmdb_id: TMDbID = UNSPECIFIED
    tvdb_id: TVDbID = UNSPECIFIED
    tvrage_id: TVRageID = UNSPECIFIED
    directory: Optional[str] = UNSPECIFIED

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('translations',
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
        return validate_argument_lists_to_dict(
            values, 'extras',
            'extra_keys', 'extra_values',
            output_key='extras',
        )

"""
Return classes
"""
class SearchResult(Base):
    title: str
    year: int
    overview: list[str] = ['No overview available']
    poster: Optional[str] = None
    ongoing: Optional[bool] = None
    emby_id: Any = None
    imdb_id: Any = None
    jellyfin_id: Any = None
    sonarr_id: Any = None
    tmdb_id: Any = None
    tvdb_id: Any = None
    tvrage_id: Any = None
    added: bool = False

class Template(BaseTemplate):
    id: int
    season_titles: dict[SeasonTitleRange, str]
    extras: dict[str, Any]

class Series(BaseSeries):
    id: int
    sync_id: Optional[int]
    full_name: str
    sort_name: str
    poster_path: Optional[str]
    poster_url: str
    small_poster_url: Optional[str]
    font_color: Optional[str]
    font_title_case: Optional[TitleCase]
    font_size: Optional[float]
    font_kerning: Optional[float]
    font_stroke_width: Optional[float]
    font_interline_spacing: Optional[int]
    font_vertical_shift: Optional[int]
    season_titles: Optional[dict[SeasonTitleRange, str]]
    extras: Optional[dict[str, Any]]
    # Don't error on ID validation errors
    emby_id: Any
    imdb_id: Any
    jellyfin_id: Any
    sonarr_id: Any
    tmdb_id: Any
    tvdb_id: Any
    tvrage_id: Any
