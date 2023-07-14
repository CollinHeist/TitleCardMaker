from datetime import datetime, timedelta
from pathlib import Path
from re import IGNORECASE, compile as re_compile
from sys import exit as sys_exit
from typing import Any, Callable, Optional, Union

from plexapi.exceptions import PlexApiException
from plexapi.server import PlexServer, NotFound, Unauthorized
from plexapi.library import Library as PlexLibrary
from plexapi.video import (
    Episode as PlexEpisode, Show as PlexShow, Season as PlexSeason
)
from requests.exceptions import (
    ReadTimeout, ConnectionError as PlexConnectionError
)
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential
from tinydb import where
from tqdm import tqdm

from modules.Debug import log, TQDM_KWARGS
from modules.Episode import Episode
from modules.EpisodeDataSource import EpisodeDataSource
from modules.EpisodeInfo import EpisodeInfo
from modules import global_objects
from modules.MediaServer import MediaServer, SourceImage
from modules.PersistentDatabase import PersistentDatabase
from modules.SeasonPosterSet import SeasonPosterSet
from modules.SeriesInfo import SeriesInfo
from modules.StyleSet import StyleSet
from modules.SyncInterface import SyncInterface
from modules.WebInterface import WebInterface


def catch_and_log(message: str, *, default: Any = None) -> Callable:
    """
    Return a decorator that logs (with the given log function) the given
    message if the decorated function raises an uncaught
    PlexApiException.

    Args:
        message: Message to log upon uncaught exception.
        default: (Keyword only) Value to return if decorated function
            raises an uncaught exception.

    Returns:
        Wrapped decorator that returns a wrapped callable.
    """

    def decorator(function: Callable) -> Callable:
        def inner(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except PlexApiException as e:
                log.exception(message, e)
                return default
            except (ReadTimeout, PlexConnectionError) as e:
                log.exception(f'Plex API has timed out, DB might be busy',e)
                raise e
            except Exception as e:
                log.exception(f'Uncaught exception', e)
                raise e
        return inner
    return decorator


class PlexInterface(EpisodeDataSource, MediaServer, SyncInterface):
    """This class describes an interface to Plex."""

    """Series ID's that can be set by TMDb"""
    SERIES_IDS = ('imdb_id', 'tmdb_id', 'tvdb_id')

    """Filepath to the database of each episode's loaded card characteristics"""
    LOADED_DB = 'loaded.json'

    """Filepath to the database of the loaded season poster characteristics"""
    LOADED_POSTERS_DB = 'loaded_posters.json'

    """How many failed episodes result in skipping a series"""
    SKIP_SERIES_THRESHOLD = 3

    """Episode titles that indicate a placeholder and are to be ignored"""
    __TEMP_IGNORE_REGEX = re_compile(r'^(tba|tbd|episode \d+)$', IGNORECASE)


    def __init__(self,
            url: str,
            x_plex_token: str = 'NA',
            verify_ssl: bool = True,
            integrate_with_pmm_overlays: bool = False,
            filesize_limit: int = 10485760,
        ) -> None:
        """
        Constructs a new instance of a Plex Interface.

        Args:
            url: URL of plex server.
            x_plex_token: X-Plex Token for sending API requests to Plex.
            verify_ssl: Whether to verify SSL requests when querying
                Plex.
            integrate_with_pmm_overlays: Whether to integrate with PMM
                overlays in image uploading.
            filesize_limit: Number of bytes to limit a single file to
                during upload.

        Raises:
            SystemExit if an Exception is raised while connecting to
                Plex.
        """

        super().__init__(filesize_limit)

        # Get global MediaInfoSet objects
        self.info_set = global_objects.info_set

        # Create Session for caching HTTP responses
        self.__session = WebInterface('Plex', verify_ssl).session

        # Create PlexServer object with these arguments
        try:
            self.__token = x_plex_token
            self.__server = PlexServer(url, x_plex_token, self.__session)
        except Unauthorized:
            log.critical(f'Invalid Plex Token "{x_plex_token}"')
            sys_exit(1)
        except Exception as e:
            log.critical(f'Cannot connect to Plex - returned error: "{e}"')
            sys_exit(1)

        # Store integration
        self.integrate_with_pmm_overlays = integrate_with_pmm_overlays

        # Create/read loaded card database
        self.__posters = PersistentDatabase(self.LOADED_POSTERS_DB)

        # List of "not found" warned series
        self.__warned = set()


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32),
           reraise=True)
    def __get_library(self, library_name: str) -> Optional[PlexLibrary]:
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
    def __get_series(self,
            library: PlexLibrary,
            series_info: SeriesInfo) -> Optional[PlexShow]:
        """
        Get the Series object from within the given Library associated
        with the given SeriesInfo. This tries to match by TVDb ID,
        TMDb ID, name, and finally name.

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
    def get_library_paths(self,
            filter_libraries: list[str] = []) -> dict[str, list[str]]:
        """
        Get all libraries and their associated base directories.

        Args:
            filer_libraries: List of library names to filter the return by.

        Returns:
            Dictionary whose keys are the library names, and whose values are
            the list of paths to that library's base directories.
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
            filter_libraries: list[str] = [],
            required_tags: list[str] = [],
        ) -> list[tuple[SeriesInfo, str, str]]:
        """
        Get all series within Plex, as filtered by the given libraries.

        Args:
            filter_libraries: Optional list of library names to filter
                returned by. If provided, only series that are within a
                given library are returned.
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

        # Go through every library in this server
        all_series = []
        for library in self.__server.library.sections():
            # Skip non-TV libraries
            if library.type != 'show':
                continue

            # If filtering libraries, skip library if unspecified
            if (len(filter_libraries) > 0
                and library.title not in filter_libraries):
                continue

            # Get all Shows in this library
            for show in library.all():
                # Skip show if tags provided and does not match
                if required_tags:
                    tags = [label.tag.lower() for label in show.labels]
                    if not all(tag.lower() in tags for tag in required_tags):
                        continue

                # Skip show if it has no year
                if show.year is None:
                    log.warning(f'Series {show.title} has no year - skipping')
                    continue

                # Skip show if it has no locations.. somehow..
                if len(show.locations) == 0:
                    log.warning(f'Series {show.title} has no files - skipping')
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
                all_series.append((series_info,show.locations[0],library.title))

        # Reset request timeout
        self.REQUEST_TIMEOUT = 30

        return all_series


    @catch_and_log('Error getting all episodes', default=[])
    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_infos: Optional[list[EpisodeInfo]] = None,
        ) -> list[EpisodeInfo]:
        """
        Gets all episode info for the given series. Only episodes that
        have  already aired are returned.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to get the episodes of.
            episode_infos: Unused argument.

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

            # Create either a new EpisodeInfo or get from the MediaInfoSet
            episode_info = self.info_set.get_episode_info(
                series_info,
                plex_episode.title,
                plex_episode.parentIndex,
                plex_episode.index,
                **ids,
                airdate=airdate,
                title_match=True,
                queried_plex=True,
            )

            # Add to list
            if episode_info is not None:
                all_episodes.append(episode_info)

        return all_episodes


    def has_series(self, library_name: str, series_info: SeriesInfo) -> bool:
        """
        Determine whether the given series is present within Plex.

        Args:
            library_name: The name of the library potentially containing
                the series.
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
            episode_map: dict[str, Episode],
            style_set: StyleSet,
        ) -> None:
        """
        Modify the Episode objects according to the watched status of the
        corresponding episodes within Plex, and the spoil status of the object.
        If a loaded card needs its spoiler status changed, the card is deleted
        and the loaded map is forced to reload that card.

        Args:
            library_name: The name of the library containing the series.
            series_info: The series to update.
            episode_map: Dictionary of episode keys to Episode objects to modify
            style_set: StyleSet object to update the style of the Episodes with.
        """

        # If no episodes, exit
        if len(episode_map) == 0:
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Get loaded characteristics of the series
        loaded_series = self.loaded_db.search(
            self._get_condition(library_name, series_info)
        )

        # Go through each episode within Plex and update Episode spoiler status
        for plex_episode in series.episodes():
            # If this Plex episode doesn't have Episode object(?) skip
            ep_key = f'{plex_episode.parentIndex}-{plex_episode.index}'
            if not (episode := episode_map.get(ep_key)):
                continue

            # Set Episode watched/spoil statuses
            episode.update_statuses(plex_episode.isWatched, style_set)

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


    @catch_and_log("Error setting series ID's")
    def set_series_ids(self,library_name: str, series_info: SeriesInfo) -> None:
        """
        Set all possible series ID's for the given SeriesInfo object.

        Args:
            library_name: The name of the library containing the series.
            series_info: SeriesInfo object to update.
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
            # No MediaInfoSet, set directly
            if self.info_set is None:
                if 'imdb://' in guid.id:
                    series_info.set_imdb_id(guid.id[len('imdb://'):])
                elif 'tmdb://' in guid.id:
                    series_info.set_tmdb_id(guid.id[len('tmdb://'):])
                elif 'tvdb://' in guid.id:
                    series_info.set_tvdb_id(guid.id[len('tvdb://'):])
            # Set using global MediaInfoSet
            else:
                if 'imdb://' in guid.id:
                    self.info_set.set_imdb_id(
                        series_info, guid.id[len('imdb://'):]
                    )
                elif 'tmdb://' in guid.id:
                    self.info_set.set_tmdb_id(
                        series_info, guid.id[len('tmdb://'):]
                    )
                elif 'tvdb://' in guid.id:
                    self.info_set.set_tvdb_id(
                        series_info, guid.id[len('tvdb://'):]
                    )

        return None


    @catch_and_log("Error setting episode ID's")
    def set_episode_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
            *,
            inplace: bool = True,
        ) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo
        objects. This sets the Sonarr and TVDb ID's for each episode. As
        a byproduct, this also updates the series ID's for the
        SeriesInfo object

        Args:
            library_name: Name of the library the series is under.
            series_info: SeriesInfo for the entry.
            episode_infos: List of EpisodeInfo objects to update.
            inplace: Unused argument.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Go through each provided EpisodeInfo and update the ID's
        for info in episode_infos:
            # Skip if EpisodeInfo already has all the possible ID's
            if info.queried_plex or info.has_ids(*self.SERIES_IDS):
                continue

            # Get episode from Plex
            info.queried_plex = True
            try:
                plex_episode = series.episode(
                    season=info.season_number,
                    episode=info.episode_number,
                )
            except NotFound:
                continue

            # Set the ID's for this object
            for guid in plex_episode.guids:
                if 'imdb://' in guid.id:
                    info.set_imdb_id(guid.id[len('imdb://'):])
                elif 'tmdb://' in guid.id:
                    info.set_tmdb_id(int(guid.id[len('tmdb://'):]))
                elif 'tvdb://' in guid.id:
                    info.set_tvdb_id(int(guid.id[len('tvdb://'):]))

        return None


    @catch_and_log('Error getting source image')
    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
        ) -> SourceImage:
        """
        Get the source image for the given episode within Plex.

        Args:
            library_name: Name of the library the series is under.
            series_info: The series to get the source image of.
            episode_info: The episode to get the source image of.

        Returns:
            URL to the thumbnail of the given Episode. None if the episode DNE.
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

            return (f'{self.__server._baseurl}{plex_episode.thumb}' # pylint: disable=protected-access
                    f'?X-Plex-Token={self.__token}')
        except NotFound:
            # Episode DNE in Plex, return
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
    def __retry_upload(self,
            plex_object: Union[PlexEpisode, PlexSeason],
            filepath: Path) -> None:
        """
        Upload the given poster to the given Episode, retrying if it fails.

        Args:
            plex_object: The plexapi object to upload the file to.
            filepath: Filepath to the poster to upload.
        """

        plex_object.uploadPoster(filepath=filepath)


    @catch_and_log('Error uploading title cards')
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
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            episode_map: Dictionary of episode keys to Episode objects
                to update the cards of.
        """

        # Filter episodes without cards, or whose cards have not changed
        filtered_episodes = self._filter_loaded_cards(
            library_name, series_info, episode_map
        )

        # If no episodes remain, exit
        if len(filtered_episodes) == 0:
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Go through each episode within Plex, set title cards
        error_count, loaded_count = 0, 0
        for pl_episode in (pbar := tqdm(series.episodes(), **TQDM_KWARGS)):
            # If error count is too high, skip this series
            if error_count >= self.SKIP_SERIES_THRESHOLD:
                log.error(f'Failed to upload {error_count} episodes, skipping '
                          f'"{series_info}"')
                break

            # Skip episodes that aren't in list of cards to update
            ep_key = f'{pl_episode.parentIndex}-{pl_episode.index}'
            if not (episode := filtered_episodes.get(ep_key)):
                continue

            # Update progress bar
            pbar.set_description(f'Updating {pl_episode.seasonEpisode.upper()}')

            # Shrink image if necessary, skip if cannot be compressed
            if (card := self.compress_image(episode.destination)) is None:
                continue

            # Upload card to Plex, optionally remove Overlay label
            try:
                self.__retry_upload(pl_episode, card.resolve())
                if self.integrate_with_pmm_overlays:
                    pl_episode.removeLabel(['Overlay'])
            except Exception as e:
                error_count += 1
                log.exception(f'Unable to upload {card.resolve()} to '
                              f'{series_info}', e)
                continue
            else:
                loaded_count += 1

            # Update/add loaded map with this entry
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


    @catch_and_log('Error uploading season posters')
    def set_season_posters(self,
            library_name: str,
            series_info: SeriesInfo,
            season_poster_set: SeasonPosterSet,
        ) -> None:
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
                (where('library') == library_name)
                & (where('series') == series_info.full_name)
                & (where('season') == season.index)
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

            # Update loaded database
            self.__posters.upsert({
                'library': library_name,
                'series': series_info.full_name,
                'season': season.index,
                'filesize': poster.stat().st_size,
            }, condition)

        # Log load operations to user
        if loaded_count > 0:
            log.info(f'Loaded {loaded_count} season posters for "{series_info}"')

        return None


    @catch_and_log('Error getting episode details')
    def get_episode_details(self,
            rating_key: int) -> list[tuple[SeriesInfo, EpisodeInfo, str]]:
        """
        Get all details for all episodes indicated by the given Plex rating key.

        Args:
            rating_key: Rating key used to fetch the item within Plex.

        Returns:
            List of tuples of the SeriesInfo, EpisodeInfo, and the library name
            corresponding to the given rating key. If the object associated with
            the rating key is a show/season, then all contained episodes are
            detailed. An empty list is returned if the item(s) associated with
            the given key cannot be found.
        """

        try:
            # Get the episode for this key
            entry = self.__server.fetchItem(rating_key)

            # New show, return all episodes in series
            if entry.type == 'show':
                assert entry.year is not None
                series_info = self.info_set.get_series_info(
                    entry.title, entry.year
                )

                return [
                    (series_info,
                     EpisodeInfo(ep.title, ep.parentIndex, ep.index),
                     entry.librarySectionTitle)
                    for ep in entry.episodes()
                ]
            # New season, return all episodes in season
            if entry.type == 'season':
                # Get series associated with this season
                series = self.__server.fetchItem(entry.parentKey)
                if series.year is None:
                    raise ValueError

                series_info = self.info_set.get_series_info(
                    entry.parentTitle, entry.year
                )

                return [
                    (series_info,
                     EpisodeInfo(ep.title, entry.index, ep.index),
                     series.librarySectionTitle)
                    for ep in entry.episodes()
                ]
            # New episode, return just that
            if entry.TYPE == 'episode':
                series = self.__server.fetchItem(entry.grandparentKey)
                assert series.year is not None
                series_info = self.info_set.get_series_info(
                    entry.grandparentTitle, series.year
                )

                return [(
                    series_info,
                    EpisodeInfo(entry.title, entry.parentIndex, entry.index),
                    entry.librarySectionTitle,
                )]
            # Movie, warn and return empty list
            if entry.type == 'movie':
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
