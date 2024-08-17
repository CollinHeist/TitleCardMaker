from base64 import b64encode
from logging import Logger
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional, Union, overload

from fastapi import HTTPException

from modules.Debug import log
from modules.EpisodeDataSource2 import (
    EpisodeDataSource, SearchResult, WatchedStatus
)
from modules.EpisodeInfo2 import EpisodeInfo
from modules.Interface import Interface
from modules.MediaServer2 import MediaServer, SourceImage
from modules.SeriesInfo2 import SeriesInfo
from modules.SyncInterface import SyncInterface
from modules.WebInterface import WebInterface

if TYPE_CHECKING:
    from app.models.card import Card
    from app.models.episode import Episode


class JellyfinInterface(MediaServer, EpisodeDataSource, SyncInterface, Interface):
    """
    This class describes an interface to a Jellyfin media server. This
    is a type of EpisodeDataSource (e.g. interface by which Episode data
    can be retrieved), as well as a MediaServer (e.g. a server in which
    cards can be loaded into).
    """

    INTERFACE_TYPE = 'Jellyfin'

    """Series ID's that can be set by Jellyfin"""
    SERIES_IDS = ('imdb_id', 'jellyfin_id', 'tmdb_id', 'tvdb_id')

    """Datetime format string for airdates reported by Jellyfin"""
    AIRDATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f000000Z'


    def __init__(self,
            url: str,
            api_key: str,
            username: Optional[str] = None,
            use_ssl: bool = True,
            filesize_limit: Optional[int] = None,
            *,
            interface_id: int = 0,
            log: Logger = log,
        ) -> None:
        """
        Construct a new instance of an interface to a Jellyfin server.

        Args:
            url: The API url communicating with Jellyfin.
            api_key: The API key for API requests.
            username: Username of the Jellyfin account to get watch
                statuses of.
            use_ssl: Whether to use SSL in all requests.
            filesize_limit: Number of bytes to limit a single file to
                during upload.
            interface_id: ID of this interface.
            log: Logger for all log messages.
        """

        # Intiialize parent classes
        super().__init__(filesize_limit)

        # Store attributes of this Interface
        self._interface_id = interface_id
        self.session = WebInterface('Jellyfin', use_ssl, log=log)
        self.url = url[:-1] if url.endswith('/') else url
        self.__params = {'api_key': api_key}
        self.username = username

        # Authenticate with server
        try:
            response = self.session.get(
                f'{self.url}/System/Info',
                params=self.__params
            )

            if not set(response).issuperset({'ServerName', 'Version', 'Id'}):
                raise ConnectionError(f'Unable to authenticate with server')
        except Exception as exc:
            log.critical(f'Cannot connect to Jellyfin - returned error')
            log.exception('Bad Jellyfin connection')
            raise HTTPException(
                status_code=400,
                detail=f'Cannot connect to Jellyfin - {exc}',
            ) from exc

        # Get user ID if indicated
        if not username:
            self.user_id = None
        elif (user_id := self._get_user_id(username)) is not None:
            self.user_id = user_id
        else:
            log.critical(f'Cannot identify ID of user "{username}"')
            self.user_id = None

        # # Get the ID's of all libraries within this server
        self.libraries = self._map_libraries()
        self.activate()


    def _get_user_id(self, username: str) -> Optional[str]:
        """
        Get the User ID associated with the given username.

        Args:
            username: Username to query for.

        Returns:
            User ID hexstring associated with the given username. None
            if the  username was not found.
        """

        # Query for list of all users on this server
        response = self.session.get(
            f'{self.url}/Users',
            params=self.__params,
        )

        # Go through returned list of users, returning on username match
        for user in response:
            if user.get('Name') == username:
                return user.get('Id')

        return None


    def _map_libraries(self) -> dict[str, str]:
        """
        Map the libraries on this interface's server.

        Returns:
            Dictionary whose keys are the names of the libraries, and
            whose values are that library's ID.
        """

        # Get all libraries in this server
        libraries = self.session.get(
            f'{self.url}/Items',
            params={
                'recursive': True,
                'includeItemTypes': 'CollectionFolder'
            } | self.__params,
        )

        return {
            library['Name']: library['Id'] for library in libraries['Items']
        }


    @overload
    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            raw_obj: Literal[False] = False,
            log: Logger = log,
        ) -> Optional[str]:
        ...
    @overload
    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            raw_obj: Literal[True] = False,
            log: Logger = log,
        ) -> Optional[SeriesInfo]:
        ...

    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            raw_obj: bool = False,
            log: Logger = log,
        ) -> Optional[Union[str, SeriesInfo]]:
        """
        Get the Jellyfin ID (or entire SeriesInfo) for the given series.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series being evaluated.
            raw_obj: Whether to return the raw object rather than just
                the dictionary.
            log: Logger for all log messages.

        Returns:
            None if the series is not found. The Jellyfin ID of the
            series if `raw_obj` is False, otherwise the SeriesInfo of
            the found series.
        """

        # If Series has Jellyfin ID, and not returning raw object, evaluate
        if (not raw_obj
            and series_info.has_id('jellyfin', self._interface_id,library_name)):
            # Query for this item within Jellyfin
            id_ = series_info.jellyfin_id[self._interface_id, library_name]
            resp = self.session.get(
                f'{self.url}/Items/{id_}?userId={self.user_id}',
                params=self.__params,
            )

            # If one item was returned, ID is still valid
            if isinstance(resp, dict) and resp.get('Id') == id_:
                return id_

            # No item found, ID must be invalid - reset and re-query
            log.warning(f'Jellyfin ID ({id_}) has been dynamically re-assigned.'
                        f' Querying for new one..')
            del series_info.jellyfin_id[self._interface_id, library_name]

        # Get ID of this library
        if (library_id := self.libraries.get(library_name)) is None:
            log.error(f'Library "{library_name}" not found in Jellyfin')
            return None

        # Base params for all queries
        params = {
            'recursive': True,
            'includeItemTypes': 'Series',
            # isSeries search filter DOES NOT work
            'searchTerm': series_info.name,
            'fields': 'ProviderIds',
            'enableImages': False,
            'parentId': library_id,
        } | self.__params

        def _query_series(year: int) -> Optional[str]:
            """Look up the series in the specified year"""

            response = self.session.get(
                f'{self.url}/Items',
                params=params | ({'years': str(year)} if year else {}),
            )

            # If no responses, return
            if response['TotalRecordCount'] == 0:
                return None

            # Parse all results into SeriesInfo objects
            results = [
                (result, SeriesInfo.from_jellyfin_info(
                    result, self._interface_id, library_name
                ))
                for result in response['Items']
            ]

            # Attempt to "smart" match by ID first
            for result, result_series in results:
                if series_info == result_series:
                    return result_series if raw_obj else result['Id']
            # Attempt to match by name alone
            for result, result_series in results:
                if series_info.matches(result['Name']):
                    return result_series if raw_obj else result['Id']

            # No match
            return None

        # Look for series in this year, then surrounding years, then no year
        for year in (
            series_info.year, series_info.year-1, series_info.year+1, None
        ):
            if (jellyfin_id := _query_series(year)) is not None:
                return jellyfin_id

        log.warning(f'Series not found in Jellyfin {series_info!r}')
        return None


    def __get_season_id(self,
            series_id: str,
            season_number: int,
        ) -> Optional[str]:
        """
        Get the Jellyfin ID of the given season.

        Args:
            series_id: Jellyfin ID of the associated series.
            season_number: Season number whose ID is being queried.

        Returns:
            The Jellyfin ID of the season, if found. None otherwise.
        """

        response = self.session.get(
            f'{self.url}/Items',
            params={
                'recursive': True,
                'includeItemTypes': 'Season',
                'parentId': series_id,
                'startIndex': season_number-1,
                'limit': 1,
            } | self.__params,
        )

        if 'Items' not in response or not response['Items']:
            return None

        return response['Items'][0]['Id']


    def __get_episode_id(self,
            library_name: str,
            series_jellyfin_id: str,
            episode_info: EpisodeInfo,
        ) -> Optional[str]:
        """
        Get the Jellyfin ID for the given episode.

        Args:
            library_name: Name of the library containing the series.
            episode_info: The episode being evaluated.

        Returns:
            Jellyfin ID of the episode, if found. None otherwise.
        """

        # If episode has a Jellyfin ID, return that
        if episode_info.has_id('jellyfin', self._interface_id, library_name):
            return episode_info.jellyfin_id[self._interface_id, library_name]

        # Query for this episode
        response = self.session.get(
            f'{self.url}/Items',
            params={
                'recursive': True,
                'includeItemTypes': 'Episode',
                'ParentId': series_jellyfin_id,
                'parentIndexNumber': episode_info.season_number,
                'startIndex': episode_info.episode_number - 1,
                'limit': 1,
            } | self.__params,
        )

        if 'Items' not in response or not response['Items']:
            return None

        return response['Items'][0]['Id']


    @overload
    def __find_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: Literal[None],
        ) -> Union[tuple[Literal[None], Literal[None]],
                   tuple[str, Literal[None]]]:
        ...
    @overload
    def __find_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
        ) -> Union[tuple[Literal[None], Literal[None]],
                   tuple[str, str]]:
        ...

    def __find_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: Optional[EpisodeInfo],
        ) -> tuple[Optional[str], Optional[str]]:
        """
        Get the Jellyfin ID's for the given series and episode.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series being evaluated.
            episode_info: The episode being evaluated.

        Returns:
            Tuple of the series and episode Jellyfin ID's. The series ID
            will be None if the series cannot be found; the epispde ID
            will be None if an episode was not provided or the episode
            cannot be found.
        """

        # Find series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            return None, None

        # If no episode to find, return
        if episode_info is None:
            return series_id, None

        return series_id, self.__get_episode_id(library_name, series_id, episode_info)


    def get_usernames(self) -> list[str]:
        """
        Get all the usernames for this interface's Jellyfin server.

        Returns:
            List of usernames.
        """

        return [
            user.get('Name') for user in
            self.session.get(f'{self.url}/Users', params=self.__params)
        ]


    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> None:
        """
        Set the series ID's for the given SeriesInfo object.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to set the ID of.
            log: Logger for all log messages.
        """

        # Find series
        result = self.__get_series_id(
            library_name, series_info, raw_obj=True, log=log
        )
        if result is None:
            log.warning(f'Series "{series_info}" was not found under library '
                        f'"{library_name}" in Jellyfin')
            return None

        del series_info.jellyfin_id[self._interface_id, library_name]
        series_info.copy_ids(result, log=log)
        return None


    def set_episode_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
            *,
            log: Logger = log,
        ) -> None:
        """
        Set the Episode ID's for the given EpisodeInfo objects.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to get the episodes of.
            infos: List of EpisodeInfo objects to set the ID's of.
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


    def query_series(self,
            query: str,
            *,
            log: Logger = log,
        ) -> list[SearchResult]:
        """
        Search Jellyfin for any Series matching the given query.

        Args:
            query: Series name or substring to look up.
            log: Logger for all log messages.

        Returns:
            List of SearchResults for the given query. Results are from
            any library.
        """

        # Perform query
        search_results = self.session.get(
            f'{self.url}/Items',
            params=self.__params | {
                'recursive': True,
                'includeItemTypes': 'Series',
                'searchTerm': query,
                'fields': 'ParentId,ProviderIds,Overview',
                'enableImages': False,
            },
        )

        return [
            SearchResult(
                name=result['Name'],
                year=result['ProductionYear'],
                ongoing=result.get('Status') == 'Continuing',
                overview=result.get('Overview', 'No overview available'),
                poster=f'{self.url}/Items/{result["Id"]}/Images/Primary?quality=75',
                imdb_id=result.get('ProviderIds', {}).get('Imdb'),
                tmdb_id=result.get('ProviderIds', {}).get('Tmdb'),
                tvdb_id=result.get('ProviderIds', {}).get('Tvdb'),
                tvrage_id=result.get('ProviderIds', {}).get('TvRage'),
            )
            for result in search_results['Items']
            if 'PremiereDate' in result
        ]


    def get_all_series(self,
            required_libraries: list[str] = [],
            excluded_libraries: list[str] = [],
            required_tags: list[str] = [],
            excluded_tags: list[str] = [],
            *,
            log: Logger = log,
        ) -> list[tuple[SeriesInfo, str]]:
        """
        Get all series within Jellyfin, as filtered by the given
        libraries and tags.

        Args:
            required_libraries: Library names that a series must be
                present in to be returned.
            excluded_libraries: Library names that a series cannot be
                present in to be returned.
            required_tags: Tags that a series must have all of in order
                to be returned.
            excluded_tags: Tags that a series cannot have any of in
                order to be returned.
            log: Logger for all log messages.

        Returns:
            List of tuples of the filtered series info and their
            corresponding library names.
        """

        # Temporarily override request timeout to 240s (4 min)
        self.REQUEST_TIMEOUT = 240

        # Base params for all queries
        params = {
            'recursive': True,
            'includeItemTypes': 'Series',
            'fields': 'ProviderIds,Tags',
            'enableImages': False,
        } | self.__params

        # Also filter by tags if any were provided
        if len(required_tags) > 0:
            params |= {'tags': '|'.join(required_tags)}

        # Get all series library at a time
        all_series = []
        for library, library_id in self.libraries.items():
            # Filter by library
            if (required_libraries and library not in required_libraries
                or excluded_libraries and library in excluded_libraries):
                continue

            response = self.session.get(
                f'{self.url}/Items',
                params=params | {'ParentId': library_id}
            )
            for series in response['Items']:
                # Skip series without airdate/year
                if series.get('PremiereDate', None) is None:
                    log.debug(f'Series {series["Name"]} has no premiere date')
                    continue

                # Skip series if an excluded tag is present
                if any(tag in series.get('Tags') for tag in excluded_tags):
                    continue

                all_series.append((
                    SeriesInfo.from_jellyfin_info(
                        series, self._interface_id, library
                    ),
                    library
                ))

        # Reset request timeout
        self.REQUEST_TIMEOUT = 30

        return all_series


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
            library_name: Name of the library containing the series.
            series_info: Series to get the episodes of.
            log: Logger for all log messages.

        Returns:
            List of tuples of the EpisodeInfo objects and the episode
            watched statuses for this series.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            log.warning(f'Series {series_info} not found in Jellyfin')
            return []

        # Get all episodes for this series
        response = self.session.get(
            f'{self.url}/Shows/{series_id}/Episodes',
            params={
                'UserId': self.user_id,
                'Fields': 'ProviderIds,PremiereDate'
            } | self.__params
        )

        # Invalid return, exit
        if not isinstance(response, dict) or 'Items' not in response:
            log.warning('Jellyfin returned bad Episode data')
            log.trace(response)
            return []

        # Parse each returned episode into EpisodeInfo object
        all_episodes = []
        for episode in response['Items']:
            # Skip episodes without required a title, season, or episode number
            if (episode.get('Name') is None
                or episode.get('IndexNumber') is None
                or episode.get('ParentIndexNumber') is None):
                log.debug(f'Series {series_info} is missing required episode data')
                log.trace(episode)
                continue

            all_episodes.append((
                EpisodeInfo.from_jellyfin_info(
                    episode, self._interface_id, library_name,
                ),
                WatchedStatus(
                    self._interface_id,
                    library_name,
                    episode.get('UserData', {}).get('Played'),
                )
            ))

        return all_episodes


    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfo,
            episodes: list['Episode'],
            *,
            log: Logger = log,
        ) -> bool:
        """
        Modify the Episodes' watched attribute according to the watched
        status of the corresponding episodes within Jellyfin.

        Args:
            library_name: The name of the library containing the series.
            series_info: The series to update.
            episodes: List of Episode objects to update.
            log: Logger for all log messages.

        Returns:
            Whether any Episode's watched statuses were modified.
        """

        # If no episodes, exit
        if not episodes:
            return False

        # Find this series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            return False

        # Get data for each Jellyfin episode
        jellyfin_episodes = self.get_all_episodes(
            library_name, series_info, log=log,
        )

        # Update watched statuses of all Episodes
        changed = False
        for episode in episodes:
            episode_info = episode.as_episode_info
            for jellyfin_episode, watched_status in jellyfin_episodes:
                if episode_info == jellyfin_episode:
                    changed |= episode.add_watched_status(watched_status)
                    break

        return changed


    def load_title_cards(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_and_cards: list[tuple['Episode', 'Card']],
            *,
            log: Logger = log,
        ) -> list[tuple['Episode', 'Card']]:
        """
        Load the title cards for the given Series and Episodes.

        Args:
            library_name: Name of the library containing the series.
            series_info: SeriesInfo whose cards are being loaded.
            episode_and_cards: List of tuple of Episode and their
                corresponding Card objects to load.
            log: Logger for all log messages.

        Returns:
            List of tuples of the Episode and the corresponding Card
            that was loaded.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            return []

        # Load each episode and card
        loaded = []
        for episode, card in episode_and_cards:
            # Find episode, skip if not found
            episode_id = self.__get_episode_id(
                library_name, series_id, episode.as_episode_info
            )
            if episode_id is None:
                continue

            # Shrink image if necessary, skip if cannot be compressed
            if (image := self.compress_image(card.card_file, log=log)) is None:
                continue

            # Submit POST request for image upload on Base64 encoded image
            card_base64 = b64encode(image.read_bytes())
            try:
                self.session.session.post(
                    url=f'{self.url}/Items/{episode_id}/Images/Primary', # Change Primary to Backdrop
                    headers={'Content-Type': 'image/jpeg'},
                    params=self.__params,
                    data=card_base64,
                )
                loaded.append((episode, card))
            except Exception:
                log.exception(f'Unable to upload {card.resolve()} to '
                              f'{series_info}')
                continue

        # Log load operations to user
        if loaded:
            log.info(f'Loaded {len(loaded)} cards for "{series_info}"')

        return loaded


    def load_season_posters(self,
            library_name: str,
            series_info: SeriesInfo,
            posters: dict[int, Union[str, Path]],
            *,
            log: Logger = log,
        ) -> None:
        """
        Load the given season posters into Jellyfin.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            posters: Dictionary of season numbers to poster URLs or
                files to upload.
            log: Logger for all log messages.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            return None

        # Load each episode and card
        for season_number, image in posters.items():
            if (sid := self.__get_season_id(series_id, season_number)) is None:
                continue

            # Shrink image if necessary, skip if cannot be compressed
            if (isinstance(image, Path)
                and (image := self.compress_image(image, log=log)) is None):
                continue

            # Download or read image
            if isinstance(image, str):
                image_bytes = WebInterface.download_image_raw(image, log=log)
                if image_bytes is None:
                    continue
            else:
                image_bytes = image.read_bytes()
            image_base64 = b64encode(image_bytes)

            # Submit POST request for image upload on Base64 encoded image
            try:
                self.session.session.post(
                    url=f'{self.url}/Items/{sid}/Images/Primary',
                    headers={'Content-Type': 'image/jpeg'},
                    params=self.__params,
                    data=image_base64,
                )
                log.debug(f'{series_info} loaded poster into season '
                          f'{season_number}')
            except Exception:
                log.exception(f'Unable to upload {image} to {series_info}')
                continue

        return None


    def load_series_poster(self,
            library_name: str,
            series_info: SeriesInfo,
            image: Union[str, Path],
            *,
            log: Logger = log
        ) -> None:
        """
        Load the given series poster into Jellyfin.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            image: URL or Path to the file to upload.
            log: Logger for all log messages.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            return None

        # Shrink image if necessary, skip if cannot be compressed
        if (isinstance(image, Path)
            and (image := self.compress_image(image, log=log)) is None):
            return None

        # Download or read image
        if isinstance(image, str):
            image_bytes = WebInterface.download_image_raw(image, log=log)
            if image_bytes is None:
                return None
        else:
            image_bytes = image.read_bytes()
        image_base64 = b64encode(image_bytes)

        # Submit POST request for image upload on Base64 encoded image
        try:
            self.session.session.post(
                url=f'{self.url}/Items/{series_id}/Images/Primary',
                headers={'Content-Type': 'image/jpeg'},
                params=self.__params,
                data=image_base64,
            )
            log.debug(f'{series_info} loaded poster')
        except Exception:
            log.exception(f'Unable to upload {image} to {series_info}')

        return None


    def load_series_background(self,
            library_name: str,
            series_info: SeriesInfo,
            image: Union[str, Path],
            *,
            log: Logger = log
        ) -> None:
        """
        Load the given series background image into Jellyfin.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            image: URL or Path to the file to upload.
            log: Logger for all log messages.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            return None

        # Shrink image if necessary, skip if cannot be compressed
        if (isinstance(image, Path)
            and (image := self.compress_image(image, log=log)) is None):
            return None

        # Download or read image
        if isinstance(image, str):
            image_bytes = WebInterface.download_image_raw(image, log=log)
            if image_bytes is None:
                return None
        else:
            image_bytes = image.read_bytes()
        image_base64 = b64encode(image_bytes)

        # Submit POST request for image upload on Base64 encoded image
        try:
            self.session.session.post(
                url=f'{self.url}/Items/{series_id}/Images/Backdrop',
                headers={'Content-Type': 'image/jpeg'},
                params=self.__params,
                data=image_base64,
            )
            log.debug(f'{series_info} loaded backdrop')
        except Exception:
            log.exception(f'Unable to upload {image} to {series_info}')

        return None


    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            *,
            log: Logger = log,
        ) -> Optional[bytes]:
        """
        Get the source image for the given episode within Jellyfin.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series whose episode is being queried.
            episode_info: The episode to get the source image of.
            log: Logger for all log messages.

        Returns:
            Bytes of the source image for the given Episode. None if the
            episode does not exist in Jellyfin, or no valid image was
            returned.
        """

        # Find series and episode
        series_id, episode_id = self.__find_ids(
            library_name, series_info, episode_info
        )

        # Exit if either series or episode was not found
        if series_id is None:
            log.warning(f'Series {series_info!r} not found in Jellyfin')
            return None
        if episode_id is None:
            log.warning(f'{series_info} Episode {episode_info!r} not found in '
                        f'Jellyfin')
            return None

        # Get the source image for this episode
        response = self.session.session.get(
            f'{self.url}/Items/{episode_id}/Images/Primary',
            params={'Quality': 100} | self.__params,
        ).content

        # Check if valid content was returned
        if b'does not have an image of type' in response:
            log.warning(f'Episode {episode_info} has no source images')
            return None

        return response


    def get_series_poster(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> SourceImage:
        """
        Get the poster for the given Series.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series to get the poster of.
            log: Logger for all log messages.

        Returns:
            URL to the poster for the given series. None if the library,
            series, or thumbnail cannot be found.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            return None

        # Get the poster image for this Series
        response = self.session.session.get(
            f'{self.url}/Items/{series_id}/Images/Primary',
            params={'Quality': 100} | self.__params,
        ).content

        # Check if valid content was returned
        if b'does not have an image of type' in response:
            log.warning(f'Series {series_info} has no poster')
            return None

        return response


    def get_series_logo(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> SourceImage:
        """
        Get the logo for the given Series within Jellyfin.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series to get the logo of.
            log: Logger for all log messages.

        Returns:
            Bytes of the logo for given series. None if the series does
            not exist in Jellyfin, or no valid image was returned.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            return None

        # Get the source image for this episode
        response = self.session.session.get(
            f'{self.url}/Items/{series_id}/Images/Logo',
            params={'Quality': 100} | self.__params,
        ).content

        # Check if valid content was returned
        if b'does not have an image of type' in response:
            log.warning(f'Series {series_info} has no logo')
            return None

        return response


    def get_libraries(self) -> list[str]:
        """
        Get the names of all libraries within this server.

        Returns:
            List of library names.
        """

        return list(self.libraries)
