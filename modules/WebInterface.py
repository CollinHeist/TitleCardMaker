from requests import get
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential

from modules.Debug import log

class WebInterface:
    """
    Abstract class that defines a WebInterface, which is a type of interface
    that makes GET requests and returns some JSON result. 
    """

    """How many requests to cache"""
    CACHE_LENGTH = 10
    
    
    def __init__(self) -> None:
        """
        Constructs a new instance of a WebInterface. This creates creates a 
        cached request and result, but no other attributes.
        """

        # Cache of the last requests to speed up identical sequential requests
        self.__cache = []
        self.__cached_results = []


    @retry(stop=stop_after_attempt(10),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32))
    def __retry_get(self, url: str, params: dict) -> dict:
        """
        Retry the given GET request until successful (or really fails).
        
        :param      url:    The URL of the GET request.
        :param      params: The params of  the GET request.

        :retuns:    Dict made from the JSON return of the specified GET request.
        """

        return get(url=url, params=params).json()


    def _get(self, url: str, params: dict) -> dict:
        """
        Wrapper for getting the JSON return of the specified GET request. If the
        provided URL and parameters are identical to the previous request, then
        a cached result is returned instead.
        
        :param      url:    URL to pass to GET.

        :param      params: Parameters to pass to GET.
        
        :returns:   Dict made from the JSON return of the specified GET request.
        """
        
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
    def download_image(image_url: str, destination: 'Path') -> None:
        """
        Download the provided image URL to the destination filepath.
        
        :param      image_url:      The image url to download.
        :param      destination:    The destination for the requested image.
        """

        # Make parent folder structure
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Attempt to download the image, if an error happens log to user
        try:
            with destination.open('wb') as file_handle:
                file_handle.write(get(image_url).content)
        except Exception as e:
            log.error(f'Cannot download image, error: "{e}"')


        