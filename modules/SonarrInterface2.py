from datetime import datetime, timedelta
from re import IGNORECASE, compile as re_compile
from typing import Literal, Optional

from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
# import modules.global_objects as global_objects
from modules.SeriesInfo import SeriesInfo
from modules.SyncInterface import SyncInterface
from modules.WebInterface import WebInterface

SeriesType = Literal['anime', 'daily', 'standard']

class SonarrInterface(WebInterface, SyncInterface):
    """
    This class describes a Sonarr interface, which is a type of
    WebInterface and SyncInterface object.
    """

    """Use a longer request timeout for Sonarr to handle slow databases"""
    REQUEST_TIMEOUT = 30

    """Series ID's that can be set by Sonarr"""
    SERIES_IDS = ('imdb_id', 'sonarr_id', 'tvdb_id', 'tvrage_id')

    """Series types that can be specified to filter a sync with"""
    VALID_SERIES_TYPES = ('anime', 'daily', 'standard')

    """Episode titles that indicate a placeholder and are to be ignored"""
    __TEMP_IGNORE_REGEX = re_compile(r'^(tba|tbd|episode \d+)$', IGNORECASE)
    __ALWAYS_IGNORE_REGEX = re_compile(r'^(tba|tbd)$', IGNORECASE)

    """Datetime format string for airDateUtc field in Sonarr API requests"""
    __AIRDATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


    def __init__(self, url: str, api_key: str, verify_ssl: bool=True,
            server_id: int=0) -> None:
        """
        Construct a new instance of an interface to Sonarr.

        Args:
            url: The API url communicating with Sonarr.
            api_key: The API key for API requests.
            verify_ssl: Whether to verify SSL requests to Sonarr.
            server_id: Server ID of this server.

        Raises:
            SystemExit: Invalid Sonarr URL/API key provided.
        """

        # Initialize parent WebInterface
        super().__init__('Sonarr', verify_ssl)

        # Get global MediaInfoSet object
        # self.info_set = global_objects.info_set

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
        self.server_id = server_id

        # Query system status to verify connection to Sonarr
        try:
            status =self._get(f'{self.url}system/status',self.__standard_params)
            if status.get('appName') != 'Sonarr':
                log.critical(f'Cannot get Sonarr status - invalid URL/API key')
                exit(1)
        except Exception as e:
            log.critical(f'Cannot connect to Sonarr - returned error: "{e}"')
            exit(1)

        # Parse all Sonarr series
        self.__series_data = {}
        self.__map_all_series_data()


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return (
            f'<SonarrInterface {self.server_id=}, {self.url=}, '
            f'{self.__api_key=}>'
        )


    def __map_all_series_data(self) -> None:
        """
        Map all Sonarr series to their Sonarr and TVDb ID's. This
        updates this object's __series_data attribute with keys of the
        full name for each series (as well as the full name version of
        each alternate title) to a SonarrSeriesInfo dataclass.
        """

        # Construct GET arguments
        url = f'{self.url}series'
        params = self.__standard_params
        all_series = self._get(url, params)

        # Reset series dictionary
        self.__series_ids = {}

        # Go through each series in Sonarr
        for series in all_series:
            # Skip unaired series with a year of 0
            if series['year'] == 0:
                continue

            # Unpopulated TVRage ID's are left as 0
            tvrage_id = None
            if series.get('tvRageId'):
                tvrage_id = series.get('tvRageId')

            # Data to store for this series, eventually for updating
            # a SeriesInfo object with
            data = {
                'imdb_id': series.get('imdbId'),
                'sonarr_id': f'{self.server_id}-{series["id"]}',
                'tvdb_id': series.get('tvdbId'),
                'tvrage_id': tvrage_id,
            }

            # Create keys to store this data under
            # Always store series under full name and sonarr ID
            keys = [
                f'{series["title"]} ({series["year"]})',
                f'sonarr:{self.server_id}-{series["id"]}',
            ]

            # Also store under any provided database ID's
            if series.get('imdbId'): keys.append(f'imdb:{series["imdbId"]}')
            if series.get('tvdbId'): keys.append(f'tvdb:{series["tvdbId"]}')
            if tvrage_id:            keys.append(f'tvrage:{tvrage_id}')

            # Also store series under any available alternative titles
            for alt_title in series['alternateTitles']:
                keys.append(f'{alt_title["title"]} ({series["year"]})')

            # Update all identified keys inside series data dict
            self.__series_data.update(dict.fromkeys(keys, data))


    def has_series(self, series_info: SeriesInfo) -> bool:
        """
        Query whether this Sonarr server has the given series.

        Args:
            series_info: Series being evaluated.

        Returns:
            True if the series is present on this server. False
            otherwise.
        """

        # Check for series under any possible keys
        if self.__series_data.get(series_info.full_name):
            return True
        elif (series_info.has_id('imdb_id')
            and self.__series_data.get(f'imdb:{series_info.imdb_id}')):
            return True
        elif (series_info.has_id('sonarr_id')
            and self.__series_data.get(f'sonarr:{series_info.sonarr_id}')):
            return True
        elif (series_info.has_id('tvdb_id')
            and self.__series_data.get(f'tvdb:{series_info.tvdb_id}')):
            return True
        elif (series_info.has_id('tvrage_id')
            and self.__series_data.get(f'tvrage_id:{series_info.tvrage_id}')):
            return True

        return False


    def get_all_series(self,
            required_tags: list[str] = [], 
            excluded_tags: list[str] = [],
            monitored_only: bool = False,
            downloaded_only: bool = False,
            required_series_type: Optional[SeriesType] = None,
            excluded_series_type: Optional[SeriesType] = None,
            ) -> list[tuple[SeriesInfo, str]]:
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
            series_type: Optional series type to filter series by.

        Returns:
            List of tuples. Tuple contains the SeriesInfo object for the series,
            and the Path to the series' media as reported by Sonarr.
        """

        # Construct GET arguments
        all_series = self._get(f'{self.url}series', self.__standard_params)

        # Get filtering tags if indicated
        required_tag_ids, excluded_tag_ids = [], []
        if len(required_tags) > 0 or len(excluded_tags) > 0:
            # Request all Sonarr tags, create mapping of label -> ID
            all_tags = {
                tag['label']: tag['id']
                for tag in self._get(f'{self.url}tag', self.__standard_params)
            }

            # Convert tag names to ID's
            required_tag_ids = [all_tags.get(tag, -1) for tag in required_tags]
            excluded_tag_ids = [all_tags.get(tag, -1) for tag in excluded_tags]

            # Log tags not identified with a matching ID
            for tag in (set(required_tags)|set(excluded_tags)) - set(all_tags):
                log.warning(f'Tag "{tag}" not found on Sonarr')

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
            if (len(excluded_tags) > 0
                and any(tag in excluded_tag_ids for tag in show['tags'])):
                continue

            # Skip show if tag isn't in filter (and filter is enabled)
            if (len(required_tags) > 0
                and not all(tag in show['tags'] for tag in required_tag_ids)):
                continue

            # Filter by series type
            if (required_series_type is not None
                and show['seriesType'] != required_series_type):
                continue
            if (excluded_series_type is not None
                and show['seriesType'] == excluded_series_type):
                continue

            # Skip show if it has a year of 0
            if show['year'] == 0:
                continue

            # Get TVRage ID (0 if not filled out)
            tvrage_id = None
            if show.get('tvRageId'):
                tvrage_id = show.get('tvRageId')

            # Construct SeriesInfo object for this show, do not use MediaInfoSet
            series_info = SeriesInfo(
                show['title'],
                show['year'],
                imdb_id=show.get('imdbId'),
                sonarr_id=f'{self.server_id}-{show.get("id")}',
                tvdb_id=show.get('tvdbId'),
                tvrage_id=tvrage_id,
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

        # If all possible ID's are defined, exit
        if series_info.has_ids(*self.SERIES_IDS):
            return None

        # Look for this series under any of the possible stored keys
        if (data := self.__series_data.get(series_info.full_name)):
            pass
        elif (series_info.has_id('imdb_id') and
            (data := self.__series_data.get(f'imdb:{series_info.imdb_id}'))):
            pass
        elif (series_info.has_id('sonarr_id') and
            (data := self.__series_data.get(f'sonarr:{series_info.sonarr_id}'))):
            pass
        elif (series_info.has_id('tvdb_id') and
            (data := self.__series_data.get(f'tvdb:{series_info.tvdb_id}'))):
            pass
        elif (series_info.has_id('tvrage_id') and
            (data := self.__series_data.get(f'tvrage_id:{series_info.tvrage_id}'))):
            pass
        else:
            log.warning(f'Series "{series_info}" not found in Sonarr')
            return None

        series_info.set_imdb_id(data['imdb_id'])
        series_info.set_sonarr_id(data['sonarr_id'])
        series_info.set_tvdb_id(data['tvdb_id'])
        series_info.set_tvrage_id(data['tvrage_id'])


    def get_all_episodes(self, series_info: SeriesInfo, *,
            preferences=None) -> list[EpisodeInfo]:
        """
        Gets all episode info for the given series. Only episodes that
        have  already aired are returned.

        Args:
            series_info: SeriesInfo for the entry.

        Returns:
            List of EpisodeInfo objects for the given series.
        """

        # If no ID was returned, error and return an empty list
        if series_info.sonarr_id is None:
            log.warning(f'Series "{series_info}" not found in Sonarr')
            return []

        # Construct GET arguments
        url = f'{self.url}episode/'
        params = {'apikey': self.__api_key,
                  'seriesId': int(series_info.sonarr_id.split('-')[1])}

        # Query Sonarr to get JSON of all episodes for this series
        all_episodes = self._get(url, params)
        all_episode_info = []

        # Go through each episode and get its season/episode number, and title
        has_bad_ids = False
        for episode in all_episodes:
            # Get airdate of this episode
            air_datetime = None
            if (ep_airdate := episode.get('airDateUtc')) is not None:
                # If episode hasn't aired, skip
                air_datetime=datetime.strptime(ep_airdate,self.__AIRDATE_FORMAT)
                if not episode['hasFile'] and air_datetime > datetime.now():
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

            # If the episode's TVDb ID is 0, then set to None to avoid mismatch
            if episode.get('tvdbId') == 0:
                episode['tvdbId'] = None
                has_bad_ids = True

            # Create EpisodeInfo object for this entry
            episode_info = EpisodeInfo(
                # series_info,
                episode['title'],
                episode['seasonNumber'],
                episode['episodeNumber'],
                episode.get('absoluteEpisodeNumber'),
                tvdb_id=episode.get('tvdbId'),
                airdate=air_datetime,
                queried_sonarr=True,
                preferences=preferences,
            )

            # Add to episode list
            if episode_info is not None:
                all_episode_info.append(episode_info)

        # If any episodes had TVDb ID's of 0, then warn user to refresh series
        if has_bad_ids:
            log.warning(f'Series "{series_info}" has no TVDb episode ID data - '
                        f'Refresh & Scan in Sonarr')

        return all_episode_info


    def set_episode_ids(self, series_info: SeriesInfo,
            infos: list[EpisodeInfo]) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo
        objects. This sets the TVDb ID for each episode.

        Args:
            series_info: SeriesInfo for the entry.
            infos: List of EpisodeInfo objects to update. Not used.
        """

        # Get all Sonarr-created EpisodeInfo objects
        self.get_all_episodes(series_info)


    def get_all_tags(self) -> list[dict[str, 'str | int']]:
        """
        Get all tags present in Sonarr.

        Returns:
            List of tag dictionary objects with the keys "id" and
            "label" for each tag.
        """

        return self._get(f'{self.url}tag', self.__standard_params)


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