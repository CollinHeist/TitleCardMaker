# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from datetime import datetime
from pathlib import Path
from random import uniform
from re import compile as re_compile, match as re_match
from typing import Any, Literal, Optional, Union

from pydantic import ( # pylint: disable=no-name-in-module
    FilePath, PositiveFloat, PositiveInt, confloat, conint, constr,
    root_validator, validator,
)

from app.schemas.base import Base, BetterColor, DictKey
from modules.FormatString import FormatString
from modules.cards.AnimeTitleCard import AnimeTitleCard
from modules.cards.BannerTitleCard import BannerTitleCard
from modules.cards.CalligraphyTitleCard import CalligraphyTitleCard
from modules.cards.ComicBookTitleCard import ComicBookTitleCard
from modules.cards.CutoutTitleCard import CutoutTitleCard
from modules.cards.DividerTitleCard import DividerTitleCard, TextGravity
from modules.cards.FadeTitleCard import FadeTitleCard
from modules.cards.FormulaOneTitleCard import (
    FormulaOneTitleCard, Country as FormulaOneCountry
)
from modules.cards.FrameTitleCard import FrameTitleCard
from modules.cards.GraphTitleCard import (
    GraphTitleCard, TextPosition as GraphTextPosition
)
from modules.cards.InsetTitleCard import InsetTitleCard
from modules.cards.LandscapeTitleCard import LandscapeTitleCard
from modules.cards.LogoTitleCard import LogoTitleCard
from modules.cards.MarvelTitleCard import MarvelTitleCard
from modules.cards.MusicTitleCard import (
    MusicTitleCard, PlayerAction, PlayerPosition, PlayerStyle,
)
from modules.cards.OlivierTitleCard import OlivierTitleCard
from modules.cards.OverlineTitleCard import OverlineTitleCard
from modules.cards.PosterTitleCard import PosterTitleCard
from modules.cards.RomanNumeralTitleCard import RomanNumeralTitleCard
from modules.cards.ShapeTitleCard import (
    Shape, ShapeTitleCard, TextPosition as ShapeTextPosition
)
from modules.cards.StandardTitleCard import StandardTitleCard
from modules.cards.StarWarsTitleCard import StarWarsTitleCard
from modules.cards.TintedFrameTitleCard import TintedFrameTitleCard
from modules.cards.TintedGlassTitleCard import TintedGlassTitleCard
from modules.cards.WhiteBorderTitleCard import WhiteBorderTitleCard

LocalCardIdentifiers = Literal[
    'anime', 'banner', 'calligraphy', 'comic book', 'cutout', 'divider', 'fade',
    'formula 1', 'frame', 'generic', 'graph', 'gundam', 'inset', 'ishalioh',
    'landscape', 'logo', 'marvel', 'music', 'musikmann', 'olivier', 'phendrena',
    'photo', 'polymath', 'poster', 'reality tv', 'roman', 'roman numeral',
    'shape', 'sherlock', 'standard', 'star wars', 'textless', 'tinted glass',
    '4x3', 'white border',
]

"""
Base classes
"""
class Extra(Base):
    name: str
    identifier: DictKey
    description: str
    tooltip: Optional[str] = None
    card_type: Optional[str] = None

class BaseCardModel(Base):
    source_file: FilePath
    card_file: Path
    blur: bool = False
    grayscale: bool = False

class BaseCardTypeAllText(BaseCardModel):
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

class BaseCardTypeCustomFontNoText(BaseCardModel):
    font_color: BetterColor
    font_file: FilePath
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_kerning: float = 1.0
    font_size: PositiveFloat = 1.0
    font_stroke_width: float = 1.0
    font_vertical_shift: int = 0

class BaseCardTypeCustomFontAllText(BaseCardTypeAllText):
    font_color: BetterColor
    font_file: FilePath
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_kerning: float = 1.0
    font_size: PositiveFloat = 1.0
    font_stroke_width: float = 1.0
    font_vertical_shift: int = 0

