from pathlib import Path
from requests import get
from urllib.request import urlretrieve

from Debug import *

class DatabaseInterface:

    API_BASE_URL: str = 'https://api.themoviedb.org/3/'

    def __init__(self, api_key: str) -> None:
        """
        Constructs a new instance.
        
        :param      api_key:  The api key
        :type       api_key:  str
        """
        
        self.__api_key = api_key


    def __get_tv_id(self, title: str, year: int=None) -> int:
        """
        Get the internal TMDb ID for the provided series. Search is done
        by name, but if the start air year is provided more accurate results
        are to be expected.

        The first result is returned every time.
        
        :param      title:  The title of the requested series

        :param      year:   The year the requested series first aired
        
        :returns:   The internal TMDb ID for the found series
        """

        # Base params are api_key and the query (title)
        url = f'{self.API_BASE_URL}search/tv/'
        params = {
            'api_key': self.__api_key,
            'query': title,
        }

        # If a year is provided, add the param
        if year:
            params.update(first_air_date_year=year)

        results = get(url=url, params=params).json()

        return results['results'][0]['id']


    def get_title_card_source_image(self, title: str, season: int,
                                    episode: int, year: int=None) -> str:

        # Get the TV id for the provided series+year
        tv_id = self.__get_tv_id(title, year)

        # GET params
        url = f'{self.API_BASE_URL}tv/{tv_id}/season/{season}/episode/{episode}/images'
        params = {'api_key': self.__api_key}

        # Make the GET request
        results = get(url=url, params=params).json()

        if len(results['stills']) == 0:
            warn(f'There are no images for "{title} ({year})" Season {season}, Episode {episode}')
            return None

        first_image = results['stills'][0]['file_path']
        
        return f'https://image.tmdb.org/t/p/original{first_image}'


    def download_image(self, image_url: str, destination: Path) -> None:
        """
        Downloads the provided image URL to the destination filepath.
        
        :param      image_url:    The image url (likely provided by this class)

        :param      destination:  The destination for the requested image.
        """

        urlretrieve(image_url, destination.resolve())



