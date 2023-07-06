from pathlib import Path
from random import uniform
from re import match as re_match
from typing import Literal, Optional, Union

from pydantic import (
    Field, FilePath, PositiveFloat, conint, constr, root_validator, validator
)

from app.schemas.base import Base, BetterColor
from modules.cards.AnimeTitleCard import AnimeTitleCard
from modules.cards.ComicBookTitleCard import ComicBookTitleCard
from modules.cards.CutoutTitleCard import CutoutTitleCard
from modules.cards.DividerTitleCard import DividerTitleCard
from modules.cards.FadeTitleCard import FadeTitleCard
from modules.cards.FrameTitleCard import FrameTitleCard
from modules.cards.LandscapeTitleCard import LandscapeTitleCard
from modules.cards.LogoTitleCard import LogoTitleCard
from modules.cards.OlivierTitleCard import OlivierTitleCard
from modules.cards.PosterTitleCard import PosterTitleCard
from modules.cards.RomanNumeralTitleCard import RomanNumeralTitleCard
from modules.cards.StandardTitleCard import StandardTitleCard
from modules.cards.StarWarsTitleCard import StarWarsTitleCard
from modules.cards.TintedFrameTitleCard import TintedFrameTitleCard
from modules.cards.TintedGlassTitleCard import TintedGlassTitleCard
from modules.Debug import log

LocalCardIdentifiers = Literal[
    'anime', 'comic book', 'cutout', 'divider', 'fade', 'frame', 'generic',
    'gundam', 'ishalioh', 'landscape', 'logo', 'olivier', 'phendrena', 'photo',
    'polymath', 'poster', 'reality tv', 'roman', 'roman numeral', 'sherlock',
    'standard', 'star wars', 'textless', 'tinted glass', '4x3',
]

"""
Base classes
"""
class BaseCardType(Base):
    source_file: FilePath
    card_file: Path
    blur: bool = Field(default=False)
    grayscale: bool = Field(default=False)

class BaseCardTypeAllText(BaseCardType):
    title_text: str
    season_text: str
    episode_text: str
    hide_season_text: bool = Field(default=False)
    hide_episode_text: bool = Field(default=False)

    @root_validator(skip_on_failure=True)
    def toggle_text_hiding(cls, values):
        values['hide_season_text'] |= (len(values['season_text']) == 0)
        values['hide_episode_text'] |= (len(values['episode_text']) == 0)

        return values

class BaseCardTypeCustomFontNoText(BaseCardType):
    font_color: BetterColor
    font_file: FilePath
    font_interline_spacing: int = Field(default=0)
    font_kerning: float = Field(default=1.0)
    font_size: PositiveFloat = Field(default=1.0)
    font_stroke_width: float = Field(default=1.0)
    font_vertical_shift: int = Field(default=0)

class BaseCardTypeCustomFontAllText(BaseCardTypeAllText):
    font_color: BetterColor
    font_file: FilePath
    font_interline_spacing: int = Field(default=0)
    font_kerning: float = Field(default=1.0)
    font_size: PositiveFloat = Field(default=1.0)
    font_stroke_width: float = Field(default=1.0)
    font_vertical_shift: int = Field(default=0)

