# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Any, Literal, Optional, Union

from pydantic import AnyUrl, constr, validator # pylint: disable=no-name-in-module

from app.schemas.base import Base, InterfaceType, UpdateBase, UNSPECIFIED
from modules.EmbyInterface2 import EmbyInterface
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface


# Names of acceptable server types
ServerName = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr']

# Any acceptable Interface to an EpisodeDataSource
EpisodeDataSourceInterface = Union[
    EmbyInterface, JellyfinInterface, PlexInterface, SonarrInterface,
    TMDbInterface,
]

# Match hexstrings of A-F and 0-9.s
Hexstring = constr(regex=r'^[a-fA-F0-9]+$')

# Acceptable units for filesize limits
FilesizeUnit = Literal['Bytes', 'Kilobytes', 'Megabytes']
FilesizeLimit = constr(regex=r'\d+\s+(Bytes|Kilobytes|Megabytes)')

# Accepted TMDb 2-letter language codes
TMDbLanguageCode = Literal[TMDbInterface.LANGUAGE_CODES]

"""
Base classes
"""
class SonarrLibrary(Base):
    interface_id: int
    name: str
    path: str

class PotentialSonarrLibrary(SonarrLibrary):
    interface_id: Optional[int] = None

class BaseServer(Base):
    id: int
    interface_type: InterfaceType
    enabled: bool
    name: str
    url: AnyUrl
    api_key: str
    use_ssl: bool = True

class BaseNewConnection(Base):
    enabled: bool = True
    name: str = 'Server'

class BaseNewServer(BaseNewConnection):
    url: AnyUrl
    api_key: Hexstring
    use_ssl: bool = True

class BaseNewMediaServer(BaseNewServer):
    filesize_limit: FilesizeLimit = '5 Megabytes'

class BaseUpdateServer(UpdateBase):
    name: str = UNSPECIFIED
    enabled: bool = UNSPECIFIED
    url: AnyUrl = UNSPECIFIED
    use_ssl: bool = UNSPECIFIED

class BaseUpdateMediaServer(BaseUpdateServer):
    filesize_limit: FilesizeLimit = UNSPECIFIED

"""
Creation classes
"""
class NewEmbyConnection(BaseNewMediaServer):
    name: str = 'Emby Server'
    interface_type: Literal['Emby'] = 'Emby'
    username: Optional[str] = None

class NewJellyfinConnection(BaseNewMediaServer):
    name: str = 'Jellyfin Server'
    interface_type: Literal['Jellyfin'] = 'Jellyfin'
    username: Optional[str] = None

class NewPlexConnection(BaseNewMediaServer):
    name: str = 'Plex Server'
    api_key: str
    interface_type: Literal['Plex'] = 'Plex'
    integrate_with_pmm: bool = False

class NewSonarrConnection(BaseNewServer):
    name: str = 'Sonarr Server'
    interface_type: Literal['Sonarr'] = 'Sonarr'
    downloaded_only: bool = True
    libraries: list[SonarrLibrary] = []

class NewTautulliConnection(BaseNewServer):
    api_key: str
    tcm_url: Optional[str] = None
    agent_name: str = 'Update TitleCardMaker (v3)'

class NewTMDbConnection(Base):
    name: str = 'TMDb'
    interface_type: Literal['TMDb'] = 'TMDb'
    enabled: bool = True
    api_key: Hexstring
    minimum_dimensions: constr(regex=r'^\d+x\d+$') = '0x0'
    skip_localized: bool = True
    logo_language_priority: list[TMDbLanguageCode] = ['en']

    @validator('minimum_dimensions')
    def validate_dimensions(cls, v):
        width, height = str(v).split('x')
        if int(width) < 0 or int(height) < 0:
            raise ValueError(f'Minimum dimensions must be positive')
        return v

    @validator('logo_language_priority', pre=True)
    def comma_separate_language_codes(cls, v):
        if v == '':
            return ['en']
        return [str(s).lower().strip() for s in v.split(',') if str(s).strip()]

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
    minimum_dimensions: constr(regex=r'^\d+x\d+$') = UNSPECIFIED
    skip_localized: bool = UNSPECIFIED
    logo_language_priority: list[TMDbLanguageCode] = UNSPECIFIED

    @validator('minimum_dimensions')
    def validate_dimensions(cls, v):
        width, height = str(v).split('x')
        if int(width) < 0 or int(height) < 0:
            raise ValueError(f'Dimensions must be positive')
        return v

    @validator('logo_language_priority', pre=True)
    def comma_separate_language_codes(cls, v):
        return list(map(lambda s: str(s).strip(), v.split(',')))

"""
Return classes
"""
class EmbyConnection(BaseServer):
    username: Optional[str]
    filesize_limit: FilesizeLimit

class JellyfinConnection(BaseServer):
    username: Optional[str]
    filesize_limit: FilesizeLimit

class PlexConnection(BaseServer):
    integrate_with_pmm: bool
    filesize_limit: FilesizeLimit

class SonarrConnection(BaseServer):
    downloaded_only: bool
    libraries: list[SonarrLibrary]

class TMDbConnection(Base):
    id: int
    interface_type: Literal['TMDb'] = 'TMDb'
    enabled: bool
    name: str
    api_key: str
    minimum_dimensions: str
    skip_localized: bool
    logo_language_priority: list[TMDbLanguageCode]

AnyConnection = Union[
    EmbyConnection, JellyfinConnection, PlexConnection, SonarrConnection,
    TMDbConnection,
]

"""
Sonarr Webhooks
"""
class WebhookSeries(Base):
    id: int
    title: str
    year: int
    imdbId: Any = None
    tvdbId: Any = None
    tvRageId: Any = None

class WebhookEpisode(Base):
    id: int
    episodeNumber: int
    seasonNumber: int
    title: str
    seriesId: int
    # Added in v4.0.0.717 (https://github.com/Sonarr/Sonarr/pull/6151)
    tvdbId: Optional[int] = None

class SonarrWebhook(Base):
    series: WebhookSeries
    episodes: list[WebhookEpisode] = []
    eventType: str # Literal['SeriesAdd', 'Download', 'SeriesDelete', 'EpisodeFileDelete']
