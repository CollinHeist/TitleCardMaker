from typing import Any, Literal, Optional

from pydantic import constr, Field, root_validator, validator

from app.models.template import OPERATIONS, ARGUMENT_KEYS
from app.schemas.base import Base, UpdateBase, UNSPECIFIED, validate_argument_lists_to_dict
from app.schemas.font import TitleCase
from app.schemas.ids import (
    EmbyID, IMDbID, JellyfinID, SonarrID, TMDbID, TVDbID, TVRageID
)
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
    card_filename_format: Optional[str] = Field(default=None)
    episode_data_source: Optional[EpisodeDataSource] = Field(default=None)
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
    hide_season_text: Optional[bool] = Field(default=None)
    hide_episode_text: Optional[bool] = Field(default=None)
    episode_text_format: Optional[str] = Field(default=None)

class BaseTemplate(BaseConfig):
    name: str = Field(..., min_length=1, title='Template name')
    filters: list[Condition] = Field(default=[])
    translations: Optional[list[Translation]] = Field(default=None)

class BaseSeries(BaseConfig):
    name: str = Field(..., min_length=1, title='Series name')
    year: int = Field(
        ...,
        ge=1900,
        title='Series year',
        description='Year the series first aired'
    )
    monitored: bool = Field(default=True)
    template_ids: Optional[list[int]] = Field(
        default=None,
        title='Template ID',
        description='ID of the Template applied to this series',
    )
    match_titles: bool = Field(default=True)
    translations: Optional[list[Translation]] = Field(default=None)

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
    emby_id: EmbyID = Field(default=None, title='Emby server ID')
    imdb_id: IMDbID = Field(default=None, title='IMDb database ID')
    jellyfin_id: JellyfinID = Field(default=None, title='Jellyfin server ID')
    sonarr_id: SonarrID = Field(default=None, title='Sonarr server ID')
    tmdb_id: TMDbID = Field(default=None, title='TMDb database ID')
    tvdb_id: TVDbID = Field(default=None, title='TVDb database ID')
    tvrage_id: TVRageID = Field(default=None, title='TVRage database ID')
    directory: Optional[str] = Field(
        default=None,
        title='Card directory',
        description='Top-level directory for all title cards of this series'
    )

class BaseUpdate(UpdateBase):
    name: Optional[str] = Field(default=UNSPECIFIED, min_length=1)
    monitored: bool = Field(default=UNSPECIFIED)
    font_id: Optional[int] = Field(default=UNSPECIFIED)
    sync_specials: Optional[bool] = Field(default=UNSPECIFIED)
    skip_localized_images: Optional[bool] = Field(default=UNSPECIFIED)
    card_filename_format: Optional[str] = Field(default=UNSPECIFIED)
    episode_data_source: Optional[EpisodeDataSource] = Field(default=UNSPECIFIED)
    translations: Optional[list[Translation]] = Field(default=UNSPECIFIED)
    card_type: Optional[str] = Field(default=UNSPECIFIED)
    hide_season_text: Optional[bool] = Field(default=UNSPECIFIED)
    season_title_ranges: Optional[list[SeasonTitleRange]] = Field(default=UNSPECIFIED)
    season_title_values: Optional[list[str]] = Field(default=UNSPECIFIED)
    hide_episode_text: Optional[bool] = Field(default=UNSPECIFIED)
    unwatched_style: Optional[Style] = Field(default=UNSPECIFIED)
    watched_style: Optional[Style] = Field(default=UNSPECIFIED)
    episode_text_format: Optional[str] = Field(default=UNSPECIFIED)
    extra_keys: Optional[list[DictKey]] = Field(default=UNSPECIFIED)
    extra_values: Optional[list[Any]] = Field(default=UNSPECIFIED)

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
    season_title_ranges: list[SeasonTitleRange] = Field(default=[])
    season_title_values: list[str] = Field(default=[])
    extra_keys: list[str] = Field(default=[])
    extra_values: list[Any] = Field(default=[])

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
    season_title_ranges: Optional[list[SeasonTitleRange]] = Field(default=None)
    season_title_values: Optional[list[str]] = Field(default=None)
    extra_keys: Optional[list[str]] = Field(default=None)
    extra_values: Optional[list[Any]] = Field(default=None)

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
    filters: list[Condition] = Field(default=UNSPECIFIED)
    season_title_ranges: list[SeasonTitleRange] = Field(default=UNSPECIFIED)
    season_title_values: list[str] = Field(default=UNSPECIFIED)
    extra_keys: list[DictKey] = Field(default=UNSPECIFIED)
    extra_values: list[Any] = Field(default=UNSPECIFIED)

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

    template_ids: Optional[list[int]] = Field(default=UNSPECIFIED)
    font_id: Optional[int] = Field(default=UNSPECIFIED)
    sync_specials: Optional[bool] = Field(default=UNSPECIFIED)
    skip_localized_images: Optional[bool] = Field(default=UNSPECIFIED)
    card_filename_format: Optional[str] = Field(default=UNSPECIFIED)
    episode_data_source: Optional[EpisodeDataSource] = Field(default=UNSPECIFIED)
    match_titles: bool = Field(default=UNSPECIFIED)
    translations: Optional[list[Translation]] = Field(default=UNSPECIFIED)
    card_type: Optional[str] = Field(default=UNSPECIFIED)
    hide_season_text: Optional[bool] = Field(default=UNSPECIFIED)
    season_title_ranges: Optional[list[SeasonTitleRange]] = Field(default=UNSPECIFIED)
    season_title_values: Optional[list[str]] = Field(default=UNSPECIFIED)
    hide_episode_text: Optional[bool] = Field(default=UNSPECIFIED)
    unwatched_style: Optional[Style] = Field(default=UNSPECIFIED)
    watched_style: Optional[Style] = Field(default=UNSPECIFIED)
    episode_text_format: Optional[str] = Field(default=UNSPECIFIED)
    extra_keys: Optional[list[DictKey]] = Field(default=UNSPECIFIED)
    extra_values: Optional[list[Any]] = Field(default=UNSPECIFIED)

    font_color: Optional[str] = Field(default=UNSPECIFIED)
    font_title_case: Optional[TitleCase] = Field(default=UNSPECIFIED)
    font_size: Optional[float] = Field(default=UNSPECIFIED)
    font_kerning: Optional[float] = Field(default=UNSPECIFIED)
    font_stroke_width: Optional[float] = Field(default=UNSPECIFIED)
    font_interline_spacing: Optional[int] = Field(default=UNSPECIFIED)
    font_vertical_shift: Optional[int] = Field(default=UNSPECIFIED)

    emby_library_name: Optional[str] = Field(default=UNSPECIFIED)
    jellyfin_library_name: Optional[str] = Field(default=UNSPECIFIED)
    plex_library_name: Optional[str] = Field(default=UNSPECIFIED)
    emby_id: EmbyID = Field(default=UNSPECIFIED)
    imdb_id: IMDbID = Field(default=UNSPECIFIED)
    jellyfin_id: JellyfinID = Field(default=UNSPECIFIED)
    sonarr_id: SonarrID = Field(default=UNSPECIFIED)
    tmdb_id: TMDbID = Field(default=UNSPECIFIED)
    tvdb_id: TVDbID = Field(default=UNSPECIFIED)
    tvrage_id: TVRageID = Field(default=UNSPECIFIED)
    
    directory: Optional[str] = Field(default=UNSPECIFIED)

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
class Template(BaseTemplate):
    id: int
    season_titles: dict[SeasonTitleRange, str]
    extras: dict[str, Any]

class Series(BaseSeries):
    id: int
    sync_id: Optional[int]
    full_name: str
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