# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, Union

from pydantic import validator, root_validator

from app.schemas.base import (
    Base,
    DictKey,
    ImageSource,
    UpdateBase,
    validate_argument_lists_to_dict
)
from app.schemas.font import TitleCase
from app.schemas.preferences import Style

"""
Models of card types and series extras.
"""
class Extra(Base):
    name: str
    identifier: Annotated[str, DictKey]
    description: str
    tooltip: Optional[str] = None
    default: Optional[Any] = None

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
    hash: str

"""
Base classes
"""
class BaseTitleCard(Base):
    card_type: str
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
    season_text: Optional[str] = None
    hide_season_text: bool = False
    episode_text: Optional[str] = None
    episode_text_format: Optional[str] = None
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
    def validate_list(cls, v: Union[str, list[str]]) -> list[str]:
        return [v] if isinstance(v, str) else v

    @root_validator
    def validate_paired_lists(cls, values: dict) -> dict:
        return validate_argument_lists_to_dict(
            values, 'extras',
            'extra_keys', 'extra_values',
            output_key='extras',
        )

class NewTitleCard(Base):
    series_id: int
    episode_id: int
    card_file: str
    source_file: str
    filesize: Optional[int] = None
    card_type: str

    @validator('card_file', pre=True)
    def convert_paths_to_str(cls, v):
        return str(v)

    @validator('source_file', pre=True)
    def convert_path_to_filename(cls, v):
        return Path(v).name

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
    data: Optional[str] = None
    url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    language: Optional[TMDbLanguage] = None
    interface_type: ImageSource = 'TMDb'

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

class LoadedDetails(Base):
    library_name: str

class TitleCard(Base):
    id: int
    series_id: int
    episode_id: int
    episode: EpisodeData
    card_file: str
    file_url: str
    filesize: int
    model_json: dict
    library_name: Optional[str] = None
    loaded: Optional[LoadedDetails] = None
