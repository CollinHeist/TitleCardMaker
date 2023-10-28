from base64 import b64encode
from datetime import datetime
from logging import Logger
from typing import Optional, Union

from fastapi import HTTPException

from modules.Debug import log
from modules.EpisodeDataSource2 import EpisodeDataSource, SearchResult
from modules.EpisodeInfo2 import EpisodeInfo
from modules.Interface import Interface
from modules.MediaServer2 import MediaServer, SourceImage
from modules.SeriesInfo2 import SeriesInfo
from modules.SyncInterface import SyncInterface
from modules.WebInterface import WebInterface


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
            use_magick_prefix: bool = False,
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
            use_magick_prefix: Whether to use 'magick' command prefix.
            interface_id: ID of this interface.
            log: Logger for all log messages.
        """

        # Intiialize parent classes
        super().__init__(filesize_limit, use_magick_prefix)

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
            log.critical(f'Cannot connect to Jellyfin - returned error {exc}')
            log.exception(f'Bad Jellyfin connection', exc)
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


    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            raw_obj: bool = False,
            log: Logger = log,
        ) -> Optional[Union[str, dict]]:
        """
        Get the Jellyfin ID for the given series.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series being evaluated.
            raw_obj: Whether to return the raw object rather than just
                the dictionary.
            log: Logger for all log messages.

        Returns:
            None if the series is not found. The Jellyfin ID of the
            series if `raw_obj` is False, otherwise the series
            dictionary itself.
        """

        # If Series has Jellyfin ID, and not returning raw object, return
        if (not raw_obj
            and series_info.has_id('jellyfin', self._interface_id,library_name)):
            return series_info.jellyfin_id[self._interface_id, library_name]

        # Get ID of this library
        if (library_id := self.libraries.get(library_name, None)) is None:
            log.error(f'Library "{library_name}" not found in Jellyfin')
            return None

        # Base params for all queries
        params = {
            'recursive': True,
            'includeItemTypes': 'Series',
            'searchTerm': series_info.name,
            'fields': 'ProviderIds',
            'enableImages': False,
            'parentId': library_id,
        } | self.__params

        # Inner function to look for the Series in a specific year
        def _query_series(year: int) -> Optional[str]:
            # Look for this series in this library
            response = self.session.get(
                f'{self.url}/Items',
                params=(params | {'years': f'{year}'}),
            )

            # If no responses, return
            if response['TotalRecordCount'] == 0:
                return None

            # Go through all items and match name and type, setting database IDs
            for result in response['Items']:
                if series_info.matches(result['Name']):
                    return result if raw_obj else result['Id']

            return None

        # Look for series in this year, then surrounding years
        for year in (series_info.year, series_info.year-1, series_info.year+1):
            if (jellyfin_id := _query_series(year)) is not None:
                return jellyfin_id

        return None


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
            return episode_info.jellyfin_id

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

        if len(response['Items']) == 0:
            return None

        return response['Items'][0]['Id']


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

        # If all possible ID's are defined
        if series_info.has_ids(*self.SERIES_IDS, interface_id=self._interface_id,
                               library_name=library_name):
            return None

        # Find series
        series = self.__get_series_id(
            library_name, series_info, raw_obj=True, log=log
        )
        if series is None:
            log.warning(f'Series "{series_info}" was not found under library '
                        f'"{library_name}" in Jellyfin')
            return None

        # Assign ID's
        series_info.set_jellyfin_id(
            series['Id'], self._interface_id, library_name
        )
        if (imdb_id := series['ProviderIds'].get('Imdb')):
            series_info.set_imdb_id(imdb_id)
        if (tmdb_id := series['ProviderIds'].get('Tmdb')):
            series_info.set_tmdb_id(tmdb_id)
        if (tvdb_id := series['ProviderIds'].get('Tvdb')):
            series_info.set_tvdb_id(tvdb_id)

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
                    # For each ID of this new EpisodeInfo, update old if upgrade
                    old_episode_info.copy_ids(new_episode_info, log=log)
                    break


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
                'fields': 'ProviderIds,Overview',
                'enableImages': False,
            },
        )

        return [
            SearchResult(
                name=result['Name'],
                year=result['ProductionYear'], # get_year(result['PremiereDate'])
                ongoing=result['Status'] == 'Continuing',
                overview=result.get('Overview', 'No overview available'),
                poster=f'{self.url}/Items/{result["Id"]}/Images/Primary?quality=75',
                imdb_id=result.get('ProviderIds', {}).get('Imdb'),
                # jellyfin_id=f'{self._interface_id}:{}' result['Id'],
                tmdb_id=result.get('ProviderIds', {}).get('Tmdb'),
                tvdb_id=result.get('ProviderIds', {}).get('Tvdb'),
                tvrage_id=result.get('ProviderIds', {}).get('TvRage'),
            ) for result in search_results['Items']
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
            filter_libraries: Optional list of library names to filter
                returned list by. If provided, only series that are
                within a given library are returned.
            required_tags: Optional list of tags to filter return by. If
                provided, only series with all the given tags are
                returned.

        Returns:
            List of tuples whose elements are the SeriesInfo of the
            series, and its corresponding library name.
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

                jellyfin_id = f'{self._interface_id}:{library}:{series["Id"]}'
                series_info = SeriesInfo(
                    series['Name'],
                    datetime.strptime(series['PremiereDate'],
                                      self.AIRDATE_FORMAT).year,
                    imdb_id=series.get('ProviderIds', {}).get('Imdb'),
                    jellyfin_id=jellyfin_id,
                    tmdb_id=series.get('ProviderIds', {}).get('Tmdb'),
                    tvdb_id=series.get('ProviderIds', {}).get('Tvdb'),
                    tvrage_id=series.get('ProviderIds', {}).get('TvRage'),
                )
                all_series.append((series_info, library))

        # Reset request timeout
        self.REQUEST_TIMEOUT = 30

        return all_series


    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> list[tuple[EpisodeInfo, Optional[bool]]]:
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
            log.warning(f'Series {series_info!r} not found in Jellyfin')
            return []

        # Get all episodes for this series
        response = self.session.get(
            f'{self.url}/Shows/{series_id}/Episodes',
            params={
                'UserId': self.user_id, 'Fields': 'ProviderIds'
            } | self.__params
        )

        # Parse each returned episode into EpisodeInfo object
        all_episodes = []
        for episode in response['Items']:
            # Skip episodes without episode or season numbers
            if (episode.get('IndexNumber', None) is None
                or episode.get('ParentIndexNumber', None) is None):
                log.debug(f'Series {series_info} episode is missing index data')
                continue

            # Parse airdate for this episode
            airdate = None
            if 'PremiereDate' in episode:
                try:
                    airdate = datetime.strptime(
                        episode['PremiereDate'], self.AIRDATE_FORMAT
                    )
                except Exception as e:
                    log.exception(f'Cannot parse airdate', e)
                    log.debug(f'Episode data: {episode}')

            jellfin_id = f'{self._interface_id}:{library_name}:{episode["Id"]}'
            episode_info = EpisodeInfo(
                episode['Name'],
                episode['ParentIndexNumber'],
                episode['IndexNumber'],
                imdb_id=episode['ProviderIds'].get('Imdb'),
                jellyfin_id=jellfin_id,
                tmdb_id=episode['ProviderIds'].get('Tmdb'),
                tvdb_id=episode['ProviderIds'].get('Tvdb'),
                tvrage_id=episode['ProviderIds'].get('TvRage'),
                airdate=airdate,
            )

            # Add to list
            if episode_info is not None:
                all_episodes.append(
                    (episode_info, episode.get('UserData', {}).get('Played'))
                )

        return all_episodes


    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfo,
            episodes: list['Episode'], # type: ignore
            *,
            log: Logger = log,
        ) -> None:
        """
        Modify the Episodes' watched attribute according to the watched
        status of the corresponding episodes within Jellyfin.

        Args:
            library_name: The name of the library containing the series.
            series_info: The series to update.
            episodes: List of Episode objects to update.
            log: Logger for all log messages.
        """

        # If no episodes, exit
        if len(episodes) == 0:
            return None

        # Find this series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            log.warning(f'Series not found in Jellyfin {series_info!r}')
            return None

        # Query for all episodes of this series
        response = self.session.get(
            f'{self.url}/Shows/{series_id}/Episodes',
            params={'UserId': self.user_id} | self.__params
        )

        # Go through each episode in Jellyfin, update Episode status/card
        for jellyfin_episode in response['Items']:
            # Skip episodes without episode or season numbers
            if (jellyfin_episode.get('IndexNumber', None) is None
                or jellyfin_episode.get('ParentIndexNumber', None) is None):
                continue

            for episode in episodes:
                if (jellyfin_episode['ParentIndexNumber']==episode.season_number
                    and jellyfin_episode["IndexNumber"]==episode.episode_number):
                    if (jellyfin_episode.get('UserData', {}).get('Played')
                        is not None):
                        episode.watched = jellyfin_episode['UserData']['Played']
                        break

        return None


    def load_title_cards(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_and_cards: list[tuple['Episode', 'Card']], # type: ignore
            *,
            log: Logger = log,
        ) -> list[tuple['Episode', 'Card']]: # type: ignore
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
            log.warning(f'Series not found in Jellyfin {series_info!r}')
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
                    url=f'{self.url}/Items/{episode_id}/Images/Primary',
                    headers={'Content-Type': 'image/jpeg'},
                    params=self.__params,
                    data=card_base64,
                )
                loaded.append((episode, card))
            except Exception as e:
                log.exception(f'Unable to upload {card.resolve()} to '
                              f'{series_info}', e)
                continue

        # Log load operations to user
        if loaded:
            log.info(f'Loaded {len(loaded)} cards for "{series_info}"')

        return loaded


    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            *,
            log: Logger = log,
        ) -> SourceImage:
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
            log.warning(f'Series not found in Jellyfin {series_info!r}')
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
            log.warning(f'Series not found in Jellyfin {series_info!r}')
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
