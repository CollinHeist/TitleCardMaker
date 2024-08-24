# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false
from pathlib import Path
from typing import Literal, Optional

from pydantic import ( # pylint: disable=no-name-in-module
    NonNegativeFloat,
    PositiveFloat,
    constr,
    root_validator,
    validator,
)

from app.schemas.base import Base, UpdateBase, UNSPECIFIED


TitleCase = Literal['blank', 'lower', 'source', 'title', 'upper']

DefaultFont = {
    'font_interline_spacing': 0,
    'font_interword_spacing': 0,
    'font_kerning': 1.0,
    'font_line_split_modifier': 0,
    'font_size': 1.0,
    'font_stroke_width': 1.0,
    'font_vertical_shift': 0,
}

"""
Base classes
"""
class BaseFont(Base):
    color: Optional[str] = None
    interline_spacing: int = 0
    interword_spacing: int = 0
    kerning: float = 1.0
    line_split_modifier: int = 0
    size: NonNegativeFloat = 1.0
    stroke_width: float = 1.0
    title_case: Optional[TitleCase] = None
    vertical_shift: int = 0

class BaseNamedFont(BaseFont):
    name: constr(min_length=1)

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
        if len(values['replacements_in']) != len(values['replacements_out']):
            raise ValueError('Must provide same number of in/out replacements')
        return values

class PreviewFont(Base):
    color: Optional[str] = None
    kerning: Optional[float] = None
    interline_spacing: Optional[int] = None
    interword_spacing: Optional[int] = None
    size: Optional[PositiveFloat] = None
    stroke_width: Optional[float] = None
    vertical_shift: Optional[int] = None

"""
Update classes
"""
class UpdateNamedFont(UpdateBase):
    name: constr(min_length=1) = UNSPECIFIED
    color: Optional[str] = UNSPECIFIED
    interline_spacing: int = UNSPECIFIED
    interword_spacing: int = UNSPECIFIED
    kerning: float = UNSPECIFIED
    line_split_modifier: int = UNSPECIFIED
    replacements_in: list[str] = UNSPECIFIED
    replacements_out: list[str] = UNSPECIFIED
    size: PositiveFloat = UNSPECIFIED
    stroke_width: float = UNSPECIFIED
    title_case: Optional[TitleCase] = UNSPECIFIED
    vertical_shift: int = UNSPECIFIED

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('replacements_in', 'replacements_out', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @root_validator
    def validate_paired_lists(cls, values):
        if len(values['replacements_in']) != len(values['replacements_out']):
            raise ValueError('Must provide same number of in/out replacements')
        return values

"""
Return classes
"""
class FontAnalysis(Base):
    replacements: dict[str, str] = {}
    missing: list[str] = []

class NamedFont(BaseNamedFont):
    id: int
    sort_name: str
    file: Optional[Path]
    file_name: Optional[str]
    replacements_in: list[str]
    replacements_out: list[str]
