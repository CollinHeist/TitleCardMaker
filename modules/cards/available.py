from typing import TYPE_CHECKING
from modules.cards.AnimeTitleCard import AnimeTitleCard
from modules.cards.BannerTitleCard import BannerTitleCard
from modules.cards.CalligraphyTitleCard import CalligraphyTitleCard
from modules.cards.ComicBookTitleCard import ComicBookTitleCard
from modules.cards.CutoutTitleCard import CutoutTitleCard
from modules.cards.DividerTitleCard import DividerTitleCard
from modules.cards.FadeTitleCard import FadeTitleCard
from modules.cards.FormulaOneTitleCard import FormulaOneTitleCard
from modules.cards.FrameTitleCard import FrameTitleCard
from modules.cards.GraphTitleCard import GraphTitleCard
from modules.cards.InsetTitleCard import InsetTitleCard
from modules.cards.LandscapeTitleCard import LandscapeTitleCard
from modules.cards.LogoTitleCard import LogoTitleCard
from modules.cards.MarvelTitleCard import MarvelTitleCard
from modules.cards.MusicTitleCard import MusicTitleCard
from modules.cards.NegativeSpaceTitleCard import NegativeSpaceTitleCard
from modules.cards.NotificationTitleCard import NotificationTitleCard
from modules.cards.OlivierTitleCard import OlivierTitleCard
from modules.cards.OverlineTitleCard import OverlineTitleCard
from modules.cards.PosterTitleCard import PosterTitleCard
from modules.cards.RomanNumeralTitleCard import RomanNumeralTitleCard
from modules.cards.ShapeTitleCard import ShapeTitleCard
from modules.cards.StandardTitleCard import StandardTitleCard
from modules.cards.StarWarsTitleCard import StarWarsTitleCard
from modules.cards.StripedTitleCard import StripedTitleCard
from modules.cards.TextlessTitleCard import TextlessTitleCard
from modules.cards.TintedFrameTitleCard import TintedFrameTitleCard
from modules.cards.TintedGlassTitleCard import TintedGlassTitleCard
from modules.cards.WhiteBorderTitleCard import WhiteBorderTitleCard

if TYPE_CHECKING:
    from modules.BaseCardType import CardTypeDescription

LocalCards: list['CardTypeDescription'] = [
    AnimeTitleCard.API_DETAILS,
    BannerTitleCard.API_DETAILS,
    CalligraphyTitleCard.API_DETAILS,
    ComicBookTitleCard.API_DETAILS,
    CutoutTitleCard.API_DETAILS,
    DividerTitleCard.API_DETAILS,
    FadeTitleCard.API_DETAILS,
    FormulaOneTitleCard.API_DETAILS,
    FrameTitleCard.API_DETAILS,
    GraphTitleCard.API_DETAILS,
    InsetTitleCard.API_DETAILS,
    LandscapeTitleCard.API_DETAILS,
    LogoTitleCard.API_DETAILS,
    MarvelTitleCard.API_DETAILS,
    MusicTitleCard.API_DETAILS,
    NegativeSpaceTitleCard.API_DETAILS,
    NotificationTitleCard.API_DETAILS,
    OlivierTitleCard.API_DETAILS,
    OverlineTitleCard.API_DETAILS,
    PosterTitleCard.API_DETAILS,
    RomanNumeralTitleCard.API_DETAILS,
    ShapeTitleCard.API_DETAILS,
    StandardTitleCard.API_DETAILS,
    StarWarsTitleCard.API_DETAILS,
    StripedTitleCard.API_DETAILS,
    TextlessTitleCard.API_DETAILS,
    TintedFrameTitleCard.API_DETAILS,
    TintedGlassTitleCard.API_DETAILS,
    WhiteBorderTitleCard.API_DETAILS,
]
