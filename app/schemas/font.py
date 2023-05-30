from typing import Literal, Optional

from pydantic import Field, validator, root_validator

from app.schemas.base import Base, UpdateBase, UNSPECIFIED, validate_argument_lists_to_dict

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
    kerning: float = Field(
        default=1.0,
        title='Font kerning (scalar)'
    )
    stroke_width: float = Field(
        default=1.0,
        title='Font stroke width (scalar)'
    )
    interline_spacing: int = Field(
        default=0,
        title='Interline spacing (pixels)',
    )
    vertical_shift: int = Field(
        default=0,
        title='Vertical shift (pixels)',
    )

class BaseNamedFont(BaseFont):
    name: str = Field(..., min_length=1, title='Font name')
    delete_missing: bool = Field(
        default=True,
        title='Delete mising characters toggle',
        description='Whether to delete missing characters before creation',
    )

"""
Creation classes
"""
class NewNamedFont(BaseNamedFont):
    replacements_in: list[str] = Field(
        default=[],
        title='Characters to replace',
    )
    replacements_out: list[str] = Field(
        default=[],
        title='Characters to substitute',
    )

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
            output_key='replacements'
        )

class PreviewFont(Base):
    color: Optional[str] = Field(default=None, min_length=1)
    size: Optional[float] = Field(default=None, gt=0.0)
    kerning: Optional[float] = Field(default=None)
    stroke_width: Optional[float] = Field(default=None)
    interline_spacing: Optional[int] = Field(default=None)
    vertical_shift: Optional[int] = Field(default=None)

"""
Update classes
"""
class UpdateNamedFont(UpdateBase):
    name: str = Field(default=UNSPECIFIED, min_length=1)
    color: Optional[str] = Field(default=UNSPECIFIED, min_length=1)
    title_case: Optional[TitleCase] = Field(default=UNSPECIFIED)
    size: float = Field(default=UNSPECIFIED, gt=0.0)
    kerning: float = Field(default=UNSPECIFIED)
    stroke_width: float = Field(default=UNSPECIFIED)
    interline_spacing: int = Field(default=UNSPECIFIED)
    vertical_shift: int = Field(default=UNSPECIFIED)
    delete_missing: bool = Field(default=UNSPECIFIED)
    replacements_in: list[str] = Field(default=UNSPECIFIED)
    replacements_out: list[str] = Field(default=UNSPECIFIED)

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
            output_key='replacements'
        )

"""
Return classes
"""
class SeriesFont(BaseFont):
    replacements: dict[str, str]
    delete_missing: bool

class NamedFont(BaseNamedFont):
    id: int
    file: Optional[str] 
    replacements: dict[str, str]