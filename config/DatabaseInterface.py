from pathlib import Path
from pickle import dump, load, HIGHEST_PROTOCOL
from requests import get
from urllib.request import urlretrieve

from Debug import *

class DatabaseInterface:

    """Base URL for sending API requests to TheMovieDB"""
    API_BASE_URL: str = 'https://api.themoviedb.org/3/'

    """Filename for where to store blacklisted entries"""
    BLACKLIST_FILE: Path = Path(__file__).parent / 'objects' / 'database_blacklist.pkl'

    def __init__(self, api_key: str) -> None:
        """
        Constructs a new instance.
        
        :param      api_key:  The api key
        """
        
        # Store API key
        self.__api_key = api_key

        # Attempt to read existing blacklist
        if self.BLACKLIST_FILE.exists():
            with self.BLACKLIST_FILE.open('rb') as file_hande:
                self.__blacklist = load(file_hande)
        else:
            self.__blacklist = []


    def __add_to_blacklist(self, title: str, year: int, season: int, episode: int) -> None:
        """
        Adds to blacklist.
        
        :param      tv_id:    The tv identifier

        :param      season:   The season

        :param      episode:  The episode
        """

        # Add to current blacklist
        self.__blacklist.append(f'{title} ({year})-{season}-{episode}')

        # Write latest version of blacklist to file, in case program exits
        with self.BLACKLIST_FILE.open('wb') as file_handle:
            dump(self.__blacklist, file_handle, HIGHEST_PROTOCOL)

        info(f'Added "{title} ({year})-{season}-{episode}" to database blacklist', 3)


    def __is_in_blacklist(self, title: str, year: int, season: int, episode: int) -> bool:
        """
        Determines if in blacklist.
        
        :param      tv_id:    The tv identifier

        :param      season:   The season

        :param      episode:  The episode

        
        :returns:   True if in blacklist, False otherwise.
        """

        return f'{title} ({year})-{season}-{episode}' in self.__blacklist


    def __get_tv_id(self, title: str, year: int) -> int:
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
        params = {'api_key': self.__api_key, 'query': title, 'first_air_date_year': year}

        # Query TheMovieDB
        results = get(url=url, params=params).json()

        if int(results['total_results']) < 1:
            error(f'TheMovieDB returned no results for "{title}"')
            return None

        return results['results'][0]['id']


    def __determine_best_image(self, images: list) -> dict:
        """
        Determines the best image, returning it's contents from within
        the database return JSON.
        
        :param      images: The results from the database. Each entry
                            is a new image to be considered.
        
        :returns:   The "best" image for title card creation. This is
                    determined using the images' aspect ratios, and 
                    dimensions. Priority given to largest image.
        """

        # Only one image, bypass this function
        if len(images) == 1:
            return images[0]

        # Pick the best image based on image dimensions, and then vote average
        best_image = {'index': 0, 'pixels': 0, 'score': 0}
        for index, image in enumerate(images):
            pixels = int(image['height']) * int(image['width'])
            score = int(image['vote_average'])

            # Priority 1 is image size, priority 2 is vote average/score
            if pixels > best_image['pixels']:
                best_image = {'index': index, 'pixels': pixels, 'score': score}
            elif pixels == best_image['pixels']:
                if score > best_image['score']:
                    best_image = {'index': index, 'pixels': pixels, 'score': score}

        return images[best_image['index']]


    def get_title_card_source_image(self, title: str, year: int, season: int,
                                    episode: int) -> str:

        # Don't query the database if this episode is in the blacklist
        if self.__is_in_blacklist(title, year, season, episode):
            return None

        # Get the TV id for the provided series+year
        tv_id = self.__get_tv_id(title, year)

        # GET params
        url = f'{self.API_BASE_URL}tv/{tv_id}/season/{season}/episode/{episode}/images'
        params = {'api_key': self.__api_key}

        # Make the GET request
        results = get(url=url, params=params).json()

        # If 'stills' wasn't in return JSON, episode wasn't found (mismatch between tvdb and tmdb)
        if 'stills' not in results:
            warn(f'TheMovieDB has no matching episode for "{title} ({year})" Season {season}, Episode {episode}', 2)
            self.__add_to_blacklist(title, year, season, episode)
            return None

        # If 'stills' is in JSON, but is an empty list, then database has no images
        if len(results['stills']) == 0:
            warn(f'There are no images for "{title} ({year})" Season {season}, Episode {episode}', 2)
            self.__add_to_blacklist(title, year, season, episode)
            return None

        best_image = self.__determine_best_image(results['stills'])['file_path']
        
        return f'https://image.tmdb.org/t/p/original{best_image}'


    def download_image(self, image_url: str, destination: Path) -> None:
        """
        Downloads the provided image URL to the destination filepath.
        
        :param      image_url:      The image url to download.

        :param      destination:    The destination for the requested image.
        """

        # Make parent folder structure
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Download the image and store it in destination
        try:
            urlretrieve(image_url, destination.resolve())
        except Exception as e:
            error(f'TheMovieDB errored: "{e}"')



