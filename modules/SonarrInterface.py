from datetime import datetime, timedelta
from re import IGNORECASE, compile as re_compile

from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo
import modules.global_objects as global_objects
from modules.SeriesInfo import SeriesInfo
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


    def __init__(self, url: str, api_key: str, verify_ssl: bool=True) -> None:
        """
        Construct a new instance of an interface to Sonarr.

        Args:
            url: The API url communicating with Sonarr.
            api_key: The API key for API requests.
            verify_ssl: Whether to verify SSL requests to Sonarr.

        Raises:
            SystemExit: Invalid Sonarr URL/API key provided.
        """

        # Initialize parent WebInterface 
        super().__init__('Sonarr', verify_ssl)
        
        # Get global MediaInfoSet object
        self.info_set = global_objects.info_set

        # Get correct URL
        url = url if url.endswith('/') else f'{url}/'
        if url.endswith('/api/v3/'):
            self.url = url
        elif (re_match := self._URL_REGEX.match(url)) is None:
            log.critical(f'Invalid Sonarr URL "{url}"')
            exit(1)
        else:
            self.url = f'{re_match.group(1)}/api/v3/'

        # Base parameters for sending requests to Sonarr
        self.__api_key = api_key
        self.__standard_params = {'apikey': api_key}

        # Query system status to verify connection to Sonarr
        try:
            status =self._get(f'{self.url}system/status',self.__standard_params)
            if status.get('appName') != 'Sonarr':
                log.critical(f'Cannot get Sonarr status - invalid URL/API key')
                exit(1)
        except Exception as e:
            log.critical(f'Cannot connect to Sonarr - returned error: "{e}"')
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
        
        # Reset series dictionary
        self.__series_ids = {}

        # Go through each series in Sonarr
        for series in all_series:
            # Get this series' internal (sonarr) and TVDb ID's
            data = {'sonarr_id': series['id'], 'tvdb_id': series['tvdbId']}

            # Map the primary title to these ID's
            si = SeriesInfo(series['title'], series['year'])
            self.__series_ids[si.full_match_name] = data
            self.__series_ids[f'sonarr:{series["id"]}'] = data
            self.__series_ids[f'tvdb:{series["tvdbId"]}'] = data

            # Map each alternate title to these ID's
            for alt_title in series['alternateTitles']:
                alt_si = SeriesInfo(alt_title['title'], series['year'])
                self.__series_ids[alt_si.full_match_name] = data


    def __warn_missing_series(self, series_info: SeriesInfo) -> None:
        """
        Warn a given series is missing from Sonarr, but only if it hasn't
        already been warned.
        
        Args:
            series_info: The SeriesInfo being warned.
        """

        # If this series has already been warned, return
        if series_info.full_name in self.__warned:
            return None

        # Series hasn't been warned - warn and add to list
        log.warning(f'Series "{series_info}" not found in Sonarr')
        self.__warned.append(series_info.full_name)


    def has_series(self, series_info: SeriesInfo) -> bool:
        """
        Query whether this Sonarr server has the given series.

        Args:
            series_info: Series being evaluated.

        Returns:
            True if the series is present on this server (checked under the full
            name); False otherwise.
        """

        # If known series ID, check under that ID and name
        if series_info.has_id('sonarr_id'):
            id_ = f'sonarr:{series_info.sonarr_id}'
            return (
                self.__series_ids.get(id_) is not None or
                self.__series_ids.get(series_info.full_match_name) is not None
            )
        if series_info.has_id('tvdb_id'):
            id_ = f'tvdb:{series_info.tvdb_id}'
            return (
                self.__series_ids.get(id_) is not None or
                self.__series_ids.get(series_info.full_match_name) is not None
            )

        return self.__series_ids.get(series_info.full_match_name) is not None


    def get_all_series(self, required_tags: list[str]=[], 
                       excluded_tags: list[str]=[], monitored_only: bool=False,
                       downloaded_only:bool=False)->list[tuple[SeriesInfo,str]]:
        """
        Get all the series within Sonarr, filtered by the given parameters.

         Args:
            required_tags: List of tags to filter return by. If provided, only
                series that have all of the given tags are returned.
            excluded_tags: List of tags to filter return by. If provided, series
                with any of the given tags are excluded from return.
            monitored_only: Whether to filter return to exclude series that are
                unmonitored within Sonarr.
            downloaded_only: Whether to filter return to exclude series that do
                not have any downloaded episodes.

        Returns:
            List of tuples. Tuple contains the SeriesInfo object for the series,
            and the Path to the series' media as reported by Sonarr.
        """

        # Construct GET arguments
        all_series = self._get(f'{self.url}series', self.__standard_params)

        # Get filter tags if indicated
        required_tag_ids, excluded_tag_ids = [], []
        if len(required_tags) > 0 or len(excluded_tags) > 0:
            # Request all Sonarr tags
            all_tags = self._get(f'{self.url}tag', self.__standard_params)

            # Convert tag names to ID's
            required_tag_ids = [tag['id'] for tag in all_tags
                                if tag['label'] in required_tags]
            excluded_tag_ids = [tag['id'] for tag in all_tags
                                if tag['label'] in excluded_tags]

        # Go through each series in Sonarr
        series = []
        for show in all_series:
            # Skip if monitored only and show isn't monitored
            if monitored_only and not show['monitored']:
                continue

            # Skip if downloaded only and filesize is 0
            if (downloaded_only
                and show.get('statistics', {}).get('sizeOnDisk') == 0):
                continue

            # Skip show if tag is in exclude list
            if (len(excluded_tag_ids) > 0
                and any(tag in excluded_tag_ids for tag in show['tags'])):
                continue

            # Skip show if tag isn't in filter (and filter is enabled)
            if (len(required_tag_ids) > 0
                and not all(tag in show['tags'] for tag in required_tag_ids)):
                continue

            # Skip show if it has a year of 0
            if show['year'] == 0:
                continue

            # Construct SeriesInfo object for this show
            series_info = SeriesInfo(
                show['title'],
                show['year'],
                imdb_id=show.get('imdbId'),
                sonarr_id=show.get('id'),
                tvdb_id=show.get('tvdbId'),
            )
            
            # Add to returned list
            series.append((series_info, show['path']))

        return series


    def set_series_ids(self, series_info: SeriesInfo) -> None:
        """
        Set the TVDb ID for the given SeriesInfo object.

        Args:
            series_info: SeriesInfo to update.
        """

        # Match priority is Sonarr ID > TVDb ID > Series name
        if (series_info.sonarr_id is not None and
            (ids := self.__series_ids.get(f'sonarr:{series_info.sonarr_id}'))):
            pass
        elif (series_info.tvdb_id is not None and 
            (ids := self.__series_ids.get(f'tvdb:{series_info.tvdb_id}'))):
            pass
        elif (ids := self.__series_ids.get(series_info.full_match_name)):
            pass
        else:
            self.__warn_missing_series(series_info)
            return None

        # Set ID's for this series
        series_info.set_sonarr_id(ids['sonarr_id'])
        series_info.set_tvdb_id(ids['tvdb_id'])


    def get_all_episodes(self, series_info: SeriesInfo) -> list[EpisodeInfo]:
        """
        Gets all episode info for the given series. Only episodes that have 
        already aired are returned.
        
        Args:
            series_info: SeriesInfo for the entry.
        
        Returns:
            List of EpisodeInfo objects for the given series.
        """

        # If no ID was returned, error and return an empty list
        if series_info.sonarr_id is None:
            self.__warn_missing_series(series_info)
            return []

        # Construct GET arguments
        url = f'{self.url}episode/'
        params = {'apikey': self.__api_key, 'seriesId': series_info.sonarr_id}

        # Query Sonarr to get JSON of all episodes for this series
        all_episodes = self._get(url, params)
        all_episode_info = []

        # Go through each episode and get its season/episode number, and title
        for episode in all_episodes:
            # Get airdate of this episode
            air_datetime = None
            if (ep_airdate := episode.get('airDateUtc')) is not None:
                # If episode hasn't aired, skip
                air_datetime=datetime.strptime(ep_airdate,self.__AIRDATE_FORMAT)
                if not episode['hasFile']and air_datetime > datetime.now():
                    continue

                # Skip temporary placeholder names if aired in the last 48 hours
                if (self.__TEMP_IGNORE_REGEX.match(episode['title'])
                    and air_datetime + timedelta(days=2) > datetime.now()):
                    log.debug(f'Temporarily ignoring "{episode["title"]}" of '
                              f'{series_info} - placeholder title')
                    continue

            # Skip permanent placeholder names
            if self.__ALWAYS_IGNORE_REGEX.match(episode['title']):
                continue
            
            # Create EpisodeInfo object for this entry
            episode_info = self.info_set.get_episode_info(
                series_info,
                episode['title'],
                episode['seasonNumber'],
                episode['episodeNumber'],
                episode.get('absoluteEpisodeNumber'),
                tvdb_id=episode.get('tvdbId'),
                title_match=True,
                queried_sonarr=True,
                airdate=air_datetime,
            )

            # Add to episode list
            if episode_info is not None:
                all_episode_info.append(episode_info)

        return all_episode_info


    def set_episode_ids(self, series_info: SeriesInfo,
                        infos: list[EpisodeInfo]) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo objects. This
        sets the TVDb ID for each episode.
        
        Args:
            series_info: SeriesInfo for the entry.
            infos: List of EpisodeInfo objects to update. Not used.
        """

        # Get all Sonarr-created EpisodeInfo objects
        self.get_all_episodes(series_info)


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