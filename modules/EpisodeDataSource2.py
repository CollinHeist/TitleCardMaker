from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, Optional, Union

from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo
from modules.SeriesInfo import SeriesInfo


class SearchResult:
    """
    Class that defines a SearchResult as returned by an
    EpisodeDataSource. This is essentially a `SeriesInfo` object, with
    additional attributes for a poster, overview, whether it's airing,
    and whether it's been added to TCM.
    """

    __slots__ = ('series_info', 'poster', 'ongoing', 'overview', 'added')


    def __init__(self,
            name: str,
            year: Optional[int] = None,
            poster: Optional[str] = None,
            overview: Union[str, list[str]] = ['No overview available'],
            ongoing: Optional[bool] = None,
            *,
            emby_id: Optional[int] = None,
            imdb_id: Optional[str] = None,
            jellyfin_id: Optional[str] = None,
            sonarr_id: Optional[str]  =None,
            tmdb_id: Optional[int] = None,
            tvdb_id: Optional[int] = None,
            tvrage_id: Optional[int] = None,
            added: bool = False,
        ) -> None:
        """
        Initialize this object. See `SeriesInfo.__init__()` for details.
        Other arguments are self-explanatory.
        """

        # Initialize SeriesInfo for the base Series attributes
        self.series_info = SeriesInfo(
            name=name, year=year, emby_id=emby_id, imdb_id=imdb_id,
            jellyfin_id=jellyfin_id, sonarr_id=sonarr_id, tmdb_id=tmdb_id,
            tvdb_id=tvdb_id, tvrage_id=tvrage_id,
        )

        # Store result-specific attributes
        self.added = added
        self.poster = poster
        self.ongoing = ongoing
        if isinstance(overview, str):
            self.overview = overview.splitlines()
        else:
            self.overview = overview


    def __getattr__(self, attribute: str) -> Any:
        """
        Get an attribute from this object. These can be attributes
        defined in `SearchResult.__slots__`, or an attribute of the
        contained `SeriesInfo` object.
        """

        if attribute in self.__slots__:
            return self.__dict__[attribute]

        return getattr(self.series_info, attribute)


class WatchedStatus:
    """
    
    """


    __slots__ = ('interface_id', 'library_name', 'status')


    def __init__(self,
            interface_id: int,
            library_name: Optional[str] = None,
            watched: Optional[bool] = None,
        ) -> None:
        """
        
        """

        self.interface_id = interface_id
        self.library_name = library_name
        self.status = watched


    @property
    def has_status(self) -> bool:
        return self.status is not None


    def as_db_entry(self) -> dict[int, dict[str, bool]]:
        """
        
        """

        if self.library_name is not None and self.status is not None:
            return {self.interface_id: {self.library_name: self.status}}

        return {}


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
        ) -> list[tuple[EpisodeInfo, WatchedStatus]]:
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
