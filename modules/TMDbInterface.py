from datetime import datetime, timedelta
from pathlib import Path
from pickle import dump, load, HIGHEST_PROTOCOL
from urllib.request import urlretrieve

from modules.Debug import *
import modules.preferences as global_preferences
from modules.SeriesInfo import SeriesInfo
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


    def __update_blacklist(self, series_info: SeriesInfo, season: int,
                           episode: int) -> None:
        """
        Adds the given entry to the blacklist; indicating that this exact entry
        shouldn't be queried to TheMovieDB (to prevent unnecessary queries).
        
        :param      series_info:    SeriesInfo for the entry.
        :param      season:         The entry's season number.
        :param      episode:        The entry's episode number.
        """

        key = f'{series_info.full_name}-{season}-{episode}'

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

        # warn(f'Query failed {self.__blacklist[key]["failures"]} times', 2)

        # Write latest version of blacklist to file, in case program exits
        with self.__BLACKLIST.open('wb') as file_handle:
            dump(self.__blacklist, file_handle, HIGHEST_PROTOCOL)


    def __is_blacklisted(self, series_info: SeriesInfo, season: int,
                         episode: int) -> bool:
        """
        Determines if the specified entry is in the blacklist (i.e. should
        not bother querying TMDb.
        
        :param      series_info:    SeriesInfo for the entry.
        :param      season:         The entry's season number.
        :param      episode:        The entry's episode number.
        
        :returns:   True if the entry is blacklisted, False otherwise.
        """

        key = f'{series_info.full_name}-{season}-{episode}'

        # If never indexed before, skip failure check
        if key not in self.__blacklist:
            return False
            
        if self.__blacklist[key]['failures'] >self.preferences.tmdb_retry_count:
            return True

        # If we haven't passed next time, then treat as temporary blacklist
        # i.e. before next = 'blacklisted', after next is not
        return datetime.now() < self.__blacklist[key]['next']


    def __add_id_to_map(self, series_info: SeriesInfo) -> None:
        """
        Adds a mapping of this full title to the corresponding TheMovieDB ID. If
        a TVDb ID was provided, map that as well
        
        :param      series_info:    SeriesInfo for the entry.
        """

        # Map full title to the TMDb id
        self.__id_map[series_info.full_name] = series_info.tmdb_id

        # If TVDb ID is available, map TVDb ID to the TMDb ID
        if series_info.tvdb_id != None:
            self.__id_map[series_info.tvdb_id] = series_info.tmdb_id

        # Write updated map to file
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


    def __set_tmdb_id(self, series_info: SeriesInfo) -> None:
        """
        Get the TMDb series ID associated with the given entry. If an ID is not
        provided, then matching is done with title and year. If this has been
        mapped previously, get value from map.
        
        :param      series_info:    SeriesInfo for the entry.
        """

        # If TVDb ID is available and is mapped, set that ID
        if series_info.tvdb_id != None and series_info.tvdb_id in self.__id_map:
            series_info.set_tmdb_id(self.__id_map[series_info.tvdb_id])
            return None

        # If already mapped, set that ID
        if series_info.full_name in self.__id_map:
            series_info.set_tmdb_id(self.__id_map[series_info.full_name])
            return None

        # Match by TVDB ID if available
        if series_info.tvdb_id != None:
            # Construct GET arguments
            url = f'{self.API_BASE_URL}find/{series_info.tvdb_id}'
            params = {'api_key': self.__api_key, 'external_source': 'tvdb_id'}

            # Query TMDb
            results = self._get(url=url, params=params)['tv_results']

            if len(results) == 0:
                # If there is no entry with this ID, error and return
                error(f'TMDb returned no results for "{series_info}"')
            elif len(results) != 1:
                # If more than one entry was returned (somehow?), warn
                warn(f'TMDb returned >1 series for "{series_info}"')
            else:
                # Get the TMDb ID for this series, set for object and add to map
                tmdb_id = results[0]['id']
                series_info.set_tmdb_id(tmdb_id)
                self.__add_id_to_map(series_info)
                return None

        # Match by title and year if no ID was given
        # Construct GET arguments
        url = f'{self.API_BASE_URL}search/tv/'
        params = {'api_key': self.__api_key, 'query': series_info.name,
                  'first_air_date_year': series_info.year}

        # Query TMDb
        results = self._get(url=url, params=params)

        # If there are no results, error and return
        if int(results['total_results']) == 0:
            error(f'TMDb returned no results for "{series_info}"')
            return None

        # Get the TMDb ID for this series, set for object and add to map
        series_info.set_tmdb_id(results['results'][0]['id'])
        self.__add_id_to_map(series_info)


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


    def get_title_card_source_image(self, series_info: SeriesInfo, season: int,
                                    episode: int, abs_number: int=None) -> str:
        """
        Get the best source image for the requested entry. The URL of this image
        is returned.
        
        :param      series_info:    SeriesInfo for the entry.
        :param      season:         The season of the requested entry.
        :param      episode:        The episode of the requested entry.
        :param      abs_number:     The absolute episode number of the entry.
        
        :returns:   URL to the 'best' source image for the requested entry. None
                    if no images are available.
        """

        # Don't query the database if this episode is in the blacklist
        if self.__is_blacklisted(series_info, season, episode):
            return None

        # Set the TV id for the provided series
        self.__set_tmdb_id(series_info)

        # GET params
        url = (f'{self.API_BASE_URL}tv/{series_info.tmdb_id}/season/{season}'
               f'/episode/{episode}/images')
        params = {'api_key': self.__api_key}

        # Make the GET request
        results = self._get(url=url, params=params)

        # If absolute number has been given and the first query failed,try again
        if (abs_number != None and 'success' in results
            and not results['success']):
            # Try surround season numbers (TMDb indexes these weirdly..)
            for new_season in range(1, season+1)[::-1]:
                url = (f'{self.API_BASE_URL}tv/{series_info.tmdb_id}/season/'
                       f'{new_season}/episode/{abs_number}/images')
                results = self._get(url=url, params=params)
                if 'stills' in results:
                    break

        # If 'stills' wasn't in return JSON, episode wasn't found
        if 'stills' not in results:
            warn(f'TMDb has no matching episode for "{series_info}" Season '
                 f'{season}, Episode {episode}', 2)
            self.__update_blacklist(series_info, season, episode)
            return None

        # If 'stills' is in JSON, but is empty, then TMDb has no images
        if len(results['stills']) == 0:
            warn(f'TMDb has no images for "{series_info}" Season {season}, '
                 f'Episode {episode}', 2)
            self.__update_blacklist(series_info, season, episode)
            return None

        # Get the best image, None is returned if requirements weren't met
        best_image = self.__determine_best_image(results['stills'])
        if not best_image:
            warn(f'TMDb images for "{series_info}" Season {season}, Episode '
                 f'{episode} do not meet dimensional requirements.', 2)
            self.__update_blacklist(series_info, season, episode)
            return None
        
        return f'https://image.tmdb.org/t/p/original{best_image["file_path"]}'


    def get_episode_title(self, series_info: SeriesInfo, season: int,
                          episode: int, abs_number: int=None,
                          language_code: str='en-US') -> str:
        """
        Get the episode title for the given entry for the given language.
        
        :param      series_info:    SeriesInfo for the entry.
        :param      season:         The season number of the episode.
        :param      episode:        The episode number of the episode
        :param      language_code:  The language code of the episode.
        
        :returns:   The episode title. None if the entry does not exist.
        """

        # Get the TV id for the provided series+year
        self.__set_tmdb_id(series_info)

        # GET params
        url = (f'{self.API_BASE_URL}tv/{series_info.tmdb_id}/season/{season}'
               f'/episode/{episode}')
        params = {'api_key': self.__api_key, 'language': language_code}

        # Make the GET request
        results = self._get(url=url, params=params)

        # If absolute number has been given and the first query failed,try again
        if (abs_number != None and 'success' in results
            and not results['success']):
            # Try surround season numbers (TMDb indexes these weirdly..)
            for new_season in range(1, season+1)[::-1]:
                url = (f'{self.API_BASE_URL}tv/{series_info.tmdb_id}/season/'
                       f'{new_season}/episode/{abs_number}')
                results = self._get(url=url, params=params)

                # Return name if this query succeeded
                if 'name' in results:
                    return results['name']

        # No absolute number to test (or tried all), skip!
        if 'success' in results and not results['success']:
            return None

        # Return the name for this episode
        return results['name']


    def get_series_logo(self, series_info: SeriesInfo) -> str:
        """
        Get the 'best' logo for the given series.
        
        :param      series_info:    SeriesInfo for the entry.
        
        :returns:   URL to the 'best' logo for the given series, and None if no
                    images are available.
        """

        # Set the TV id for the provided series+year
        self.__set_tmdb_id(series_info)

        # GET params
        url = f'{self.API_BASE_URL}tv/{series_info.tmdb_id}/images'
        params = {'api_key': self.__api_key}

        # Make the GET request
        results = self._get(url=url, params=params)

        # If there are no logos, warn and exit
        if len(results['logos']) == 0:
            warn(f'TMDb has no logos for "{series_info}"', 1)
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



