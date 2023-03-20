from typing import Literal, Optional

from app.schemas.base import Base
from app.schemas.font import Font

LocalCards = Literal[
    'anime', 'cutout', 'fade', 'frame', 'generic', 'gundam', 'ishalioh',
    'landscape', 'logo', 'olivier', 'phendrena', 'photo', 'polymath', 'poster',
    'reality tv', 'roman', 'roman numeral', 'sherlock', 'standard', 'star wars',
    'textless', 'tinted glass', '4x3'
]

class ExtraInput(Base):
    identifier: str
    value: str

class Extra(Base):
    name: str
    identifier: str
    description: str


class BaseTitleCard(Base):
    card_type: str
    font: Font
    title: str
    season_text: str
    episode_text: str
    hide_season: bool
    blur: bool
    grayscale: bool
    url: str
    filesize: int
    season_number: Optional[int]
    episode_number: Optional[int]
    absolute_number: Optional[int]
    extras: list[Extra]

class TemporaryTitleCard(BaseTitleCard):
    ...

class TitleCard(Base):
    id: Optional[int]
    source: str
    output: str


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