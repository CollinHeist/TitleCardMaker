from typing import Literal, Optional

from pydantic import Field, validator, root_validator

from app.schemas.base import Base, validate_argument_lists_to_dict
# from app.schemas.font import NewUnnamedEpisodeFont, PreviewFont
from app.schemas.preferences import Style

LocalCardIdentifiers = Literal[
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
    supports_custom_seasons: bool=False
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

"""
Creation classes
"""
class PreviewTitleCard(Base):
    card_type: str = Field(..., title='Card type identifier')
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


class NewTitleCard(Base):
    # Meta fields
    series_id: int = Field(...)
    episode_id: int = Field(...)
    # Required fields
    source_file: str = Field(..., description='Path to the card source file')
    card_file: str = Field(..., description='Path to the card file')
    card_type: str = Field(..., title='Type of title card')
    filesize: Optional[int] = Field(default=None, title='Card filesize (bytes)')
    title_text: str = Field(...)
    season_text: str = Field(...)
    hide_season_text: bool = Field(
        ...,
        description='Whether season text is omitted from this card',
    )
    episode_text: str = Field(...)
    hide_episode_text: bool = Field(
        ...,
        description='Whether episode text is omitted from this card',
    )
    font_file: str = Field(..., description='Path to the font file')
    font_color: str = Field(...)
    font_size: float = Field(..., title='Font size (scalar)')
    font_kerning: float = Field(..., title='Font kerning (scalar)')
    font_stroke_width: float = Field(..., title='Font stroke width (scalar)')
    font_interline_spacing: int = Field(..., title='Interline spacing (pixels)')
    font_vertical_shift: int = Field(..., title='Vertical shift (pixels)')
    blur: bool = Field(
        ...,
        description='Whether this card is blurred',
    )
    grayscale: bool = Field(
        ...,
        description='Whether this card has a grayscale filter',
    )
    extras: dict[str, str] = Field(default={}, title='Extra data')
    # Optional fields
    season_number: int = Field(default=0)
    episode_number: int = Field(default=0)
    absolute_number: int = Field(default=0)

    @validator('source_file', 'card_file', pre=True)
    def convert_paths_to_str(cls, v):
        return str(v)

"""
Update classes
"""

"""
Return classes
"""
class TitleCard(Base):
    # Meta fields
    id: int
    series_id: int
    episode_id: int
    # Required fields
    source_file: str = Field(..., description='Path to the card source file')
    card_file: str = Field(..., description='Path to the card file')
    card_type: str = Field(..., title='Type of title card')
    filesize: int = Field(..., title='Card filesize (bytes)')
    title_text: str
    season_text: str
    hide_season_text: bool = Field(
        ...,
        description='Whether season text is omitted from this card',
    )
    episode_text: str
    hide_episode_text: bool = Field(
        ...,
        description='Whether episode text is omitted from this card',
    )
    font_file: str = Field(..., description='Path to the font file')
    font_color: str
    font_size: float = Field(..., title='Font size (scalar)')
    font_kerning: float = Field(..., title='Font kerning (scalar)')
    font_stroke_width: float = Field(..., title='Font stroke width (scalar)')
    font_interline_spacing: int = Field(..., title='Interline spacing (pixels)')
    font_vertical_shift: int = Field(..., title='Vertical shift (pixels)')
    blur: bool = Field(
        ...,
        description='Whether this card is blurred',
    )
    grayscale: bool = Field(
        ...,
        description='Whether this card has a grayscale filter',
    )
    extras: dict[str, str] = Field(default={}, title='Extra data')
    # Optional fields
    season_number: int = Field(default=0)
    episode_number: int = Field(default=0)
    absolute_number: int = Field(default=0)