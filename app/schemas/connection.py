# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from pathlib import Path
from typing import Literal, Optional

from pydantic import ( # pylint: disable=no-name-in-module
    AnyUrl, DirectoryPath, Field, NonNegativeInt, PositiveInt, SecretStr,
    constr, root_validator, validator
)
from pydantic.error_wrappers import ValidationError

from app.schemas.base import Base, UpdateBase, UNSPECIFIED


"""
Match hexstrings of A-F and 0-9.
"""
Hexstring = constr(regex=r'^[a-fA-F0-9]+$')

"""
Base classes
"""
class SonarrLibrary(Base):
    name: str
    path: str

"""
Creation classes
"""
class NewSonarrConnection(Base):
    enabled: bool = True
    url: AnyUrl
    api_key: Hexstring
    verify_ssl: bool = True
    downloaded_only: bool = False
    libraries: list[SonarrLibrary] = []

"""
Update classes
"""
class UpdateServerBase(UpdateBase):
    url: AnyUrl = UNSPECIFIED

class UpdateSonarr2(UpdateServerBase):
    api_key: Hexstring = UNSPECIFIED
    verify_ssl: bool = UNSPECIFIED
    downloaded_only: bool = UNSPECIFIED
    libraries: list[SonarrLibrary] = UNSPECIFIED

    @validator('libraries', pre=False)
    def validate_list(cls, v):
        # Filter out empty strings - all arguments can accept empty lists
        return [library for library in v if library.name and library.path]

"""
Return classes
"""
class SonarrConnection2(Base):
    interface_id: int
    enabled: bool
    url: AnyUrl
    api_key: SecretStr
    verify_ssl: bool
    downloaded_only: bool
    libraries: list[SonarrLibrary]