"""
Creation classes
"""
class AnimeCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = AnimeTitleCard.TITLE_COLOR
    font_file: FilePath = AnimeTitleCard.TITLE_FONT
    kanji: Optional[str] = None
    require_kanji: bool = False
    kanji_color: Optional[str] = AnimeTitleCard.TITLE_COLOR
    kanji_vertical_shift: int = 0
    separator: str = '·'
    omit_gradient: bool = False
    stroke_color: BetterColor = 'black'
    episode_stroke_color: str = AnimeTitleCard.EPISODE_STROKE_COLOR
    episode_text_color: BetterColor = AnimeTitleCard.SERIES_COUNT_TEXT_COLOR

    @root_validator(skip_on_failure=True)
    def validate_kanji(cls, values: dict) -> dict:
        if values['require_kanji'] and not values['kanji']:
            raise ValueError(f'Kanji is required and not specified')

        return values

class BannerCardType(BaseCardTypeAllText):
    font_color: BetterColor = BannerTitleCard.TITLE_COLOR
    font_file: FilePath = BannerTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_kerning: float = 1.0
    font_size: PositiveFloat = 1.0
    font_vertical_shift: int = 0
    alternate_color: BetterColor = BannerTitleCard.EPISODE_TEXT_COLOR
    banner_color: Optional[BetterColor] = None
    banner_height: PositiveInt = BannerTitleCard.BANNER_HEIGHT
    episode_text_font_size: PositiveFloat = 1.0
    hide_banner: bool = False
    x_offset: PositiveInt = BannerTitleCard.X_OFFSET

    @root_validator(skip_on_failure=True)
    def assign_unassigned_color(cls, values):
        # None means match font color
        if values['banner_color'] is None:
            values['banner_color'] = values['font_color']

        return values

class CalligraphyCardType(BaseCardTypeCustomFontAllText):
    season_text: str
    episode_text: str
    font_color: BetterColor = CalligraphyTitleCard.TITLE_COLOR
    font_file: FilePath = CalligraphyTitleCard.TITLE_FONT
    logo_file: Path
    watched: bool = False
    add_texture: bool = True
    deep_blur_if_unwatched: bool = True
    episode_text_color: Optional[BetterColor] = None
    episode_text_font_size: PositiveFloat = 1.0
    logo_size: PositiveFloat = 1.0
    offset_titles: bool = True
    randomize_texture: bool = True
    separator: str = '-'
    shadow_color: BetterColor = 'black'

    @root_validator(skip_on_failure=True)
    def assign_unassigned_color(cls, values):
        # None means match font color
        if values['episode_text_color'] is None:
            values['episode_text_color'] = values['font_color']

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
            if lower >= upper:
                raise ValueError(f'Lower bound must be below upper bound')

            return uniform(lower, upper)

        return val

    @root_validator(skip_on_failure=True)
    def assign_unassigned_color(cls, values):
        # None means match font color
        if values['text_box_edge_color'] is None:
            values['text_box_edge_color'] = values['font_color']

        return values

class CutoutCardType(BaseCardModel):
    title_text: str
    episode_text: constr(to_upper=True)
    font_color: BetterColor = CutoutTitleCard.TITLE_COLOR
    font_file: FilePath = CutoutTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_size: PositiveFloat = 1.0
    font_vertical_shift: int = 0
    blur_edges: bool = False
    overlay_color: BetterColor = 'black'
    overlay_transparency: confloat(ge=0.0, le=1.0) = 0.0

TextPosition = Literal[
    'upper left', 'upper right', 'right', 'lower right', 'lower left', 'left'
]
class DividerCardType(BaseCardTypeCustomFontAllText):
    season_text: str
    episode_text: str
    font_color: BetterColor = DividerTitleCard.TITLE_COLOR
    font_file: FilePath = DividerTitleCard.TITLE_FONT
    stroke_color: BetterColor = 'black'
    divider_color: Optional[BetterColor] = None
    text_gravity: Optional[TextGravity] = None
    title_text_position: Literal['left', 'right'] = 'left'
    text_position: TextPosition = 'lower right'

    @root_validator(skip_on_failure=True)
    def assign_unassigned_color(cls, values):
        # None means match font color
        if values['divider_color'] is None:
            values['divider_color'] = values['font_color']

        return values

class FadeCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = FadeTitleCard.TITLE_COLOR
    font_file: FilePath = FadeTitleCard.TITLE_FONT
    logo_file: Optional[Path] = None
    episode_text_color: BetterColor = FadeTitleCard.EPISODE_TEXT_COLOR
    separator: str = '•'

