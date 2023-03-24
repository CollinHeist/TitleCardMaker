from typing import Literal, Optional, Union

from fastapi import UploadFile
from pydantic import Field

from app.schemas.base import Base, UNSPECIFIED

TitleCase = Literal['blank', 'lower', 'source', 'title', 'upper']

class BaseFont(Base):
    name: str = Field(..., min_length=1, title='Font name')
    color: Optional[str] = Field(default=None, title='Font color')
    title_case: Optional[TitleCase] = Field(
        default=None,
        title='Name of the case function to apply to the title text',
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
    validate_characters: bool = Field(
        default=True,
        title='Character validation toggle',
        description='Whether to require a font has a character before creation',
    )
    delete_missing: bool = Field(
        default=True,
        title='Delete mising characters toggle',
        description='Whether to delete missing characters before creation',
    )

class NewFont(BaseFont):
    replacements_in: list[str] = Field(
        default=[],
        title='Characters to replace',
    )
    replacements_out: list[str] = Field(
        default=[],
        title='Characters to substitute',
    )

class UpdateFont(NewFont):
    name: Optional[str] = Field(default=None, min_length=1)
    color: Optional[str] = Field(default=None)
    title_case: Optional[TitleCase] = Field(default=None)
    size: Optional[float] = Field(default=None, gt=0.0)
    kerning: Optional[float] = Field(default=None)
    stroke_width: Optional[float] = Field(default=None)
    interline_spacing: Optional[int] = Field(default=None)
    vertical_shift: Optional[int] = Field(default=None)
    validate_characters: Optional[bool] = Field(default=None)
    delete_missing: Optional[bool] = Field(default=None)
    replacements_in: Optional[list[str]] = Field(default=UNSPECIFIED)
    replacements_out: Optional[list[str]] = Field(default=UNSPECIFIED)

class ExistingBaseFont(BaseFont):
    id: int = Field(..., title='Font ID')
    file_path: Optional[str] = Field(
        default=None,
        title='Font file path'
    )
    replacements: dict[str, str] = Field(
        default={},
        title='Character replacements',
    )

class Font(ExistingBaseFont):
    ...

class PreviewFont(Base):
    color: Optional[str] = Field(default=None)
    size: float = Field(default=1.0, gt=0.0, title='Font size (scalar)')
    kerning: float = Field(default=1.0, title='Font kerning (scalar)')
    stroke_width: float = Field( default=1.0,title='Font stroke width (scalar)')
    interline_spacing: int = Field(default=0,title='Interline spacing (pixels)')
    vertical_shift: int = Field(default=0, title='Vertical shift (pixels)')