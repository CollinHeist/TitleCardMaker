# pylint: disable=missing-class-docstring,missing-function-docstring,no-name-in-module
from typing import Optional

from pydantic import DirectoryPath, Field

from app.schemas.base import Base
from app.schemas.preferences import CardExtension

"""
Base classes
"""
class ImportBase(Base):
    yaml: str

"""
Return classes
"""
class ImportYaml(ImportBase):
    ...

class ImportSeriesYaml(ImportBase):
    default_library: Optional[str] = Field(default=None, min_length=1)

class ImportCardDirectory(Base):
    directory: Optional[DirectoryPath] = None
    image_extension: CardExtension = '.jpg'
    force_reload: bool = False

class MultiCardImport(Base):
    series_ids: list[int]
    image_extension: CardExtension = '.jpg'
    force_reload: bool = False
