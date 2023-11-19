from abc import ABC, abstractmethod
from logging import Logger
from typing import Optional, Union
from pathlib import Path

from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
from modules.ImageMagickInterface import ImageMagickInterface
from modules.SeriesInfo import SeriesInfo


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
    def __init__(self,
            filesize_limit: Optional[int],
            use_magick_prefix: bool,
        ) -> None:
        """
        Initialize an instance of this object.
        
        Args:
            filesize_limit: Number of bytes to limit a single file to
                during upload.
            use_magick_prefix: Whether to use 'magick' command prefix.
        """

        self.filesize_limit = filesize_limit
        self._magick = ImageMagickInterface(use_magick_prefix=use_magick_prefix)


    def compress_image(self,
            image: Path,
            *,
            log: Logger = log
        ) -> Optional[Path]:
        """
        Compress the given image until below the filesize limit.

        Args:
            image: Path to the image to compress.
            log: (Keyword) Logger for all log messages.

        Returns:
            Path to the compressed image, or None if the image could not
            be compressed.
        """

        # No compression necessary
        if (self.filesize_limit is None
            or (image := Path(image)).stat().st_size <= self.filesize_limit):
            return image

        # Start with a quality of 90%, decrement by 5% each time
        quality = 95
        small_image = image

        # Compress the given image until below the filesize limit
        while small_image.stat().st_size > self.filesize_limit:
            # Process image, exit if cannot be reduced
            quality -= 5
            small_image = self._magick.reduce_file_size(image, quality)
            if small_image is None:
                log.warning(f'Cannot reduce filesize of "{image.resolve()}" '
                            f'below limit')
                return None

        # Compression successful, log and return intermediate image
        log.debug(f'Compressed "{image.resolve()}" at {quality}% quality')
        return small_image


    @abstractmethod
    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfo,
            episodes: list['Episode'], # type: ignore
        ) -> None:
        """Abstract method to update watched statuses of Episode objects."""
        raise NotImplementedError


    @abstractmethod
    def load_title_cards(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_and_cards: list[tuple['Episode', 'Card']], # type: ignore
            *,
            log: Logger = log,
        ) -> None:
        """Abstract method to load title cards within this MediaServer."""
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
