from typing import Literal, Optional, Union

from app.schemas.base import Base

TitleCase = Literal['blank', 'lower', 'source', 'title', 'upper']

class Font(Base):
    id: int
    name: str
    file_path: Optional[str]
    color: Optional[str]
    title_case: Optional[TitleCase]
    size: float
    kerning: float
    stroke_width: float
    interline_spacing: int
    vertical_shift: int
    validate_characters: bool
    delete_missing: bool
    replacements: dict[str, str]