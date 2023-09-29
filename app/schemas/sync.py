# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Literal, Optional

from pydantic import constr, validator # pylint: disable=no-name-in-module

from app.schemas.base import Base, UpdateBase, UNSPECIFIED


SonarrSeriesType = Literal['anime', 'daily', 'standard']
Interface = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr']


class Tag(Base):
    id: int
    label: str

class NewBaseSync(Base):
    name: constr(min_length=1)
    interface_id: int
    template_ids: list[int] = []
    required_tags: list[str] = []
    excluded_tags: list[str] = []

    @validator('template_ids', pre=False)
    def validate_unique_template_ids(cls, val):
        assert len(val) == len(set(val)), 'Template IDs must be unique'
        return val

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
    id: int
    interface: Interface

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
    name: constr(min_length=1) = UNSPECIFIED
    interface_id: int = UNSPECIFIED
    template_ids: list[int] = UNSPECIFIED
    required_tags: list[str] = UNSPECIFIED
    excluded_tags: list[str] = UNSPECIFIED
    required_libraries: list[str] = UNSPECIFIED
    excluded_libraries: list[str] = UNSPECIFIED
    downloaded_only: bool = UNSPECIFIED
    monitored_only: bool = UNSPECIFIED
    required_series_type: Optional[SonarrSeriesType] = UNSPECIFIED
    excluded_series_type: Optional[SonarrSeriesType] = UNSPECIFIED

    @validator('template_ids', pre=False)
    def validate_unique_template_ids(cls, val):
        if len(val) != len(set(val)):
            raise ValueError('Template IDs must be unique')
        return val
