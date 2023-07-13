# pylint: disable=missing-class-docstring,missing-function-docstring
from typing import Literal, Optional

from pydantic import Field

from app.schemas.base import Base, UpdateBase, UNSPECIFIED

SonarrSeriesType = Literal['anime', 'daily', 'standard']
Interface = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr']

class Tag(Base):
    id: int
    label: str

class NewBaseSync(Base):
    name: str = Field(..., min_length=1, title='Sync name')
    template_ids: list[int] = []
    required_tags: list[str] = []
    excluded_tags: list[str] = []

class NewMediaServerSync(NewBaseSync):
    required_libraries: list[str] = []
    excluded_libraries: list[str] = []

class NewEmbySync(NewMediaServerSync):
    interface = 'Emby'

class NewJellyfinSync(NewMediaServerSync):
    interface = 'Jellyfin'

class NewPlexSync(NewMediaServerSync):
    interface = 'Plex'

class NewSonarrSync(NewBaseSync):
    interface = 'Sonarr'
    downloaded_only: bool = False
    monitored_only: bool = False
    required_series_type: Optional[SonarrSeriesType] = None
    excluded_series_type: Optional[SonarrSeriesType] = None

class ExistingBaseSync(NewBaseSync):
    id: int = Field(..., title='Sync ID')
    interface: Interface = Field(..., title='Sync interface')

class EmbySync(ExistingBaseSync, NewMediaServerSync):
    interface: Interface = 'Emby'

class JellyfinSync(ExistingBaseSync, NewMediaServerSync):
    interface: Interface = 'Jellyfin'

class PlexSync(ExistingBaseSync, NewMediaServerSync):
    interface: Interface = 'Plex'

class SonarrSync(ExistingBaseSync, NewSonarrSync):
    interface: Interface = 'Sonarr'

class Sync(ExistingBaseSync, NewSonarrSync):
    ...

class UpdateSync(UpdateBase):
    name: Optional[str] = Field(default=UNSPECIFIED, min_length=1)
    template_ids: list[int] = UNSPECIFIED
    required_tags: list[str] = UNSPECIFIED
    excluded_tags: list[str] = UNSPECIFIED
    required_libraries: list[str] = UNSPECIFIED
    excluded_libraries: list[str] = UNSPECIFIED
    downloaded_only: bool = UNSPECIFIED
    monitored_only: bool = UNSPECIFIED
    required_series_type: Optional[SonarrSeriesType] = UNSPECIFIED
    excluded_series_type: Optional[SonarrSeriesType] = UNSPECIFIED
