from abc import ABC, abstractmethod, abstractproperty
from typing import Any, Optional, Union
from pathlib import Path

from tinydb import where, Query

from modules.Debug import log
from modules.Episode import Episode
from modules.ImageMaker import ImageMaker
from modules.PersistentDatabase import PersistentDatabase
from modules.SeriesInfo import SeriesInfo
from modules.StyleSet import StyleSet

SourceImage = Union[str, bytes, None]

class MediaServer(ABC):
    """
    This class describes an abstract base class for all MediaServer
    classes. MediaServer objects are servers like Plex, Emby, and
    JellyFin that can have title cards loaded into them, as well as
    source images retrieved from them.
    """

    """Maximum time allowed for a single GET request"""
    REQUEST_TIMEOUT = 30

    """Default filesize limit for all uploaded assets"""
    DEFAULT_FILESIZE_LIMIT = '10 MB'

    @abstractproperty
    def LOADED_DB(self) -> str:
        """
        Filename of the PersistentDatabase of loaded assets within this
        MediaServer.
        """
        raise NotImplementedError('All MediaServer objects must implement this')


    @abstractmethod
    def __init__(self, filesize_limit: int) -> None:
        """
        Initialize an instance of this object. This stores creates an
        attribute loaded_db that is a PersistentDatabase of the
        LOADED_DB file.
        """

        self.loaded_db = PersistentDatabase(self.LOADED_DB)
        self.filesize_limit = filesize_limit


    def compress_image(self, image: Path) -> Optional[Path]:
        """
        Compress the given image until below the filesize limit.

        Args:
            image: Path to the image to compress.

        Returns:
            Path to the compressed image, or None if the image could not
            be compressed.
        """

        # Ensure image is Path object
        image = Path(image)

        # No compression necessary
        if (self.filesize_limit is None
            or image.stat().st_size < self.filesize_limit):
            return image

        # Start with a quality of 90%, decrement by 5% each time
        quality = 95
        small_image = image

        # Compress the given image until below the filesize limit
        while small_image.stat().st_size > self.filesize_limit:
            # Process image, exit if cannot be reduced
            quality -= 5
            small_image = ImageMaker.reduce_file_size(image, quality)
            if small_image is None:
                log.warning(f'Cannot reduce filesize of "{image.resolve()}" '
                            f'below limit')
                return None

        # Compression successful, log and return intermediate image
        log.debug(f'Compressed "{image.resolve()}" with {quality}% quality')
        return small_image


    def _get_condition(self,
            library_name: str,
            series_info: SeriesInfo,
            episode: 'Episode' = None) -> Query:
        """
        Get the tinydb Query condition for the given entry.

        Args:
            library_name: Library name containing the series to get the
                details of.
            series_info: Series to get the details of.
            episode: Optional Episode to get the series of.

        Returns:
            Query condition to filter a TinyDB database for the
            requested entry.
        """

        # If no episode was given, get condition for entire series
        if episode is None:
            return (
                (where('library') == library_name) &
                (where('series') == series_info.full_name)
            )

        return (
            (where('library') == library_name) &
            (where('series') == series_info.full_name) &
            (where('season') == episode.episode_info.season_number) &
            (where('episode') == episode.episode_info.episode_number)
        )


    def _get_loaded_episode(self,
            loaded_series: list[dict[str, Any]],
            episode: Episode
        ) -> Optional[dict[str, Any]]:
        """
        Get the loaded details of the given Episode from the given list
        of loaded series details.

        Args:
            loaded_series: Filtered List from the loaded database to
                search.
            episode: The Episode to get the details of.

        Returns:
            Loaded details for the specified episode. None if an episode
            of that index DNE in the given list.
        """

        for entry in loaded_series:
            if (entry['season'] == episode.episode_info.season_number and
                entry['episode'] == episode.episode_info.episode_number):
                return entry

        return None


    def _filter_loaded_cards(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_map: dict[str, Episode]
        ) -> dict[str, Episode]:
        """
        Filter the given episode map and remove all Episode objects
        without created cards, or whose card's filesizes matches that of
        the already uploaded card.

        Args:
            library_name: Name of the library containing this series.
            series_info: SeriesInfo object for these episodes.
            episode_map: Dictionary of Episode objects to filter.

        Returns:
            Filtered episode map. Episodes without existing cards, or
            whose existing card filesizes' match those already loaded
            are removed.
        """

        # Get all loaded details for this series
        series = self.loaded_db.search(
            self._get_condition(library_name, series_info)
        )

        filtered = {}
        for key, episode in episode_map.items():
            # Filter out episodes without cards
            if not episode.destination or not episode.destination.exists():
                continue

            # If no cards have been loaded, add all episodes with cards
            if not series:
                filtered[key] = episode
                continue

            # Get current details of this episode
            found = False
            if (entry := self._get_loaded_episode(series, episode)):
                # Episode found, check filesize
                found = True
                if entry['filesize'] != episode.destination.stat().st_size:
                    filtered[key] = episode

            # If this episode has never been loaded, add
            if not found:
                filtered[key] = episode

        return filtered


    def remove_records(self, library_name: str, series_info: SeriesInfo) ->None:
        """
        Remove all records for the given library and series from the
        loaded database.

        Args:
            library_name: The name of the library containing the series
                whose records are being removed.
            series_info: SeriesInfo whose records are being removed.
        """

        # Get condition to find records matching this library + series
        condition = self._get_condition(library_name, series_info)

        # Delete records matching this condition
        records = self.loaded_db.remove(condition)
        log.info(f'Deleted {len(records)} records')


    @abstractmethod
    def has_series(self) -> bool:
        """
        Determine whether the given series is present within this
        MediaServer.
        """
        raise NotImplementedError('All MediaServer objects must implement this')

    @abstractmethod
    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_map: dict[str, Episode],
            style_set: StyleSet) -> None:
        """Abstract method to update watched statuses of Episode objects."""
        raise NotImplementedError('All MediaServer objects must implement this')

    @abstractmethod
    def set_title_cards(self) -> None:
        """Abstract method to load title cards within this MediaServer."""
        raise NotImplementedError('All MediaServer objects must implement this')

    @abstractmethod
    def set_season_posters(self) -> None:
        """Abstract method to load title cards within this MediaServer."""
        raise NotImplementedError('All MediaServer objects must implement this')

    @abstractmethod
    def get_source_image(self) -> SourceImage:
        """
        Abstract method to get textless source images from this
        MediaServer.
        """
        raise NotImplementedError('All MediaServer objects must implement this')

    @abstractmethod
    def get_libraries(self) -> list[str]:
        """
        Abstract method to get all libraries from this MediaServer.
        """
        raise NotImplementedError('All MediaServer objects must implement this')