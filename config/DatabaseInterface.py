from datetime import datetime, timedelta
from pathlib import Path
from pickle import dump, load, HIGHEST_PROTOCOL
from requests import get
from urllib.request import urlretrieve

from Debug import *

class DatabaseInterface:
    """
    This class defines an interface to TheMovieDatabase. Once initialized with
    a valid API key, the primary purpose of this class is to automatically 
    gather source images for episodes of series.
    """

    """Base URL for sending API requests to TheMovieDB"""
    API_BASE_URL: str = 'https://api.themoviedb.org/3/'

    """Filename for where to store blacklisted entries"""
    __BLACKLIST: Path = Path(__file__).parent / '.objects' / 'db_blacklist.pkl'
    __BLACKLIST_THRESHOLD = 5

    """Filename where mappings of series full titles to TMDB ids is stored"""
    __ID_MAP: Path = Path(__file__).parent / '.objects' / 'db_id_map.pkl'

    def __init__(self, api_key: str) -> None:
        """
        Constructs a new instance of an interface to TheMovieDB.
        
        :param      api_key:    The api key used to communicate with TMDB.
        """

        # Attempt to read existing ID map
        if self.__ID_MAP.exists():
            with self.__ID_MAP.open('rb') as file_handle:
                self.__id_map = load(file_handle)
        else:
            self.__id_map = {}

        # Attempt to read existing blacklist
        if self.__BLACKLIST.exists():
            with self.__BLACKLIST.open('rb') as file_handle:
                self.__blacklist = load(file_handle)
        else:
            self.__blacklist = {}

        # If unspecified, create an inactive object
        if not api_key:
            self.__active = False
            self.__api_key = None
            return

        self.__active = True
        
        # Store API key
        self.__api_key = api_key
        

    def __bool__(self) -> bool:
        """
        Get the truthiness of this object.

        :returns:   Whether this interface is active orn ot.
        """

        return self.__active


    def __update_blacklist(self, title: str, year: int, season: int, episode: int) -> None:
        """
        Adds the given entry to the blacklist; indicating that this exact entry
        shouldn't be queried to TheMovieDB (to prevent unnecessary queries).
        
        :param      title:      The show's title.

        :param      year:       The show's year.

        :param      season:     The entry's season number.

        :param      episode:    The entry's episode number.
        """

        key = f'{title} ({year})-{season}-{episode}'

        # If previously indexed and next has passed, increase count and set next
        later = datetime.now() + timedelta(days=1)
        if key in self.__blacklist:
            if datetime.now() >= self.__blacklist[key]['next']:
                # One day has passed, and still failed, increment count
                self.__blacklist[key]['failures'] += 1
                self.__blacklist[key]['next'] = later
            else:
                return
        else:
            # Add new entry to blacklist with 1 failure, next time is in one day
            self.__blacklist[key] = {'failures': 1, 'next': later}

        warn(f'Query failed {self.__blacklist[key]["failures"]} times', 3)

        # Write latest version of blacklist to file, in case program exits
        with self.__BLACKLIST.open('wb') as file_handle:
            dump(self.__blacklist, file_handle, HIGHEST_PROTOCOL)


    def __is_blacklisted(self, title: str, year: int, season: int, episode: int) -> bool:
        """
        Determines if the specified entry is in the blacklist (i.e. has no entry
        in TheMovieDB).
        
        :param      title:      The show's title.

        :param      year:       The show's year.

        :param      season:     The entry's season number.

        :param      episode:    The entry's episode number.
        
        :returns:   True if in blacklist, False otherwise.
        """

        key = f'{title} ({year})-{season}-{episode}'

        # If never indexed before, skip failure check
        if key not in self.__blacklist:
            return False
            
        if self.__blacklist[key]['failures'] > self.__BLACKLIST_THRESHOLD:
            return True

        # If we haven't passed next time, then treat as temporary blacklist
        # i.e. before next = 'blacklisted', after next is not
        return datetime.now() < self.__blacklist[key]['next']


    def __add_id_to_map(self, title: str, year: int, id_: int) -> None:
        """
        Adds a mapping of this full title to the corresponding TheMovieDB ID.
        
        :param      title:  The show's title.

        :param      year:   The show's year.

        :param      id_:    The show's ID, as returned by `__get_tv_id()`.
        """

        self.__id_map[f'{title} ({year})'] = id_

        with self.__ID_MAP.open('wb') as file_handle:
            dump(self.__id_map, file_handle, HIGHEST_PROTOCOL)


    @staticmethod
    def manually_specify_id(*args, **kwargs) -> None:
        """Public (static) implementation of `__add_id_to_map()`."""

        DatabaseInterface(None).__add_id_to_map(*args, **kwargs)


    def __get_tv_id(self, title: str, year: int) -> int:
        """
        Get the internal TMDb ID for the provided series. Search is done
        by name and the start air year.

        The first result is returned every time.
        
        :param      title:  The title of the requested series

        :param      year:   The year the requested series first aired
        
        :returns:   The internal TMDb ID for the found series
        """

        # If this full title has been mapped, no need to query 
        if f'{title} ({year})' in self.__id_map:
            return self.__id_map[f'{title} ({year})']

        # Base params are api_key and the query (title)
        url = f'{self.API_BASE_URL}search/tv/'
        params = {'api_key': self.__api_key, 'query': title, 'first_air_date_year': year}

        # Query TheMovieDB
        results = get(url=url, params=params).json()

        # If there are no results, error and return
        if int(results['total_results']) == 0:
            error(f'TheMovieDB returned no results for "{title}"')
            return None

        # Found new ID, add to map and return
        new_id = results['results'][0]['id']
        self.__add_id_to_map(title, year, new_id)

        return new_id


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
        """
        Get the best source image for the requested entry. The URL of this
        image is returned.
        
        :param      title:    The title of the requested series.

        :param      year:     The year of the requested series.

        :param      season:   The season of the requested entry.

        :param      episode:  The episode of the requested entry.
        
        :returns:   URL to the 'best' source image for the requested
                    entry. None if no images are available.
        """

        if not self:
            return

        # Don't query the database if this episode is in the blacklist
        if self.__is_blacklisted(title, year, season, episode):
            return None

        # Get the TV id for the provided series+year
        tv_id = self.__get_tv_id(title, year)

        # GET params
        url = f'{self.API_BASE_URL}tv/{tv_id}/season/{season}/episode/{episode}/images'
        params = {'api_key': self.__api_key}

        # Make the GET request
        results = get(url=url, params=params).json()

        # If 'stills' wasn't in return JSON, episode wasn't found (mismatch)
        if 'stills' not in results:
            warn(f'TheMovieDB has no matching episode for "{title} ({year})" Season {season}, Episode {episode}', 2)
            self.__update_blacklist(title, year, season, episode)
            return None

        # If 'stills' is in JSON, but is an empty list, then database has no images
        if len(results['stills']) == 0:
            warn(f'There are no images for "{title} ({year})" Season {season}, Episode {episode}', 2)
            self.__update_blacklist(title, year, season, episode)
            return None

        best_image = self.__determine_best_image(results['stills'])['file_path']
        
        return f'https://image.tmdb.org/t/p/original{best_image}'


    def download_image(self, image_url: str, destination: Path) -> None:
        """
        Downloads the provided image URL to the destination filepath.
        
        :param      image_url:      The image url to download.

        :param      destination:    The destination for the requested image.
        """

        if not self:
            return

        # Make parent folder structure
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Download the image and store it in destination
        try:
            urlretrieve(image_url, destination.resolve())
        except Exception as e:
            error(f'TheMovieDB errored: "{e}"')



