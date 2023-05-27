from collections import namedtuple
from datetime import datetime, timedelta
from pathlib import Path
from re import IGNORECASE, compile as re_compile
from typing import Optional

from fastapi import HTTPException
from plexapi.exceptions import PlexApiException
from plexapi.server import PlexServer, NotFound, Unauthorized
from requests.exceptions import ReadTimeout, ConnectionError
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential
from tinydb import where
from tqdm import tqdm

from modules.Debug import log, TQDM_KWARGS
from modules.EpisodeDataSource import EpisodeDataSource
from modules.EpisodeInfo2 import EpisodeInfo
from modules.ImageMaker import ImageMaker
from modules.MediaServer2 import MediaServer
from modules.PersistentDatabase import PersistentDatabase
from modules.SeriesInfo import SeriesInfo
from modules.SyncInterface import SyncInterface
from modules.WebInterface import WebInterface

EpisodeDetails = namedtuple(
    'EpisodeDetails',
    ('series_info', 'episode_info', 'watched_status')
)

class PlexInterface(EpisodeDataSource, MediaServer, SyncInterface):
    """This class describes an interface to Plex."""

    """Series ID's that can be set by TMDb"""
    SERIES_IDS = ('imdb_id', 'tmdb_id', 'tvdb_id')

    """How many failed episodes result in skipping a series"""
    SKIP_SERIES_THRESHOLD = 3

    """Episode titles that indicate a placeholder and are to be ignored"""
    __TEMP_IGNORE_REGEX = re_compile(r'^(tba|tbd|episode \d+)$', IGNORECASE)


    def __init__(self,
            url: str,
            token: str = 'NA',
            verify_ssl: bool = True,
            integrate_with_pmm: bool = False,
            filesize_limit: int = 10485760) -> None:
        """
        Constructs a new instance of a Plex Interface.

        Args:
            url: URL of plex server.
            token: X-Plex Token for sending API requests to Plex.
            verify_ssl: Whether to verify SSL requests when querying
                Plex.
            integrate_with_pmm: Whether to integrate with PMM in image
                uploading.
            filesize_limit: Number of bytes to limit a single file to
                during upload.
        """

        super().__init__(filesize_limit)

        # Create Session for caching HTTP responses
        self.__session = WebInterface('Plex', verify_ssl).session

        # Create PlexServer object with these arguments
        try:
            self.__token = token
            self.__server = PlexServer(url, token, self.__session)
        except Unauthorized:
            log.critical(f'Invalid Plex Token "{token}"')
            raise HTTPException(
                status_code=401,
                detail=f'Invalid Plex Token',
            )
        except Exception as e:
            log.critical(f'Cannot connect to Plex - returned error: "{e}"')
            raise HTTPException(
                status_code=400,
                detail=f'Cannot connect to Plex - {e}',
            )

        # Store integration
        self.integrate_with_pmm = integrate_with_pmm

        # List of "not found" warned series
        self.__warned = set()


    def catch_and_log(message: str, *, default=None) -> callable:
        """
        Return a decorator that logs (with the given log function) the
        given message if the decorated function raises an uncaught
        PlexApiException.

        Args:
            message: Message to log upon uncaught exception.
            default: (Keyword only) Value to return if decorated
                function raises an uncaught exception.

        Returns:
            Wrapped decorator that returns a wrapped callable.
        """

        def decorator(function: callable) -> callable:
            def inner(*args, **kwargs):
                try:
                    return function(*args, **kwargs)
                except PlexApiException as e:
                    log.exception(message, e)
                    return default
                except (ReadTimeout, ConnectionError) as e:
                    log.exception(f'Plex API has timed out, DB might be busy',e)
                    raise e
                except Exception as e:
                    log.exception(f'Uncaught exception', e)
                    raise e
            return inner
        return decorator


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32),
           reraise=True)
    def __get_library(self, library_name: str) -> 'Library':
        """
        Get the Library object under the given name.

        Args:
            library_name: The name of the library to get.

        Returns:
            The Library object if found, None otherwise.
        """

        try:
            return self.__server.library.section(library_name)
        except NotFound:
            log.error(f'Library "{library_name}" was not found in Plex')
            return None


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32),
           reraise=True)
    def __get_series(self, library: 'Library',
            series_info: SeriesInfo) -> 'Show':
        """
        Get the Series object from within the given Library associated
        with the given SeriesInfo. This tries to match by TVDb ID,
        TMDb ID, name, and finally full name.

        Args:
            library: The Library object to search for within Plex.
            series_info: Series to get the episodes of.

        Returns:
            The Series associated with this SeriesInfo object.
        """

        # Try by IMDb ID
        if series_info.has_id('imdb_id'):
            try:
                return library.getGuid(f'imdb://{series_info.imdb_id}')
            except NotFound:
                pass

        # Try by TVDb ID
        if series_info.has_id('tvdb_id'):
            try:
                return library.getGuid(f'tvdb://{series_info.tvdb_id}')
            except NotFound:
                pass

        # Try by TMDb ID
        if series_info.has_id('tmdb_id'):
            try:
                return library.getGuid(f'tmdb://{series_info.tmdb_id}')
            except NotFound:
                pass

        # Try by name
        try:
            for series in library.search(title=series_info.name,
                    year=series_info.year, libtype='show'):
                if series.title in (series_info.name, series_info.full_name):
                    return series
        except NotFound:
            pass

        # Not found, return None
        key = f'{library.title}-{series_info.full_name}'
        if key not in self.__warned:
            log.warning(f'Series "{series_info}" was not found under '
                        f'library "{library.title}" in Plex')
            self.__warned.add(key)

        return None


    @catch_and_log('Error getting library paths', default={})
    def get_library_paths(self, filter_libraries: list[str] = []
            ) -> dict[str, list[str]]:
        """
        Get all libraries and their associated base directories.

        Args:
            filter_libraries: List of library names to filter the return
                by.

        Returns:
            Dictionary whose keys are the library names, and whose
            values are the list of paths to that library's base
            directories.
        """

        # Go through every library in this server
        all_libraries = {}
        for library in self.__server.library.sections():
            # Skip non-TV libraries
            if library.type != 'show':
                continue

            # If filtering, skip unspecified libraries
            if (len(filter_libraries) > 0
                and library.title not in filter_libraries):
                continue

            # Add library's paths to the dictionary under the library
            all_libraries[library.title] = library.locations

        return all_libraries


    @catch_and_log('Error getting all series', default=[])
    def get_all_series(self,
            required_libraries: list[str] = [],
            excluded_libraries: list[str] = [],
            required_tags: list[str] = [], 
            excluded_tags: list[str] = [],
            ) -> list[tuple[SeriesInfo, str]]: 
        """
        Get all series within Plex, as filtered by the given arguments.

        Args:
            filter_libraries: Optional list of library names to filter
                returned by. If provided, only series that are within a
                given library are returned.
            required_tags: Optional list of tags to filter return by. If
                provided, only series with all the given tags are
                returned.

        Returns:
            List of tuples whose elements are the SeriesInfo of the
            series, and its corresponding library name.
        """

        # Temporarily override request timeout to 240s (4 min)
        self.REQUEST_TIMEOUT = 240

        # Go through every library in this server
        all_series = []
        for library in self.__server.library.sections():
            # Skip non-TV libraries
            if library.type != 'show':
                continue

            # If filtering libraries, skip library if unspecified
            if required_libraries and library.title not in required_libraries:
                continue
            if excluded_libraries and library.title in excluded_libraries:
                continue

            # Get all Shows in this library
            for show in library.all():
                # Skip show if tags provided and does not match
                if required_tags or excluded_tags:
                    tags = [label.tag.lower() for label in show.labels]
                    if (required_tags
                        and not all(t.lower() in tags for t in required_tags)):
                        continue
                    if (excluded_tags
                        and not all(t.lower() in tags for t in excluded_tags)):
                        continue

                # Skip show if it has no year
                if show.year is None:
                    log.warning(f'Series {show.title} has no year - skipping')
                    continue

                # Get all ID's for this series
                ids = {}
                for guid in show.guids:
                    for id_type in ('imdb', 'tmdb', 'tvdb'):
                        if (prefix := f'{id_type}://') in guid.id:
                            ids[f'{id_type}_id'] = guid.id[len(prefix):]
                            break

                # Create SeriesInfo object for this show, add to return
                series_info = SeriesInfo(show.title, show.year, **ids)
                all_series.append((series_info, library.title))

        # Reset request timeout
        self.REQUEST_TIMEOUT = 30

        return all_series


    @catch_and_log('Error getting all episodes', default=[])
    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfo) -> list[tuple[EpisodeInfo, bool]]:
        """
        Gets all episode info for the given series. Only episodes that have 
        already aired are returned.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to get the episodes of.

        Returns:
            List of EpisodeInfo objects for this series.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return []

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return []

        # Create list of all episodes in Plex
        all_episodes = []
        for plex_episode in series.episodes():
            # Skip if episode has no season or episode number
            if (plex_episode.parentIndex is None
                or plex_episode.index is None):
                log.warning(f'Episode {plex_episode} of {series_info} in '
                            f'"{library_name}" has no index - skipping')
                continue

            # Skip temporary titles
            airdate = plex_episode.originallyAvailableAt
            if (airdate is not None
                and self.__TEMP_IGNORE_REGEX.match(plex_episode.title)
                and airdate + timedelta(days=2) > datetime.now()):
                log.debug(f'Temporarily ignoring '
                          f'{plex_episode.seasonEpisode.upper()} of '
                          f'{series_info} - placeholder title')
                continue

            # Get all ID's for this episode
            ids = {}
            for guid in plex_episode.guids:
                if 'tvdb://' in guid.id:
                    ids['tvdb_id'] = guid.id[len('tvdb://'):]
                elif 'imdb://' in guid.id:
                    ids['imdb_id'] = guid.id[len('imdb://'):]
                elif 'tmdb://' in guid.id:
                    ids['tmdb_id'] = guid.id[len('tmdb://'):]

            # Create a new EpisodeInfo
            episode_info = EpisodeInfo(
                plex_episode.title,
                plex_episode.parentIndex,
                plex_episode.index,
                **ids,
                airdate=airdate,
            )

            # Add to list
            if episode_info is not None:
                all_episodes.append((episode_info, plex_episode.isWatched))

        return all_episodes


    def has_series(self, library_name: str, series_info: 'SeriesInfo') -> bool:
        """
        Determine whether the given series is present within Plex.

        Args:
            library_name: The name of the library potentially containing the
                series.
            series_info: The series to being evaluated.

        Returns:
            True if the series is present within Plex. False otherwise.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return False

        # If the given series cannot be found in this library, exit
        return self.__get_series(library, series_info) is not None


    @catch_and_log('Error updating watched statuses')
    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfo,
            episodes: list['Episode']) -> None:
        """
        Modify the Episodes' watched attribute according to the watched
        status of the corresponding episodes within Plex. 

        Args:
            library_name: The name of the library containing the Series.
            series_info: The Series to update.
            episodes: List of Episode objects to update.
        """

        # If no episodes, exit
        if len(episodes) == 0:
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            log.warning(f'Cannot find library "{library_name}" of {series_info}')
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            log.warning(f'Cannot find {series_info} in library "{library}"')
            return None

        # Go through each episode within Plex and update Episode spoiler status
        for plex_episode in series.episodes():
            for episode in episodes:
                if (plex_episode.parentIndex == episode.season_number
                    and plex_episode.index == episode.episode_number):
                    episode.watched = plex_episode.isWatched
                    break

        return None

    @catch_and_log("Error setting series ID's")
    def set_series_ids(self,
            library_name: str, series_info: SeriesInfo) -> None:
        """
        Set all possible series ID's for the given SeriesInfo object.

        Args:
            library_name: The name of the library containing the series.
            series_info: SeriesInfo to update.
        """

        # If all possible ID's are defined
        if series_info.has_ids(*self.SERIES_IDS):
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Set series ID's of all provided GUIDs
        for guid in series.guids:
            if 'imdb://' in guid.id:
                series_info.set_imdb_id(guid.id[len('imdb://'):])
            elif 'tmdb://' in guid.id:
                series_info.set_tmdb_id(int(guid.id[len('tmdb://'):]))
            elif 'tvdb://' in guid.id:
                series_info.set_tvdb_id(int(guid.id[len('tvdb://'):]))


    @catch_and_log("Error setting episode ID's")
    def set_episode_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo]) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo objects. This
        sets the Sonarr and TVDb ID's for each episode. As a byproduct, this
        also updates the series ID's for the SeriesInfo object

        Args:
            library_name: Name of the library the series is under.
            series_info: SeriesInfo for the entry.
            infos: List of EpisodeInfo objects to update.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Go through each provided EpisodeInfo and update the ID's
        for episode_info in episode_infos:
            # Skip if EpisodeInfo already has all the possible ID's
            if episode_info.has_ids(*self.SERIES_IDS):
                continue

            # Get episode from Plex
            try:
                plex_episode = series.episode(
                    season=episode_info.season_number,
                    episode=episode_info.episode_number,
                )
            except NotFound:
                continue

            # Set the ID's for this object
            for guid in plex_episode.guids:
                if 'imdb://' in guid.id:
                    episode_info.set_imdb_id(guid.id[len('imdb://'):])
                elif 'tmdb://' in guid.id:
                    episode_info.set_tmdb_id(int(guid.id[len('tmdb://'):]))
                elif 'tvdb://' in guid.id:
                    episode_info.set_tvdb_id(int(guid.id[len('tvdb://'):]))
            

    @catch_and_log('Error getting source image')
    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo, *,
            raise_exc: bool = True) -> Optional[str]:
        """
        Get the source image for the given episode within Plex.

        Args:
            library_name: Name of the library the series is under.
            series_info: The series to get the source image of.
            episode_info: The episode to get the source image of.
            raise_exc: Whether to raise any HTTPExceptions that arise.

        Returns:
            URL to the thumbnail of the given Episode. None if the
            episode DNE or otherwise has no source image.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Get Episode from within Plex
        try:
            plex_episode = series.episode(
                season=episode_info.season_number,
                episode=episode_info.episode_number
            )

            return (
                f'{self.__server._baseurl}{plex_episode.thumb}'
                f'?X-Plex-Token={self.__token}'
            )
        # Episode DNE in Plex, return
        except NotFound:
            return None

        return None


    @catch_and_log('Error getting library names', default=[])
    def get_libraries(self) -> list[str]:
        """
        Get the names of all libraries within this server.

        Returns:
            List of library names.
        """

        return [
            library.title
            for library in self.__server.library.sections()
            if library.type == 'show'
        ]


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32),
           before_sleep=lambda _:log.warning('Cannot upload image, retrying..'),
           reraise=True)
    def __retry_upload(self, plex_object: 'Episode', filepath: Path) -> None:
        """
        Upload the given poster to the given Episode, retrying if it fails.

        Args:
            plex_object: The plexapi object to upload the file to.
            filepath: Filepath to the poster to upload.
        """

        plex_object.uploadPoster(filepath=filepath)


    @catch_and_log('Error uploading title cards')
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

        # No episodes to load, exit
        if len(episode_and_cards) == 0:
            log.debug(f'No episodes to load for {series_info}')
            return []

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return []

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return []

        # Go through each episode within Plex, set title cards
        loaded, error_count = [], 0
        for plex_episode in series.episodes():
            # If error count is too high, skip this series
            if error_count >= self.SKIP_SERIES_THRESHOLD:
                log.error(f'Failed to upload {error_count} episodes, skipping '
                          f'"{series_info}"')
                break

            # Skip episode if no associated episode was provided
            found = False
            for episode, card in episode_and_cards:
                if (episode.season_number == plex_episode.parentIndex
                    and episode.episode_number == plex_episode.index):
                    found = True
                    break
            if not found:
                continue

            # Shrink image if necessary, skip if cannot be compressed
            if (image := self.compress_image(card.card_file)) is None:
                continue

            # Upload card to Plex, optionally remove Overlay label
            try:
                self.__retry_upload(plex_episode, image.resolve())
                if self.integrate_with_pmm:
                    plex_episode.removeLabel(['Overlay'])
            except Exception as e:
                error_count += 1
                log.exception(f'Unable to upload {image.resolve()} to '
                              f'{series_info}', e)
                continue
            else:
                loaded.append((episode, card))

        # Log load operations to user
        if loaded:
            log.info(f'Loaded {len(loaded)} cards for "{series_info}"')

        return loaded


    @catch_and_log('Error uploading season posters')
    def load_season_posters(self,
            library_name: str,
            series_info: SeriesInfo,
            season_poster_set: 'SeasonPosterSet') -> None:
        """
        Set the season posters from the given set within Plex.

        Args:
            library_name: Name of the library containing the series to update.
            series_info: The series to update.
            season_poster_set: SeasonPosterSet with season posters to set.
        """

        # If no posters to upload, skip
        if not season_poster_set.has_posters:
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Condition for this series
        loaded_count = 0
        for season in series.seasons():
            # Skip if no season poster for this seasons
            if (poster := season_poster_set.get_poster(season.index)) is None:
                continue

            # Get the loaded details for this season
            condition = (
                (where('library') == library_name) &
                (where('series') == series_info.full_name) &
                (where('season') == season.index)
            )
            details = self.__posters.get(condition)

            # Skip if this exact poster has been loaded 
            if (details is not None
                and details['filesize'] == poster.stat().st_size):
                continue

            # Shrink image if necessary
            if (resized_poster := self.compress_image(poster)) is None:
                continue

            # Upload this poster
            try:
                self.__retry_upload(season, resized_poster)
            except Exception:
                continue
            else:
                loaded_count += 1

        # Log load operations to user
        if loaded_count > 0:
            log.info(f'Loaded {loaded_count} season posters for "{series_info}"')


    @catch_and_log('Error getting rating key details')
    def get_episode_details(self, rating_key: int) -> list[EpisodeDetails]:
        """
        Get all details for all episodes indicated by the given Plex
        rating key.

        Args:
            rating_key: Rating key used to fetch the item within Plex.

        Returns:
            List of tuples of the library name, SeriesInfo, EpisodeInfo,
            and the episode watch status corresponding to the given
            rating key. If the object associated with the rating key is
            a show/season, then all contained episodes are detailed.
            An empty list is returned if the item(s) associated with the
            given key cannot be found.
        """

        try:
            # Get the episode for this key
            entry = self.__server.fetchItem(rating_key)

            # New show, return all episodes in series
            if entry.type == 'show':
                assert entry.year is not None
                series_info = SeriesInfo(entry.title, entry.year)

                return [EpisodeDetails(
                    series_info,
                    EpisodeInfo.from_plex_episode(ep),
                    ep.isWatched
                ) for ep in entry.episodes()]
            # New season, return all episodes in season
            elif entry.type == 'season':
                # Get series associated with this season
                series = self.__server.fetchItem(entry.parentKey)
                if series.year is None:
                    raise ValueError(f'Series has no year')

                series_info = SeriesInfo(entry.title, series.year)
                return [EpisodeDetails(
                    series_info,
                    EpisodeInfo.from_plex_episode(ep),
                    ep.isWatched
                ) for ep in entry.episodes()]
            # New episode, return just that
            elif entry.TYPE == 'episode':
                series = self.__server.fetchItem(entry.grandparentKey)
                assert series.year is not None

                series_info = SeriesInfo(entry.grandparentTitle, series.year)
                return [EpisodeDetails(
                    series_info,
                    EpisodeInfo.from_plex_episode(entry),
                    entry.isWatched,
                )]
            # Movie, warn and return empty list
            elif entry.type == 'movie':
                log.warning(f'Item with rating key {rating_key} is a movie')
            return []
        except NotFound:
            log.error(f'No item with rating key {rating_key} exists')
        except ValueError:
            log.warning(f'Item with rating key {rating_key} has no year')
        except Exception as e:
            log.exception(f'Rating key {rating_key} has some error', e)

        # Error occurred, return empty list
        return []