class FormulaOneCardType(BaseCardTypeAllText):
    airdate: Optional[datetime] = None
    font_color: BetterColor = FormulaOneTitleCard.TITLE_COLOR
    font_file: FilePath = FormulaOneTitleCard.TITLE_FONT
    font_size: PositiveFloat = 1.0
    country: Optional[FormulaOneCountry] = None
    episode_text_color: str = FormulaOneTitleCard.EPISODE_TEXT_COLOR
    episode_text_font_size: PositiveFloat = 1.0
    flag: Optional[Path] = None
    frame_year: Optional[Union[Literal[2023], Literal[2024]]] = None
    race: constr(min_length=1, to_upper=True) = 'GRAND PRIX'

    @root_validator(skip_on_failure=True)
    def parse_country(cls, values: dict) -> dict:
        if values['country'] is None:
            if values['season_text'].upper() in FormulaOneTitleCard._COUNTRY_FLAGS:
                values['country'] = values['season_text']
            else:
                values['country'] = 'generic'

        return values

    @root_validator(skip_on_failure=True)
    def validate_flag(cls, values: dict) -> dict:
        if values['flag'] is not None:
            if not values['flag'].exists():
                raise ValueError(f'Specified Flag file does not exist')
        return values

    @root_validator(skip_on_failure=True)
    def validate_frame_year(cls, values: dict) -> dict:
        if values['frame_year'] is None:
            if values.get('airdate'):
                values['frame_year'] = values['airdate'].year
            else:
                values['frame_year'] = 2024
        return values


class FrameCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = FrameTitleCard.TITLE_COLOR
    font_file: FilePath = FrameTitleCard.TITLE_FONT
    episode_text_color: BetterColor = FrameTitleCard.EPISODE_TEXT_COLOR
    episode_text_position: Literal['left', 'right', 'surround'] = 'surround'

_graph_episode_text_regex = re_compile(r'^(\d+)\s*\/\s*(\d+)$')
class GraphCardType(BaseCardModel):
    title_text: str
    episode_text: constr(to_upper=True)
    hide_episode_text: bool = False
    font_color: BetterColor
    font_file: FilePath
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_kerning: float = 1.0
    font_size: PositiveFloat = 1.0
    font_vertical_shift: int = 0
    graph_text_font_size: Optional[PositiveFloat] = None
    grayscale: bool = False
    graph_background_color: str = GraphTitleCard.BACKGROUND_GRAPH_COLOR
    graph_color: str = GraphTitleCard.GRAPH_COLOR
    graph_inset: conint(ge=0, le=1800) = GraphTitleCard.GRAPH_INSET
    graph_radius: conint(ge=50, le=900) = GraphTitleCard.GRAPH_RADIUS
    graph_width: PositiveInt = GraphTitleCard.GRAPH_WIDTH
    fill_scale: confloat(gt=0.0, le=1.0) = GraphTitleCard.GRAPH_FILL_SCALE
    percentage: confloat(ge=0.0, le=1.0) = 0.75
    text_position: GraphTextPosition = 'lower left'

    @root_validator(skip_on_failure=True)
    def validate_extras(cls, values: dict) -> dict:
        # Toggle text hiding
        values['hide_episode_text'] |= (len(values['episode_text']) == 0)

        # Ensure graph width is less than radius
        if values.get('graph_width', 0) > values.get('graph_radius', 0):
            values['graph_width'] = values['graph_radius']

        # Scale episode text size by radius if not provided
        if values.get('graph_text_font_size', None) is None:
            values['graph_text_font_size'] = \
                (values['graph_radius'] - 0) / GraphTitleCard.GRAPH_RADIUS

        # Episode text formatted as {nom} / {den}; calculate percentage
        if (_match := _graph_episode_text_regex.match(values['episode_text'])):
            values['percentage'] = int(_match[1]) / int(_match[2])

        return values

class InsetCardType(BaseCardTypeAllText):
    font_color: BetterColor = InsetTitleCard.TITLE_COLOR
    font_file: FilePath = InsetTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_kerning: float = 1.0
    font_size: PositiveFloat = 1.0
    font_vertical_shift: int = 0
    episode_text_color: BetterColor = InsetTitleCard.EPISODE_TEXT_COLOR
    episode_text_font_size: PositiveFloat = 1.0
    omit_gradient: bool = False
    separator: str = '-'
    transparency: confloat(ge=0.0, le=1.0) = 1.0

