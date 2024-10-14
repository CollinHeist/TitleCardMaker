# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Optional

from pydantic import AnyUrl, DirectoryPath, conint

from app.schemas.base import Base
from app.schemas.preferences import CardExtension

"""
Base classes
"""
SeasonNumber: int = conint(ge=0)

class ImportBase(Base):
    yaml: str

class _KometaEpisode(Base):
    url_poster: Optional[AnyUrl] = None

class _KometaSeason(Base):
    url_poster: Optional[AnyUrl] = None
    episodes: dict[SeasonNumber, _KometaEpisode] = {}

class _KometaSeries(Base):
    url_poster: Optional[AnyUrl] = None
    url_background: Optional[AnyUrl] = None
    seasons: dict[SeasonNumber, _KometaSeason] = {}

class KometaYaml(Base):
    yaml: dict[int, _KometaSeries]

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
