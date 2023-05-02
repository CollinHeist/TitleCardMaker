from base64 import b64encode
from datetime import datetime
from typing import Optional, Union

from modules.Debug import log
from modules.EpisodeDataSource import EpisodeDataSource
from modules.EpisodeInfo2 import EpisodeInfo
import modules.global_objects as global_objects
from modules.MediaServer import MediaServer
from modules.SeriesInfo import SeriesInfo
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


    def __init__(self,
            url: str,
            api_key: str,
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
        """

        # Intiialize parent classes
        super().__init__(filesize_limit)

        # Store attributes of this Interface
        self.session = WebInterface('Jellyfin', verify_ssl)
        self.url = url[:-1] if url.endswith('/') else url
        self.__params = {'api_key': api_key}
        self.username = username

        # Authenticate with server
        try:
            response = self.session._get(
                f'{self.url}/System/Info',
                params=self.__params
            )

            if not set(response).issuperset({'ServerName', 'Version', 'Id'}):
                raise Exception(f'Unable to authenticate with server')
        except Exception as e:
            log.critical(f'Cannot connect to Jellyfin - returned error {e}')
            log.exception(f'Bad Jellyfin connection', e)

        # Get user ID if indicated
        if (username is not None
            and (user_id := self._get_user_id(username)) is None):
            log.critical(f'Cannot identify ID of user "{username}"')
        else:
            self.user_id = user_id

        # Get the ID's of all libraries within this server
        self.libraries = self._map_libraries()


    def _get_user_id(self, username: str) -> 'str | None':
        """
        Get the User ID associated with the given username.

        Args:
            username: Username to query for.

        Returns:
            User ID hexstring associated with the given username. None
            if the  username was not found.
        """

        # Query for list of all users on this server
        response = self.session._get(
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
        libraries = self.session._get(
            f'{self.url}/Items',
            params={
                'recursive': True,
                'includeItemTypes': 'CollectionFolder'
            } | self.__params,
        )

        return {
            library['Name']: library['Id']
            for library in libraries['Items']
            if library['CollectionType'] == 'tvshows'
        }


    def get_usernames(self) -> list[str]:
        """
        Get all the usernames for this interface's Jellyfin server.

        Returns:
            List of usernames.
        """

        return [
            user.get('Name') for user in
            self.session._get(f'{self.url}/Users', params=self.__params)
        ]


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
        response = self.session._get(f'{self.url}/Items', params=params)

        # If no responses, skip
        if response['TotalRecordCount'] > 0:
            # Go through all items and match name and type, setting database IDs
            for result in response['Items']:
                if (result['Type'] == 'Series'
                    and series_info.matches(result['Name'])):
                    series_info.set_jellyfin_id(result['Id'])
                    if (imdb_id := result['ProviderIds'].get('Imdb')):
                        series_info.set_imdb_id(imdb_id)
                    if (tmdb_id := result['ProviderIds'].get('Tmdb')):
                        series_info.set_tmdb_id(int(tmdb_id))
                    if (tvdb_id := result['ProviderIds'].get('Tvdb')):
                        series_info.set_tvdb_id(int(tvdb_id))
                        
                    return None

        # Not found on server
        log.warning(f'Series "{series_info}" was not found under library '
                    f'"{library_name}" in Jellyfin')
        return None 


    def set_episode_ids(self, series_info: SeriesInfo) -> None:
        """
        Set the Episode ID's for the given EpisodeInfo objects.

        Args:
            series_info: Series to get the episodes of.
            infos: List of EpisodeInfo objects to set the ID's of.
        """

        # Get all episodes for this series
        new_episode_infos = self.get_all_episodes(series_info)

        # Match to existing info
        for old_episode_info in episode_infos:
            for new_episode_info in new_episode_infos:
                if old_episode_info == new_episode_info:
                    # For each ID of this new EpisodeInfo, update old if upgrade
                    for id_type, id_ in new_episode_info.ids.items():
                        if (getattr(old_episode_info, id_type) is None
                            and id_ is not None):
                            setattr(old_episode_info, id_type, id_)
                            log.debug(f'Set {old_episode_info}.{id_type}={id_}')
                    break


    def get_library_paths(self, filter_libraries: list[str]=[]
            ) -> dict[str, list[str]]:
        """
        Get all libraries and their associated base directories.

        Args:
            filter_libraries: List of library names to filter the return.

        Returns:
            Dictionary whose keys are the library names, and whose values are
            the list of paths to that library's base directories.
        """

        # Get all library folders 
        libraries = self.session._get(
            f'{self.url}/Library/VirtualFolders',
            params=self.__params
        )

        # Inner function on whether to include this library in the return
        def include_library(library_name) -> bool:
            if len(filter_libraries) == 0: return True
            return library_name in filter_libraries

        return {
            lib['Name']: [location for location in lib['Locations']]
            for lib in libraries
            if (lib['CollectionType'] == 'tvshows'
                and include_library(lib['Name']))
        }


    def get_all_series(self,
            filter_libraries: list[str] = [],
            required_tags: list[str] = []
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

            response = self.session._get(
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
                )
                all_series.append((series_info, series['Path'], library))

        # Reset request timeout
        self.REQUEST_TIMEOUT = 30

        return all_series


    def get_all_episodes(self, series_info: SeriesInfo) -> list[EpisodeInfo]:
        """
        Gets all episode info for the given series. Only episodes that
        have  already aired are returned.

        Args:
            series_info: Series to get the episodes of.

        Returns:
            List of EpisodeInfo objects for this series.
        """

        # If series has no Jellyfin ID, cannot query episodes
        if not series_info.has_id('jellyfin_id'):
            log.warning(f'Series not found in Jellyfin {series_info!r}')
            return []

        # Get all episodes for this series
        response = self.session._get(
            f'{self.url}/Shows/{series_info.jellyfin_id}/Episodes',
            params={'Fields': 'ProviderIds'} | self.__params
        )

        # Parse each returned episode into EpisodeInfo object
        all_episodes = []
        for episode in response['Items']:
            # Parse airdate for this episode
            airdate = None
            if 'PremiereDate' in episode:
                try:
                    airdate = datetime.strptime(episode['PremiereDate'],
                                                self.AIRDATE_FORMAT)
                except Exception as e:
                    log.exception(f'Cannot parse airdate', e)
                    log.debug(f'Episode data: {episode}')

            episode_info = EpisodeInfo(
                episode['Name'],
                episode['ParentIndexNumber'],
                episode['IndexNumber'],
                jellyfin_id=episode.get('Id'),
                imdb_id=episode['ProviderIds'].get('Imdb'),
                tmdb_id=episode['ProviderIds'].get('Tmdb'),
                tvdb_id=episode['ProviderIds'].get('Tvdb'),
                tvrage_id=episode['ProviderIds'].get('TvRage'),
                airdate=airdate,
            )

            # Add to list
            if episode_info is not None:
                all_episodes.append(episode_info)

        return all_episodes


    def has_series(self, series_info: SeriesInfo) -> bool:
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
            episodes: list['Episode']) -> None:
        """
        Modify the Episodes' watched attribute according to the watched
        status of the corresponding episodes within Jellyfin.

        Args:
            library_name: The name of the library containing the series.
            series_info: The series to update.
            episodes: List of Episode objects to update.
        """

        # If no episodes, or series has no ID, exit
        if len(episodes) == 0 or not series_info.has_id('jellyfin_id'):
            return None

        # Query for all episodes of this series
        response = self.session._get(
            f'{self.url}/Shows/{series_info.jellyfin_id}/Episodes',
            params={'UserId': self.user_id} | self.__params
        )

        # Go through each episode in Jellyfin, update Episode status/card
        for jellyfin_episode in response['Items']:
            for episode in episodes:
                if (jellyfin_episode['ParentIndexNumber'] == episode.season_number
                    and jellyfin_episode["IndexNumber"] == episode.episode_number):
                    episode.watched = jellyfin_episode['UserData']['Played']
                    break

        return None


    def load_title_cards(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_and_cards: list[tuple['Episode', 'Card']],
            ) -> list[tuple['Episode', 'Card']]:
        """
        Load the title cards for the given Series and Episodes.

        Args:
            library_name: Name of the library containing the series.
            series_info: SeriesInfo whose cards are being loaded.
            episode_and_cards: List of tuple of Episode and their
                corresponding Card objects to load.
        """

        # If series has no Jellyfin ID, or no episodes, exit
        if not series_info.has_id('jellyfin_id') or len(episode_and_cards) == 0:
            return None

        # Load each episode and card
        loaded = []
        for episode, card in episode_and_cards.values():
            # Skip episodes without ID's (e.g. not in Jellyfin)
            if (jellyfin_id := episode.jellyfin_id) is None:
                continue

            # Shrink image if necessary, skip if cannot be compressed
            if (image := self.compress_image(card.card_file)) is None:
                continue

            # Submit POST request for image upload on Base64 encoded image
            card_base64 = b64encode(image.read_bytes())
            try:
                self.session.session.post(
                    url=f'{self.url}/Items/{jellyfin_id}/Images/Primary',
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


    def load_season_posters(self,
            library_name: str,
            series_info: SeriesInfo,
            season_poster_set: 'SeasonPosterSet') -> None:
        """
        Set the season posters from the given set within Plex.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            season_poster_set: SeasonPosterSet with season posters to
                set.
        """

        pass


    def get_source_image(self, episode_info: EpisodeInfo) -> SourceImage:
        """
        Get the source image for the given episode within Jellyfin.

        Args:
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


    def get_series_logo(self, series_info: SeriesInfo) -> SourceImage:
        """
        Get the logo for the given Series within Jellyfin.

        Args:
            series_info: The Series to get the logo of.

        Returns:
            Bytes of the logo for given Series. None if the Series does
            not exist in Jellyfin, or no valid image was returned.
        """

        if not series_info.has_id('jellyfin_id'):
            log.warning(f'Series not found in Jellyfin {series_info!r}')
            return None

        # Get the source image for this episode
        response = self.session.session.get(
            f'{self.url}/Items/{episode_info.jellyfin_id}/Images/Logo',
            params={'Quality': 100} | self.__params,
        ).content

        # Check if valid content was returned
        if b'does not have an image of type' in response:
            log.warning(f'Episode {episode_info} has no logo')
            return None 

        return response


    def get_libraries(self) -> list[str]:
        """
        Get the names of all libraries within this server.

        Returns:
            List of library names.
        """

        return list(self.libraries)