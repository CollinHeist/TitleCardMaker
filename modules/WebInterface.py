from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from random import choices as random_choices
from string import hexdigits
from typing import Any, Optional, TypedDict, Union

from PIL import Image
from re import IGNORECASE, compile as re_compile
from niquests import get, Session
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential
import urllib3

from modules.Debug import Logger, log


class CachedResult(TypedDict):
    expiration: datetime
    result: Any


class WebInterface:
    """
    This class defines a WebInterface, which is a type of interface that
    makes requests using some persistent session and returns JSON
    results. This object caches requests/results for better performance.
    """

    """Maximum time allowed for a single GET request"""
    REQUEST_TIMEOUT = 15

    """Directory for all temporary images created during image creation"""
    _TEMP_DIR = Path(__file__).parent / '.objects'

    """Regex to match URL's"""
    _URL_REGEX = re_compile(r'^((?:https?:\/\/)?.+)(?=\/)', IGNORECASE)

    """Content to ignore if returned by any GET request"""
    BAD_CONTENT = (
        b'<html><head><title>',
        b'<Code>AccessDenied</Code>',
        b'<!DOCTYPE html>',
    )


    def __init__(self,
            name: str,
            verify_ssl: bool = True,
            *,
            cache: bool = True,
            cache_age: timedelta = timedelta(minutes=20),
            log: Logger = log,
        ) -> None:
        """
        Construct a new instance of a WebInterface. This creates creates
        cached request and results lists, and establishes a session for
        future use.

        Args:
            name: Name (for logging) of this interface.
            verify_ssl: Whether to verify SSL requests with this
                interface.
            cache: Whether to cache requests with this interface.
            cache_age: Maximum duration to cache an individual request
                (if enabled).
            log: Logger for all log messages.
        """

        # Store name of this interface
        self.name = name

        # Create session for persistent requests
        self.session = Session()

        # Whether to verify SSL
        self.session.verify = verify_ssl
        if not self.session.verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            log.debug(f'Not verifying SSL connections for {name}')

        # Cache details
        self.__do_cache = cache
        # Cache maps URLS to dicts of string-params to results
        self.__cache: dict[str, dict[str, CachedResult]] = {}
        self.__max_cache_age = cache_age
        self.__last_request: Optional[datetime] = None


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'<WebInterface to {self.name}>'


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(5)+wait_exponential(min=1, max=16),
           before_sleep=lambda _:log.warning('Failed to submit GET request, retrying..'),
           reraise=True)
    def __retry_get(self, url: str, params: dict) -> Any:
        """
        Retry the given GET request until successful (or really fails).

        Args:
            url: The URL of the GET request.
            params: The params of the GET request.

        Returns:
            JSON return of the specified GET request.
        """

        return self.session.get(
            url=url,
            params=params,
            timeout=self.REQUEST_TIMEOUT
        ).json()


    def __clear_outdated_cache(self) -> None:
        """
        Clear the cache of all requests whose expiration has passed.
        """

        # Only need to evaluate cache if the last request was too long ago
        now = datetime.now()
        if (not self.__last_request
            or not self.__last_request + self.__max_cache_age < now):
            return None

        # Identify which elements need to be removed
        to_remove: list[tuple[str, str]] = []
        for url, sub in self.__cache.items():
            for params, expiration in sub.items():
                if expiration['expiration'] < now:
                    to_remove.append((url, params))

        # Remove elements from queries and results
        for url, params in to_remove:
            self.__cache.get(url, {}).pop(params, None)

        return None


    @staticmethod
    def get_image_size(url: str, *, log: Logger = log) -> tuple[int, int]:
        """
        Get the size of the image at the given URL.

        Args:
            url: URL of the image to get the dimensions of.
            log: Logger for all log messages.

        Returns:
            Tuple of the image dimensions (width, height) in pixels.
            Values of (0, 0) are returned if the dimensions cannot be
            determined.
        """

        try:
            if (response := get(url, timeout=30)).ok and response.content:
                return Image.open(BytesIO(response.content)).size
            raise ValueError
        except Exception:
            log.exception('Unable to determine image dimensions')
            return 0, 0


    def get(self,
            url: str,
            params: dict = {},
            *,
            cache: bool = True,
        ) -> Union[dict, Any]:
        """
        Wrapper for getting the JSON return of the specified GET
        request. If the provided URL and parameters are identical to the
        previous request, then a cached result is returned instead (if
        enabled).

        Args:
            url: URL to pass to GET.
            Parameters to pass to GET.
            cache: Whether to utilized cached results for this request.

        Returns:
            Parsed JSON return of the specified GET request.
        """

        # If not caching, just query and return
        if not self.__do_cache or not cache:
            return self.__retry_get(url=url, params=params)

        # Look through all cached results for this exact URL+params; if
        # found, skip the request and return that result - if caching
        if cache:
            self.__clear_outdated_cache()
            result = self.__cache.get(url, {}).get(str(params), '_None')
            if result != '_None':
                return result['result']

        # Make new request
        result = self.__retry_get(url=url,params=params)
        self.__last_request = datetime.now()

        # Add to cache
        if url not in self.__cache:
            self.__cache[url] = {}
        self.__cache[url][str(params)] = {
            'result': result,
            'expiration': self.__last_request + self.__max_cache_age
        }

        # Return result
        return result


    @staticmethod
    def get_random_filename(base: Path, extension: str = 'webp') -> Path:
        """
        Get the path to a randomly named image.

        Args:
            base: Base image used for the randomized path.
            extension: Extension of randomized file to create.

        Returns:
            Path to the randomized file. This file LIKELY DOES NOT
            exist.
        """

        random_chars = ''.join(random_choices(hexdigits, k=8))

        return base.parent / f'{base.stem}.{random_chars}.{extension}'


    @staticmethod
    def download_image(
            image: Union[str, bytes],
            destination: Path,
            *,
            log: Logger = log,
        ) -> bool:
        """
        Download the provided image to the destination filepath.

        Args:
            image: URL to the image to download, or bytes of the image
                to write.
            destination: Destination path to download the image to.
            log: Logger for all log messages.

        Returns:
            Whether the image was successfully downloaded.
        """

        # Make parent folder structure
        destination.parent.mkdir(parents=True, exist_ok=True)

        # If content of image, just write directly to file
        if isinstance(image, bytes):
            destination.write_bytes(image)
            log.trace(f'Downloaded {len(image):,} bytes')
            return True

        # Attempt download
        url = image
        try:
            # Download from URL
            if not (content := get(url, timeout=30).content):
                raise ValueError(f'URL {url} returned no content')
            if any(bc in content for bc in WebInterface.BAD_CONTENT):
                raise ValueError(f'URL {url} returned malformed content')

            # Write content to file, return success
            destination.write_bytes(content)
            log.trace(f'Downloaded {len(content):,} bytes from {url}')
            return True
        except Exception: # pylint: disable=broad-except
            log.exception('Cannot download image, returned error')
            return False


    @staticmethod
    def download_image_raw(
            image: str,
            *,
            log: Logger = log,
        ) -> Optional[bytes]:
        """
        Download and return the provided image URL.

        Args:
            image: URL to the image to download.
            log: Logger for all log messages.

        Returns:
            The bytes of the downloaded image. None if the image could
            not be downloaded.
        """

        url = image
        try:
            # Download and verify content is valid
            if not (content := get(url, timeout=30).content):
                raise ValueError(f'URL {url} returned no content')
            if any(bc in content for bc in WebInterface.BAD_CONTENT):
                raise ValueError(f'URL {url} returned malformed content')
        except Exception: # pylint: disable=broad-except
            log.exception('Cannot download image, returned error')
            return None

        log.trace(f'Downloaded {len(content):,} bytes from {url}')
        return content
