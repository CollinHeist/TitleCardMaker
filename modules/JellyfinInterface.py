from base64 import b64encode
from datetime import datetime
from sys import exit as sys_exit
from typing import Optional, Union

from modules import global_objects
from modules.Debug import log
from modules.Episode import Episode
from modules.EpisodeDataSource import EpisodeDataSource
from modules.EpisodeInfo import EpisodeInfo
from modules.SeasonPosterSet import SeasonPosterSet
from modules.MediaServer import MediaServer
from modules.SeriesInfo import SeriesInfo
from modules.StyleSet import StyleSet
from modules.SyncInterface import SyncInterface
from modules.WebInterface import WebInterface


SourceImage = Union[bytes, None]


class JellyfinInterface(EpisodeDataSource, MediaServer, SyncInterface):
    """
    This class describes an interface to a Jellyfin media server. This
    is a type of EpisodeDataSource (e.g. interface by which Episode data
    can be retrieved), as well as a MediaServer (e.g. a server in which
    cards can be loaded into).
    """

    """Default no filesize limit for all uploaded assets"""
    DEFAULT_FILESIZE_LIMIT = None

    """Filepath to the database of each episode's loaded card characteristics"""
    LOADED_DB = 'loaded_jellyfin.json'

    """Series ID's that can be set by Jellyfin"""
    SERIES_IDS = ('imdb_id', 'jellyfin_id', 'tmdb_id', 'tvdb_id')

    """Datetime format string for airdates reported by Jellyfin"""
    AIRDATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f000000Z'


    def __init__(self, url: str, api_key: str,
            username: Optional[str] = None,
            verify_ssl: bool = True,
            filesize_limit: Optional[int] = None) -> None:
        """
        Construct a new instance of an interface to a Jellyfin server.

        Args:
            url: The API url communicating with Jellyfin.
            api_key: The API key for API requests.
            username: Username of the Jellyfin account to get watch
                statuses of.
            verify_ssl: Whether to verify SSL requests.
            filesize_limit: Number of bytes to limit a single file to
                during upload.

        Raises:
            SystemExit: Invalid URL/API key provided.
        """

        # Intiialize parent classes
        super().__init__(filesize_limit)

        # Store attributes of this Interface
        self.session = WebInterface('Jellyfin', verify_ssl)
        self.info_set = global_objects.info_set
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
            sys_exit(1)

        # Get user ID if indicated
        if (user_id := self._get_user_id(username)) is None:
            log.critical(f'Cannot identify ID of user "{username}"')
            sys_exit(1)
        else:
            self.user_id = user_id

        # Get the ID's of all libraries within this server
        self.libraries = self._map_libraries()


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


    def _map_libraries(self) -> dict[str, int]:
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
            library['Name']: library['Id']
            for library in libraries['Items']
            if library.get('CollectionType', None) == 'tvshows'
        }


    def set_series_ids(self, library_name: str, series_info: SeriesInfo) ->None:
        """
        Set the series ID's for the given SeriesInfo object.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to set the ID of.
        """

        # If all possible ID's are defined
        if series_info.has_ids(*self.SERIES_IDS):
            return None

        # If library not mapped, error and exit
        if (library_id := self.libraries.get(library_name)) is None:
            log.error(f'Library "{library_name}" not found in Jellyfin')
            return None

        # Base params for all requests
        params = {
            'recursive': True,
            'years': series_info.year,
            'includeItemTypes': 'Series',
            'searchTerm': series_info.name,
            'fields': 'ProviderIds',
            'parentId': library_id,
        } | self.__params

        # Look for this series in this library
        response = self.session.get(f'{self.url}/Items', params=params)

        # If no responses, skip
        if response['TotalRecordCount'] > 0:
            # Go through all items and match name and type, setting database IDs
            for result in response['Items']:
                if (result['Type'] == 'Series'
                    and series_info.matches(result['Name'])):
                    ids = result.get('ProviderIds', {})
                    # No MediaInfoSet, set directly
                    if self.info_set is None:
                        series_info.set_jellyfin_id(result['Id'])
                        series_info.set_imdb_id(ids.get('Imdb', None))
                        series_info.set_imdb_id(ids.get('Tmdb', None))
                        series_info.set_imdb_id(ids.get('Tvdb', None))
                    # Set using global MediaInfoSet
                    else:
                        self.info_set.set_jellyfin_id(series_info, result['Id'])
                        self.info_set.set_imdb_id(
                            series_info, ids.get('Imdb', None)
                        )
                        self.info_set.set_imdb_id(
                            series_info, ids.get('Tmdb', None)
                        )
                        self.info_set.set_imdb_id(
                            series_info, ids.get('Tvdb', None)
                        )

                    return None

        # Not found on server
        log.warning(f'Series "{series_info}" was not found under library '
                    f'"{library_name}" in Jellyfin')
        return None


    def set_episode_ids(self,
            library_name: Optional[str],
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
            *,
            inplace: bool = False,
        ) -> None:
        """
        Set the Episode ID's for the given EpisodeInfo objects.

        Args:
            library_name: Name of the library the series is under.
            series_info: SeriesInfo for the entry.
            episode_infos: List of EpisodeInfo objects to update.
            inplace: Unused argument.
        """

        self.get_all_episodes(library_name, series_info, episode_infos)


    def get_library_paths(self,
            filter_libraries: list[str] = [],
        ) -> dict[str, list[str]]:
        """
        Get all libraries and their associated base directories.

        Args:
            filter_libraries: List of library names to filter the
                return.

        Returns:
            Dictionary whose keys are the library names, and whose
            values are the list of paths to that library's base
            directories.
        """

        # Get all library folders
        libraries = self.session.get(
            f'{self.url}/Library/VirtualFolders',
            params=self.__params
        )

        # Inner function on whether to include this library in the return
        def include_library(library_name) -> bool:
            if len(filter_libraries) == 0:
                return True
            return library_name in filter_libraries

        return {
            lib['Name']: list(lib['Locations'])
            for lib in libraries
            if (lib.get('CollectionType', None) == 'tvshows'
                and include_library(lib['Name']))
        }


    def get_all_series(self,
            filter_libraries: list[str] = [],
            required_tags: list[str] = [],
        ) -> list[tuple[SeriesInfo, str, str]]:
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
            series, the  path (string) it is located, and its
            corresponding library name.
        """

        # Temporarily override request timeout to 240s (4 min)
        self.REQUEST_TIMEOUT = 240

        # Base params for all queries
        params = {
            'recursive': True,
            'includeItemTypes': 'Series',
            'fields': 'ProviderIds,Path',
        } | self.__params

        # Also filter by tags if any were provided
        if len(required_tags) > 0:
            params |= {'tags': '|'.join(required_tags)}

        # Get all series library at a time
        all_series = []
        for library, library_id in self.libraries.items():
            # If filtering by library, skip if not specified
            if filter_libraries and library not in filter_libraries:
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

                series_info = SeriesInfo(
                    series['Name'],
                    datetime.strptime(series['PremiereDate'],
                                      self.AIRDATE_FORMAT).year,
                    jellyfin_id=series['Id'],
                    imdb_id=series['ProviderIds'].get('Imdb'),
                    tmdb_id=series['ProviderIds'].get('Tmdb'),
                    tvdb_id=series['ProviderIds'].get('Tvdb'),
                    tvrage_id=series['ProviderIds'].get('TvRage'),
                )
                all_series.append((series_info, series['Path'], library))

        # Reset request timeout
        self.REQUEST_TIMEOUT = 30

        return all_series


    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_infos: Optional[list[EpisodeInfo]] = None,
        ) -> list[EpisodeInfo]:
        """
        Gets all episode info for the given series. Only episodes that
        have already aired are returned.

        Args:
            library_name: Unused argument.
            series_info: Series to get the episodes of.
            episode_infos: Optional EpisodeInfos to set the ID's of.

        Returns:
            List of EpisodeInfo objects for this series.
        """

        # If series has no Jellyfin ID, cannot query episodes
        if not series_info.has_id('jellyfin_id'):
            log.warning(f'Series not found in Jellyfin {series_info!r}')
            return []

        # Get all episodes for this series
        response = self.session.get(
            f'{self.url}/Shows/{series_info.jellyfin_id}/Episodes',
            params={'Fields': 'ProviderIds'} | self.__params
        )

        if not isinstance(response, dict) or 'Items' not in response:
            log.error(f'Jellyfin returned bad Episode data for {series_info}')
            log.debug(f'{response=}')
            return []

        # Parse each returned episode into EpisodeInfo object
        all_episodes = []
        for episode in response['Items']:
            # Skip Episodes without episode or season numbers
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

            # Create new EpisodeInfo via global MediaInfoSet object
            if episode_infos is None:
                episode_info = self.info_set.get_episode_info(
                    series_info,
                    episode['Name'],
                    episode['ParentIndexNumber'],
                    episode['IndexNumber'],
                    jellyfin_id=episode.get('Id'),
                    imdb_id=episode['ProviderIds'].get('Imdb'),
                    tmdb_id=episode['ProviderIds'].get('Tmdb'),
                    tvdb_id=episode['ProviderIds'].get('Tvdb'),
                    tvrage_id=episode['ProviderIds'].get('TvRage'),
                    airdate=airdate,
                    title_match=True,
                    queried_jellyfin=True,
                )

                # Add to list
                if episode_info is not None:
                    all_episodes.append(episode_info)
            # If updating existing infos, match by index
            else:
                tmp_ei = (episode['ParentIndexNumber'], episode['IndexNumber'])
                for episode_info in episode_infos:
                    # Index match, update ID's
                    if episode_info == tmp_ei:
                        ep_ids = episode['ProviderIds']
                        episode_info.set_jellyfin_id(episode.get('Id'))
                        episode_info.set_imdb_id(ep_ids.get('Imdb'))
                        episode_info.set_tmdb_id(ep_ids.get('Tmdb'))
                        episode_info.set_tvdb_id(ep_ids.get('Tvdb'))
                        episode_info.set_tvrage_id(ep_ids.get('TvRage'))
                        all_episodes.append(episode_info)
                        break

        return all_episodes


    def has_series(self, library_name: str, series_info: SeriesInfo) -> bool:
        """
        Determine whether the given series is present within Jellyfin.

        Args:
            series_info: The series being evaluated.

        Returns:
            True if the series is present within Jellyfin. False
            otherwise.
        """

        return series_info.has_id('jellyfin_id')


    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_map: dict[str, Episode],
            style_set: StyleSet,
        ) -> None:
        """
        Modify the Episode objects according to the watched status of
        the corresponding episodes within Jellyfin, and the spoil status
        of the object. If a loaded card needs its spoiler status
        changed, the card is deleted and the loaded map is updated to
        reload that card.

        Args:
            library_name: The name of the library containing the series.
            series_info: The series to update.
            episode_map: Dictionary of episode keys to Episode objects
                to modify.
            style_set: StyleSet object to update the style of the
                Episodes with.
        """

        # If no episodes, or series has no ID, exit
        if len(episode_map) == 0 or not series_info.has_id('jellyfin_id'):
            return None

        # Get current loaded characteristics of the series
        loaded_series = self.loaded_db.search(
            self._get_condition(library_name, series_info)
        )

        # Query for all episodes of this series
        response = self.session.get(
            f'{self.url}/Shows/{series_info.jellyfin_id}/Episodes',
            params={'UserId': self.user_id} | self.__params
        )

        # Go through each episode in Jellyfin, update Episode status/card
        for jellyfin_episode in response['Items']:
            # Skip if this episode isn't in TCM
            season_number = jellyfin_episode['ParentIndexNumber']
            ep_key = f'{season_number}-{jellyfin_episode["IndexNumber"]}'
            if not (episode := episode_map.get(ep_key)):
                continue

            # Set Episode watch/spoil statuses
            episode.update_statuses(
                jellyfin_episode['UserData']['Played'],
                style_set
            )

            # Get characteristics of this Episode's loaded card
            details = self._get_loaded_episode(loaded_series, episode)
            loaded = details is not None
            spoiler_status = details['spoiler'] if loaded else None

            # Delete and reset card if current spoiler type doesn't match
            delete_and_reset = ((episode.spoil_type != spoiler_status)
                                and bool(spoiler_status))

            # Delete card, reset size in loaded map to force reload
            if delete_and_reset and loaded:
                episode.delete_card(reason='updating style')
                self.loaded_db.update(
                    {'filesize': 0},
                    self._get_condition(library_name, series_info, episode)
                )

        return None


    def set_title_cards(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_map: dict[str, Episode],
        ) -> None:
        """
        Set the title cards for the given series. This only updates
        episodes that have title cards, and those episodes whose card
        filesizes are different than what has been set previously.

        Args:
            library_name: The name of the library containing the series.
            series_info: The series to update.
            episode_map: Dictionary of episode keys to Episode objects
                to update the cards of.
        """

        # If series has no ID, cannot set title cards
        if not series_info.has_id('jellyfin_id'):
            log.debug(f'Not loading "{series_info}" - not found in Jellyfin')
            return None

        # Filter loaded cards
        filtered_episodes = self._filter_loaded_cards(
            library_name, series_info, episode_map
        )

        # If no episodes remain, exit
        if len(filtered_episodes) == 0:
            return None

        # Go through each remaining episode and load the card
        loaded_count = 0
        for episode in filtered_episodes.values():
            # Skip episodes without ID's (e.g. not in Jellyfin)
            if (jellyfin_id := episode.episode_info.jellyfin_id) is None:
                log.debug(f'Skipping {episode.episode_info!r} - not found in '
                          f'Jellyfin')
                continue

            # Shrink image if necessary, skip if cannot be compressed
            if (card := self.compress_image(episode.destination)) is None:
                continue

            # Image content must be Base64-encoded
            card_base64 = b64encode(card.read_bytes())

            # Submit POST request for image upload
            try:
                self.session.session.post(
                    url=f'{self.url}/Items/{jellyfin_id}/Images/Primary',
                    headers={'Content-Type': 'image/jpeg'},
                    params=self.__params,
                    data=card_base64,
                )
                loaded_count += 1
                log.debug(f'Loaded "{series_info}" Episode '
                          f'{episode.episode_info} into Jellyfin')
            except Exception as e:
                log.exception(f'Unable to upload {card.resolve()} to '
                              f'"{series_info}"', e)
                continue

            # Update loaded database for this episode
            self.loaded_db.upsert({
                'library': library_name,
                'series': series_info.full_name,
                'season': episode.episode_info.season_number,
                'episode': episode.episode_info.episode_number,
                'filesize': episode.destination.stat().st_size,
                'spoiler': episode.spoil_type,
            }, self._get_condition(library_name, series_info, episode))

        # Log load operations to user
        if loaded_count > 0:
            log.info(f'Loaded {loaded_count} cards for "{series_info}"')

        return None


    def set_season_posters(self,
            library_name: str,
            series_info: SeriesInfo,
            season_poster_set: SeasonPosterSet,
        ) -> None:
        """
        Set the season posters from the given set within Plex.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            season_poster_set: SeasonPosterSet with season posters to
                set.
        """

        return None


    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
        ) -> SourceImage:
        """
        Get the source image given episode within Jellyfin.

        Args:
            library_name: Unused argument
            series_info: The series to get the source image of.
            episode_info: The episode to get the source image of.

        Returns:
            Bytes of the source image for the given Episode. None if the
            episode does not exist in Jellyfin, or no valid image was
            returned.
        """

        # If series has no Jellyfin ID, cannot query episodes
        if not episode_info.has_id('jellyfin_id'):
            log.warning(f'Episode {episode_info} not found in Jellyfin')
            return None

        # Get the source image for this episode
        response = self.session.session.get(
            f'{self.url}/Items/{episode_info.jellyfin_id}/Images/Primary',
            params={'Quality': 100} | self.__params,
        ).content

        # Check if valid content was returned
        if b'does not have an image of type' in response:
            log.warning(f'Episode {episode_info} has no source images')
            return None

        return response


    def get_libraries(self) -> list[str]:
        """
        Get the names of all libraries within this server.

        Returns:
            List of library names.
        """

        return list(self.libraries)
