from abc import ABC, abstractmethod

from requests import get

class WebInterface(ABC):
    """
    Abstract class that defines a WebInterface, which is a type of interface
    that makes GET requests and returns some JSON result. 
    """
    
    @abstractmethod
    def __init__(self) -> None:
        """
        Constructs a new instance of a WebInterface. This creates creates a 
        cached request and result, but no other attributes.
        """

        # Cache of the last request+result to speed up identical sequential requests
        self.__cache = {'url': None, 'params': None}
        self.__cached_result = None


    def _get(self, url: str, params: dict) -> dict:
        """
        Wrapper for getting the JSON return of the specified GET request. If the
        provided URL and parameters are identical to the previous request, then
        a cached result is returned instead.
        
        :param      url:    URL to pass to GET.

        :param      params: Parameters to pass to GET.
        
        :returns:   Dict made from the JSON return of the specified GET request.
        """

        # If this exact URL+params were requested last time, skip the request
        if self.__cache['url'] == url and self.__cache['params'] == str(params):
            return self.__cached_result

        # Make new request, add to cache
        self.__cached_result = get(url=url, params=params).json()
        self.__cache = {'url': url, 'params': str(params)}

        return self.__cached_result