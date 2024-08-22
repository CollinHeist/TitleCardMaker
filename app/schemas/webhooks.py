# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false
from typing import Any, Literal, Optional

from pydantic import AnyUrl

from app.schemas.base import Base

"""
Sonarr models
"""
class SonarrWebhookSeries(Base):
    id: int
    title: str
    year: int
    imdbId: Any = None
    tvdbId: Any = None
    tvRageId: Any = None

class SonarrWebhookEpisode(Base):
    id: int
    episodeNumber: int
    seasonNumber: int
    title: str
    seriesId: int
    # Added in v4.0.0.717 (https://github.com/Sonarr/Sonarr/pull/6151)
    tvdbId: Optional[int] = None

class SonarrWebhook(Base):
    series: SonarrWebhookSeries
    episodes: list[SonarrWebhookEpisode] = []
    eventType: str # Literal['SeriesAdd', 'Download', 'SeriesDelete', 'EpisodeFileDelete']


"""
Plex models - see https://support.plex.tv/articles/115002267687-webhooks/
"""
PlexEvent = Literal[
    # New content
    'library.on.deck',
        # A new item is added that appears in the user’s On Deck. A
        # poster is also attached to this event.
    'library.new',
        # A new item is added to a library to which the user has access.
        # A poster is also attached to this event.
    # Playback
    'media.pause',
        # Media playback pauses.
    'media.play',
        # Media starts playing. An appropriate poster is attached.
    'media.rate',
        # Media is rated. A poster is also attached to this event.
    'media.resume',
        # Media playback resumes.
    'media.scrobble',
        # Media is viewed (played past the 90% mark).
    'media.stop',
        # Media playback stops.
    # Server Owner
    'admin.database.backup',
        # A database backup is completed successfully via Scheduled Tasks.
    'admin.database.corrupted',
        # Corruption is detected in the server database.
    'device.new',
        # A device accesses the owner’s server for any reason, which may
        # come from background connection testing and doesn’t
        # necessarily indicate active browsing or playback.
    'playback.started',
        # Playback is started by a shared user for the server. A poster
        # is also attached to this event.
]

class PlexAccount(Base):
    id: int
    thumb: AnyUrl
    title: str

class PlexServer(Base):
    title: str
    uuid: str

class PlexPlayer(Base):
    local: bool
    publicAddress: str
    title: str
    uuid: str

class PlexMetadata(Base):
    # librarySectionType: str
    ratingKey: int
    # key: str
    # parentRatingKey: int
    # grandparentRatingKey: int
    # guid: str
    # librarySectionID: int
    # type: str
    # title: str
    # grandparentKey: str
    # parentKey: str
    # grandparentTitle: str
    # parentTitle: str
    # summary: str
    # index: int
    # parentIndex: int
    # ratingCount: int
    # thumb: str
    # art: str
    # parentThumb: str
    # grandparentThumb: str
    # grandparentArt: str
    # addedAt: int
    # updatedAt: int

class PlexWebhook(Base):
    event: PlexEvent
    # user: bool
    # owner: bool
    # Account: PlexAccoun
    # Server: PlexServer
    # Player: PlexPlayer
    Metadata: PlexMetadata
