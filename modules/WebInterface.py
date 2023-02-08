from re import IGNORECASE, compile as re_compile
from requests import get, Session
from typing import Any
import urllib3

from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential

from modules.Debug import log

class WebInterface:
    """
    This class defines a WebInterface, which is a type of interface that makes
    requests using some persistent session and returns JSON results. This object
    caches requests/results for better performance.
    """

    """How many requests to cache"""
    CACHE_LENGTH = 10

    """Regex to match URL's"""
    _URL_REGEX = re_compile(r'^((?:https?:\/\/)?.+)(?=\/)', IGNORECASE)

    """404 content to ignore"""
    BAD_CONTENT = (
        b'<html><head><title>Not Found</title></head>'
        b'<body><h1>404 Not Found</h1></body></html>',
    )


    def __init__(self, name: str, verify_ssl: bool=True, *,
                 cache: bool=True) -> None:
        """
        Construct a new instance of a WebInterface. This creates creates cached
        request and results lists, and establishes a session for future use.

        Args:
            name: Name (for logging) of this Interface.
            verify_ssl: Whether to verify SSL requests with this Interface.
            cache: (Keyword only) Whether to cache requests with this interface.
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


    @retry(stop=stop_after_attempt(10),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32))
    def __retry_get(self, url: str, params: dict[str: Any]) -> dict[str: Any]:
        """
        Retry the given GET request until successful (or really fails).

        Args:
            url: The URL of the GET request.
            params: The params of  the GET request.

        Returns:
            Dict made from the JSON return of the specified GET request.
        """

        return self.session.get(url=url, params=params).json()


    def _get(self, url: str, params: dict) -> dict:
        """
        Wrapper for getting the JSON return of the specified GET request. If the
        provided URL and parameters are identical to the previous request, then
        a cached result is returned instead (if enabled).

        Args:
            url: URL to pass to GET.
            Parameters to pass to GET.

        Returns:
            Dict made from the JSON return of the specified GET request.
        """

        # If not caching, just query and return
        if not self.__do_cache:
            return self.__retry_get(url=url, params=params)

        # Look through all cached results for this exact URL+params; if found,
        # skip the request and return that result
        for cache, result in zip(self.__cache, self.__cached_results):
            if cache['url'] == url and cache['params'] == str(params):
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
    def download_image(image: 'str | bytes', destination: 'Path') -> bool:
        """
        Download the provided image to the destination filepath.

        Args:
            image: URL to the image to download, or bytes of the image to write.
            destination: Destination path to download the image to.

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
            error = lambda s: f'URL {image} returned {s} content'
            image = get(image).content
            assert len(image) > 0, error('no')
            assert image not in WebInterface.BAD_CONTENT, error('bad')

            # Write content to file, return success
            destination.write_bytes(image)
            return True
        except Exception as e:
            log.exception(f'Cannot download image, returned error', e)
            return False