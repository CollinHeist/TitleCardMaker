from typing import Literal, Optional

from app.schemas.base import Base

SonarrSeriesType = Literal['anime', 'daily', 'standard']
SyncSource = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr']

class Sync(Base):
    id: int
    name: str
    interface: SyncSource
    template_id: Optional[int]
    required_tags: list[str]
    required_libraries: list[str]
    excluded_tags: list[str]
    excluded_libraries: list[str]
    downloaded_only: bool
    monitored_only: bool
    required_series_type: Optional[str]
    excluded_series_type: Optional[str]

class EmbySync(Sync):
    interface: SyncSource = 'Emby'

class JellyfinSync(Sync):
    interface: SyncSource = 'Jellyfin'

class PlexSync(Sync):
    interface: SyncSource = 'Plex'

class SonarrSync(Sync):
    interface: SyncSource = 'Sonarr'