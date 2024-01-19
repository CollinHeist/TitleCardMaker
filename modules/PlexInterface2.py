from datetime import datetime, timedelta
from logging import Logger, LoggerAdapter
from pathlib import Path
from re import IGNORECASE, compile as re_compile
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Optional, Union

from fastapi import HTTPException
from PIL import Image
from plexapi.exceptions import PlexApiException
from plexapi.library import Library as PlexLibrary
from plexapi.video import Episode as PlexEpisode, Season as PlexSeason
from plexapi.server import PlexServer, NotFound, Unauthorized
from plexapi.video import Show as PlexShow
from requests.exceptions import (
    ReadTimeout, ConnectionError as PlexConnectionError
)
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential

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


class EpisodeDetails(NamedTuple): # pylint: disable=missing-class-docstring
    series_info: SeriesInfo
    episode_info: EpisodeInfo
    watched_status: WatchedStatus


def catch_and_log(
        message: str,
        *,
        default: Any = None,
    ) -> Callable:
    """
    Return a decorator that logs (with the given log function) the
    given message if the decorated function raises an uncaught
    PlexApiException.

    Args:
        message: Message to log upon uncaught exception.
        default: Value to return if decorated function raises
            an uncaught exception.

    Returns:
        Wrapped decorator that returns a wrapped callable.
    """

    def decorator(function: Callable) -> Callable:
        def inner(*args, **kwargs):
            # Get contextual logger if provided as argument to function
            if ('log' in kwargs
                and isinstance(kwargs['log'], (Logger, LoggerAdapter))):
                clog = kwargs['log']
            else:
                clog = log

            try:
                return function(*args, **kwargs)
            except PlexApiException as e:
                clog.exception(message, e)
                return default
            except (ReadTimeout, PlexConnectionError) as e:
                clog.exception(f'Plex API has timed out, DB might be busy',e)
                raise e
            except Exception as e:
                clog.exception(f'Uncaught exception', e)
                raise e
        return inner
    return decorator


