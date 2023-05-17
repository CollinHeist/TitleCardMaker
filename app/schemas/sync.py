from typing import Literal, Optional

from pydantic import Field

from app.schemas.base import Base

SonarrSeriesType = Literal['anime', 'daily', 'standard']
Interface = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr']

class Tag(Base):
    id: int
    label: str

class NewBaseSync(Base):
    name: str = Field(..., min_length=1, title='Sync name')
    template_id: Optional[int] = Field(
        default=None,
        title='Template ID',
        description='ID of the template to apply to all synced series',
    )
    required_tags: list[str] = Field(
        default=[],
        description='List of tags required for this sync',
    )
    excluded_tags: list[str] = Field(
        default=[],
        description='List of tags to exclude from this sync',
    )

class NewMediaServerSync(NewBaseSync):
    required_libraries: list[str] = Field(
        default=[],
        description='List of libraries required for this sync',
    )
    excluded_libraries: list[str] = Field(
        default=[],
        description='List of libraries to exclude from this sync',
    )

class NewEmbySync(NewMediaServerSync):
    interface = 'Emby'

class NewJellyfinSync(NewMediaServerSync):
    interface = 'Jellyfin'

class NewPlexSync(NewMediaServerSync):
    interface = 'Plex'

class NewSonarrSync(NewBaseSync):
    interface = 'Sonarr'
    downloaded_only: bool = Field(
        default=False,
        description='Whether to only sync downloaded series',
    )
    monitored_only: bool = Field(
        default=False,
        description='Whether to only sync monitored series',
    )
    required_series_type: Optional[SonarrSeriesType] = Field(
        default=None,
        description='Series type to include in this sync',
    )
    excluded_series_type: Optional[SonarrSeriesType] = Field(
        default=None,
        description='Series type to exclude from this sync',
    )

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

class UpdateSync(Base):
    name: Optional[str] = Field(default=None, min_length=1)
    template_id: Optional[int] = Field(default=None)
    required_tags: Optional[list[str]] = Field(default=None)
    excluded_tags: Optional[list[str]] = Field(default=None)
    required_libraries: Optional[list[str]] = Field(default=None)
    excluded_libraries: Optional[list[str]] = Field(default=None)
    downloaded_only: Optional[bool] = Field(default=None)
    monitored_only: Optional[bool] = Field(default=None)
    required_series_type: Optional[SonarrSeriesType] = Field(default=None)
    excluded_series_type: Optional[SonarrSeriesType] = Field(default=None)