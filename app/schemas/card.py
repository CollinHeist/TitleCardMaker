# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Literal, Optional, Union

from pydantic import Field, PositiveInt, validator, root_validator # pylint: disable=no-name-in-module

from app.schemas.base import (
    Base, DictKey, UpdateBase, validate_argument_lists_to_dict
)
from app.schemas.font import TitleCase
from app.schemas.preferences import Style

"""
Models of card types and series extras.
"""
class TitleCharacteristics(Base):
    max_line_width: PositiveInt
    max_line_count: PositiveInt
    top_heavy: Union[bool, Literal['even']]

class Extra(Base):
    name: str
    identifier: DictKey
    description: str
    tooltip: Optional[str] = None

class CardTypeDescription(Base):
    name: str
    identifier: str
    example: str
    creators: list[str]
    source: Literal['builtin', 'local', 'remote']
    supports_custom_fonts: bool
    supports_custom_seasons: bool
    supported_extras: list[Extra]
    description: list[str]

class BuiltinCardType(CardTypeDescription):
    source: str = 'builtin'

class LocalCardType(CardTypeDescription):
    source: str = 'local'

class RemoteCardType(CardTypeDescription):
    source: str = 'remote'

"""
Base classes
"""
class BaseTitleCard(Base):
    card_type: str = Field(title='Card type identifier')
    title_text: str
    season_text: str
    hide_season_text: bool = False
    episode_text: str
    hide_episode_text: bool = False
    blur: bool = False
    grayscale: bool = False
    season_number: int = 1
    episode_number: int = 1
    absolute_number: int = 1

"""
Creation classes
"""
class PreviewTitleCard(UpdateBase):
    card_type: str
    title_text: str = 'Example Title'
    season_text: str = 'Season 1'
    hide_season_text: bool = False
    episode_text: str = 'Episode 1'
    hide_episode_text: bool = False
    blur: bool = False
    grayscale: bool = False
    watched: bool = True
    season_number: int = 1
    episode_number: int = 1
    absolute_number: int = 1
    style: Style = 'unique'
    font_id: Optional[int] = None
    font_color: Optional[str] = None
    font_interline_spacing: Optional[int] = None
    font_interword_spacing: Optional[int] = None
    font_kerning: Optional[float] = None
    font_size: Optional[float] = None
    font_stroke_width: Optional[float] = None
    font_title_case: Optional[TitleCase] = None
    font_vertical_shift: Optional[int] = None
    extra_keys: Optional[list[str]] = None
    extra_values: Optional[list[str]] = None

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @root_validator
    def validate_paired_lists(cls, values):
        # Extras
        return validate_argument_lists_to_dict(
            values, 'extras',
            'extra_keys', 'extra_values',
            output_key='extras',
        )


class NewTitleCard(Base):
    series_id: int
    episode_id: int
    card_file: str
    filesize: Optional[int] = None
    card_type: str

    @validator('card_file', pre=True)
    def convert_paths_to_str(cls, v):
        return str(v)

"""
Update classes
"""

"""
Return classes
"""
class TMDbLanguage(Base):
    english_name: str
    iso_639_1: str
    name: str

class ExternalSourceImage(Base):
    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    language: Optional[TMDbLanguage] = None

class SourceImage(Base):
    episode_id: int
    season_number: int
    episode_number: int
    source_file_name: str
    source_file: str
    source_url: str
    exists: bool
    filesize: int = 0
    width: int = 0
    height: int = 0

class CardActions(Base):
    creating: int = 0
    existing: int = 0
    deleted: int = 0
    missing_source: int = 0
    imported: int = 0
    invalid: int = 0

class EpisodeData(Base):
    season_number: int
    episode_number: int
    absolute_number: Optional[int] = None

class TitleCard(Base):
    id: int
    series_id: int
    episode_id: int
    episode: EpisodeData
    card_file: str
    filesize: int
    model_json: dict
    library_name: Optional[str] = None
