# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Literal, Optional
from pydantic import ( # pylint: disable=no-name-in-module
    AnyUrl, NonNegativeInt, PositiveInt, SecretStr, constr, validator  
)

from app.schemas.base import Base, MediaServer, UpdateBase, UNSPECIFIED


# Match hexstrings of A-F and 0-9.s
Hexstring = constr(regex=r'^[a-fA-F0-9]+$')

# Acceptable units for filesize limits
FilesizeUnit = Literal['Bytes', 'Kilobytes', 'Megabytes']

# Accepted TMDb 2-letter language codes
TMDbLanguageCode = Literal[
    'ar', 'bg', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es', 'fa', 'fr', 'he',
    'hu', 'id', 'it', 'ja', 'ko', 'my', 'pl', 'pt', 'ro', 'ru', 'sk', 'sr',
    'th', 'tr', 'uk', 'vi', 'zh',
]

"""
Base classes
"""
class SonarrLibrary(Base):
    name: str
    path: str
    media_server: MediaServer
    interface_id: int

class BaseServer(Base):
    interface_id: int
    enabled: bool
    url: AnyUrl
    api_key: SecretStr
    use_ssl: bool = True

class BaseNewConnection(Base):
    enabled: bool = True

class BaseNewServer(BaseNewConnection):
    url: AnyUrl
    api_key: Hexstring
    use_ssl: bool = True

class BaseNewMediaServer(BaseNewServer):
    filesize_limit_number: PositiveInt = 5
    filesize_limit_unit: FilesizeUnit = 'Megabytes'

class BaseUpdateServer(UpdateBase):
    url: AnyUrl = UNSPECIFIED
    use_ssl: bool = UNSPECIFIED

class BaseUpdateMediaServer(BaseUpdateServer):
    filesize_limit_number: PositiveInt = UNSPECIFIED
    filesize_limit_unit: FilesizeUnit = UNSPECIFIED

"""
Creation classes
"""
class NewEmbyConnection(BaseNewMediaServer):
    username: Optional[str] = None

class NewJellyfinConnection(BaseNewMediaServer):
    username: Optional[str] = None

class NewPlexConnection(BaseNewMediaServer):
    integrate_with_pmm: bool = False

class NewSonarrConnection(BaseNewServer):
    downloaded_only: bool = True
    libraries: list[SonarrLibrary] = []

class NewTautulliConnection(BaseNewServer):
    agent_name: str

"""
Update classes
"""
class UpdateEmby(BaseUpdateMediaServer):
    api_key: Hexstring = UNSPECIFIED
    username: Optional[str] = UNSPECIFIED

class UpdateJellyfin(BaseUpdateMediaServer):
    api_key: Hexstring = UNSPECIFIED
    username: Optional[str] = UNSPECIFIED

class UpdatePlex(BaseUpdateMediaServer):
    api_key: str = UNSPECIFIED
    integrate_with_pmm: bool = UNSPECIFIED

class UpdateSonarr(BaseUpdateServer):
    api_key: Hexstring = UNSPECIFIED
    use_ssl: bool = UNSPECIFIED
    downloaded_only: bool = UNSPECIFIED
    libraries: list[SonarrLibrary] = UNSPECIFIED

    @validator('libraries', pre=False)
    def remove_empty_strings(cls, v):
        return [library for library in v if library.name and library.path]

class UpdateTMDb(UpdateBase):
    api_key: Hexstring = UNSPECIFIED
    minimum_width: NonNegativeInt = UNSPECIFIED
    minimum_height: NonNegativeInt = UNSPECIFIED
    skip_localized: bool = UNSPECIFIED
    download_logos: bool = UNSPECIFIED
    logo_language_priority: list[TMDbLanguageCode] = UNSPECIFIED

    @validator('logo_language_priority', pre=True)
    def comma_separate_language_codes(cls, v):
        return list(map(lambda s: str(s).lower().strip(), v.split(',')))

"""
Return classes
"""
class EmbyConnection(BaseServer):
    username: Optional[str]
    # filesize_limit: Optional[int] # TODO evaluate

class JellyfinConnection(BaseServer):
    username: Optional[str]
    # filesize_limit: Optional[int] # TODO evaluate

class PlexConnection(BaseServer):
    integrate_with_pmm: bool
    # filesize_limit: Optional[int] # TODO evaluate

class SonarrConnection(BaseServer):
    downloaded_only: bool
    libraries: list[SonarrLibrary]

class TMDbConnection(Base):
    use_tmdb: bool
    tmdb_api_key: SecretStr
    tmdb_minimum_width: NonNegativeInt
    tmdb_minimum_height: NonNegativeInt
    tmdb_skip_localized: bool
    tmdb_download_logos: bool
    tmdb_logo_language_priority: list[TMDbLanguageCode]
