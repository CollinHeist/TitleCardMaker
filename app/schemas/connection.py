# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Any

from app.schemas.base import Base


"""
Base classes
"""

"""
Creation classes
"""

"""
Update classes
"""

"""
Return classes
"""

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

class SonarrWebhook(Base):
    series: WebhookSeries
    episodes: list[WebhookEpisode] = []
    eventType: str # Literal['SeriesAdd', 'Download']