BoxAdjustmentRegex = r'^([-+]?\d+)\s+([-+]?\d+)\s+([-+]?\d+)\s+([-+]?\d+)$'
BoxAdjustments = constr(regex=BoxAdjustmentRegex)
class LandscapeCardType(BaseCardModel):
    title_text: str
    font_color: BetterColor = LandscapeTitleCard.TITLE_COLOR
    font_file: FilePath = LandscapeTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_kerning: float = 1.0
    font_size: PositiveFloat = 1.0
    font_vertical_shift: int = 0
    add_bounding_box: bool = True
    box_adjustments: BoxAdjustments = (0, 0, 0, 0)
    box_color: Optional[BetterColor] = None
    box_width: PositiveInt = LandscapeTitleCard.BOX_WIDTH
    darken: Union[Literal['all', 'box'], bool] = 'box'

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
    source_file: Optional[Path] = None
    logo_file: FilePath
    font_color: BetterColor = LogoTitleCard.TITLE_COLOR
    font_file: Path = LogoTitleCard.TITLE_FONT
    background: BetterColor = 'black'
    blur_only_image: bool = False
    logo_size: PositiveFloat = 1.0
    logo_vertical_shift: int = 0
    omit_gradient: bool = True
    separator: str = '•'
    stroke_color: BetterColor = 'black'
    use_background_image: bool = False

    @root_validator(skip_on_failure=True)
    def validate_source_file(cls, values):
        if (values['use_background_image'] and
            (not values['source_file'] or not values['source_file'].exists())):
            raise ValueError(f'Source file indicated and does not exist')

        return values

class MarvelCardType(BaseCardTypeCustomFontAllText):
    font_file: FilePath = MarvelTitleCard.TITLE_FONT
    font_color: BetterColor = MarvelTitleCard.TITLE_COLOR
    border_color: BetterColor = MarvelTitleCard.DEFAULT_BORDER_COLOR
    border_size: PositiveInt = MarvelTitleCard.DEFAULT_BORDER_SIZE
    episode_text_color: BetterColor = MarvelTitleCard.EPISODE_TEXT_COLOR
    episode_text_location: Literal['compact', 'fixed'] = 'fixed'
    fit_text: bool = True
    hide_border: bool = False
    text_box_color: BetterColor = MarvelTitleCard.DEFAULT_TEXT_BOX_COLOR
    text_box_height: PositiveInt = MarvelTitleCard.DEFAULT_TEXT_BOX_HEIGHT

