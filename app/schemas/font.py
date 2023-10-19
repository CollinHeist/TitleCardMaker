# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from pathlib import Path
from typing import Literal, Optional

from pydantic import ( # pylint: disable=no-name-in-module
    NonNegativeFloat, PositiveFloat, constr, validator, root_validator
)

from app.schemas.base import (
    Base, BetterColor, UpdateBase, UNSPECIFIED, validate_argument_lists_to_dict
)


TitleCase = Literal['blank', 'lower', 'source', 'title', 'upper']

DefaultFont = {
    'font_interline_spacing': 0,
    'font_interword_spacing': 0,
    'font_kerning': 1.0,
    'font_size': 1.0,
    'font_stroke_width': 1.0,
    'font_vertical_shift': 0,
}

"""
Base classes
"""
class BaseFont(Base):
    color: Optional[BetterColor] = None
    title_case: Optional[TitleCase] = None
    size: NonNegativeFloat = 1.0
    kerning: float = 1.0
    stroke_width: float = 1.0
    interline_spacing: int = 0
    interword_spacing: int = 0
    vertical_shift: int = 0

class BaseNamedFont(BaseFont):
    name: constr(min_length=1)
    delete_missing: bool = True

"""
Creation classes
"""
class NewNamedFont(BaseNamedFont):
    replacements_in: list[constr(min_length=1)] = []
    replacements_out: list[str] = []

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('replacements_in', 'replacements_out', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @root_validator
    def validate_paired_lists(cls, values):
        return validate_argument_lists_to_dict(
            values, 'character replacements',
            'replacements_in', 'replacements_out',
            output_key='replacements',
            allow_empty_strings=True,
        )

class PreviewFont(Base):
    color: Optional[BetterColor] = None
    size: Optional[PositiveFloat] = None
    kerning: Optional[float] = None
    stroke_width: Optional[float] = None
    interline_spacing: Optional[int] = None
    interword_spacing: Optional[int] = None
    vertical_shift: Optional[int] = None

"""
Update classes
"""
class UpdateNamedFont(UpdateBase):
    name: constr(min_length=1) = UNSPECIFIED
    color: Optional[BetterColor] = UNSPECIFIED
    title_case: Optional[TitleCase] = UNSPECIFIED
    size: PositiveFloat = UNSPECIFIED
    kerning: float = UNSPECIFIED
    stroke_width: float = UNSPECIFIED
    interline_spacing: int = UNSPECIFIED
    interword_spacing: int = UNSPECIFIED
    vertical_shift: int = UNSPECIFIED
    delete_missing: bool = UNSPECIFIED
    replacements_in: list[str] = UNSPECIFIED
    replacements_out: list[str] = UNSPECIFIED

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('replacements_in', 'replacements_out', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @root_validator
    def validate_paired_lists(cls, values):
        return validate_argument_lists_to_dict(
            values, 'character replacements',
            'replacements_in', 'replacements_out',
            output_key='replacements',
            allow_empty_strings=True,
        )

"""
Return classes
"""
class FontAnalysis(Base):
    replacements: dict[str, str] = {}
    missing: list[str] = []

class SeriesFont(BaseFont):
    replacements: dict[str, str]
    delete_missing: bool

class NamedFont(BaseNamedFont):
    id: int
    sort_name: str
    file: Optional[Path]
    file_name: Optional[str]
    replacements: dict[str, str]
