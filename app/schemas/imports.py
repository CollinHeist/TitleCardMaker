from typing import Optional

from pydantic import Field

from app.schemas.base import Base

"""
Base classes
"""
class ImportBase(Base):
    yaml: str

"""
Return classes
"""
class ImportFontYaml(ImportBase):
    ...

class ImportTemplateYaml(ImportBase):
    ...

class ImportSeriesYaml(ImportBase):
    default_library: Optional[str] = Field(default=None, min_length=1)