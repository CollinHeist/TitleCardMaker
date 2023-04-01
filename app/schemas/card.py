from typing import Literal, Optional

from pydantic import Field, validator, root_validator

from app.schemas.base import Base, validate_argument_lists_to_dict
# from app.schemas.font import NewUnnamedEpisodeFont, PreviewFont
from app.schemas.preferences import Style

LocalCards = Literal[
    'anime', 'cutout', 'fade', 'frame', 'generic', 'gundam', 'ishalioh',
    'landscape', 'logo', 'olivier', 'phendrena', 'photo', 'polymath', 'poster',
    'reality tv', 'roman', 'roman numeral', 'sherlock', 'standard', 'star wars',
    'textless', 'tinted glass', '4x3'
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
    example: str
    creators: list[str]
    source: Literal['local', 'remote']
    supports_custom_fonts: bool
    supports_custom_seasons: bool
    supported_extras: list[Extra]
    description: list[str]

class LocalCardType(CardType):
    name: LocalCards
    source: str = 'local'

class RemoteCardType(CardType):
    source: str = 'remote'

"""
Models for title cards.
"""

class BaseTitleCard(Base):
    card_type: str = Field(..., title='Card type identifier')
    # font: Font # this would be existing Font from the db, e.g. ID + attributes
    title_text: Optional[str] = Field(...)
    season_text: Optional[str] = Field(...)
    hide_season_text: Optional[bool] = Field(
        default=False,
        description='Whether to omit the season text from this card',
    )
    episode_text: Optional[str] = Field(...)
    hide_episode_text: Optional[bool] = Field(
        default=False,
        description='Whether to omit the episode text from this card',
    )
    blur: Optional[bool] = Field(
        default=False,
        description='Whether to blur this card',
    )
    grayscale: Optional[bool] = Field(
        default=False,
        description='Whether to apply a grayscale filter this card',
    )
    season_number: Optional[int] = Field(default=1)
    episode_number: Optional[int] = Field(default=1)
    absolute_number: Optional[int] = Field(default=1)

class NewTitleCard(BaseTitleCard):
    # font: Optional[NewUnnamedEpisodeFont] = Field(default=None)
    font_id: Optional[int] = Field(default=None)
    extra_keys: Optional[list[str]] = Field(default=None)
    extra_values: Optional[list[str]] = Field(default=None)

class UpdateTitleCard(BaseTitleCard):
    extra_keys: Optional[list[str]] = Field(default=None)
    extra_values: Optional[list[str]] = Field(default=None)

    @validator('extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

class TitleCard(BaseTitleCard):
    episode_id: Optional[int]
    source_file: str
    card_file: str
    font_file: str
    font_color: str
    font_title_case: str
    font_size: float
    font_kerning: float
    font_stroke_width: float
    font_interline_spacing: int
    font_vertical_shift: int
    extras: dict[str, str]
    filesize: int

class PreviewTitleCard(BaseTitleCard):
    title_text: str = Field(default='Example Title')
    season_text: str = Field(default='Season 1')
    episode_text: str = Field(default='Episode 1')
    style: Style = Field(default='unique')
    font_color: Optional[str] = Field(default=None)
    font_size: Optional[float] = Field(default=None)
    font_kerning: Optional[float] = Field(default=None)
    font_stroke_width: Optional[float] = Field(default=None)
    font_interline_spacing: Optional[int] = Field(default=None)
    font_vertical_shift: Optional[int] = Field(default=None)
    font_id: Optional[int] = Field(default=None)
    extra_keys: Optional[list[str]] = Field(default=None)
    extra_values: Optional[list[str]] = Field(default=None)

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @root_validator
    def delete_unspecified_args(cls, values):
        delete_keys = [key for key, value in values.items() if value == None]
        for key in delete_keys:
            del values[key]

        return values

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