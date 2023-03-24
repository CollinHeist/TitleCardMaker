from typing import Literal, Optional

from pydantic import Field

from app.schemas.base import Base
from app.schemas.font import Font, PreviewFont
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
    title_text: Optional[str] = Field(default='')
    season_text: Optional[str] = Field(default='')
    hide_season_text: Optional[bool] = Field(
        default=False,
        description='Whether to omit the season text from this card',
    )
    episode_text: Optional[str] = Field(default='')
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
    extra_keys: Optional[list[str]] = Field(default=None)
    extra_values: Optional[list[str]] = Field(default=None)

class UpdateTitleCard(BaseTitleCard):
    extra_keys: Optional[list[str]] = Field(default=None)
    extra_values: Optional[list[str]] = Field(default=None)

class TitleCard(BaseTitleCard):
    extras: dict[str, str]
    filesize: int

class PreviewTitleCard(BaseTitleCard):
    style: Optional[Style] = Field(default='unique')
    custom_font: Optional[PreviewFont] = Field(default=None)
    font_id: Optional[int] = Field(default=None)
    extra_keys: Optional[list[str]] = Field(default=None)
    extra_values: Optional[list[str]] = Field(default=None)