# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Optional

from pydantic import DirectoryPath, Field # pylint: disable=no-name-in-module

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

class ImportCardDirectory(Base):
    directory: Optional[DirectoryPath] = None
    image_extension: CardExtension = '.jpg'
    force_reload: bool = False

class MultiCardImport(Base):
    series_ids: list[int]
    image_extension: CardExtension = '.jpg'
    force_reload: bool = False
