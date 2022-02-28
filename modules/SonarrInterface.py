from datetime import datetime
from pathlib import Path
from pickle import dump, load, HIGHEST_PROTOCOL

from modules.Debug import *
from modules.SeriesInfo import SeriesInfo
from modules.Title import Title
from modules.WebInterface import WebInterface

class SonarrInterface(WebInterface):
    """
    This class describes a Sonarr interface, which is a type of WebInterface.
    The primary purpose of this class is to get episode titles for series
    entries.
    """

    """Datetime format string for airDateUtc field in Sonarr API requests"""
    __AIRDATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    """Path to the map of sonarr titles to ID's"""
    __ID_MAP = Path(__file__).parent / '.objects' / 'sonarr_id_map.pkl'

    """Path to the mapping of Sonarr IDs to TVDb ID's"""
    __TVDB_ID_MAP = Path(__file__).parent / '.objects' / 'sid_tvdb_id.pkl'

    def __init__(self, url: str, api_key: str) -> None:
        """
        Constructs a new instance of an interface to Sonarr.
        
        :param      url:        The base url of Sonarr.
        :param      api_key:    The api key for requesting data to/from Sonarr.
        """

        # Initialize parent WebInterface 
        super().__init__()

        # Create objects directory if it does not exist
        self.__ID_MAP.parent.mkdir(parents=True, exist_ok=True)
        self.__TVDB_ID_MAP.parent.mkdir(parents=True, exist_ok=True)

        # Attempt to read existing ID map
        if self.__ID_MAP.exists():
            with self.__ID_MAP.open('rb') as file_handle:
                self.__id_map = load(file_handle)
        else:
            self.__id_map = {}

        if self.__TVDB_ID_MAP.exists():
            with self.__TVDB_ID_MAP.open('rb') as file_handle:
                self.__tvdb_id_map = load(file_handle)
        else:
            self.__tvdb_id_map = {}

        # Add /api/ endpoint if not provided
        if not url.endswith('api') and not url.endswith('api/'):
            url += 'api/' if url.endswith('/') else '/api/'
        self._url_base = url + ('' if url.endswith('/') else '/')

        # Base parameters for sending requests to Sonarr
        self._param_base = {'apikey': api_key}


    def __map_title_to_id(self, series_info: SeriesInfo) -> None:
        """
        Add the given ID to the object's map. Write this updated map object to
        the file.
        
        :param      series_info:    SeriesInfo to modify
        """

        # Add to map
        self.__id_map[series_info.full_name] = series_info.sonarr_id

        # Write new map to file
        with self.__ID_MAP.open('wb') as file_handle:
            dump(self.__id_map, file_handle, HIGHEST_PROTOCOL)


    def __map_id_to_tvdb(self, series_info: SeriesInfo) -> None:
        """
        Add the given Sonarr ID to the object's mapping of Sonarr ID's to TVDb
        ID's. Write this updated map object to the file.
        
        :param      series_info:    SeriesInfo to modify
        """

        # Add to map
        self.__tvdb_id_map[series_info.sonarr_id] = series_info.tvdb_id

        # Write new map to file
        with self.__TVDB_ID_MAP.open('wb') as file_handle:
            dump(self.__tvdb_id_map, file_handle, HIGHEST_PROTOCOL)


    def __set_sonarr_id(self, series_info: SeriesInfo) -> None:
        """
        Gets the series ID used by Sonarr to identify this show.
        
        :param      series_info:    SeriesInfo to modify
        """

        # If already mapped, return th
        if series_info.full_name in self.__id_map:
            series_info.set_sonarr_id(self.__id_map[series_info.full_name])
            return None

        # Construct GET arguments
        url = f'{self._url_base}series/'
        params = self._param_base

        # Query Sonarr to get JSON of all series in the library
        all_series = self._get(url, params)

        # Go through each series
        for show in all_series:
            # Skip shows with a year mismatch, prevents parsing titles (slower)
            if int(show['year']) != series_info.year:
                continue

            # Year matches, verify the given title matches main/alternate titles
            if series_info.matches(show['title'], *show['alternateTitles']):
                series_info.set_sonarr_id(show['id'])
                self.__map_title_to_id(series_info)

                return None


    def get_absolute_episode_number(self, series_info: SeriesInfo,
                                    season_number: int,
                                    episode_number: int) -> int:
        """
        Gets the absolute episode number of the given entry.
        
        :param      series_info:    SeriesInfo for the entry.
        :param      season_number:  The season number of the entry.
        :param      episode_number: The episode number of the entry.
        
        :returns:   The absolute episode number. None if not found, or if the
                    entry does not have an absolute number.
        """

        # Get the ID for this series
        self.__set_sonarr_id(series_info)

        # If not found, skip
        if not series_info.sonarr_id:
            error(f'Cannot find series "{series_info}" in Sonarr')
            return None

        # Get all episodes, and match by season+episode number
        for episode in self._get_all_episode_data_for_id(series_info):
            season_match = (episode['season_number'] == season_number)
            episode_match = (episode['episode_number'] == episode_number)

            if season_match and episode_match and 'abs_number' in episode:
                return episode['abs_number']

        return None


    def list_all_series_id(self) -> None:
        """List all the series ID's of all shows used by Sonarr. """

        # Construct GET arguments
        url = f'{self._url_base}series/'
        params = self._param_base
        
        # Query Sonarr to get JSON of all series in the library
        all_series = self._get(url, params)

        if 'error' in all_series:
            error(f'Sonarr returned error "{all_series["error"]}"')
            return None

        # Go through each series
        for show in all_series:
            main_title = show['title']
            alt_titles = [_['title'] for _ in show['alternateTitles']]

            padding = len(f'{show["id"]} : ')
            titles = f'\n{" " * padding}'.join([main_title] + alt_titles)
            print(f'{show["id"]} : {titles}')


    def _get_all_episode_data_for_id(self, series_id: int) -> list:
        """
        Gets all episode data for identifier. Only returns episodes that have
        aired already.
        
        :param      series_id:  The series identifier.
        
        :returns:   All episode data for the given series id. Only entries that
                    have ALREADY aired (or do not air) are returned.
        """

        # Construct GET arguments
        url = f'{self._url_base}episode/'
        params = self._param_base
        params.update(seriesId=series_id)

        # Query Sonarr to get JSON of all episodes for this series id
        all_episodes = self._get(url, params)

        # Go through each episode and get its season/episode number, and title
        episode_info = []
        for episode in all_episodes:
            # Unaired episodes (such as specials) won't have airDateUtc key
            if 'airDateUtc' in episode:
                # Verify this episode has already aired, skip if not
                air_datetime = datetime.strptime(
                    episode['airDateUtc'],
                    self.__AIRDATE_FORMAT
                )
                if air_datetime > datetime.now():
                    continue

            # Skip episodes whose titles aren't in Sonarr yet to avoid
            # placeholder names
            if episode['title'].lower() == 'tba':
                continue

            new_info = {
                'season_number':    int(episode['seasonNumber']),
                'episode_number':   int(episode['episodeNumber']),
                'title':            Title(episode['title']),
                # 'filename':         Path(episode['episodeFile']['path']).stem,
            }

            # Non-cannon episodes don't have an absolute number
            if 'absoluteEpisodeNumber' in episode:
                new_info['abs_number'] = int(episode['absoluteEpisodeNumber'])

            episode_info.append(new_info)

        return episode_info


    def get_all_episodes_for_series(self, series_info: SeriesInfo) -> list:
        """
        Gets all episode info for the given series title from Sonarr. The
        returned info is season/episode number and title for each episode.

        Only episodes that have already aired are returned.
        
        :param      series_info:    SeriesInfo for the entry.
        
        :returns:   List of dictionaries of episode data.
        """

        # Set the Sonarr ID for this series
        self.__set_sonarr_id(series_info)

        # If no ID was returned, error and return an empty list
        if series_info.sonarr_id == None:
            error(f'Series "{series_info}" not found in Sonarr')
            return []

        return self._get_all_episode_data_for_id(series_info.sonarr_id)


    def set_tvdb_id_for_series(self, series_info: SeriesInfo) -> None:
        """
        Set the TVDb ID to the given SeriesInfo object.

        :param      series_info:    SeriesInfo for the entry.
        """

        # Set the Sonarr ID for this series
        self.__set_sonarr_id(series_info)

        # If no ID was returned, error and return
        if series_info.sonarr_id == None:
            error(f'Series "{series_info}" not found in Sonarr')
            return None

        # If the series ID has already been mapped, return that value
        if series_info.sonarr_id in self.__tvdb_id_map:
            series_info.set_tvdb_id(self.__tvdb_id_map[series_info.sonarr_id])
            return None

        # Construct GET arguments
        url = f'{self._url_base}series/{series_info.sonarr_id}'
        params = self._param_base
        params.update({'id': series_info.sonarr_id})

        # Query Sonarr for info on this series
        sonarr_info = self._get(url, params)

        # Add this ID to the map
        series_info.set_tvdb_id(sonarr_info['tvdbId'])
        self.__map_id_to_tvdb(series_info)


    @staticmethod
    def manually_specify_id(title: str, year: int, sonarr_id: int) -> None:
        """
        Manually override the Sonarr ID for the given full title.

        :param      title:      The title of the series.
        :param      year:       The year of the series.
        :param      sonarr_id:  The Sonarr ID for this series.
        """

        # Create SeriesInfo object for this info
        series_info = SeriesInfo(title, year)
        series_info.set_sonarr_id(sonarr_id)

        SonarrInterface('', '').__map_title_to_id(series_info)

        info(f'Specified ID {series_info.sonarr_id} for "{series_info}"')
        


        