"""
Creation classes
"""
class AnimeCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = Field(default=AnimeTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(
        default=AnimeTitleCard.REF_DIRECTORY / 'Flanker Griffo.otf'
    )

    kanji: Optional[str] = Field(default=None)
    require_kanji: bool = Field(default=False)
    kanji_vertical_shift: int = Field(default=0)
    separator: str = Field(default='·')
    omit_gradient: bool = Field(default=False)
    stroke_color: BetterColor = Field(default='black')
    episode_text_color: BetterColor = Field(
        default=AnimeTitleCard.SERIES_COUNT_TEXT_COLOR
    )

RandomAngleRegex = r'random\[([+-]?\d+.?\d*),\s*([+-]?\d+.?\d*)\]'
RandomAngle = constr(regex=RandomAngleRegex)
class ComicBookCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = Field(default=ComicBookTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(default=ComicBookTitleCard.TITLE_FONT)
    episode_text_color: BetterColor = Field(default='black')
    index_text_position: Literal['left', 'middle', 'right'] = Field(
        default='left'
    )
    text_box_fill_color: BetterColor = Field(default='white')
    text_box_edge_color: Optional[BetterColor] = Field(default=None)
    title_text_rotation_angle: Union[float, RandomAngle] = Field(default=-4.0)
    index_text_rotation_angle: Union[float, RandomAngle] = Field(default=-4.0)
    banner_fill_color: BetterColor = Field(default='rgba(235,73,69,0.6)')
    title_banner_shift: int = Field(default=0)
    index_banner_shift: int = Field(default=0)
    hide_title_banner: bool = Field(default=None)
    hide_index_banner: bool = Field(default=None)

    @validator('title_text_rotation_angle', 'index_text_rotation_angle')
    def validate_random_angle(cls, val):
        # If angle is a random range string, replace with random value in range
        if isinstance(val, str):
            # Get bounds from the random range string
            lower, upper = map(float, re_match(RandomAngleRegex, val).groups())

            # Lower bound cannot be above upper bound
            if lower > upper:
                raise ValueError(f'Lower bound must be below upper bound')

            return uniform(lower, upper)

        return val
    
    @root_validator(skip_on_failure=True)
    def assign_unassigned_color(cls, values):
        # None means match font color
        if values['text_box_edge_color'] is None:
            values['text_box_edge_color'] = values['font_color']

        return values
            
class CutoutCardType(BaseCardType):
    title_text: str
    episode_text: str
    font_color: BetterColor = Field(default=CutoutTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(default=CutoutTitleCard.TITLE_FONT)
    overlay_color: BetterColor = Field(default='black')
    blur_edges: bool = Field(default=False)

TextPosition = Literal[
    'upper left', 'upper right', 'right', 'lower right', 'lower left', 'left'
]
class DividerCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = Field(default=DividerTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(default=DividerTitleCard.TITLE_FONT)
    stroke_color: BetterColor = Field(default='black')
    title_text_position: Literal['left', 'right'] = Field(default='left')
    text_position: TextPosition = Field(default='lower right')

class FadeCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = Field(default=FadeTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(default=FadeTitleCard.TITLE_FONT)
    logo: Optional[FilePath] = Field(default=None)
    episode_text_color: BetterColor = Field(default=FadeTitleCard.EPISODE_TEXT_COLOR)
    separator: str = Field(default='•')

class FrameCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = Field(default=FrameTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(default=FrameTitleCard.TITLE_FONT)
    episode_text_color: BetterColor = Field(default=FrameTitleCard.EPISODE_TEXT_COLOR)
    episode_text_position: Literal['left', 'right', 'surround'] = Field(default='surround')
    interword_spacing: int = Field(default=0)

BoxAdjustmentRegex = r'^([-+]?\d+)\s+([-+]?\d+)\s+([-+]?\d+)\s+([-+]?\d+)$'
BoxAdjustments = constr(regex=BoxAdjustmentRegex)
class LandscapeCardType(BaseCardType):
    title_text: str
    font_color: BetterColor = Field(default=LandscapeTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(default=LandscapeTitleCard.TITLE_FONT)
    font_interline_spacing: int = Field(default=0)
    font_kerning: float = Field(default=1.0)
    font_size: PositiveFloat = Field(default=1.0)
    font_vertical_shift: int = Field(default=0)
    darken: Union[Literal['all', 'box'], bool] = Field(default=False)
    add_bounding_box: bool = Field(default=False)
    box_adjustments: BoxAdjustments = Field(default=(0, 0, 0, 0))

    @validator('box_adjustments')
    def parse_box_adjustments(cls, val):
        return tuple(map(int, re_match(BoxAdjustmentRegex, val).groups()))
    
class LogoCardType(BaseCardTypeCustomFontAllText):
    source_file: Path
    font_color: BetterColor = Field(default=LogoTitleCard.TITLE_COLOR)
    font_file: Path = Field(default=LogoTitleCard.TITLE_FONT)
    separator: str = Field(default='•')
    stroke_color: BetterColor = Field(default='black')
    omit_gradient: bool = Field(default=True)
    use_background_image: bool = Field(default=False)
    blur_only_image: bool = Field(default=False)

    @root_validator(skip_on_failure=True)
    def validate_source_file(cls, values):
        if values['use_background_image'] and not values['source_file'].exists():
            raise ValueError(f'Source file indicated and does not exist')
        
        return values

class OlivierCardType(BaseCardTypeCustomFontNoText):
    title_text: str
    episode_text: str
    hide_episode_text: bool = Field(default=False)
    font_color: BetterColor = Field(default=OlivierTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(default=OlivierTitleCard.TITLE_FONT)
    episode_text_color: BetterColor = Field(default=OlivierTitleCard.EPISODE_TEXT_COLOR)
    stroke_color: BetterColor = Field(default=OlivierTitleCard.STROKE_COLOR)

class PosterCardType(BaseCardType):
    title_text: str 
    episode_text: str
    font_color: BetterColor = Field(default=PosterTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(default=PosterTitleCard.TITLE_FONT)
    font_interline_spacing: int = Field(default=0)
    font_size: PositiveFloat = Field(default=1.0)
    logo_file: Optional[FilePath] = Field(default=None)
    episode_text_color: Optional[BetterColor] = Field(default=None)

    @root_validator(skip_on_failure=True)
    def assign_episode_text_color(cls, values):
        # None means match font color
        if values['episode_text_color'] is None:
            values['episode_text_color'] = values['font_color']

        return values

RomanNumeralValue = conint(gt=0, le=RomanNumeralTitleCard.MAX_ROMAN_NUMERAL)
class RomanNumeralCardType(BaseCardTypeAllText):
    card_file: Path
    episode_number: RomanNumeralValue
    font_color: BetterColor = Field(default=RomanNumeralTitleCard.TITLE_COLOR)
    font_size: PositiveFloat = Field(default=1.0)
    background: BetterColor = Field(default=RomanNumeralTitleCard.BACKGROUND_COLOR)
    roman_numeral_color: BetterColor = Field(
        default=RomanNumeralTitleCard.ROMAN_NUMERAL_TEXT_COLOR
    )
    season_text_color: BetterColor = Field(
        default=RomanNumeralTitleCard.SEASON_TEXT_COLOR
    )

class StandardCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = Field(default=StandardTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(default=StandardTitleCard.TITLE_FONT)
    omit_gradient: bool = Field(default=False)
    separator: str = Field(default='•')
    stroke_color: BetterColor = Field(default='black')
    episode_text_color: BetterColor = Field(
        default=StandardTitleCard.SERIES_COUNT_TEXT_COLOR
    )

class StarWarsCardType(BaseCardType):
    title_text: str
    episode_text: str
    hide_episode_text: bool = Field(default=False)
    font_color: BetterColor = Field(default=StarWarsTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(default=StarWarsTitleCard.TITLE_FONT)
    font_interline_spacing: int = Field(default=0)
    font_size: PositiveFloat = Field(default=1.0)
    episode_text_color: BetterColor = Field(default=StarWarsTitleCard.EPISODE_TEXT_COLOR)
    
    @root_validator(skip_on_failure=True)
    def toggle_text_hiding(cls, values):
        values['hide_episode_text'] |= (len(values['episode_text']) == 0)

        return values

class TextlessCardType(BaseCardType):
    pass

OuterElement = Literal['index', 'logo', 'omit', 'title']
MiddleElement = Literal['logo', 'omit']
class TintedFrameCardType(BaseCardTypeAllText):
    logo_file: Path
    font_color: BetterColor = Field(default=TintedFrameTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(default=TintedFrameTitleCard.TITLE_FONT)
    font_interline_spacing: int = Field(default=0)
    font_kerning: float = Field(default=1.0)
    font_size: PositiveFloat = Field(default=1.0)
    font_vertical_shift: int = Field(default=0)
    separator: str = Field(default='-')
    episode_text_color: Optional[BetterColor] = Field(default=None)
    frame_color: Optional[BetterColor] = Field(default=None)
    top_element: OuterElement = Field(default='title')
    middle_element: MiddleElement = Field(default='omit')
    bottom_element: OuterElement = Field(default='index')
    logo_size: PositiveFloat = Field(default=1.0)
    blur_edges: bool = Field(default=True)

    @root_validator(skip_on_failure=True)
    def validate_extras(cls, values):
        # Logo indicated, verify it exists
        top = values['top_element']
        middle = values['middle_element']
        bottom = values['bottom_element']
        if (top == 'logo' or middle == 'logo' or bottom == 'logo'
            and not values['logo_file'].exists()):
            raise ValueError(f'Logo file indicated and does not exist')

        # Verify no two elements are the same
        if ((top != 'omit' and (top == middle or top == bottom))
            or (middle != 'omit' and (middle == bottom))):
            raise ValueError(f'Top/middle/bottom elements cannot be the same')

        # Convert None colors to the default font color
        if values['episode_text_color'] is None:
            values['episode_text_color'] = values['font_color']
        if values['frame_color'] is None:
            values['frame_color'] = values['font_color']

        return values

EpisodeTextPosition = Literal['left', 'center', 'right']
class TintedGlassCardType(BaseCardTypeCustomFontNoText):
    title_text: str
    episode_text: str
    hide_episode_text: bool = Field(default=False)
    font_color: BetterColor = Field(default=TintedGlassTitleCard.TITLE_COLOR)
    font_file: FilePath = Field(default=TintedGlassTitleCard.TITLE_FONT)
    episode_text_color: BetterColor = Field(
        default=TintedGlassTitleCard.EPISODE_TEXT_COLOR
    )
    episode_text_position: EpisodeTextPosition = Field(default='center')
    box_adjustments: BoxAdjustments = Field(default=(0, 0, 0, 0))

    @validator('box_adjustments')
    def parse_box_adjustments(cls, val):
        return tuple(map(int, re_match(BoxAdjustmentRegex, val).groups()))

    @root_validator(skip_on_failure=True)
    def toggle_text_hiding(cls, values):
        values['hide_episode_text'] |= (len(values['episode_text']) == 0)

        return values

LocalCardTypeModels = {
    '4x3': FadeCardType,
    'anime': AnimeCardType,
    'blurred border': TintedFrameCardType,
    'comic book': ComicBookCardType,
    'cutout': CutoutCardType,
    'divider': DividerCardType,
    'fade': FadeCardType, 
    'frame': FrameCardType,
    'generic': StandardCardType,
    'gundam': PosterCardType,
    'ishalioh': OlivierCardType,
    'landscape': LandscapeCardType,
    'logo': LogoCardType,
    'olivier': OlivierCardType,
    'phendrena': CutoutCardType,
    'photo': FrameCardType,
    'polymath': StandardCardType,
    'poster': PosterCardType,
    'reality tv': LogoCardType,
    'roman': RomanNumeralCardType,
    'roman numeral': RomanNumeralCardType,
    'sherlock': TintedGlassCardType,
    'standard': StandardCardType,
    'star wars': StarWarsCardType,
    'textless': TextlessCardType,
    'tinted glass': TintedGlassCardType,
    'tinted frame': TintedFrameCardType,
}