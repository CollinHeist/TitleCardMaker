from abc import ABC, abstractmethod, abstractproperty
from typing import Any, Union
from pathlib import Path

from modules.Debug import log
from modules.ImageMaker import ImageMaker

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


    @abstractmethod
    def __init__(self, filesize_limit: int) -> None:
        """
        Initialize an instance of this object. This stores creates an
        attribute loaded_db that is a PersistentDatabase of the
        LOADED_DB file.
        """

        self.filesize_limit = filesize_limit


    def compress_image(self, image: Path) -> Union[Path, None]:
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


    @abstractmethod
    def has_series(self) -> bool:
        """
        Determine whether the given series is present within this
        MediaServer.
        """
        raise NotImplementedError('All MediaServer objects must implement this')

    @abstractmethod
    def update_watched_statuses(self, library_name: str,
            series_info: 'SeriesInfo', episode_map: dict[str, 'Episode'],
            style_set: 'StyleSet') -> None:
        """Abstract method to update watched statuses of Episode objects."""
        raise NotImplementedError('All MediaServer objects must implement this')

    @abstractmethod
    def load_title_cards(self) -> None:
        """Abstract method to load title cards within this MediaServer."""
        raise NotImplementedError('All MediaServer objects must implement this')

    @abstractmethod
    def load_season_posters(self) -> None:
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