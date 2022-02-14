from datetime import datetime, timedelta
from pathlib import Path
from pickle import dump, load, HIGHEST_PROTOCOL
from urllib.request import urlretrieve

from modules.Debug import *
import modules.preferences as global_preferences
from modules.WebInterface import WebInterface

class TMDbInterface(WebInterface):
    """
    This class defines an interface to TheMovieDatabase (TMDb). Once initialized 
    with a valid API key, the primary purpose of this class is to gather 
    images for title cards, or logos for summaries.
    """

    """Base URL for sending API requests to TheMovieDB"""
    API_BASE_URL: str = 'https://api.themoviedb.org/3/'

    """Default for how many failed requests lead to an entry being blacklisted"""
    BLACKLIST_THRESHOLD: int = 3

    """Filename for where to store blacklisted entries"""
    __BLACKLIST: Path = Path(__file__).parent / '.objects' / 'db_blacklist.pkl'

    """Filename where mappings of series full titles to TMDB ids is stored"""
    __ID_MAP: Path = Path(__file__).parent / '.objects' / 'db_id_map.pkl'

    def __init__(self, api_key: str) -> None:
        """
        Constructs a new instance of an interface to TheMovieDB.
        
        :param      api_key:    The api key to communicate with TMDb.
        """

        # Initialize parent WebInterface 
        super().__init__()

        self.preferences = global_preferences.pp

        # Create objects directory if it does not exist
        self.__ID_MAP.parent.mkdir(parents=True, exist_ok=True)

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
        
        # Store API key
        self.__api_key = api_key


    def __update_blacklist(self, title: str, year: int, season: int,
                           episode: int) -> None:
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


    def __is_blacklisted(self, title: str, year: int, season: int,
                         episode: int) -> bool:
        """
        Determines if the specified entry is in the blacklist (i.e. should
        not bother querying TMDb.
        
        :param      title:      The show's title.

        :param      year:       The show's year.

        :param      season:     The entry's season number.

        :param      episode:    The entry's episode number.
        
        :returns:   True if the entry is blacklisted, False otherwise.
        """

        key = f'{title} ({year})-{season}-{episode}'

        # If never indexed before, skip failure check
        if key not in self.__blacklist:
            return False
            
        if self.__blacklist[key]['failures'] >self.preferences.tmdb_retry_count:
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
    def manually_specify_id(title: str, year: int, id_: int) -> None:
        """Public (static) implementation of `__add_id_to_map()`."""

        TMDbInterface(None).__add_id_to_map(title, year, id_)


    @staticmethod
    def manually_download_season(api_key: str, title: str, year: int,
                                 season: int, episode_count: int,
                                 directory: Path) -> None:
        """
        Download episodes 1-episode_count of the requested season for the given
        show. They will be named as s{season}e{episode}.jpg.
        
        :param      api_key:        The api key for sending requsts to TMDb.

        :param      title:          The title of the requested show.

        :param      year:           The year of the requested show.

        :param      season:         The season to download.

        :param      episode_count:  The number of episodes to download

        :param      directory:      The directory to place the downloaded images
                                    in.
        """

        # Create a temporary interface object for this function
        dbi = TMDbInterface(api_key)

        for episode in range(1, episode_count+1):
            image_url=dbi.get_title_card_source_image(title,year,season,episode)

            # If a valid URL was returned, download it
            if image_url:
                filename = f's{season}e{episode}.jpg'
                dbi.download_image(image_url, directory / filename)


    @staticmethod
    def delete_blacklist() -> None:
        """Delete the blacklist file referenced by this class."""

        TMDbInterface.__BLACKLIST.unlink(missing_ok=True)
        info(f'Deleted blacklist file "{TMDbInterface.__BLACKLIST.resolve()}"')


    def __get_tv_id(self, title: str, year: int) -> int:
        """
        Get the internal TMDb ID for the provided series. Matching is done by
        name and the start air year.

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
        params = {'api_key': self.__api_key, 'query': title,
                  'first_air_date_year': year}

        # Query TheMovieDB
        results = self._get(url=url, params=params)

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
        Determines the best image, returning it's contents from within the
        database return JSON.
        
        :param      images: The results from the database. Each entry is a new
                            image to be considered.
        
        :returns:   The "best" image for title card creation. This is determined
                    using the images' dimensions. Priority given to largest
                    image. None is returned if no images passed the minimum
                    dimension requirements in preferences.
        """

        # Pick the best image based on image dimensions, and then vote average
        best_image = {'index': 0, 'pixels': 0, 'score': 0}
        valid_image = False
        for index, image in enumerate(images):
            # If either dimension is too small, skip
            width, height = int(image['width']), int(image['height'])
            if not self.preferences.meets_minimum_resolution(width, height):
                continue

            # If the image has valid dimensions,get pixel count and vote average
            valid_image = True
            pixels = height * width
            score = int(image['vote_average'])

            # Priority 1 is image size, priority 2 is vote average/score
            if pixels > best_image['pixels']:
                best_image = {'index': index, 'pixels': pixels, 'score': score}
            elif pixels == best_image['pixels']:
                if score > best_image['score']:
                    best_image = {'index':index, 'pixels':pixels, 'score':score}

        return images[best_image['index']] if valid_image else None


    def get_title_card_source_image(self, title: str, year: int, season: int,
                                    episode: int, abs_number: int=None) -> str:
        """
        Get the best source image for the requested entry. The URL of this image
        is returned.
        
        :param      title:      The title of the requested series.

        :param      year:       The year of the requested series.

        :param      season:     The season of the requested entry.

        :param      episode:    The episode of the requested entry.

        :param      abs_number: The absolute episode number of the entry.
        
        :returns:   URL to the 'best' source image for the requested entry. None
                    if no images are available.
        """

        # Don't query the database if this episode is in the blacklist
        if self.__is_blacklisted(title, year, season, episode):
            return None

        # Get the TV id for the provided series+year
        tv_id = self.__get_tv_id(title, year)

        # GET params
        url = f'{self.API_BASE_URL}tv/{tv_id}/season/{season}/episode/{episode}/images'
        params = {'api_key': self.__api_key}

        # Make the GET request
        results = self._get(url=url, params=params)

        # If an absolute number has been given and the first query failed, try again
        if abs_number != None and 'success' in results and not results['success']:
            info(f'Trying absolute episode number {abs_number} in different seasons', 2)

            # Try surround season numbers (TMDb indexes these weirdly..)
            for new_season in range(1, season+1)[::-1]:
                info(f'Trying /season/{new_season}/episode/{abs_number}', 3)
                url = f'{self.API_BASE_URL}tv/{tv_id}/season/{new_season}/episode/{abs_number}/images'
                results = self._get(url=url, params=params)
                if 'stills' in results:
                    break

        # If 'stills' wasn't in return JSON, episode wasn't found
        if 'stills' not in results:
            warn(f'TMDb has no matching episode for "{title} ({year})" Season '
                 f'{season}, Episode {episode}', 2)
            self.__update_blacklist(title, year, season, episode)
            return None

        # If 'stills' is in JSON, but is empty, then TMDb has no images
        if len(results['stills']) == 0:
            warn(f'TMDb has no images for "{title} ({year})" Season {season}, '
                 f'Episode {episode}', 2)
            self.__update_blacklist(title, year, season, episode)
            return None

        # Get the best image, None is returned if requirements weren't met
        best_image = self.__determine_best_image(results['stills'])
        if not best_image:
            warn(f'TMDb images for "{title} ({year})" Season {season}, Episode '
                 f'{episode} do not meet dimensional requirements.', 2)
            self.__update_blacklist(title, year, season, episode)
            return None
        
        return f'https://image.tmdb.org/t/p/original{best_image["file_path"]}'


    def get_series_logo(self, title: str, year: int) -> str:
        """
        Get the 'best' logo for the given series.
        
        :param      title:  The title of the requested series.

        :param      year:   The year of the requested series.
        
        :returns:   URL to the 'best' logo for the given series, and None if no
                    images are available.
        """

        # Get the TV id for the provided series+year
        tv_id = self.__get_tv_id(title, year)

        # GET params
        url = f'{self.API_BASE_URL}tv/{tv_id}/images'
        params = {'api_key': self.__api_key}

        # Make the GET request
        results = self._get(url=url, params=params)

        # If there are no logos, warn and exit
        if len(results['logos']) == 0:
            warn(f'TMDb has no logos for "{title} ({year})"', 1)
            return None

        # Pick the best image based on image dimensions
        best = results['logos'][0]
        valid_image = False
        for index, image in enumerate(results['logos']):
            # Skip SVG images (for now!)
            if image['file_path'].endswith('.svg'):
                continue

            # Skip logos that aren't english
            if image['iso_639_1'] != 'en':
                continue

            # Choose the best image on the pixel count alone
            valid_image = True
            if image['width']*image['height'] > best['width']*best['height']:
                best = results['logos'][index]

        if not valid_image:
            return None

        return f'https://image.tmdb.org/t/p/original{best["file_path"]}'


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



