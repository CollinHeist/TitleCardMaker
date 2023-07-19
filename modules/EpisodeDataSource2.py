from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from logging import Logger
from typing import Any, Optional

from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo
from modules.SeriesInfo import SeriesInfo


@dataclass
class SearchResult: # pylint: disable=missing-class-docstring
    title: str
    year: int
    poster: Optional[str] = None
    overview: list[str] = field(default_factory=lambda: ['No overview available'])
    ongoing: Optional[bool] = None
    emby_id: Any = None
    imdb_id: Any = None
    jellyfin_id: Any = None
    sonarr_id: Any = None
    tmdb_id: Any = None
    tvdb_id: Any = None
    tvrage_id: Any = None


class EpisodeDataSource(ABC):
    """
    This class describes an abstract episode data source. Classes of
    this type define sources of Episode data.
    """


    @property
    @abstractmethod
    def SERIES_IDS(self) -> tuple[str]:
        """Valid SeriesInfo ID's that can be set by this data source."""
        raise NotImplementedError


    @abstractmethod
    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> None:
        """Set the series ID's for the given SeriesInfo object."""

        raise NotImplementedError


    @abstractmethod
    def set_episode_ids(self,
            library_name: Optional[str],
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
            *,
            log: Logger = log,
        ) -> None:
        """Set the episode ID's for the given EpisodeInfo objects."""

        raise NotImplementedError


    @abstractmethod
    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> list[EpisodeInfo]:
        """Get all the EpisodeInfo objects associated with the given series."""

        raise NotImplementedError


    @abstractmethod
    def query_series(self,
            query: str,
            *,
            log: Logger = log,
        ) -> list[SearchResult]:
        """Query for a Series on this interface."""

        raise NotImplementedError
