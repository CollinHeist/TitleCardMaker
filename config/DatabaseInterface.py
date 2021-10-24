from datetime import datetime
from requests import get

class DatabaseInterface:

    API_BASE_URL: str = 'https://api.themoviedb.org/3/'

    DATE_FORMAT: str = '%Y-%m-%d'

    def __init__(self, api_key: str) -> None:
        """
        Constructs a new instance.
        
        :param      api_key:  The api key
        :type       api_key:  str
        """
        
        self.__api_key = api_key


    def __get_tv_id(self, title: str, year: int=None) -> int:

        # Base params are api_key and the query (title)
        url = f'{self.API_BASE_URL}search/tv/'
        params = {
            'api_key': self.__api_key,
            'query': title,
        }

        # If a year is provided, add the param
        if year:
            params.update(first_air_date_year=year)

        results = get(url=url, params=params)

        return results[0]['id']


    def get_title_card_source_image(self, title: str, season: int,
                                    episode: int, year: int=None) -> str:

        # Get the TV id for the provided series+year
        tv_id = self.__get_tv_id(title, year)

        # GET params
        url = f'{self.API_BASE_URL}tv/{tv_id}/season/{season}/episode/{episode}/images'
        params = {'api_key': self.__api_key}

        # Make the GET request
        results = get(url=url, params=params)
        first_image = results['stills'][0]['file_path']
        
        return f'https://image.tmdb.org/t/p/original{first_image}'



