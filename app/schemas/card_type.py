# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from pathlib import Path
from random import uniform
from re import match as re_match
from typing import Literal, Optional, Union

from pydantic import (
    FilePath, PositiveFloat, conint, constr, root_validator, validator
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
from modules.cards.WhiteBorderTitleCard import WhiteBorderTitleCard

LocalCardIdentifiers = Literal[
    'anime', 'comic book', 'cutout', 'divider', 'fade', 'frame', 'generic',
    'gundam', 'ishalioh', 'landscape', 'logo', 'musikmann', 'olivier',
    'phendrena', 'photo', 'polymath', 'poster', 'reality tv', 'roman',
    'roman numeral', 'sherlock', 'standard', 'star wars', 'textless',
    'tinted glass', '4x3', 'white border',
]

"""
Base classes
"""
class BaseCardType(Base):
    source_file: FilePath
    card_file: Path
    blur: bool = False
    grayscale: bool = False

class BaseCardTypeAllText(BaseCardType):
    title_text: str
    season_text: constr(to_upper=True)
    episode_text: constr(to_upper=True)
    hide_season_text: bool = False
    hide_episode_text: bool = False

    @root_validator(skip_on_failure=True)
    def toggle_text_hiding(cls, values):
        values['hide_season_text'] |= (len(values['season_text']) == 0)
        values['hide_episode_text'] |= (len(values['episode_text']) == 0)

        return values

class BaseCardTypeCustomFontNoText(BaseCardType):
    font_color: BetterColor
    font_file: FilePath
    font_interline_spacing: int = 0
    font_kerning: float = 1.0
    font_size: PositiveFloat = 1.0
    font_stroke_width: float = 1.0
    font_vertical_shift: int = 0

class BaseCardTypeCustomFontAllText(BaseCardTypeAllText):
    font_color: BetterColor
    font_file: FilePath
    font_interline_spacing: int = 0
    font_kerning: float = 1.0
    font_size: PositiveFloat = 1.0
    font_stroke_width: float = 1.0
    font_vertical_shift: int = 0

"""
Creation classes
"""
class AnimeCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = AnimeTitleCard.TITLE_COLOR
    font_file: FilePath = AnimeTitleCard.REF_DIRECTORY / 'Flanker Griffo.otf'
    kanji: Optional[str] = None
    require_kanji: bool = False
    kanji_vertical_shift: int = 0
    separator: str = '·'
    omit_gradient: bool = False
    stroke_color: BetterColor = 'black'
    episode_text_color: BetterColor = AnimeTitleCard.SERIES_COUNT_TEXT_COLOR

    @root_validator(skip_on_failure=True)
    def validate_kanji(cls, values):
        if values['require_kanji'] and not values['kanji']:
            raise ValueError(f'Kanji is required and not specified')

        return values

RandomAngleRegex = r'random\[([+-]?\d+.?\d*),\s*([+-]?\d+.?\d*)\]'
RandomAngle = constr(regex=RandomAngleRegex)
class ComicBookCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = ComicBookTitleCard.TITLE_COLOR
    font_file: FilePath = ComicBookTitleCard.TITLE_FONT
    episode_text_color: BetterColor = 'black'
    index_text_position: Literal['left', 'middle', 'right'] = 'left'
    text_box_fill_color: BetterColor = 'white'
    text_box_edge_color: Optional[BetterColor] = None
    title_text_rotation_angle: Union[float, RandomAngle] = -4.0
    index_text_rotation_angle: Union[float, RandomAngle] = -4.0
    banner_fill_color: BetterColor = 'rgba(235,73,69,0.6)'
    title_banner_shift: int = 0
    index_banner_shift: int = 0
    hide_title_banner: bool = None
    hide_index_banner: bool = None

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
    episode_text: constr(to_upper=True)
    font_color: BetterColor = CutoutTitleCard.TITLE_COLOR
    font_file: FilePath = CutoutTitleCard.TITLE_FONT
    overlay_color: BetterColor = 'black'
    blur_edges: bool = False

TextPosition = Literal[
    'upper left', 'upper right', 'right', 'lower right', 'lower left', 'left'
]
class DividerCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = DividerTitleCard.TITLE_COLOR
    font_file: FilePath = DividerTitleCard.TITLE_FONT
    stroke_color: BetterColor = 'black'
    title_text_position: Literal['left', 'right'] = 'left'
    text_position: TextPosition = 'lower right'

class FadeCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = FadeTitleCard.TITLE_COLOR
    font_file: FilePath = FadeTitleCard.TITLE_FONT
    logo_file: Optional[FilePath] = None
    episode_text_color: BetterColor = FadeTitleCard.EPISODE_TEXT_COLOR
    separator: str = '•'

class FrameCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = FrameTitleCard.TITLE_COLOR
    font_file: FilePath = FrameTitleCard.TITLE_FONT
    episode_text_color: BetterColor = FrameTitleCard.EPISODE_TEXT_COLOR
    episode_text_position: Literal['left', 'right', 'surround'] = 'surround'
    interword_spacing: int = 0

BoxAdjustmentRegex = r'^([-+]?\d+)\s+([-+]?\d+)\s+([-+]?\d+)\s+([-+]?\d+)$'
BoxAdjustments = constr(regex=BoxAdjustmentRegex)
class LandscapeCardType(BaseCardType):
    title_text: str
    font_color: BetterColor = LandscapeTitleCard.TITLE_COLOR
    font_file: FilePath = LandscapeTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_kerning: float = 1.0
    font_size: PositiveFloat = 1.0
    font_vertical_shift: int = 0
    add_bounding_box: bool = False
    box_adjustments: BoxAdjustments = (0, 0, 0, 0)
    box_color: BetterColor = None
    darken: Union[Literal['all', 'box'], bool] = False

    @validator('box_adjustments')
    def parse_box_adjustments(cls, val):
        return tuple(map(int, re_match(BoxAdjustmentRegex, val).groups()))

    @root_validator(skip_on_failure=True)
    def assign_unassigned_color(cls, values):
        # None means match font color
        if values['box_color'] is None:
            values['box_color'] = values['font_color']

        return values

class LogoCardType(BaseCardTypeCustomFontAllText):
    source_file: Path
    logo_file: FilePath
    font_color: BetterColor = LogoTitleCard.TITLE_COLOR
    font_file: Path = LogoTitleCard.TITLE_FONT
    separator: str = '•'
    stroke_color: BetterColor = 'black'
    omit_gradient: bool = True
    use_background_image: bool = False
    blur_only_image: bool = False

    @root_validator(skip_on_failure=True)
    def validate_source_file(cls, values):
        if values['use_background_image']:
            if not values['source_file'] or not values['source_file'].exists():
                raise ValueError(f'Source file indicated and does not exist')

        return values

class OlivierCardType(BaseCardTypeCustomFontNoText):
    title_text: str
    episode_text: constr(to_upper=True)
    hide_episode_text: bool = False
    font_color: BetterColor = OlivierTitleCard.TITLE_COLOR
    font_file: FilePath = OlivierTitleCard.TITLE_FONT
    episode_text_color: BetterColor = OlivierTitleCard.EPISODE_TEXT_COLOR
    stroke_color: BetterColor = OlivierTitleCard.STROKE_COLOR
    interword_spacing: int = 0

class PosterCardType(BaseCardType):
    title_text: str
    episode_text: constr(to_upper=True)
    font_color: BetterColor = PosterTitleCard.TITLE_COLOR
    font_file: FilePath = PosterTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_size: PositiveFloat = 1.0
    logo_file: Optional[FilePath] = None
    episode_text_color: Optional[BetterColor] = None

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
    font_color: BetterColor = RomanNumeralTitleCard.TITLE_COLOR
    font_size: PositiveFloat = 1.0
    background: BetterColor = RomanNumeralTitleCard.BACKGROUND_COLOR
    roman_numeral_color: BetterColor = RomanNumeralTitleCard.ROMAN_NUMERAL_TEXT_COLOR
    season_text_color: BetterColor = RomanNumeralTitleCard.SEASON_TEXT_COLOR

class StandardCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = StandardTitleCard.TITLE_COLOR
    font_file: FilePath = StandardTitleCard.TITLE_FONT
    omit_gradient: bool = False
    separator: str = '•'
    stroke_color: BetterColor = 'black'
    episode_text_color: BetterColor = StandardTitleCard.SERIES_COUNT_TEXT_COLOR

class StarWarsCardType(BaseCardType):
    title_text: str
    episode_text: constr(to_upper=True)
    hide_episode_text: bool = False
    font_color: BetterColor = StarWarsTitleCard.TITLE_COLOR
    font_file: FilePath = StarWarsTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_size: PositiveFloat = 1.0
    episode_text_color: BetterColor = StarWarsTitleCard.EPISODE_TEXT_COLOR

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
    font_color: BetterColor = TintedFrameTitleCard.TITLE_COLOR
    font_file: FilePath = TintedFrameTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_kerning: float = 1.0
    font_size: PositiveFloat = 1.0
    font_vertical_shift: int = 0
    separator: str = '-'
    episode_text_color: Optional[BetterColor] = None
    frame_color: Optional[BetterColor] = None
    top_element: OuterElement = 'title'
    middle_element: MiddleElement = 'omit'
    bottom_element: OuterElement = 'index'
    logo_size: PositiveFloat = 1.0
    blur_edges: bool = True

    @root_validator(skip_on_failure=True)
    def validate_extras(cls, values):
        # Logo indicated, verify it exists
        top = values['top_element']
        middle = values['middle_element']
        bottom = values['bottom_element']
        if ((top == 'logo' or middle == 'logo' or bottom == 'logo')
            and not values['logo_file'].exists()):
            raise ValueError(f'Logo file indicated and does not exist')

        # Verify no two elements are the same
        if ((top != 'omit' and top in (middle, bottom))
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
    episode_text: constr(to_upper=True)
    hide_episode_text: bool = False
    font_color: BetterColor = TintedGlassTitleCard.TITLE_COLOR
    font_file: FilePath = TintedGlassTitleCard.TITLE_FONT
    episode_text_color: BetterColor = TintedGlassTitleCard.EPISODE_TEXT_COLOR
    episode_text_position: EpisodeTextPosition = 'center'
    box_adjustments: BoxAdjustments = (0, 0, 0, 0)

    @validator('box_adjustments')
    def parse_box_adjustments(cls, val):
        return tuple(map(int, re_match(BoxAdjustmentRegex, val).groups()))

    @root_validator(skip_on_failure=True)
    def toggle_text_hiding(cls, values):
        values['hide_episode_text'] |= (len(values['episode_text']) == 0)

        return values

class WhiteBorderCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = WhiteBorderTitleCard.TITLE_COLOR
    font_file: FilePath = WhiteBorderTitleCard.TITLE_FONT
    omit_gradient: bool = False
    separator: str = '•'
    stroke_color: BetterColor = WhiteBorderTitleCard.STROKE_COLOR
    episode_text_color: BetterColor = WhiteBorderTitleCard.TITLE_COLOR
    interword_spacing: float = 0.0

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
    'musikmann': WhiteBorderCardType,
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
    'white border': WhiteBorderCardType,
}
