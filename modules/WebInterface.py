from logging import Logger
from pathlib import Path
from typing import Any, Union

from re import IGNORECASE, compile as re_compile
from requests import get, Session
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential
import urllib3

from modules.Debug import log


class WebInterface:
    """
    This class defines a WebInterface, which is a type of interface that
    makes requests using some persistent session and returns JSON
    results. This object caches requests/results for better performance.
    """

    """Maximum time allowed for a single GET request"""
    REQUEST_TIMEOUT = 15

    """How many requests to cache"""
    CACHE_LENGTH = 10

    """Regex to match URL's"""
    _URL_REGEX = re_compile(r'^((?:https?:\/\/)?.+)(?=\/)', IGNORECASE)

    """Content to ignore if returned by any GET request"""
    BAD_CONTENT = (
        b'<html><head><title>',
        b'<Code>AccessDenied</Code>',
    )


    def __init__(self,
            name: str,
            verify_ssl: bool = True,
            *,
            cache: bool = True,
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
            cache: (Keyword only) Whether to cache requests with this
                interface.
            log: (Keyword) Logger for all log messages.
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

        # Cache of the last requests to speed up identical sequential requests
        self.__do_cache = cache
        self.__cache = []
        self.__cached_results = []


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'<WebInterface to {self.name}>'


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(5)+wait_exponential(min=1, max=16),
           before_sleep=lambda _:log.warning('Failed to submit GET request, retrying..'),
           reraise=True)
    def __retry_get(self, url: str, params: dict) -> dict:
        """
        Retry the given GET request until successful (or really fails).

        Args:
            url: The URL of the GET request.
            params: The params of  the GET request.

        Returns:
            Dict made from the JSON return of the specified GET request.
        """

        return self.session.get(
            url=url,
            params=params,
            timeout=self.REQUEST_TIMEOUT
        ).json()


    def get(self, url: str, params: dict, *, cache: bool = True) -> Any:
        """
        Wrapper for getting the JSON return of the specified GET
        request. If the provided URL and parameters are identical to the
        previous request, then a cached result is returned instead (if
        enabled).

        Args:
            url: URL to pass to GET.
            Parameters to pass to GET.
            cache: (Keyword) Whether to utilized cached results for this
                request.

        Returns:
            Parsed JSON return of the specified GET request.
        """

        # If not caching, just query and return
        if not self.__do_cache:
            return self.__retry_get(url=url, params=params)

        # Look through all cached results for this exact URL+params; if found,
        # skip the request and return that result - if caching
        if cache:
            for cached, result in zip(self.__cache, self.__cached_results):
                if cached['url'] == url and cached['params'] == str(params):
                    return result

        # Make new request, add to cache
        self.__cached_results.append(self.__retry_get(url=url, params=params))
        self.__cache.append({'url': url, 'params': str(params)})

        # Delete element from cache if length has been exceeded
        if len(self.__cache) > self.CACHE_LENGTH:
            self.__cache.pop(0)
            self.__cached_results.pop(0)

        # Return latest result
        return self.__cached_results[-1]


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
            log: (Keyword) Logger for all log messages.

        Returns:
            Whether the image was successfully downloaded.
        """

        # Make parent folder structure
        destination.parent.mkdir(parents=True, exist_ok=True)

        # If content of image, just write directly to file
        if isinstance(image, bytes):
            destination.write_bytes(image)
            return True

        # Attempt to download the image, if an error happens log to user
        try:
            # Get content from URL
            image = get(image, timeout=30).content
            if len(image) == 0:
                raise ValueError(f'URL {image} returned no content error')
            if any(bad_content in image for bad_content in WebInterface.BAD_CONTENT):
                raise ValueError(f'URL {image} returned (bad) malormed content')

            # Write content to file, return success
            destination.write_bytes(image)
            return True
        except Exception as e:
            log.exception(f'Cannot download image, returned error', e)
            return False
