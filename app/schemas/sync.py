from typing import Literal, Optional

from pydantic import Field

from app.schemas.base import Base, UNSPECIFIED

SonarrSeriesType = Literal['anime', 'daily', 'standard']
Interface = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr']

class Tag(Base):
    id: int
    label: str

class NewBaseSync(Base):
    name: str = Field(..., min_length=1, title='Sync name')
    template_ids: list[int] = Field(
        default=[],
        title='Template IDs',
        description='IDs of the Templates to apply to all synced Series',
    )
    required_tags: list[str] = Field(
        default=[],
        description='List of tags required for this Sync',
    )
    excluded_tags: list[str] = Field(
        default=[],
        description='List of tags to exclude from this Sync',
    )

class NewMediaServerSync(NewBaseSync):
    required_libraries: list[str] = Field(
        default=[],
        description='List of libraries required for this Sync',
    )
    excluded_libraries: list[str] = Field(
        default=[],
        description='List of libraries to exclude from this Sync',
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
        description='Whether to only sync downloaded Series',
    )
    monitored_only: bool = Field(
        default=False,
        description='Whether to only sync monitored Series',
    )
    required_series_type: Optional[SonarrSeriesType] = Field(
        default=None,
        description='Series type to include in this Sync',
    )
    excluded_series_type: Optional[SonarrSeriesType] = Field(
        default=None,
        description='Series type to exclude from this Sync',
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
    name: Optional[str] = Field(default=UNSPECIFIED, min_length=1)
    template_ids: list[int] = Field(default=UNSPECIFIED)
    required_tags: list[str] = Field(default=UNSPECIFIED)
    excluded_tags: list[str] = Field(default=UNSPECIFIED)
    required_libraries: list[str] = Field(default=UNSPECIFIED)
    excluded_libraries: list[str] = Field(default=UNSPECIFIED)
    downloaded_only: bool = Field(default=UNSPECIFIED)
    monitored_only: bool = Field(default=UNSPECIFIED)
    required_series_type: Optional[SonarrSeriesType] = Field(default=UNSPECIFIED)
    excluded_series_type: Optional[SonarrSeriesType] = Field(default=UNSPECIFIED)