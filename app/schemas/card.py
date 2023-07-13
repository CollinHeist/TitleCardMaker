# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Literal, Optional

from pydantic import Field, validator, root_validator

from app.schemas.base import Base, UpdateBase, validate_argument_lists_to_dict
from app.schemas.font import TitleCase
from app.schemas.preferences import Style

LocalCardIdentifiers = Literal[
    'anime', 'comic book', 'cutout', 'fade', 'frame', 'generic', 'gundam',
    'ishalioh', 'landscape', 'logo', 'olivier', 'phendrena', 'photo', 'polymath',
    'poster', 'reality tv', 'roman', 'roman numeral', 'sherlock', 'standard',
    'star wars', 'textless', 'tinted glass', '4x3'
]

"""
Models of card types and series extras.
"""

class Extra(Base):
    name: str
    identifier: str
    description: str

class CardType(Base):
    name: str
    identifier: str
    example: str
    creators: list[str]
    source: Literal['local', 'remote']
    supports_custom_fonts: bool
    supports_custom_seasons: bool
    supported_extras: list[Extra]
    description: list[str]

class LocalCardType(CardType):
    name: LocalCardIdentifiers
    source: str = 'local'

class RemoteCardType(CardType):
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
    title_text: str
    season_text: str
    episode_text: str
    style: Style = 'unique'
    font_id: Optional[int] = None
    font_color: Optional[str] = None
    font_interline_spacing: Optional[int] = None
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
    # Meta fields
    series_id: int
    episode_id: int
    # Required fields
    source_file: str
    card_file: str
    card_type: str
    filesize: Optional[int] = None
    title_text: str
    season_text: str
    hide_season_text: bool
    episode_text: str
    hide_episode_text: bool
    font_file: str
    font_color: str
    font_size: float
    font_kerning: float
    font_stroke_width: float
    font_interline_spacing: int
    font_vertical_shift: int
    blur: bool
    grayscale: bool
    # Optional fields
    extras: dict[str, str] = {}
    season_number: int = 1
    episode_number: int = 1
    absolute_number: int = 1

    @validator('source_file', 'card_file', pre=True)
    def convert_paths_to_str(cls, v):
        return str(v)

"""
Update classes
"""

"""
Return classes
"""
class TMDbImage(Base):
    url: str
    width: int
    height: int

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

class TitleCard(Base):
    # Meta fields
    id: int
    series_id: int
    episode_id: int
    # Required fields
    source_file: str
    card_file: str
    card_type: str
    filesize: int
    title_text: str
    season_text: str
    hide_season_text: bool
    episode_text: str
    hide_episode_text: bool
    font_file: str
    font_color: str
    font_size: float
    font_kerning: float
    font_stroke_width: float
    font_interline_spacing: int
    font_vertical_shift: int
    blur: bool
    grayscale: bool
    extras: dict[str, str] = {}
    # Optional fields
    season_number: int = 1
    episode_number: int = 1
    absolute_number: int = 1
