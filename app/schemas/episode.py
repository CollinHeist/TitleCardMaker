# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from datetime import datetime
from typing import Any, Optional

from pydantic import PositiveFloat, root_validator, validator # pylint: disable=no-name-in-module

from app.schemas.base import (
    Base, UpdateBase, UNSPECIFIED, validate_argument_lists_to_dict
)
from app.schemas.card import TitleCard
from app.schemas.ids import EmbyID, IMDbID, JellyfinID, TMDbID, TVDbID, TVRageID
from app.schemas.preferences import Style

"""
Base classes
"""

"""
Creation classes
"""
class NewEpisode(Base):
    series_id: int
    template_ids: list[int] = []
    font_id: Optional[int] = None

    source_file: Optional[str] = None
    card_file: Optional[str] = None
    watched: Optional[bool] = None

    season_number: int = 1
    episode_number: int = 1
    absolute_number: Optional[int] = None

    title: str
    match_title: Optional[bool] = None
    auto_split_title: bool = True

    card_type: Optional[str]
    hide_season_text: Optional[bool]
    season_text: Optional[str]
    hide_episode_text: Optional[bool]
    episode_text: Optional[str]
    unwatched_style: Optional[Style]
    watched_style: Optional[Style]

    font_color: Optional[str] = None
    font_size: Optional[PositiveFloat] = None
    font_kerning: Optional[float] = None
    font_stroke_width: Optional[float] = None
    font_interline_spacing: Optional[int] = None
    font_interword_spacing: Optional[int] = None
    font_vertical_shift: Optional[int] = None

    airdate: Optional[datetime] = None
    emby_id: EmbyID = None
    imdb_id: IMDbID = None
    jellyfin_id: JellyfinID = None
    tmdb_id: TMDbID = None
    tvdb_id: TVDbID = None
    tvrage_id: TVRageID = None

    extras: Optional[dict[str, Any]] = None
    translations: dict[str, str] = {}

    @validator('template_ids', pre=False)
    def validate_unique_template_ids(cls, val):
        if len(val) != len(set(val)):
            raise ValueError('Template IDs must be unique')
        return val

"""
Update classes
"""
class UpdateEpisode(UpdateBase):
    template_ids: list[int] = UNSPECIFIED
    font_id: Optional[int] = UNSPECIFIED

    source_file: Optional[str] = UNSPECIFIED
    card_file: Optional[str] = UNSPECIFIED
    watched: Optional[bool] = UNSPECIFIED

    season_number: int = UNSPECIFIED
    episode_number: int = UNSPECIFIED
    absolute_number: Optional[int] = UNSPECIFIED

    title: str = UNSPECIFIED
    match_title: Optional[bool] = UNSPECIFIED
    auto_split_title: bool = UNSPECIFIED

    card_type: Optional[str] = UNSPECIFIED
    hide_season_text: Optional[bool] = UNSPECIFIED
    season_text: Optional[str] = UNSPECIFIED
    hide_episode_text: Optional[bool] = UNSPECIFIED
    episode_text: Optional[str] = UNSPECIFIED
    unwatched_style: Optional[Style] = UNSPECIFIED
    watched_style: Optional[Style] = UNSPECIFIED

    font_color: Optional[str] = UNSPECIFIED
    font_size: Optional[PositiveFloat] = UNSPECIFIED
    font_kerning: Optional[float] = UNSPECIFIED
    font_stroke_width: Optional[float] = UNSPECIFIED
    font_interline_spacing: Optional[int] = UNSPECIFIED
    font_interword_spacing: Optional[int] = UNSPECIFIED
    font_vertical_shift: Optional[int] = UNSPECIFIED

    airdate: Optional[datetime] = UNSPECIFIED
    emby_id: EmbyID = UNSPECIFIED
    imdb_id: IMDbID = UNSPECIFIED
    jellyfin_id: JellyfinID = UNSPECIFIED
    tmdb_id: TMDbID = UNSPECIFIED
    tvdb_id: TVDbID = UNSPECIFIED
    tvrage_id: TVRageID = UNSPECIFIED

    extra_keys: Optional[list[str]] = UNSPECIFIED
    extra_values: Optional[list[Any]] = UNSPECIFIED
    translations: dict[str, str] = UNSPECIFIED

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @validator('template_ids', pre=False)
    def validate_unique_template_ids(cls, val):
        if len(val) != len(set(val)):
            raise ValueError('Template IDs must be unique')
        return val

    @root_validator
    def validate_paired_lists(cls, values):
        return validate_argument_lists_to_dict(
            values, 'extras',
            'extra_keys', 'extra_values',
            output_key='extras',
        )

class BatchUpdateEpisode(Base):
    episode_id: int
    update_episode: UpdateEpisode

"""
Return classes
"""

class Episode(Base):
    id: int
    series_id: int
    template_ids: list[int]
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
    font_size: Optional[PositiveFloat]
    font_kerning: Optional[float]
    font_stroke_width: Optional[float]
    font_interline_spacing: Optional[int]
    font_interword_spacing: Optional[int]
    font_vertical_shift: Optional[int]

    airdate: Optional[datetime]
    emby_id: EmbyID
    imdb_id: IMDbID
    jellyfin_id: JellyfinID
    tmdb_id: TMDbID
    tvdb_id: TVDbID
    tvrage_id: TVRageID

    extras: Optional[dict[str, Any]]
    translations: dict[str, str]
    card: list[TitleCard]
