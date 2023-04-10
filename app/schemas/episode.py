from typing import Any, Literal, Optional, Union

from pydantic import Field, root_validator, validator

from app.schemas.base import Base, UNSPECIFIED, validate_argument_lists_to_dict
from app.schemas.preferences import Style

"""
Base classes
"""
...

"""
Creation classes
"""
class NewEpisode(Base):
    series_id: int = Field(..., description='ID of the Series this Episode belongs to')
    template_id: Optional[int] = Field(default=None, description='ID of the Template for this Episode')
    font_id: Optional[int] = Field(default=None, description='ID of the Font of this Episode')

    source_file: Optional[str] = Field(description='Path to the source image for this episode card')
    card_file: Optional[str] = Field(description='Path to the card for this episode')
    watched: Optional[bool] = Field(default=None, description='Whether this episode has been watched')

    season_number: int = Field(default=1)
    episode_number: int = Field(default=1)
    absolute_number: Optional[int] = Field(default=None)

    title: str = Field(...)
    match_title: Optional[bool] = Field(default=None)
    auto_split_title: bool = Field(default=True)

    card_type: Optional[str]
    hide_season_text: Optional[bool]
    season_text: Optional[str]
    hide_episode_text: Optional[bool]
    episode_text: Optional[str]
    unwatched_style: Optional[Style]
    watched_style: Optional[Style]

    font_color: Optional[str] = Field(default=None)
    font_size: Optional[float] = Field(default=None)
    font_kerning: Optional[float] = Field(default=None)
    font_stroke_width: Optional[float] = Field(default=None)
    font_interline_spacing: Optional[int] = Field(default=None)
    font_vertical_shift: Optional[int] = Field(default=None)

    emby_id: Optional[int] = Field(default=None)
    imdb_id: Optional[str] = Field(default=None)
    jellyfin_id: Optional[str] = Field(default=None)
    tmdb_id: Optional[int] = Field(default=None)
    tvdb_id: Optional[int] = Field(default=None)
    tvrage_id: Optional[int] = Field(default=None)

    extras: Optional[dict[str, str]] = Field(default=None)

"""
Update classes
"""
class UpdateEpisode(Base):
    template_id: Optional[int] = Field(default=UNSPECIFIED)
    font_id: Optional[int] = Field(default=UNSPECIFIED)

    source_file: Optional[str] = Field(default=UNSPECIFIED)
    card_file: Optional[str] = Field(default=UNSPECIFIED)
    watched: Optional[bool] = Field(default=UNSPECIFIED)

    season_number: int = Field(default=UNSPECIFIED)
    episode_number: int = Field(default=UNSPECIFIED)
    absolute_number: Optional[int] = Field(default=UNSPECIFIED)

    title: str = Field(default=UNSPECIFIED)
    match_title: Optional[bool] = Field(default=UNSPECIFIED)
    auto_split_title: bool = Field(default=UNSPECIFIED)

    card_type: Optional[str] = Field(default=UNSPECIFIED)
    hide_season_text: Optional[bool] = Field(default=UNSPECIFIED)
    season_text: Optional[str] = Field(default=UNSPECIFIED)
    hide_episode_text: Optional[bool] = Field(default=UNSPECIFIED)
    episode_text: Optional[str] = Field(default=UNSPECIFIED)
    unwatched_style: Optional[Style] = Field(default=UNSPECIFIED)
    watched_style: Optional[Style] = Field(default=UNSPECIFIED)

    font_color: Optional[str] = Field(default=UNSPECIFIED)
    font_size: Optional[float] = Field(default=UNSPECIFIED)
    font_kerning: Optional[float] = Field(default=UNSPECIFIED)
    font_stroke_width: Optional[float] = Field(default=UNSPECIFIED)
    font_interline_spacing: Optional[int] = Field(default=UNSPECIFIED)
    font_vertical_shift: Optional[int] = Field(default=UNSPECIFIED)

    emby_id: Optional[int] = Field(default=UNSPECIFIED)
    imdb_id: Optional[str] = Field(default=UNSPECIFIED)
    jellyfin_id: Optional[str] = Field(default=UNSPECIFIED)
    tmdb_id: Optional[int] = Field(default=UNSPECIFIED)
    tvdb_id: Optional[int] = Field(default=UNSPECIFIED)
    tvrage_id: Optional[int] = Field(default=UNSPECIFIED)
    extra_keys: list[str] = Field(default=UNSPECIFIED)
    extra_values: list[Any] = Field(default=UNSPECIFIED)

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @root_validator
    def delete_unspecified_args(cls, values):
        delete_keys = [key for key, value in values.items() if value == UNSPECIFIED]
        for key in delete_keys:
            del values[key]

        return values

    @validator('extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @root_validator
    def validate_paired_lists(cls, values):
        return validate_argument_lists_to_dict(
            values, 'extras',
            'extra_keys', 'extra_values',
            output_key='extras',
        )

"""
Return classes
"""
class Episode(Base):
    id: int
    series_id: int
    template_id: Optional[int]
    font_id: Optional[int]

    source_file: Optional[str]
    card_file: Optional[str]
    watched: Optional[bool]

    season_number: int
    episode_number: int
    absolute_number: Optional[int]

    title: str
    match_title: Optional[bool]
    auto_split_title: bool

    card_type: Optional[str]
    hide_season_text: Optional[bool]
    season_text: Optional[str]
    hide_episode_text: Optional[bool]
    episode_text: Optional[str]
    unwatched_style: Optional[str]
    watched_style: Optional[str]

    font_color: Optional[str]
    font_size: Optional[float]
    font_kerning: Optional[float]
    font_stroke_width: Optional[float]
    font_interline_spacing: Optional[int]
    font_vertical_shift: Optional[int]

    emby_id: Optional[int]
    imdb_id: Optional[str]
    jellyfin_id: Optional[str]
    tmdb_id: Optional[int]
    tvdb_id: Optional[int]
    tvrage_id: Optional[int]

    extras: Optional[dict[str, str]]