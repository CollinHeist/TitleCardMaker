# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Literal, Optional

from pydantic import Field, constr, validator, root_validator

from app.schemas.base import (
    Base, UpdateBase, UNSPECIFIED, validate_argument_lists_to_dict
)


TitleCase = Literal['blank', 'lower', 'source', 'title', 'upper']

DefaultFont = {
    'font_interline_spacing': 0,
    'font_kerning': 1.0,
    'font_size': 1.0,
    'font_stroke_width': 1.0,
    'font_vertical_shift': 0,
}

"""
Base classes
"""
class BaseFont(Base):
    color: Optional[str] = Field(default=None, min_length=1, title='Font color')
    title_case: Optional[TitleCase] = Field(
        default=None,
        description='Name of the case function to apply to the title text',
    )
    size: float = Field(
        default=1.0,
        gt=0.0,
        title='Font size (scalar)'
    )
    kerning: float = 1.0
    stroke_width: float = 1.0
    interline_spacing: int = 0
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
    color: Optional[str] = Field(default=None, min_length=1)
    size: Optional[float] = Field(default=None, gt=0.0)
    kerning: Optional[float] = None
    stroke_width: Optional[float] = None
    interline_spacing: Optional[int] = None
    vertical_shift: Optional[int] = None

"""
Update classes
"""
class UpdateNamedFont(UpdateBase):
    name: str = Field(default=UNSPECIFIED, min_length=1)
    color: Optional[str] = Field(default=UNSPECIFIED, min_length=1)
    title_case: Optional[TitleCase] = UNSPECIFIED
    size: float = Field(default=UNSPECIFIED, gt=0.0)
    kerning: float = UNSPECIFIED
    stroke_width: float = UNSPECIFIED
    interline_spacing: int = UNSPECIFIED
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
class SeriesFont(BaseFont):
    replacements: dict[str, str]
    delete_missing: bool

class NamedFont(BaseNamedFont):
    id: int
    sort_name: str
    file: Optional[str]
    file_name: Optional[str]
    replacements: dict[str, str]
