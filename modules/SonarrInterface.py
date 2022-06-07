from datetime import datetime, timedelta
from pathlib import Path
from re import IGNORECASE, compile as re_compile

from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo
from modules.SeriesInfo import SeriesInfo
from modules.Title import Title
from modules.WebInterface import WebInterface

class SonarrInterface(WebInterface):
    """
    This class describes a Sonarr interface, which is a type of WebInterface.
    The primary purpose of this class is to get episode titles, as well as
    database ID's for episodes.
    """

    """Episode titles that indicate a placeholder and are to be ignored"""
    __TEMP_IGNORE_REGEX = re_compile(r'^(tba|tbd|episode \d+)$', IGNORECASE)
    __ALWAYS_IGNORE_REGEX = re_compile(r'^(tba|tbd)$', IGNORECASE)

    """Datetime format string for airDateUtc field in Sonarr API requests"""
    __AIRDATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


    def __init__(self, url: str, api_key: str) -> None:
        """
        Constructs a new instance of an interface to Sonarr.
        
        :param      url:        The API url communicating with Sonarr.
        :param      api_key:    The api key for API requests.
        """

        # Initialize parent WebInterface 
        super().__init__()

        # Add / if not given
        self.url = url + ('' if url.endswith('/') else '/')

        # If non-api URL, exit
        if not self.url.endswith(('/api/v3/', '/api/')):
            log.critical(f'Sonarr URL must be an API url, add /api/')
            exit(1)

        # Warn if a v3 API url has not been provided
        if not self.url.endswith('/v3/'):
            log.warning(f'Provided Sonarr URL ({self.url}) is not v3, add /v3/')

        # Base parameters for sending requests to Sonarr
        self.__api_key = api_key
        self.__standard_params = {'apikey': api_key}

        # Query system status to verify connection to Sonarr
        try:
            status =self._get(f'{self.url}system/status',self.__standard_params)
            if 'error' in status and status['error'] == 'Unauthorized':
                raise Exception('Invalid API key')
        except Exception as e:
            log.critical(f'Cannot query Sonarr - returned error: "{e}"')
            exit(1)

        # Create blank dictionary of titles -> ID's
        self.__series_ids = {}

        # List of missing series that have already been warned 
        self.__warned = []

        # Parse all Sonarr series
        self.__map_all_ids()


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return (f'<SonarrInterface {self.url=}, {self.__api_key=}'
                f', mapping of {len(self.__series_ids)} series>')


    def __warn_missing_series(self, series_info: SeriesInfo) -> None:
        """
        Warn a given series is missing from Sonarr, but only if it hasn't
        already been warned.
        
        :param      series_info:  The SeriesInfo being warned.
        """

        # If this series has already been warned, return
        if series_info.full_name in self.__warned:
            return None

        # Series hasn't been warned - warn and add to list
        log.warning(f'Series "{series_info}" not found in Sonarr')
        self.__warned.append(series_info.full_name)


    def __set_ids(self, series_info: SeriesInfo) -> None:
        """
        Set the Sonarr series ID and the TVDb ID for the given SeriesInfo
        object.
        
        :param      series_info:    SeriesInfo to modify.
        """

        # Series does not exist in Sonarr
        if series_info.full_match_name not in self.__series_ids:
            return None

        # Get the Sonarr ID from the ID map
        sonarr_id = self.__series_ids[series_info.full_match_name]['sonarr_id']
        series_info.set_sonarr_id(sonarr_id)

        # Get the TVDb ID from the ID map
        tvdb_id = self.__series_ids[series_info.full_match_name]['tvdb_id']
        series_info.set_tvdb_id(tvdb_id)


    def __map_all_ids(self) -> None:
        """
        Map all Sonarr series to their Sonarr and TVDb ID's. This updates this
        object's __series_ids attribute with keys of the full name for each
        series (as well as the full name version of each alternate title) to a
        dictionary with data 'sonarr_id' and 'tvdb_id'.
        """

        # Construct GET arguments
        url = f'{self.url}series'
        params = self.__standard_params
        all_series = self._get(url, params)

        # Go through each series in Sonarr
        for series in all_series:
            # Get this series' internal (sonarr) and TVDb ID's
            data = {
                'sonarr_id': series['id'],
                'tvdb_id': series['tvdbId'],
            }

            # Map the primary title to these ID's
            si = SeriesInfo(series['title'], series['year'])
            self.__series_ids[si.full_match_name] = data

            # Map each alternate title to these ID's
            for alt_title in series['alternateTitles']:
                alt_si = SeriesInfo(alt_title['title'], series['year'])
                self.__series_ids[alt_si.full_match_name] = data


    def list_all_series_id(self) -> None:
        """List all the series ID's of all shows used by Sonarr. """

        # Construct GET arguments
        url = f'{self.url}series'
        params = self.__standard_params
        all_series = self._get(url, params)

        # Go through each series in Sonarr
        for show in all_series:
            # Print the main and alternate titles
            main_title = show['title']
            alt_titles = [_['title'] for _ in show['alternateTitles']]

            padding = len(f'{show["id"]} : ')
            titles = f'\n{" " * padding}'.join([main_title] + alt_titles)
            print(f'{show["id"]} : {titles}')


    def __get_all_episode_info(self, series_id: int) -> [EpisodeInfo]:
        """
        Gets all episode info for the given series ID. Only returns episodes
        that have aired already.
        
        :param      series_id:  The series identifier.
        
        :returns:   List of EpisodeInfo for the given series id. Only entries 
                    that have ALREADY aired (or do not air) are returned.
        """

        # Construct GET arguments
        url = f'{self.url}episode/'
        params = {'apikey': self.__api_key, 'seriesId': series_id}

        # Query Sonarr to get JSON of all episodes for this series
        all_episodes = self._get(url, params)
        all_episode_info = []

        # Go through each episode and get its season/episode number, and title
        for episode in all_episodes:
            # Get airdate of this episode
            if (ep_airdate := episode.get('airDateUtc')) is not None:
                # If episode hasn't aired, skip
                air_datetime=datetime.strptime(ep_airdate,self.__AIRDATE_FORMAT)
                if (not episode['hasFile']
                    and air_datetime > datetime.now() + timedelta(hours=2)):
                        continue

                # Skip temporary placeholder names if aired in the last 48 hours
                if (self.__TEMP_IGNORE_REGEX.match(episode['title'])
                    and air_datetime > datetime.now() + timedelta(days=2)):
                        continue

            # Skip permanent placeholder names
            if self.__ALWAYS_IGNORE_REGEX.match(episode['title']):
                continue

            # Create EpisodeInfo object for this entry
            # Non-canon episodes don't have absolute numbers
            episode_info = EpisodeInfo(
                Title(episode['title']),
                episode['seasonNumber'],
                episode['episodeNumber'],
                episode.get('absoluteEpisodeNumber', None)
            )

            # Add info for the Sonarr ID
            episode_info.set_sonarr_id(episode['id'])

            # If this episode has a non-zero TVDb ID (that exists), add that
            if episode.get('tvdbId'):
                episode_info.set_tvdb_id(episode['tvdbId'])

            all_episode_info.append(episode_info)

        return all_episode_info


    def get_all_episodes_for_series(self,
                                    series_info: SeriesInfo) -> [EpisodeInfo]:
        """
        Gets all episode info for the given series title from Sonarr. Only
        episodes that have already aired are returned.
        
        :param      series_info:    SeriesInfo for the entry.
        
        :returns:   List of EpisodeInfo objects for this series.
        """

        # Set the Sonarr ID for this series
        self.__set_ids(series_info)

        # If no ID was returned, error and return an empty list
        if series_info.sonarr_id is None:
            self.__warn_missing_series(series_info)
            return []

        return self.__get_all_episode_info(series_info.sonarr_id)


    def set_series_ids(self, series_info: SeriesInfo) -> None:
        """
        Set the TVDb ID to the given SeriesInfo object.

        :param      series_info:    SeriesInfo for the entry.
        """

        # Set the Sonarr ID for this series
        self.__set_ids(series_info)

        # If no ID was returned, error and return
        if series_info.sonarr_id is None:
            self.__warn_missing_series(series_info)


    def set_all_episode_ids(self, series_info: SeriesInfo,
                            all_episodes: ['Episode']) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo objects. This
        sets the Sonarr and TVDb ID's for each episode. As a byproduct, this
        also updates the series ID's for the SeriesInfo object
        
        :param      series_info:    SeriesInfo for the entry.
        :param      all_episodes:   List of Episodes to update the EpisodeInfo
                                    object of.
        """

        # Set the Sonarr ID for this series
        self.__set_ids(series_info)

        # Get all sonarr-created EpisodeInfo objects
        all_sonarr_episodes = self.get_all_episodes_for_series(series_info)

        # Go through each episode 
        for episode in all_episodes:
            # Find the matching EpisodeInfo object returned by Sonarr
            for sonarr_info in all_sonarr_episodes:
                # If these objects correspond to the same data, transfer ID's
                # from the Sonarr EpisodeInfo objects to the primary ones
                if episode.episode_info == sonarr_info:
                    episode.episode_info.copy_ids(sonarr_info)
                    break


    def get_series(self, filter_tags: list=[]) -> [(SeriesInfo, Path)]:
        """
        Get a list of tuples of series and their paths within Sonarr. The list
        can be filtered by a list of tags, any series with any of those tags
        are returned.

        :param      filter_tags:    Optional list of tag NAMES to filter the
                                    returned list by. If provided, a series must
                                    have at least one of the given tags.
        
        :returns:   List of tuples. The tuple contains the SeriesInfo object
                    for the series, and the Path to the media as reported by
                    Sonarr.
        """

        # Construct GET arguments
        all_series = self._get(f'{self.url}series', self.__standard_params)

        # Get filter tags if indicated
        filter_tag_ids = []
        if len(filter_tags) > 0:
            # Request all Sonarr tags
            all_tags = self._get(f'{self.url}tag', self.__standard_params)
            filter_tag_ids = [tag['id'] for tag in all_tags
                              if tag['label'] in filter_tags]

        # Go through each series in Sonarr
        series = []
        for show in all_series:
            # Skip show if tag isn't in filter (and filter is enabled)
            if (len(filter_tag_ids) > 0
                and not any(tag in filter_tag_ids for tag in show['tags'])):
                    continue

            # Construct SeriesInfo object for this show
            series_info = SeriesInfo(show['title'], show['year'])
            series_info.set_tvdb_id(show['tvdbId'])
            
            series.append((series_info, Path(show['path'])))

        return series

        