ControlColorRegex = r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$'
ColorControls = constr(regex=ControlColorRegex)
class MusicCardType(BaseCardTypeCustomFontAllText):
    font_file: FilePath = MusicTitleCard.TITLE_FONT
    font_color: str = MusicTitleCard.TITLE_COLOR
    add_controls: bool = False
    album_cover: Optional[FilePath] = None
    album_size: PositiveFloat = 1.0
    control_colors: ColorControls = MusicTitleCard.DEFAULT_CONTROL_COLORS
    draw_heart: bool = False
    episode_text_color: str = MusicTitleCard.EPISODE_TEXT_COLOR
    percentage: Union[confloat(ge=0.0, le=1.0), str, Literal['random']] = 'random'
    heart_color: str = 'transparent'
    heart_stroke_color: str = 'white'
    pause_or_play: PlayerAction = None
    player_color: str = MusicTitleCard.DEFAULT_PLAYER_COLOR
    player_inset: conint(ge=0, le=1800) = MusicTitleCard.DEFAULT_INSET
    player_position: PlayerPosition = MusicTitleCard.DEFAULT_PLAYER_POSITION
    player_style: PlayerStyle = MusicTitleCard.DEFAULT_PLAYER_STYLE
    player_width: conint(ge=400, le=3200) = MusicTitleCard.DEFAULT_PLAYER_WIDTH
    round_corners: bool = True
    subtitle: str = '{series_name}'
    timeline_color: str = MusicTitleCard.DEFAULT_TIMELINE_COLOR
    truncate_long_titles: Union[PositiveInt, Literal['False']] = 2
    watched: Optional[bool] = None

    @validator('control_colors')
    def parse_control_colors(cls, val):
        return tuple(re_match(ControlColorRegex, val).groups())

    @root_validator(skip_on_failure=True)
    def assign_unassigned_player_action(cls, values: dict) -> dict:
        if (values['pause_or_play'] is None
            and values['watched'] is not None):
            values['pause_or_play']  = 'pause' if values['watched'] else 'play'
        return values

    @root_validator(skip_on_failure=True)
    def validate_player_width(cls, values: dict) -> dict:
        if values['add_controls'] and values['player_width'] < 600:
            raise ValueError('Player width must be at least 600')
        return values

    @root_validator(skip_on_failure=True, pre=True)
    def finalize_format_strings(cls, values: dict) -> dict:
        if ((percentage := values.get('percentage', 'random')) is not None
            and isinstance(percentage, str)
            and percentage != 'random'):
            p = float(FormatString(percentage, data=values).result)
            values['percentage'] = max(0.0, min(1.0, p)) # Limit [0.0, 1.0]
        if (subtitle := values.get('subtitle', '{series_name}')) is not None:
            values['subtitle'] = FormatString(subtitle, data=values).result

        return values

    @root_validator(skip_on_failure=True)
    def truncate_long_titles_(cls, values: dict) -> dict:
        if (truncate := values.get('truncate_long_titles', 2)) != 'False':
            if len(lines := values['title_text'].splitlines()) > truncate:
                values['title_text'] = '\n'.join(lines[:truncate]) + ' ...'
            if len(values['season_text']) > 3:
                values['season_text'] = values['season_text'][:3] + '..'
            if len(values['episode_text']) > 3:
                values['episode_text'] = values['episode_text'][:3] + '..'

        return values

    @root_validator(skip_on_failure=True, pre=True)
    def validate_album_cover(cls, values: dict) -> dict:
        # Set album cover based on indicated player style
        if values.get('album_cover') is None:
            style = values.get('player_style', MusicTitleCard.DEFAULT_PLAYER_STYLE)
            if style == 'artwork':
                values['album_cover'] = values['backdrop_file']
            elif style == 'logo':
                values['album_cover'] = values['logo_file']
            elif style == 'poster':
                values['album_cover'] = values['poster_file']

        # Parse format strings in album cover
        if (cover := values.get('album_cover')):
            cover = Path(FormatString(str(cover), data=values).result)
            if not cover.exists():
                cover = values['source_file'].parent / cover.name
            values['album_cover'] = cover

        # If no album cover is indicated and not in basic mode, error
        if (values.get('album_cover') is None
            and values['player_style'] != 'basic'):
            raise ValueError(f'Cover must exist')

        return values

class OlivierCardType(BaseCardTypeCustomFontNoText):
    title_text: str
    episode_text: constr(to_upper=True)
    hide_episode_text: bool = False
    font_color: BetterColor = OlivierTitleCard.TITLE_COLOR
    font_file: FilePath = OlivierTitleCard.TITLE_FONT
    episode_text_color: BetterColor = OlivierTitleCard.EPISODE_TEXT_COLOR
    episode_text_font_size: PositiveFloat = 1.0
    episode_text_vertical_shift: int = 0
    stroke_color: BetterColor = OlivierTitleCard.STROKE_COLOR

    @root_validator(skip_on_failure=True)
    def toggle_text_hiding(cls, values):
        values['hide_episode_text'] |= (len(values['episode_text']) == 0)

        return values

class OverlineCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = OverlineTitleCard.TITLE_COLOR
    font_file: FilePath = OverlineTitleCard.TITLE_FONT
    episode_text_color: Optional[BetterColor] = None
    hide_line: bool = False
    line_color: Optional[BetterColor] = None
    line_position: Literal['top', 'bottom'] = 'top'
    line_width: PositiveInt = OverlineTitleCard.LINE_THICKNESS
    omit_gradient: bool = False
    separator: str = '-'

    @root_validator(skip_on_failure=True)
    def assign_unassigned_color(cls, values):
        if values['episode_text_color'] is None:
            values['episode_text_color'] = values['font_color']
        if values['line_color'] is None:
            if values['episode_text_color'] is None:
                values['line_color'] = values['font_color']
            else:
                values['line_color'] = values['episode_text_color']

        return values

