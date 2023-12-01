from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, Optional, Union

from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
from modules.SeriesInfo2 import SeriesInfo


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
    This object defines a single watched status within a specific
    interface (Connection) and library. For example:

    >>> status = WatchedStatus(1, 'TV Shows', True)

    When associated with an Episode, this indicates that the Episode has
    been watched (True) in the 'TV Shows' library of the interface /
    Connection with ID 1.
    """


    __slots__ = ('interface_id', 'library_name', 'status')


    def __init__(self,
            interface_id: int,
            library_name: Optional[str] = None,
            watched: Optional[bool] = None,
        ) -> None:
        """
        Initialize this WatchedStatus for the given library details.

        Args:
            interface_id: ID of the interface associated with this
                status.
            library_name: Name of the library associated with this
                status.
            watched: The actual watched status.
        """

        self.interface_id = interface_id
        self.library_name = library_name
        self.status = watched


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'<WatchedStatus {self.interface_id}:{self.library_name}:{self.status}>'


    @property
    def db_key(self) -> str:
        """
        The key which this object should be stored at in the Episode
        database.
        """

        return f'{self.interface_id}:{self.library_name}'

    @property
    def has_status(self) -> bool:
        """Whether this watched status is defined (i.e. not `None`)."""

        return self.status is not None


    @property
    def as_db_entry(self) -> dict[str, dict[str, bool]]:
        """SQL database representatin of this status."""

        if self.library_name is not None and self.status is not None:
            return {self.db_key: self.status}

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
