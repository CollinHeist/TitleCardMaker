from datetime import datetime, timedelta
from pathlib import Path
from re import IGNORECASE, compile as re_compile
from typing import Any, Literal, Optional

from fastapi import HTTPException

from modules.Debug import Logger, log
from modules.EpisodeDataSource2 import (
    EpisodeDataSource,
    SearchResult,
    WatchedStatus,
)
from modules.EpisodeInfo2 import EpisodeInfo
from modules.Interface import Interface
from modules.SeriesInfo2 import SeriesInfo
from modules.SyncInterface import SyncInterface
from modules.WebInterface import WebInterface


SeriesType = Literal['anime', 'daily', 'standard']


class SonarrInterface(EpisodeDataSource, WebInterface, SyncInterface, Interface):
    """
    This class describes a Sonarr interface, which is a type of
    EpisodeDataSource, WebInterface, and SyncInterface object which
    connects to an instance of Sonarr.
    """

    INTERFACE_TYPE = 'Sonarr'

    """Use a longer request timeout for Sonarr to handle slow databases"""
    REQUEST_TIMEOUT = 600

    """Series ID's that can be set by Sonarr"""
    SERIES_IDS = ('imdb_id', 'sonarr_id', 'tvdb_id', 'tvrage_id')

    """Series types that can be specified to filter a sync with"""
    VALID_SERIES_TYPES = ('anime', 'daily', 'standard')

    """Episode titles that indicate a placeholder and are to be ignored"""
    __TEMP_IGNORE_REGEX = re_compile(r'^(tba|tbd|episode \d+)$', IGNORECASE)
    __ALWAYS_IGNORE_REGEX = re_compile(r'^(tba|tbd)$', IGNORECASE)

    """Datetime format string for airDateUtc field in Sonarr API requests"""
    __AIRDATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


    def __init__(self,
            url: str,
            api_key: str,
            verify_ssl: bool = True,
            downloaded_only: bool = True,
            *,
            interface_id: int = 0,
            log: Logger = log,
            **_,
        ) -> None:
        """
        Construct a new instance of an interface to Sonarr.

        Args:
            url: The API url communicating with Sonarr.
            api_key: The API key for API requests.
            verify_ssl: Whether to verify SSL requests to Sonarr.
            downloaded_only: Whether to ignore Episode that are not
                downloaded when querying Sonarr for Episode data.
            interface_id: Interface ID of this interface.
            log: Logger for all log messages.

        Raises:
            HTTPException (401): The Sonarr system status cannot be
                pinged.
            HTTPException (422): An invalid URL is provided.
        """

        # Initialize parent WebInterface
        super().__init__('Sonarr', verify_ssl, cache=False, log=log)

        # Get correct URL
        url = url if url.endswith('/') else f'{url}/'
        if url.endswith('/api/v3/'):
            self.url = url
        elif (re_match := self._URL_REGEX.match(url)) is None:
            log.critical(f'Invalid Sonarr URL "{url}"')
            raise HTTPException(
                status_code=422,
                detail=f'Invalid Sonarr URL',
            )
        else:
            self.url = f'{re_match.group(1)}/api/v3/'

        # Base parameters for sending requests to Sonarr
        self.__standard_params = {'apikey': api_key}
        self.interface_id = interface_id
        self.downloaded_only = downloaded_only

        # Query system status to verify connection to Sonarr
        try:
            status = self.get(
                f'{self.url}system/status',
                self.__standard_params,
            )
            if status.get('appName') != 'Sonarr':
                raise HTTPException(
                    status_code=401,
                    detail='Invalid URL / API key',
                )
        except Exception as e:
            log.critical(f'Cannot connect to Sonarr - returned error: "{e}"')
            raise e

        self.activate()


    def get_root_folders(self) -> list[Path]:
        """
        Get all the root folder paths from Sonarr.

        Returns:
            List of root folder paths in Sonarr.
        """

        return [
            Path(folder['path']) for folder in
            self.get(f'{self.url}rootfolder', self.__standard_params)
        ]


    def get_all_series(self,
            required_tags: list[str] = [],
            excluded_tags: list[str] = [],
            monitored_only: bool = False,
            downloaded_only: bool = False,
            required_series_type: Optional[SeriesType] = None,
            excluded_series_type: Optional[SeriesType] = None,
            required_root_folders: list[str] = [],
            *,
            log: Logger = log,
        ) -> list[tuple[SeriesInfo, str]]:
        """
        Get all the series within Sonarr, filtered by the given
        parameters.

         Args:
            required_tags: List of tags to filter return by. Only series
                that have all of the given tags are returned.
            excluded_tags: List of tags to filter return by. Series with
                any of the given tags are excluded from return.
            monitored_only: Whether to filter return to exclude series
                that are unmonitored within Sonarr.
            downloaded_only: Whether to filter return to exclude series
                that do not have any downloaded episodes.
            required_series_type: Type of series that must is required
                to be included.
            excluded_series_type: Type of series to exclude from the
                return.
            required_root_folders: List of root folders to filter the
                returned series by.
            log: Logger for all log messages.

        Returns:
            List of tuples. Tuple contains the SeriesInfo object for the
            series, and the Path to the series' media as reported by
            Sonarr.
        """

        # Construct GET arguments
        all_series = self.get(f'{self.url}series', self.__standard_params)

        # Get filtering tags if indicated
        required_tag_ids, excluded_tag_ids = [], []
        if len(required_tags) > 0 or len(excluded_tags) > 0:
            # Request all Sonarr tags, create mapping of label -> ID
            all_tags = {
                tag['label']: tag['id']
                for tag in self.get(f'{self.url}tag', self.__standard_params)
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
            # Apply filters/exclusions
            if ((monitored_only and not show['monitored'])
                or (downloaded_only
                    and show.get('statistics', {}).get('sizeOnDisk') == 0)
                or (excluded_tags
                    and any(tag in excluded_tag_ids for tag in show['tags']))
                or (required_tags
                    and not all(tag in show['tags'] for tag in required_tag_ids))
                or (required_series_type
                    and show['seriesType'] != required_series_type)
                or (excluded_series_type
                    and show['seriesType'] == excluded_series_type)
                or (required_root_folders
                    and not any(show['rootFolderPath'].startswith(folder)
                                for folder in required_root_folders))
                or show['year'] == 0):
                continue

            # Construct SeriesInfo object for this show
            series_info = SeriesInfo(
                show['title'],
                show['year'],
                imdb_id=show.get('imdbId'),
                sonarr_id=f'{self.interface_id}:{show.get("id")}',
                tvdb_id=show.get('tvdbId'),
                tvrage_id=show.get('tvRageId'),
            )

            # Add to returned list
            series.append((series_info, show['path']))

        return series


    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> None:
        """
        Set the TVDb ID for the given SeriesInfo object.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo to update.
            log: Logger for all log messages.
        """

        # If all possible ID's are defined, exit
        if series_info.has_ids(*self.SERIES_IDS, interface_id=self.interface_id):
            return None

        # Search for Series
        search_results: list[dict] = self.get(
            url=f'{self.url}series/lookup',
            params={'term': series_info.name} | self.__standard_params,
        )

        # No results, nothing to set
        if len(search_results) == 0:
            return None

        # Find matching Series
        for series in search_results:
            try:
                reference_series_info = SeriesInfo(
                    series['title'],
                    series['year'],
                    imdb_id=series.get('imdbId'),
                    tvdb_id=series.get('tvdbId'),
                    tvrage_id=series.get('tvRageId'),
                )
            except TypeError:
                log.warning(f'Error evaluating {series}')
                continue

            # Add Sonarr ID if added to this server
            if (sonarr_id := series.get('id')) is not None:
                reference_series_info.set_sonarr_id(sonarr_id, self.interface_id)

            if series_info == reference_series_info:
                if not reference_series_info.has_id('sonarr', self.interface_id):
                    log.debug(f'Found {series_info} via Sonarr, but not in server')
                series_info.copy_ids(reference_series_info, log=log)
                break

        return None


    def query_series(self,
            query: str,
            *,
            log: Logger = log,
        ) -> list[SearchResult]:
        """
        Search Sonarr for any Series matching the given query.

        Args:
            query: Series name or substring to look up.
            log: Logger for all log messages.

        Returns:
            List of SearchResults for the given query. Results include
            Series not added to this Server. All returned poster URL's
            utilize the Sonarr proxy API endpoint to to (1) obfuscate
            this server's API, and so the local `SonarrAuth` cookie can
            be sent when querying for the poster.
        """

        # Perform query
        search_results = self.get(
            url=f'{self.url}series/lookup',
            params={'term': query} | self.__standard_params,
        )

        def get_poster_proxy(images: list[dict[str, str]]) -> Optional[str]:
            """
            Get the proxy URL of for the poster indicated in the given
            set of images.

            Args:
                images: List of image types/URL's to parse for a poster.

            Returns:
                Proxied URL for the poster, if provided. None if there
                are no valid posters.
            """

            for image in images:
                if image['coverType'] == 'poster':
                    url = image['url'].rsplit('?', maxsplit=1)[0]
                    return (
                        f'/api/proxy/sonarr?url={url}'
                        f'&interface_id={self.interface_id}'
                    )

            return None

        def get_sonarr_id(id_: Optional[int], /) -> Optional[str]:
            return None if id_ is None else f'{self.interface_id}:{id_}'

        return [
            SearchResult(
                name=result['title'],
                year=result['year'],
                ongoing=not result['ended'],
                overview=result.get('overview', 'No overview available'),
                poster=get_poster_proxy(result.get('images', [])),
                imdb_id=result.get('imdbId', None),
                sonarr_id=get_sonarr_id(result.get('id', None)),
                tvdb_id=result.get('tvdbId', None),
                tvrage_id=result.get('tvRageId', None) or None,
            ) for result in search_results if result['year']
        ]


    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> list[tuple[EpisodeInfo, WatchedStatus]]:
        """
        Gets all episode info for the given series. Only episodes that
        have  already aired are returned.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo for the entry.
            log: Logger for all log messages.

        Returns:
            List of tuples of the EpisodeInfo objects and None (as the
            Episode watched status cannot be determined) for the given
            series.
        """

        # If no ID was returned, error and return an empty list
        if not series_info.has_id('sonarr_id', self.interface_id):
            self.set_series_ids(None, series_info, log=log)
            if not series_info.has_id('sonarr_id', self.interface_id):
                log.debug(f'Series "{series_info}" not found in Sonarr')
                return []

        # Construct GET arguments
        url = f'{self.url}episode/'
        params = {
            'seriesId': series_info.sonarr_id[self.interface_id]
        } | self.__standard_params

        # Query Sonarr to get JSON of all episodes for this series
        all_episodes: list[dict] = self.get(url, params)
        all_episode_info: list[tuple[EpisodeInfo, WatchedStatus]] = []

        # Go through each episode and get its season/episode number, and title
        has_bad_ids = False
        for episode in all_episodes:
            # Skip if not downloaded and ignoring non-downloaded Episodes
            if self.downloaded_only and not episode['hasFile']:
                continue

            # Skip permanent placeholder names if title matching is disabled
            if (not series_info.match_titles
                and self.__ALWAYS_IGNORE_REGEX.match(episode['title'])):
                log.trace(f'Temporarily ignoring "{episode["title"]}" of '
                          f'{series_info} - placeholder title')
                continue

            # Get airdate of this episode
            air_datetime = None
            if (ep_airdate := episode.get('airDateUtc')) is not None:
                # If episode hasn't aired, skip
                air_datetime=datetime.strptime(ep_airdate,self.__AIRDATE_FORMAT)
                if not episode['hasFile'] and air_datetime > datetime.now():
                    log.trace(f'Ignoring "{episode["title"]}" of {series_info} '
                              f'- has not aired yet and is not downloaded')
                    continue

                # Skip temporary placeholder names if aired in the last 48 hours
                # and title matching is disabled
                if (not series_info.match_titles
                    and air_datetime + timedelta(days=2) > datetime.now()
                    and self.__TEMP_IGNORE_REGEX.match(episode['title'])):
                    log.trace(f'Temporarily ignoring "{episode["title"]}" of '
                              f'{series_info} - placeholder title')
                    continue

            # If the episode's TVDb ID is 0, then set to None to avoid mismatch
            if episode.get('tvdbId') == 0:
                episode['tvdbId'] = None
                has_bad_ids = True

            # Create EpisodeInfo object for this entry
            all_episode_info.append((
                EpisodeInfo(
                    episode['title'],
                    episode['seasonNumber'],
                    episode['episodeNumber'],
                    episode.get('absoluteEpisodeNumber'),
                    tvdb_id=episode.get('tvdbId'),
                    airdate=air_datetime,
                ),
                WatchedStatus(self.interface_id),
            ))

        # If any episodes had TVDb ID's of 0, then warn user to refresh series
        if has_bad_ids:
            log.warning(f'Series "{series_info}" has no TVDb episode ID data - '
                        f'Refresh & Scan in Sonarr')

        return all_episode_info


    def set_episode_ids(self,
            library_name: Optional[str],
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
            *,
            log: Logger = log,
        ) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo
        objects. This sets the TVDb ID for each episode.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo for the entry.
            episode_infos: List of EpisodeInfo objects to update.
            log: Logger for all log messages.
        """

        # Get all episodes for this series
        new_episode_infos = self.get_all_episodes(
            library_name, series_info, log=log
        )

        # Match to existing info
        for old_episode_info in episode_infos:
            for new_episode_info, _ in new_episode_infos:
                if old_episode_info == new_episode_info:
                    old_episode_info.copy_ids(new_episode_info, log=log)
                    break

        return None


    def get_all_tags(self) -> list[dict[Literal['id', 'label'], Any]]:
        """
        Get all tags present in Sonarr.

        Returns:
            List of tag dictionary objects.
        """

        return self.get(f'{self.url}tag', self.__standard_params)