class PosterCardType(BaseCardModel):
    title_text: str
    episode_text: constr(to_upper=True)
    font_color: BetterColor = PosterTitleCard.TITLE_COLOR
    font_file: FilePath = PosterTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_size: PositiveFloat = 1.0
    logo_file: Optional[Path] = None
    episode_text_color: Optional[BetterColor] = None

    @root_validator(skip_on_failure=True)
    def assign_episode_text_color(cls, values):
        # None means match font color
        if values['episode_text_color'] is None:
            values['episode_text_color'] = values['font_color']

        return values

RomanNumeralValue = conint(gt=0, le=RomanNumeralTitleCard.MAX_ROMAN_NUMERAL)
class RomanNumeralCardType(BaseCardTypeAllText):
    source_file: Any
    episode_number: RomanNumeralValue
    font_color: BetterColor = RomanNumeralTitleCard.TITLE_COLOR
    font_file: FilePath = RomanNumeralTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_size: PositiveFloat = 1.0
    background: BetterColor = RomanNumeralTitleCard.BACKGROUND_COLOR
    roman_numeral_color: BetterColor = RomanNumeralTitleCard.ROMAN_NUMERAL_TEXT_COLOR
    season_text_color: BetterColor = RomanNumeralTitleCard.SEASON_TEXT_COLOR

RandomShapeRegex = (
    r'random\[\s*((circle|diamond|square|down triangle|up triangle)'
    r'\s*(,\s*(circle|diamond|square|down triangle|up triangle))*)\]'
)
RandomShape = constr(regex=RandomShapeRegex)
class ShapeCardType(BaseCardTypeAllText):
    season_text: str
    episode_text: str
    font_color: BetterColor = ShapeTitleCard.TITLE_COLOR
    font_file: FilePath = ShapeTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_kerning: float = 1.0
    font_size: PositiveFloat = 1.0
    font_stroke_width: float = 1.0
    font_vertical_shift: int = 0
    hide_shape: bool = False
    italicize_season_text: bool = False
    omit_gradient: bool = False
    season_text_color: Optional[BetterColor] = None
    season_text_font_size: PositiveFloat = 1.0
    season_text_position: Literal['above', 'below'] = 'below'
    shape: Union[Shape, Literal['random'], RandomShape] = ShapeTitleCard.DEFAULT_SHAPE
    shape_color: BetterColor = ShapeTitleCard.SHAPE_COLOR
    shape_inset: conint(ge=0, le=1800) = ShapeTitleCard.SHAPE_INSET
    shape_size: confloat(gt=0.3) = 1.0
    shape_stroke_color: str = ShapeTitleCard.SHAPE_STROKE_COLOR
    shape_stroke_width: conint(ge=0) = 0
    shape_width: PositiveInt = ShapeTitleCard.SHAPE_WIDTH
    stroke_color: BetterColor = 'black'
    text_position: ShapeTextPosition = 'lower left'

    @root_validator(skip_on_failure=True)
    def validate_extras(cls, values):
        # Add episode text before title text if not hiding
        if values.get('hide_episode_text', False) is not True:
            values['title_text'] = f'{values["episode_text"]} {values["title_text"]}'

        # Convert None colors to the default font color
        if values['season_text_color'] is None:
            values['season_text_color'] = values['shape_color']

        return values

class StandardCardType(BaseCardTypeCustomFontAllText):
    font_color: BetterColor = StandardTitleCard.TITLE_COLOR
    font_file: FilePath = StandardTitleCard.TITLE_FONT
    omit_gradient: bool = False
    separator: str = '•'
    stroke_color: BetterColor = 'black'
    episode_text_color: BetterColor = StandardTitleCard.SERIES_COUNT_TEXT_COLOR
    episode_text_font_size: PositiveFloat = 1.0