class PlexInterface(MediaServer, EpisodeDataSource, SyncInterface, Interface):
    """This class describes an interface to Plex."""

    INTERFACE_TYPE = 'Plex'

    """Series ID's that can be set by TMDb"""
    SERIES_IDS = ('imdb_id', 'tmdb_id', 'tvdb_id')

    """EXIF data to write to images if PMM integration is enabled"""
    EXIF_TAG = {'key': 0x4242, 'data': 'titlecard'}

    """Episode titles that indicate a placeholder and are to be ignored"""
    __TEMP_IGNORE_REGEX = re_compile(r'^(tba|tbd|episode \d+)$', IGNORECASE)


    def __init__(self,
            url: str,
            api_key: str = 'NA',
            use_ssl: bool = True,
            integrate_with_pmm: bool = False,
            filesize_limit: int = 10485760,
            *,
            interface_id: int = 0,
            log: Logger = log,
        ) -> None:
        """
        Constructs a new instance of a Plex Interface.

        Args:
            url: URL of plex server.
            api_key: X-Plex Token for sending API requests to Plex.
            use_ssl: Whether to use SSL in all requests.
            integrate_with_pmm: Whether to integrate with PMM in image
                uploads.
            filesize_limit: Number of bytes to limit a single file to
                during upload.
            interface_id: ID of this interface.
            log: Logger for all log messages.
        """

        super().__init__(filesize_limit)

        # Create Session for caching HTTP responses
        self._interface_id = interface_id
        self.__session = WebInterface('Plex', use_ssl, log=log).session

        # Create PlexServer object with these arguments
        try:
            self.__token = api_key
            self.__server = PlexServer(url, api_key, self.__session)
        except Unauthorized as e:
            log.critical(f'Invalid Plex Token "{api_key}"')
            raise HTTPException(
                status_code=401,
                detail=f'Invalid Plex Token',
            ) from e
        except Exception as exc:
            log.critical(f'Cannot connect to Plex - returned error: "{exc}"')
            raise HTTPException(
                status_code=400,
                detail=f'Cannot connect to Plex - {exc}',
            ) from exc

        # Store integration
        self.integrate_with_pmm = integrate_with_pmm

        # List of "not found" warned series
        self.__warned = set()
        self.activate()


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32),
           reraise=True)
    def __get_library(self,
            library_name: str,
            *,
            log: Logger = log,
        ) ->  PlexLibrary:
        """
        Get the Library object under the given name.

        Args:
            library_name: The name of the library to get.
            log: Logger for all log messages.

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
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> PlexShow:
        """
        Get the Series object from within the given Library associated
        with the given SeriesInfo. This tries to match by TVDb ID,
        TMDb ID, name, and finally full name.

        Args:
            library: The Library object to search for within Plex.
            series_info: Series to get the episodes of.
            log: Logger for all log messages.

        Returns:
            The series associated with this SeriesInfo object.
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
            results = library.search(
                title=series_info.name, year=series_info.year, libtype='show'
            )
            for series in results:
                if series_info.matches(series.title):
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
            filter_libraries: list[str] = []
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
            *,
            log: Logger = log,
        ) -> list[tuple[SeriesInfo, str]]:
        """
        Get all series within Plex, as filtered by the given arguments.

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

        # Go through every library in this server
        all_series = []
        for library in self.__server.library.sections():
            # Skip non-TV libraries
            if library.type != 'show':
                continue

            # If filtering libraries, skip library if unspecified
            if ((required_libraries and library.title not in required_libraries)
                or (excluded_libraries and library.title in excluded_libraries)):
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
                        and any(t.lower() in tags for t in excluded_tags)):
                        continue

                # Skip show if it has no year
                if show.year is None:
                    log.warning(f'Series {show.title} has no year - skipping')
                    continue

                # Create SeriesInfo object for this show, add to return
                series_info = SeriesInfo.from_plex_show(show)
                all_series.append((series_info, library.title))

        # Reset request timeout
        self.REQUEST_TIMEOUT = 30

        return all_series


    @catch_and_log('Error getting all episodes', default=[])
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
            library_name: The name of the library containing the series.
            series_info: Series to get the episodes of.
            log: Logger for all log messages.

        Returns:
            List of tuples of the EpisodeInfos and that episode's
            corresponding watched status for this series.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return []

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return []

        # Create list of all episodes in Plex
        all_episodes = []
        for plex_episode in series.episodes(container_size=500):
            # Skip if episode has no season or episode number
            if (plex_episode.parentIndex is None
                or plex_episode.index is None):
                log.warning(f'Episode {plex_episode} of {series_info} in '
                            f'"{library_name}" has no index - skipping')
                continue

            # Skip temp titles if title matching and within 2 days of airing
            airdate = plex_episode.originallyAvailableAt
            if (not series_info.match_titles
                and airdate is not None
                and self.__TEMP_IGNORE_REGEX.match(plex_episode.title)
                and airdate + timedelta(days=2) > datetime.now()):
                log.debug(f'Temporarily ignoring '
                          f'{plex_episode.seasonEpisode.upper()} of '
                          f'{series_info} - placeholder title')
                continue

            # Create a new EpisodeInfo, add to list
            episode_info = EpisodeInfo.from_plex_episode(plex_episode)
            all_episodes.append((
                episode_info,
                WatchedStatus(
                    self._interface_id,
                    library_name,
                    plex_episode.isWatched,
                ),
            ))

        return all_episodes


    @catch_and_log('Error updating watched statuses', default=False)
    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfo,
            episodes: list['Episode'],
            *,
            log: Logger = log,
        ) -> bool:
        """
        Modify the Episodes' watched attribute according to the watched
        status of the corresponding episodes within Plex.

        Args:
            library_name: The name of the library containing the Series.
            series_info: The Series to update.
            episodes: List of Episode objects to update.
            log: Logger for all log messages.

        Returns:
            Whether any Episode's watched statuses were modified.
        """

        # If no episodes, exit
        if len(episodes) == 0:
            return False

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            log.warning(f'Cannot find library "{library_name}" of {series_info}')
            return False

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            log.warning(f'Cannot find {series_info} in library "{library}"')
            return False

        # Get data for each Plex episode
        plex_episodes = [
            (
                EpisodeInfo.from_plex_episode(episode),
                WatchedStatus(
                    self._interface_id, library_name, episode.isWatched,
                )
            )
            for episode in series.episodes(container_size=500)
        ]

        # Update watched statuses of all Episodes
        changed = False
        for episode in episodes:
            episode_info = episode.as_episode_info
            for plex_episode, watched_status in plex_episodes:
                if episode_info == plex_episode:
                    changed |= episode.add_watched_status(watched_status)
                    break

        return changed


    @catch_and_log("Error setting series ID's")
    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> None:
        """
        Set all possible series ID's for the given SeriesInfo object.

        Args:
            library_name: The name of the library containing the series.
            series_info: SeriesInfo to update.
            log: Logger for all log messages.
        """

        # If all possible ID's are defined
        if series_info.has_ids(*self.SERIES_IDS):
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return None

        # Set series ID's of all provided GUIDs
        for guid in series.guids:
            if 'imdb://' in guid.id:
                series_info.set_imdb_id(guid.id[len('imdb://'):])
            elif 'tmdb://' in guid.id:
                series_info.set_tmdb_id(int(guid.id[len('tmdb://'):]))
            elif 'tvdb://' in guid.id:
                series_info.set_tvdb_id(int(guid.id[len('tvdb://'):]))

        return None


    @catch_and_log("Error setting episode ID's")
    def set_episode_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
            *,
            log: Logger = log,
        ) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo objects. This
        sets the Sonarr and TVDb ID's for each episode. As a byproduct, this
        also updates the series ID's for the SeriesInfo object

        Args:
            library_name: Name of the library the series is under.
            series_info: SeriesInfo for the entry.
            infos: List of EpisodeInfo objects to update.
            log: Logger for all log messages.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return None

        # Filter EpisodeInfo's with all ID's
        filtered_episode_infos = {
            episode_info.key: episode_info
            for episode_info in episode_infos
            if not episode_info.has_ids(*self.SERIES_IDS)
        }

        # Go through all of this Series' Episodes
        for plex_episode in series.episodes(container_size=500):
            # Find matching EpisodeInfo, skip if not found
            plex_episode: PlexEpisode
            episode_info = filtered_episode_infos.get(
                f's{plex_episode.seasonNumber}e{plex_episode.episodeNumber}'
            )
            if episode_info is None:
                continue

            # Set the ID's for this object
            for guid in plex_episode.guids:
                if 'imdb://' in guid.id:
                    episode_info.set_imdb_id(guid.id[len('imdb://'):])
                elif 'tmdb://' in guid.id:
                    episode_info.set_tmdb_id(int(guid.id[len('tmdb://'):]))
                elif 'tvdb://' in guid.id:
                    episode_info.set_tvdb_id(int(guid.id[len('tvdb://'):]))

        return None


    @catch_and_log('Error querying for Series')
    def query_series(self,
            query: str,
            *,
            log: Logger = log,
        ) -> list[SearchResult]:
        """
        Search Plex for any Series matching the given query.

        Args:
            query: Series name or substring to look up.
            log: Logger for all log messages.

        Returns:
            List of SearchResults for the given query. Results are from
            any library. All returned poster URL's utilize the Plex
            proxy API endpoint to obfuscate this Server's token.
        """

        # Search Plex for this query
        results: list[PlexShow] = self.__server.search(
            query, mediatype='show', limit=50
        )

        def parse_ids(show: PlexShow) -> dict:
            """
            Parse any database IDs from the given object.

            Args:
                show: Show object whose GUIDs are being parsed.

            Returns:
                Dictionary of DB ID's. Each ID is set, or None.
            """

            ids = {'imdb_id': None, 'tmdb_id': None, 'tvdb_id': None}
            for guid in show.guids:
                if 'imdb://' in guid.id:
                    ids['imdb_id'] = guid.id[len('imdb://'):]
                elif 'tmdb://' in guid.id:
                    ids['tmdb_id'] = int(guid.id[len('tmdb://'):])
                elif 'tvdb://' in guid.id:
                    ids['tvdb_id'] = int(guid.id[len('tvdb://'):])
            return ids

        # Return results, use proxy endpoint for poster URL
        return [
            SearchResult(
                name=result.title, year=result.year,
                poster=f'/api/proxy/plex?url={result.thumb}&interface_id={self._interface_id}',
                overview=result.summary,
                **parse_ids(result),
            ) for result in results
        ]


    @catch_and_log('Error getting source image')
    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            *,
            proxy_url: bool = False,
            log: Logger = log,
        ) -> Optional[str]:
        """
        Get the source image for the given episode within Plex.

        Args:
            library_name: Name of the library the series is under.
            series_info: The series to get the source image of.
            episode_info: The episode to get the source image of.
            proxy_url: Whether to proxy the returned URL.
            log: Logger for all log messages.

        Returns:
            URL to the thumbnail of the given Episode. None if the
            episode DNE or otherwise has no source image.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return None

        # Labels that will result in source skip
        bad_labels = ('Overlay', 'TCM') if self.integrate_with_pmm else ('TCM',)

        # Get Episode from within Plex
        try:
            plex_episode = series.episode(
                season=episode_info.season_number,
                episode=episode_info.episode_number
            )
        # Episode DNE in Plex, return
        except NotFound:
            return None

        # Verify this Episode does not have the PMM overlay label (if not proxying)
        if any(label.tag in bad_labels for label in plex_episode.labels):
            log.debug(f'{series_info} {episode_info} Cannot use Plex '
                        f'thumbnail, has existing Overlay or Title Card')
            return None

        # If proxying, use API redirect URL; token will be embedded by endpoint
        if proxy_url:
            return (
                f'/api/proxy/plex?url={plex_episode.thumb}'
                f'&interface_id={self._interface_id}'
            )

        # pylint: disable=protected-access
        return (
            f'{self.__server._baseurl}{plex_episode.thumb}'
            f'?X-Plex-Token={self.__token}'
        )


    @catch_and_log('Error getting Series poster')
    def get_series_poster(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> SourceImage:
        """
        Get the poster for the given Series.

        Args:
            library_name: Name of the library the series is under.
            series_info: The series to get the poster of.
            log: Logger for all log messages.

        Returns:
            URL to the poster for the given series. None if the library,
            series, or thumbnail cannot be found.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return None

        return series.thumbUrl


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
            filepath: Path,
        ) -> None:
        """
        Upload the given poster to the given Episode, retrying if it fails.

        Args:
            plex_object: The plexapi object to upload the file to.
            filepath: Filepath to the poster to upload.
        """

        plex_object.uploadPoster(filepath=filepath)
        plex_object.addLabel(['TCM'])


    def __add_exif_tag(self, card: Path) -> None:
        """
        Add an EXIF tag to the given Card file. This adds "titlecard" at
        0x4242, and overwrites the existing file.

        Args:
            card: Path to the Card file to modify.
        """

        # Create Image object, read EXIF data
        card_image = Image.open(card)
        exif = card_image.getexif()

        # Add EXIF data, write modified file
        exif[self.EXIF_TAG['key']] = self.EXIF_TAG['data']
        card_image.save(card.resolve(), exif=exif)


    @catch_and_log('Error uploading title cards')
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
        """

        # No episodes to load, exit
        if len(episode_and_cards) == 0:
            log.debug(f'No episodes to load for {series_info}')
            return []

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return []

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return []

        # Go through each episode within Plex, set title cards
        loaded = []
        for plex_episode in series.episodes(container_size=500):
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
            # pylint: disable=undefined-loop-variable
            if (image := self.compress_image(card.card_file, log=log)) is None:
                continue

            # Upload card to Plex, optionally remove Overlay label
            try:
                # If integrating with PMM, add EXIF data
                if self.integrate_with_pmm:
                    self.__add_exif_tag(image)

                # Upload card
                self.__retry_upload(plex_episode, image.resolve())

                # If integrating with PMM, remove label
                if self.integrate_with_pmm:
                    plex_episode.removeLabel(['Overlay'])
                log.debug(f'{series_info} S{plex_episode.seasonNumber:02}E'
                          f'{plex_episode.episodeNumber:02} Loaded Card into '
                          f'"{library_name}"')
            except Exception as e:
                log.exception(f'Unable to upload {image.resolve()} to '
                              f'{series_info}', e)
                continue
            else:
                loaded.append((episode, card))

        return loaded


    @catch_and_log('Error getting rating key details')
    def get_episode_details(self,
            rating_key: int,
            *,
            log: Logger = log,
        ) -> list[EpisodeDetails]:
        """
        Get all details for all episodes indicated by the given Plex
        rating key.

        Args:
            rating_key: Rating key used to fetch the item within Plex.
            log: Logger for all log messages.

        Returns:
            List of tuples of the SeriesInfo, EpisodeInfo, and the watch
            status corresponding to the given rating key. If the object
            associated with the rating key is a show or season, then all
            contained episodes are detailed. An empty list is returned
            if the item(s) associated with the given key cannot be
            found.
        """

        try:
            # Get the entry for this key
            entry = self.__server.fetchItem(rating_key)

            # Show, return all episodes in series
            if entry.type == 'show':
                entry: PlexShow
                series_info = SeriesInfo.from_plex_show(entry)
                return [EpisodeDetails(
                    series_info,
                    EpisodeInfo.from_plex_episode(ep),
                    WatchedStatus(
                        self._interface_id,
                        entry.librarySectionTitle, # entry.parent TODO evaluate
                        ep.isWatched,
                    )
                ) for ep in entry.episodes()]

            # Season, return all episodes in season
            if entry.type == 'season':
                entry: PlexSeason
                series: PlexShow = self.__server.fetchItem(entry.parentRatingKey)
                series_info = SeriesInfo.from_plex_show(series)
                return [EpisodeDetails(
                    series_info,
                    EpisodeInfo.from_plex_episode(ep),
                    WatchedStatus(
                        self._interface_id,
                        ep.librarySectionTitle, # TODO double check
                        ep.isWatched,
                    ),
                ) for ep in entry.episodes()]

            # Episode, return just that
            if entry.type == 'episode':
                entry: PlexEpisode
                series: PlexShow = self.__server.fetchItem(entry.grandparentRatingKey)
                series_info = SeriesInfo.from_plex_show(series)
                return [EpisodeDetails(
                    series_info,
                    EpisodeInfo.from_plex_episode(entry),
                    WatchedStatus(
                        self._interface_id,
                        entry.librarySectionTitle, # TODO double check
                        entry.isWatched,
                    ),
                )]

            log.warning(f'Item with rating key {rating_key} has no episodes')
            return []
        except NotFound:
            log.warning(f'No item with rating key {rating_key} exists')
        except (ValueError, AssertionError):
            log.warning(f'Item with rating key {rating_key} has no year')
        except Exception as e:
            log.exception(f'Rating key {rating_key} has some error', e)

        # Error occurred, return empty list
        return []


    @catch_and_log('Error removing Series labels')
    def remove_series_labels(self,
            library_name: str,
            series_info: SeriesInfo,
            labels: list[str] = ['TCM', 'Overlay'],
            *,
            log: Logger = log,
        ) -> None:
        """
        Remove the given labels from all Episodes of the associated
        Series.

        Args:
            library_name: Name of the library containing the series.
            series_info: SeriesInfo whose Episodes' labels are being
                removed.
            labels: List of labels to remove.
            log: Logger for all log messages.
        """

        # Exit if no labels to remove
        if len(labels) == 0:
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return None

        # Remove labels from all Episodes
        for plex_episode in series.episodes(container_size=500):
            plex_episode: PlexEpisode
            log.debug(f'Removed {labels} from {plex_episode.labels} of {plex_episode}')
            plex_episode.removeLabel(labels)

        return None
