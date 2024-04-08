from abc import ABC, abstractmethod
from logging import Logger
from typing import Optional, TypeVar, Union
from pathlib import Path

from PIL import Image

from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
from modules.SeriesInfo2 import SeriesInfo


_Card = TypeVar('_Card')
_Episode = TypeVar('_Episode')
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
    def __init__(self, filesize_limit: Optional[int]) -> None:
        """
        Initialize an instance of this object.
        
        Args:
            filesize_limit: Number of bytes to limit a single file to
                during upload.
        """

        self.filesize_limit = filesize_limit


    def compress_image(self,
            image: Union[str, Path],
            *,
            log: Logger = log
        ) -> Optional[Path]:
        """
        Compress the given image until below the filesize limit.

        Args:
            image: Path to the image to compress.
            log: Logger for all log messages.

        Returns:
            Path to the compressed image, or None if the image could not
            be compressed (or image DNE).
        """

        image = Path(image)
        if not (image := Path(image)).exists():
            return None

        # No compression necessary
        if (self.filesize_limit is None
            or image.stat().st_size <= self.filesize_limit):
            return image

        # Start with a quality of 95%, decrement by 5% each time
        quality = 100
        small_image = image

        # Compress the given image until below the filesize limit
        while quality > 0 and small_image.stat().st_size > self.filesize_limit:
            # Process image, exit if cannot be reduced
            quality -= 5
            # TODO Verify if need to resize with .resize((W, H))
            Image.open(small_image)\
                .save(small_image, optimize=True, quality=quality)

        # If still above the limit, warn and return
        if small_image.stat().st_size > self.filesize_limit:
            log.warning(f'Cannot reduce filesize of "{image.resolve()}" below '
                        f'limit')
            return None

        # Compression successful, log and return intermediate image
        log.trace(f'Compressed "{image.resolve()}" at {quality}% quality')
        return small_image


    @abstractmethod
    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfo,
            episodes: list[_Episode],
            *,
            log: Logger = log,
        ) -> bool:
        """Method to get the watched statuses of Episodes."""
        raise NotImplementedError


    @abstractmethod
    def load_title_cards(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_and_cards: list[tuple[_Episode, _Card]],
            *,
            log: Logger = log,
        ) -> list[tuple[_Episode, _Card]]:
        """
        Abstract method to load title cards within this MediaServer.
        """
        raise NotImplementedError


    @abstractmethod
    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            *,
            log: Logger = log,
        ) -> SourceImage:
        """
        Abstract method to get textless source images from this
        MediaServer.
        """
        raise NotImplementedError


    @abstractmethod
    def get_series_poster(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> SourceImage:
        """
        Abstract method to get a Series poster from this MediaServer.
        """
        raise NotImplementedError


    @abstractmethod
    def get_libraries(self) -> list[str]:
        """
        Abstract method to get all libraries from this MediaServer.
        """
        raise NotImplementedError