class StarWarsCardType(BaseCardModel):
    title_text: str
    episode_text: constr(to_upper=True)
    hide_episode_text: bool = False
    font_color: BetterColor = StarWarsTitleCard.TITLE_COLOR
    font_file: FilePath = StarWarsTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_size: PositiveFloat = 1.0
    font_vertical_shift: int = 0
    episode_text_color: BetterColor = StarWarsTitleCard.EPISODE_TEXT_COLOR

    @root_validator(skip_on_failure=True)
    def toggle_text_hiding(cls, values):
        values['hide_episode_text'] |= (len(values['episode_text']) == 0)

        return values

class TextlessCardType(BaseCardModel):
    pass

OuterElement = Literal['index', 'logo', 'omit', 'title']
MiddleElement = Literal['logo', 'omit']
class TintedFrameCardType(BaseCardTypeAllText):
    logo_file: Path
    font_color: BetterColor = TintedFrameTitleCard.TITLE_COLOR
    font_file: FilePath = TintedFrameTitleCard.TITLE_FONT
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_kerning: float = 1.0
    font_size: PositiveFloat = 1.0
    font_vertical_shift: int = 0
    separator: str = '-'
    episode_text_color: Optional[BetterColor] = None
    episode_text_font: FilePath = TintedFrameTitleCard.EPISODE_TEXT_FONT
    episode_text_font_size: PositiveFloat = 1.0
    episode_text_vertical_shift: int = 0
    frame_color: Optional[BetterColor] = None
    frame_width: PositiveInt = TintedFrameTitleCard.BOX_WIDTH
    top_element: OuterElement = 'title'
    middle_element: MiddleElement = 'omit'
    bottom_element: OuterElement = 'index'
    logo_size: PositiveFloat = 1.0
    logo_vertical_shift: int = 0
    blur_edges: bool = True
    shadow_color: str = TintedFrameTitleCard.SHADOW_COLOR

    @root_validator(skip_on_failure=True)
    def validate_episode_text_font_file(cls, values: dict) -> dict:
        etf = values['episode_text_font']
        # Episode text font does not exist, search alongside source image
        if isinstance(etf, Path) and not etf.exists():
            if (new_etf := values['source_file'].parent / etf.name).exists():
                values['episode_text_font'] = new_etf

        return values

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
    box_adjustments: BoxAdjustments = (0, 0, 0, 0)
    episode_text_color: BetterColor = TintedGlassTitleCard.EPISODE_TEXT_COLOR
    episode_text_position: EpisodeTextPosition = 'center'
    glass_color: BetterColor = TintedGlassTitleCard.DARKEN_COLOR
    vertical_adjustment: int = 0

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
    border_color: BetterColor = 'white'
    stroke_color: BetterColor = WhiteBorderTitleCard.STROKE_COLOR
    episode_text_color: BetterColor = WhiteBorderTitleCard.TITLE_COLOR
    episode_text_font_size: PositiveFloat = 1.0

LocalCardTypeModels: dict[str, Base] = {
    '4x3': FadeCardType,
    'anime': AnimeCardType,
    'banner': BannerCardType,
    'blurred border': TintedFrameCardType,
    'calligraphy': CalligraphyCardType,
    'comic book': ComicBookCardType,
    'cutout': CutoutCardType,
    'divider': DividerCardType,
    'fade': FadeCardType,
    'formula 1': FormulaOneCardType,
    'frame': FrameCardType,
    'generic': StandardCardType,
    'graph': GraphCardType,
    'gundam': PosterCardType,
    'inset': InsetCardType,
    'ishalioh': OlivierCardType,
    'landscape': LandscapeCardType,
    'logo': LogoCardType,
    'marvel': MarvelCardType,
    'music': MusicCardType,
    'musikmann': WhiteBorderCardType,
    'olivier': OlivierCardType,
    'overline': OverlineCardType,
    'phendrena': CutoutCardType,
    'photo': FrameCardType,
    'polymath': StandardCardType,
    'poster': PosterCardType,
    'reality tv': LogoCardType,
    'roman': RomanNumeralCardType,
    'roman numeral': RomanNumeralCardType,
    'shape': ShapeCardType,
    'sherlock': TintedGlassCardType,
    'standard': StandardCardType,
    'star wars': StarWarsCardType,
    'textless': TextlessCardType,
    'tinted glass': TintedGlassCardType,
    'tinted frame': TintedFrameCardType,
    'white border': WhiteBorderCardType,
}
