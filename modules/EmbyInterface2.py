from base64 import b64encode
from datetime import datetime
from logging import Logger
from typing import Optional, Union

from fastapi import HTTPException
from modules.DatabaseInfoContainer import InterfaceID

from modules.Debug import log
from modules.EpisodeDataSource2 import EpisodeDataSource, SearchResult
from modules.EpisodeInfo2 import EpisodeInfo
from modules.Interface import Interface
from modules.MediaServer2 import MediaServer, SourceImage
from modules.SeriesInfo2 import SeriesInfo
from modules.SyncInterface import SyncInterface
from modules.WebInterface import WebInterface


class EmbyInterface(MediaServer, EpisodeDataSource, SyncInterface, Interface):
    """
    This class describes an interface to an Emby media server. This is a
    type of EpisodeDataSource (e.g. interface by which Episode data can
    be retrieved), as well as a MediaServer (e.g. a server in which
    cards can be loaded into).
    """

    INTERFACE_TYPE = 'Emby'

    """Default no filesize limit for all uploaded assets"""
    DEFAULT_FILESIZE_LIMIT = None

    """Filepath to the database of each episode's loaded card characteristics"""
    LOADED_DB = 'loaded_emby.json'

    """Series ID's that can be set by Emby"""
    SERIES_IDS = ('emby_id', 'imdb_id', 'tmdb_id', 'tvdb_id')

    """Datetime format string for airdates reported by Emby"""
    AIRDATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f000000Z'

    """Range of years to query series by"""
    YEARS = ','.join(map(str, range(1960, datetime.now().year)))


    def __init__(self,
            url: str,
            api_key: str,
            username: str,
            use_ssl: bool = True,
            filesize_limit: Optional[int] = None,
            use_magick_prefix: bool = False,
            *,
            interface_id: int = 0,
            log: Logger = log,
        ) -> None:
        """
        Construct a new instance of an interface to an Emby server.

        Args:
            url: The API url communicating with Emby.
            api_key: The API key for API requests.
            username: Username of the Emby account to get watch statuses
                of.
            use_ssl: Whether to use SSL in all requests.
            filesize_limit: Number of bytes to limit a single file to
                during upload.
            use_magick_prefix: Whether to use 'magick' command prefix.
            interface_id: ID of this interface.
            log: Logger for all log messages.

        Raises:
            SystemExit: Invalid URL/API key provided.
        """

        # Intiialize parent classes
        super().__init__(filesize_limit, use_magick_prefix)

        # Store attributes of this Interface
        self._interface_id = interface_id
        self.session = WebInterface('Emby', use_ssl, log=log)
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
        except Exception as e:
            log.critical(f'Cannot connect to Emby - returned error {e}')
            log.exception(f'Bad Emby connection', e)
            raise HTTPException(
                status_code=400,
                detail=f'Cannot connect to Emby - {e}',
            ) from e

        # Get user ID
        self.user_id = None
        if self.username is not None:
            if (user_id := self._get_user_id(username)) is None:
                log.critical(f'Cannot identify ID of user "{username}"')
                raise HTTPException(
                    status_code=400,
                    detail=f'Cannot identify ID of user "{username}"',
                )
            self.user_id = user_id

        # Get the ID's of all libraries within this server
        self.libraries: dict[str, tuple[int]] = self._map_libraries()
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
            f'{self.url}/Users/Query',
            params=self.__params,
        )

        # Go through returned list of users, returning when username matches
        for user in response.get('Items'):
            if user.get('Name') == username:
                return user.get('Id')

        return None


    def _map_libraries(self) -> dict[str, tuple[int]]:
        """
        Map the libraries on this interface's Emby server.

        Returns:
            Dictionary whose keys are the names of the libraries, and
            whose values are tuples of the folder ID's for those
            libraries.
        """

        # Get all library folders
        libraries = self.session.get(
            f'{self.url}/Library/SelectableMediaFolders',
            params=self.__params
        )

        # Parse each library name into tuples of parent ID's
        return {
            lib['Name']:tuple(int(folder['Id']) for folder in lib['SubFolders'])
            for lib in libraries
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
            log: Logger for all log messages.

        Returns:
            None if the series is not found. The Jellyfin ID of the
            series if raw_obj is False, otherwise the series dictionary
            itself.
        """

        if series_info.has_id('emby_id', interface_id=self._interface_id):
            return series_info.emby_id[self._interface_id]

        # Get ID of this library
        if (library_ids := self.libraries.get(library_name, None)) is None:
            log.error(f'Library "{library_name}" not found in Emby')
            return None

        # Generate provider ID query string
        ids = []
        if series_info.has_id('imdb_id'):
            ids += [f'imdb.{series_info.imdb_id}']
        if series_info.has_id('tmdb_id'):
            ids += [f'tmdb.{series_info.tmdb_id}']
        if series_info.has_id('tvdb_id'):
            ids += [f'tvdb.{series_info.tvdb_id}']
        provider_id_str = ','.join(ids)

        # Base params for all requests
        params = {
            'Recursive': True,
            'Years': series_info.year,
            'IncludeItemTypes': 'series',
            'SearchTerm': series_info.name,
            'Fields': 'ProviderIds',
        } | self.__params \
          |({'AnyProviderIdEquals': provider_id_str} if provider_id_str else {})

        # Look for this series in each library subfolder
        for parent_id in library_ids:
            response = self.session.get(
                f'{self.url}/Items',
                params=params | {'ParentId': parent_id}
            )

            # If no responses, skip
            if response['TotalRecordCount'] == 0:
                continue

            # Go through all items and match name and type, setting database IDs
            for result in response['Items']:
                if (result['Type'] == 'Series'
                    and series_info.matches(result['Name'])):
                    return result if raw_obj else result['Id']

        # Not found on server
        return None


    def get_usernames(self) -> list[str]:
        """
        Get all the usernames for this interface's Emby server.

        Returns:
            List of usernames.
        """

        return [
            user['Name'] for user in
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
        if series_info.has_ids(*self.SERIES_IDS):
            return None

        # Find series
        series = self.__get_series_id(
            library_name, series_info, raw_obj=True, log=log
        )
        if series is None:
            log.warning(f'Series "{series_info}" was not found under library '
                        f'"{library_name}" in Emby')
            return None

        # Set database ID's
        series_info.set_emby_id(series['Id'], self._interface_id)
        if (imdb_id := series['ProviderIds'].get('IMDB')):
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
            library_name: Name of the library the series is under.
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
            for new_episode_info in new_episode_infos:
                if old_episode_info == new_episode_info:
                    old_episode_info.copy_ids(new_episode_info)


    def query_series(self,
            query: str,
            *,
            log: Logger = log,
        ) -> list[SearchResult]:
        """
        Search Emby for any Series matching the given query.

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
                'Recursive': True,
                'IncludeItemTypes': 'Series',
                'SearchTerm': query,
                'Fields': 'ProviderIds,Overview,ProductionYear,Status',
                'EnableImages': True,
                'ImageTypes': 'Primary',
            },
        )

        return [
            SearchResult(
                name=result['Name'],
                year=result['ProductionYear'], # get_year(result['PremiereDate'])
                ongoing=result['Status'] == 'Continuing',
                overview=result.get('Overview', 'No overview available'),
                poster=f'{self.url}/Items/{result["Id"]}/Images/Primary?quality=75',
                imdb_id=result.get('ProviderIds', {}).get('IMDB'),
                jellyfin_id=f'{self._interface_id}:{result["Id"]}',
                tmdb_id=result.get('ProviderIds', {}).get('Tmdb'),
                tvdb_id=result.get('ProviderIds', {}).get('Tvdb'),
                tvrage_id=result.get('ProviderIds', {}).get('TvRage'),
            ) for result in search_results['Items']
            if 'ProductionYear' in result
        ]


    def get_library_paths(self,
            filter_libraries: list[str] = [],
        ) -> dict[str, list[str]]:
        """
        Get all libraries and their associated base directories.

        Args:
            filer_libraries: List of library names to filter the return.

        Returns:
            Dictionary whose keys are the library names, and whose
            values are the list of paths to that library's base
            directories.
        """

        # Get all library folders
        libraries = self.session.get(
            f'{self.url}/Library/SelectableMediaFolders',
            params=self.__params
        )

        # Inner function on whether to include this library in the return
        def include_library(emby_library) -> bool:
            if len(filter_libraries) == 0:
                return True
            return emby_library in filter_libraries

        # Parse each library name into tuples of parent ID's
        return {
            lib['Name']: list(folder['Path'] for folder in lib['SubFolders'])
            for lib in libraries
            if include_library(lib['Name'])
        }


    def get_all_series(self,
            required_libraries: list[str] = [],
            excluded_libraries: list[str] = [],
            required_tags: list[str] = [],
            excluded_tags: list[str] = [],
            *,
            log: Logger = log,
        ) -> list[tuple[SeriesInfo, str]]:
        """
        Get all series within Emby, as filtered by the given libraries.

        Args:
            filter_libraries: Optional list of library names to filter
                returned list by. If provided, only series that are
                within a given library are returned.
            excluded_libraries: Optional list of library names to filter
                returned list by. If provided, only series that are not
                within a given library are returned.
            required_tags: Optional list of tags to filter return by. If
                provided, only series with all the given tags are
                returned.
            excluded_tags: Optional list of tags to filter return by. If
                provided, series with any of the given tags are not
                returned.
            log: Logger for all log messages.

        Returns:
            List of tuples whose elements are the SeriesInfo and its
            corresponding library name.
        """

        # Temporarily override request timeout to 240s (4 min)
        self.REQUEST_TIMEOUT = 240

        # Base params for all queries
        params = {
            'Recursive': True,
            'IncludeItemTypes': 'series',
            'Fields': 'ProviderIds',
        } | self.__params

        # Get excluded series ID's if excluding by tags
        if len(excluded_tags) > 0:
            # Get all items (series) for any of the excluded tags
            response = self.session.get(
                f'{self.url}/Items',
                params=params | {'Tags': '|'.join(excluded_tags)},
            )
            params |= {
                'ExcludeItemIds': ','.join(
                    map(str, [series['Id'] for series in response['Items']])
                )
            }

        # Also filter by tags if any were provided
        if len(required_tags) > 0:
            params |= {'Tags': '|'.join(required_tags)}

        # Go through each library in this server
        all_series = []
        for library, library_ids in self.libraries.items():
            # Filter by library
            if ((required_libraries and library not in required_libraries)
                or (excluded_libraries and library in excluded_libraries)):
                continue

            # Go through every subfolder (the parent ID) in this library
            for parent_id in library_ids:
                # Get all items (series) in this subfolder
                response = self.session.get(
                    f'{self.url}/Items',
                    params=params | {'ParentId': parent_id, 'Years': self.YEARS}
                )

                # Process each returned Series
                for series in response['Items']:
                    try:
                        ids = series.get('ProviderIds', {})
                        series_info = SeriesInfo(
                            series['Name'], None,
                            emby_id=f'{self._interface_id}:{series["Id"]}',
                            imdb_id=ids.get('IMDB'),
                            tmdb_id=ids.get('Tmdb'),
                            tvdb_id=ids.get('Tvdb'),
                        )
                        all_series.append((series_info, library))
                    except ValueError:
                        log.error(f'Series {series["Name"]} is missing a year')
                        continue

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
        have already aired are returned.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to get the episodes of.
            log: Logger for all log messages.

        Returns:
            List of EpisodeInfo objects for this series.
        """

        # Find series
        emby_id = self.__get_series_id(library_name, series_info, log=log)
        if emby_id is None:
            log.warning(f'Series not found in Emby {series_info!r}')
            return []

        # Get all episodes for this series
        response = self.session.get(
            f'{self.url}/Shows/{emby_id}/Episodes',
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
            try:
                airdate = datetime.strptime(
                    episode['PremiereDate'], self.AIRDATE_FORMAT
                )
            except Exception as e:
                log.exception(f'Cannot parse airdate', e)
                log.debug(f'Episode data: {episode}')

            episode_info = EpisodeInfo(
                episode['Name'],
                episode['ParentIndexNumber'],
                episode['IndexNumber'],
                emby_id=f'{self._interface_id}:{episode.get("Id")}',
                imdb_id=episode['ProviderIds'].get('Imdb'),
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
        status of the corresponding episodes within Emby.

        Args:
            library_name: The name of the library containing the series.
            series_info: The series to update.
            episodes: List of Episode objects to update.
            log: Logger for all log messages.
        """

        # If no episodes, exit
        if len(episodes) == 0:
            return None

        # Find series, exit if not found
        emby_id = self.__get_series_id(library_name, series_info, log=log)
        if emby_id is None:
            return None

        # Query for all episodes of this series
        response = self.session.get(
            f'{self.url}/Shows/{emby_id}/Episodes',
            params={'UserId': self.user_id} | self.__params
        )

        # Go through each episode in Emby, update Episode status/card
        for emby_episode in response['Items']:
            for episode in episodes:
                if (emby_episode['ParentIndexNumber'] == episode.season_number
                    and emby_episode["IndexNumber"] == episode.episode_number):
                    episode.watched = emby_episode['UserData']['Played']
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
        """

        # If series has no Emby ID, or no episodes, exit
        if len(episode_and_cards) == 0:
            return None

        # Load each episode and card
        loaded = []
        for episode, card in episode_and_cards:
            # Skip episodes without Emby ID's (e.g. not in Emby)
            if (emby_id := episode.emby_id) is None:
                continue
            interface_id = InterfaceID(episode.emby_id, type_=str)
            if (emby_id := interface_id[self._interface_id]) is None:
                continue

            # Shrink image if necessary, skip if cannot be compressed
            if (image := self.compress_image(card.card_file, log=log)) is None:
                continue

            # Submit POST request for image upload on Base64 encoded image
            card_base64 = b64encode(image.read_bytes())
            try:
                self.session.session.post(
                    url=f'{self.url}/Items/{emby_id}/Images/Primary',
                    headers={'Content-Type': 'image/jpeg'},
                    params=self.__params,
                    data=card_base64,
                )
                loaded.append((episode, card))
            except Exception as e:
                log.exception(f'Unable to upload {image.resolve()} to '
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
        Get the source image for the given episode within Emby.

        Args:
            library_name: Name of the library the series is under.
            series_info: The series to get the source image of.
            episode_info: The episode to get the source image of.
            log: Logger for all log messages.

        Returns:
            Bytes of the source image for the given Episode. None if the
            episode does not exist in Emby, or no valid image was
            returned.
        """

        # Find series, exit if not found
        emby_id = self.__get_series_id(library_name, series_info, log=log)
        if emby_id is None:
            log.warning(f'Episode {episode_info} not found in Emby')
            return None

        # Get the source image for this episode
        response = self.session.session.get(
            f'{self.url}/Items/{emby_id}/Images/Primary',
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
            series_info: The series to get the poster of.
            log: Logger for all log messages.

        Returns:
            URL to the poster for the given series. None if the library,
            series, or thumbnail cannot be found.
        """

        # Find series, exit if not found
        emby_id = self.__get_series_id(library_name, series_info, log=log)
        if emby_id is None:
            log.warning(f'Series not found in Emby {series_info!r}')
            return None

        # Get the poster image for this Series
        response = self.session.session.get(
            f'{self.url}/Items/{emby_id}/Images/Primary',
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
        Get the logo for the given Series within Emby.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series to get the logo of.
            log: Logger for all log messages.

        Returns:
            Bytes of the logo for given series. None if the series does
            not exist in Emby, or no valid image was returned.
        """

        # Find series, exit if not found
        emby_id = self.__get_series_id(library_name, series_info, log=log)
        if emby_id is None:
            log.warning(f'Series not found in Emby {series_info!r}')
            return None

        # Get the source image for this episode
        response = self.session.session.get(
            f'{self.url}/Items/{emby_id}/Images/Logo',
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
