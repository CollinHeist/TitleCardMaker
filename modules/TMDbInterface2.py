from datetime import datetime, timedelta
from typing import Any, Callable, Optional, Union

from fastapi import HTTPException
from tmdbapis import (
    Poster,
    TMDbAPIs,
    NotFound,
    TMDbException,
    TMDbImage,
    Unauthorized,
)
from tmdbapis.objs.reload import Episode as TMDbEpisode, Movie as TMDbMovie
from tmdbapis.objs.image import Still as TMDbStill

from modules.Debug import Logger, log
from modules.EpisodeDataSource2 import (
    EpisodeDataSource,
    SearchResult,
    WatchedStatus
)
from modules.EpisodeInfo2 import EpisodeInfo
from modules.Interface import Interface
from modules.SeriesInfo2 import SeriesInfo
from modules.WebInterface import WebInterface


def catch_and_log(
        message: str,
        *,
        default: Any = None,
    ) -> Callable:
    """
    Return a decorator that logs the given message if the decorated
    function raises an uncaught TMDbException. This utilizes the
    wrapped function's contextual logger if that's provided as the
    `log` keyword.

    Args:
        message: Message to log upon uncaught exception.
        default: Value to return if decorated function raises an
            uncaught exception.

    Returns:
        Wrapped decorator that returns a wrapped callable.
    """

    def decorator(function: Callable) -> Callable:
        def inner(*args, **kwargs) -> Any:
            try:
                return function(*args, **kwargs)
            except TMDbException:
                # Get contextual logger if provided as argument to function
                if ('log' in kwargs
                    and hasattr(kwargs['log'], 'error')
                    and callable(kwargs['log'].error)):
                    clog = kwargs['log']
                else:
                    clog = log

                # Log message and exception
                clog.error(message)
                clog.exception(f'TMDbException from {function.__name__}'
                                f'({args}, {kwargs})')
                return default

        return inner
    return decorator


class DecoratedAPI:
    """
    A purely transparent object which decorates all function calls to
    the initializing API object and catches all exceptions. NotFound and
    TMDbExceptions are re-raised, and all other Exceptions are logged
    and then raised under the guide of a TMDbException.

    The intention of this class is to handle uncaught API errors while
    not catching all exceptions within the `catch_and_log` decorator.
    """

    def __init__(self, api: TMDbAPIs) -> None:
        """Initialize this decorated object with the given instance."""

        self.api = api


    def __getattr__(self, function: str) -> Callable:
        """
        Get an arbitrary function for this object. This returns a
        wrapped version of the given function that catches any uncaught
        Exceptions, logs them, and then raises them as an
        `TMDbException`.

        Args:
            function: The function to wrap.

        Returns:
            Wrapped callable.
        """

        def wrapper(*args, **kwargs):
            try:
                return getattr(self.api, function)(*args, **kwargs)
            except (NotFound, TMDbException) as exc:
                raise exc
            except Exception as exc:
                # Get contextual logger if provided as argument to function
                if 'log' in kwargs and hasattr(kwargs['log'], 'debug'):
                    clog = kwargs['log']
                else:
                    clog = log

                # Log message and exception
                clog.debug(f'Uncaught Exception from {function}'
                                f'({args}, {kwargs})', exc)
                raise TMDbException from exc

        return wrapper


class TMDbInterface(EpisodeDataSource, WebInterface, Interface):
    """
    This class defines an interface to TheMovieDatabase (TMDb). Once
    initialized  with a valid API key, the primary purpose of this class
    is to communicate with TMDb.
    """

    INTERFACE_TYPE: str = 'TMDb'

    """Default for how many failed requests lead to a blacklisted entry"""
    BLACKLIST_THRESHOLD = 5

    """Series ID's that can be set by TMDb"""
    SERIES_IDS = ('imdb_id', 'tmdb_id', 'tvdb_id', 'tvrage_id')

    """Language codes"""
    LANGUAGES = {
        'ar': 'Arabic',
        'ar-AE': 'Arabic (United Arab Emirates)',
        'ar-SA': 'Arabic (Saudi Arabian)',
        'bg': 'Bulgarian',
        'ca': 'Catalan',
        'cn-CN': 'Cantonense',
        'cs': 'Czech',
        'da': 'Danish',
        'de-AT': 'German (Austria)',
        'de-CH': 'German (Switzerland)',
        'de-DE': 'German (Germany)',
        'el': 'Greek',
        'en': 'English',
        'es-ES': 'Spanish (Spain)',
        'es-MX': 'Spanish (Mexico)',
        'fa': 'Persian',
        'fi': 'Finnish',
        'fr-CA': 'French (Canada)',
        'fr-FR': 'French (France)',
        'he': 'Hebrew',
        'hi': 'Hindi',
        'hu': 'Hungarian',
        'id': 'Indonesian',
        'it-IT': 'Italian',
        'it-CH': 'Italian (Switzerland)',
        'ja': 'Japanese',
        'ka': 'Georgian',
        'ko': 'Korean',
        'lb': 'Luxembourgish',
        'lt': 'Lithuanian',
        'lv': 'Latvian',
        'my': 'Burmese',
        'nb-NO': 'Norwegian (Bokmål)',
        'nl-BE': 'Dutch (Belgium)',
        'nl-NL': 'Dutch (Netherlands)',
        'nn-NO': 'Norwegian (Nynorsk)',
        'ms-BN': 'Malay (Brunei Darussalam)',
        'ms-MY': 'Malay (Malaysia)',
        'ms-SG': 'Malay (Singapore)',
        'no': 'Norwegian',
        'pl': 'Polish',
        'pt-BR': 'Portuguese (Brazil)',
        'pt-PT': 'Portuguese (Portugal)',
        'ro': 'Romanian',
        'ru': 'Russian',
        'sk': 'Slovak',
        'sr-RS': 'Serbian',
        'sv-FI': 'Swedish (Findland)',
        'sv-SE': 'Swedish (Sweden)',
        'th': 'Thai',
        'tr': 'Turkish',
        'uk': 'Ukrainian',
        'uz-UZ': 'Uzbek',
        'vi': 'Vietnamese',
        'zh': 'Chinese (Simplified)',
        'zh-CN': 'Chinese (Simplified, Mainland China)',
        'zh-HK': 'Chinese (Hong Kong)',
        'zh-SG': 'Chinese (Singapore)'
    }
    LANGUAGE_CODES = tuple(LANGUAGES.keys())

    """Generic translated episode format strings for each language code"""
    GENERIC_TITLE_FORMATS = {
        'ar': r'الحلقة {number}',
        'bs': r'Episode {number}',
        'cs': r'{number}. epizoda',
        'de': r'Episode {number}',
        'de-AT': r'Episode {number}',
        'de-CH': r'Episode {number}',
        'de-DE': r'Episode {number}',
        'el': r'Επεισόδιο {number}',
        'en': r'Episode {number}',
        'en-US': r'Episode {number}',
        'es-ES': r'Episodio {number}',
        'es-MX': r'Episodio {number}',
        'fi': r'Jakso {number}',
        'fr': r'Épisode {number}',
        'fr-CA': r'Épisode {number}',
        'fr-FR': r'Épisode {number}',
        'he': r'פרק {number}',
        'hi': r'Episode {number}',
        'hu': r'{number}. epizód',
        'id': r'Episode {number}',
        'it': r'Episodio {number}',
        'it-IT': r'Episodio {number}',
        'it-CH': r'Episodio {number}',
        'ja': r'第{number}話',
        'ka': r'Episode {number}',
        'ko': r'에피소드 {number}',
        'lb': r'Episode {number}',
        'lt': r'Epizodas {number}',
        'lv': r'Epizode {number}',
        'ms-BN': r'Episode {number}',
        'ms-MY': r'Episode {number}',
        'ms-SG': r'Episode {number}',
        'nl': r'Aflevering {number}',
        'nl-BE': r'Aflevering {number}',
        'nl-NL': r'Aflevering {number}',
        'nn-NO': r'Episode {number}',
        'no': r'Episode {number}',
        'pl': r'Odcinek {number}',
        'pt': r'Episódio {number}',
        'pt-BR': r'Episódio {number}',
        'pt-PT': r'Episódio {number}',
        'ro': r'Episodul {number}',
        'ru': r'Эпизод {number}',
        'sk': r'Epizóda {number}',
        'sr-RS': r'Епизода {number}',
        'sv-FI': r'Avsnitt {number}',
        'sv-SE': r'Avsnitt {number}',
        'th': r'Episode {number}',
        'tr': r'{number}. Bölüm',
        'uk': r'Серія {number}',
        'uz-UZ': r'Episode {number}',
        'vi': r'Episode {number}',
        'zh': r'第 {number} 集',
    }

    """Filename for where to store blacklisted entries"""
    __BLACKLIST_DB = 'tmdb_blacklist.json'


    def __init__(self,
            api_key: str,
            minimum_source_width: int = 0,
            minimum_source_height: int = 0,
            language_priority: list[str] = ['en'],
            *,
            interface_id: int = 0,
            log: Logger = log,
        ) -> None:
        """
        Construct a new instance of an interface to TMDb.

        Args:
            api_key: The API key to communicate with TMDb.
            minimum_source_width: Minimum width (in pixels) required for
                source images.
            minimum_source_height: Minimum height (in pixels) required
                for source images.
            language_priority: Priority which localized should be
                evaluated at.
            log: Logger for all log messages.

        Raises:
            HTTPException (401): The API key is invalid.
        """

        super().__init__('TMDb', log=log)

        # Store attributes
        self.minimum_source_width = minimum_source_width
        self.minimum_source_height = minimum_source_height
        self.language_priority = language_priority
        self._interface_id = interface_id

        # Create API object, validate key
        try:
            self.api: TMDbAPIs = DecoratedAPI(TMDbAPIs(api_key, self.session))
        except Unauthorized as exc:
            log.critical('TMDb API key is invalid')
            raise HTTPException(
                status_code=401,
                detail='Invalid API Key'
            ) from exc

        self.activate()


    def __sort_asset(self, asset: TMDbImage) -> float:
        """
        Get the sort "score" for the given asset. This can be used in a
        `sorted()` call.

        Args:
            asset: Object being sorted. Must be a subclass of
                `TMDbImage`.

        Returns:
            Sorted score for the object. Higher score indicates a higher
            quality asset.
        """

        # Score dimensionally 0 -> 2.0 @ 4K resolution
        dimension_score: float = (asset.width / 3840) + (asset.height / 2160)

        # Textless posters get scored as neutral priority
        if asset.iso_639_1 is None:
            return dimension_score

        # Give priority scoring to languages in the priority list
        try:
            # Reverse list so first elements get higher index
            lang_score = self.language_priority[::-1].index(asset.iso_639_1)
            return (lang_score * 10) + dimension_score
        # Languages not in the priority list use a negative modifier
        except ValueError:
            return -10 + dimension_score


    @catch_and_log('Error setting series ID')
    def set_series_ids(self,
            library_name: Any,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> None:
        """
        Set all possible series ID's for the given SeriesInfo object.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo to update.
            log: Logger for all log messages.
        """

        # If all possible ID's are defined
        if series_info.has_ids(*self.SERIES_IDS):
            return None

        # Try and find by TMDb ID first
        found = False
        if not found and series_info.tmdb_id:
            try:
                results = [self.api.tv_show(series_info.tmdb_id)]
                found = True
            except NotFound:
                pass

        # Find by TVDb ID
        if not found and series_info.tvdb_id:
            try:
                results = self.api.find_by_id(
                    tvdb_id=series_info.tvdb_id
                ).tv_results
                found = len(results) > 0
            except NotFound:
                pass

        # Find by IMDb ID
        if not found and series_info.imdb_id:
            try:
                results = self.api.find_by_id(
                    imdb_id=series_info.imdb_id
                ).tv_results
                found = len(results) > 0
            except NotFound:
                pass

        # Find by TVRage ID
        if not found and series_info.tvrage_id:
            try:
                results = self.api.find_by_id(
                    tvrage_id=series_info.tvrage_id
                ).tv_results
                found = len(results) > 0
            except NotFound:
                pass

        # Find by series name + year
        if not found:
            try:
                # Search by name+year, and exclude adult content
                results = self.api.tv_search(
                    series_info.name, False, series_info.year
                )
                found = results.total_results > 0
            except NotFound:
                pass

        # If found, update TMDb, IMDb, TVDb, and TVRage ID's
        if found:
            result = results[0]
            series_info.set_tmdb_id(int(result.id))
            if (imdb_id := result.imdb_id):
                series_info.set_imdb_id(imdb_id)
            if (tvdb_id := result.tvdb_id):
                series_info.set_tvdb_id(tvdb_id)
            if (tvrage_id := result.tvrage_id):
                series_info.set_tvrage_id(tvrage_id)
        else:
            log.warning(f'Series "{series_info}" not found on TMDb')

        return None


    @catch_and_log('Error querying for series', default=[])
    def query_series(self,
            query: str,
            *,
            log: Logger = log,
        ) -> list[SearchResult]:
        """
        Search TMDb for any Series matching the given query.

        Args:
            query: Series name or substring to look up.
            log: Logger for all log messages.

        Returns:
            List of SearchResults for the given query.
        """

        try:
            results = self.api.tv_search(query).results
            if not results:
                raise NotFound
        except NotFound:
            log.debug(f'No results found for {query}')
            return []

        return [
            SearchResult(
                name=result.name,
                year=result.first_air_date.year,
                poster=result.poster_url,
                overview=result.overview,
                ongoing=result.in_production,
                imdb_id=result.imdb_id,
                tmdb_id=result.id,
                tvdb_id=result.tvdb_id,
            )
            for result in results if result.first_air_date
        ]


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
            library_name: Unused argument.
            series_info: Series to get the episodes of.
            log: Logger for all log messages.

        Returns:
            List of EpisodeInfo objects and None (as watched statuses
            cannot be determined) for this series.
        """

        # Cannot query TMDb if no series TMDb ID
        if series_info.tmdb_id is None:
            log.error(f'Cannot source episodes from TMDb for {series_info}')
            return []

        # Get all seasons on TMDb
        try:
            seasons = self.api.tv_show(series_info.tmdb_id).seasons
            if not seasons:
                raise NotFound
        except NotFound:
            log.error(f'Cannot source episodes from TMDb for {series_info}')
            return []

        # Go through each season, getting episodes from each
        all_episodes = []
        for season in seasons:
            # Load episodes, now iterate through them
            season.reload()
            for episode in season.episodes:
                # Skip episodes until they've aired
                if (episode.air_date is not None
                    and episode.air_date > datetime.now()):
                    continue

                # Create a new EpisodeInfo
                try:
                    episode.reload()
                except NotFound:
                    log.exception(f'TMDb error - skipping {episode}')
                    continue

                episode_info = EpisodeInfo(
                    episode.name,
                    season.season_number,
                    episode.episode_number,
                    tmdb_id=episode.id,
                    tvdb_id=episode.tvdb_id if episode.tvdb_id != 0 else None,
                    imdb_id=None if episode.imdb_id is None else episode.imdb_id,
                    airdate=episode.air_date,
                )

                # Create EpisodeInfo for this episode, add to list
                all_episodes.append((
                    episode_info,
                    WatchedStatus(self._interface_id)
                ))

        return all_episodes


    def __find_episode(self,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            title_match: bool = True,
            *,
            log: Logger = log
        ) -> Optional[Union[TMDbEpisode, TMDbMovie]]:
        """
        Finds the episode index for the given entry. Searching is done
        in the following priority:

        1. Episode TVDb ID
        2. Episode IMDb ID (as episode)
        3. Episode TVRage ID
        4. Episode IMDb ID (as movie)
        5. Episode title as movie (if no series TMDb ID is present)
        6. Series TMDb ID and season+episode index with title match
        7. Series TMDb ID and season+absolute episode index with title
        match
        8. Series TMDb ID and fuzzy title match on any episode

        Args:
            series_info: The series information.
            episode_info: The episode information.
            title_match: Whether to require the title within
                episode_info to match the title on TMDb.
            log: Logger for all log messages.

        Returns:
            Dictionary of the index for the given entry. This dictionary
            has keys 'season' and 'episode'. None if returned if the
            entry cannot be found.
        """

        exception_group = (AttributeError, NotFound, IndexError, TMDbException)

        # Query with TVDb ID first
        if episode_info.tvdb_id is not None:
            try:
                results = self.api.find_by_id(tvdb_id=episode_info.tvdb_id)
                (episode := results.tv_episode_results[0]).reload()
                return episode
            except exception_group:
                pass

        # Query with IMDb ID
        if episode_info.imdb_id is not None:
            try:
                results = self.api.find_by_id(imdb_id=episode_info.imdb_id)
                # Check for an episode, then check for a movie
                if len(results.tv_episode_results) > 0:
                    (episode := results.tv_episode_results[0]).reload()
                elif len(results.movie_results) > 0:
                    (episode := results.movie_results[0]).reload()
                else:
                    raise NotFound
                return episode
            except exception_group:
                pass

        # Query with TVRage ID
        if episode_info.tvrage_id is not None:
            try:
                results = self.api.find_by_id(tvrage_id=episode_info.tvrage_id)
                # Check for an episode, then check for a movie
                if len(results.tv_episode_results) > 0:
                    (episode := results.tv_episode_results[0]).reload()
                elif len(results.movie_results) > 0:
                    (episode := results.movie_results[0]).reload()
                else:
                    raise NotFound
                return episode
            except exception_group:
                pass

        # Search for movie with this episode title
        def _find_episode_as_movie(
                episode_info: EpisodeInfo
            ) -> Optional[TMDbMovie]:
            """Attempt to find the given Episode as a Movie"""

            try:
                # Search for movies with this title
                results = self.api.movie_search(episode_info.title)
                (movie := results[0]).reload()

                # Check for TMDb ID match
                id_match = (episode_info.has_id('tmdb_id')
                            and episode_info.tmdb_id == movie.id)

                # Check for title match
                title_match = episode_info.full_title.matches(
                    movie.title,*(alt.title for alt in movie.alternative_titles)
                )

                # Verify release date match +/- 1 day
                release_date = movie.release_date
                release_date_match = (
                    episode_info.airdate is not None
                    and release_date is not None
                    and (episode_info.airdate - timedelta(days=1)
                         <= release_date
                         <= episode_info.airdate + timedelta(days=1))
                )
                if not id_match and not (title_match and release_date_match):
                    raise NotFound

                # Actual match, return "movie"
                log.trace(f'Matched {episode_info} of "{series_info}" to TMDb '
                          f'Movie {movie}')
                return movie
            except exception_group:
                return None

        # If series TMDb ID is not present, try as movie, no other attempts
        if not series_info.tmdb_id is not None:
            return _find_episode_as_movie(episode_info)

        # Verify series ID is valid
        try:
            series = self.api.tv_show(series_info.tmdb_id)
        except (NotFound, TMDbException):
            return None

        def _match_by_index(
                episode_info: EpisodeInfo,
                season_number: int,
                episode_number: int
            ) -> Optional[TMDbEpisode]:
            # Find episode with series TMDb ID and given index
            try:
                (episode := self.api.tv_episode(
                    series_info.tmdb_id, season_number, episode_number
                )).reload()
            except (NotFound, TMDbException):
                return None

            # If TMDb ID matches, or title matches
            id_match = (episode_info.has_id('tmdb_id')
                        and episode_info.tmdb_id == episode.id)
            does_match = (not title_match or (title_match and
                          episode_info.full_title.matches(episode.name)))
            return episode if id_match or does_match else None

        # Try and match by index
        indices = episode_info.season_number, episode_info.episode_number
        if (episode := _match_by_index(episode_info, *indices)) is not None:
            episode.reload()
            return episode

        # Match by absolute number
        if episode_info.absolute_number is not None:
            # Try for this season
            indices = episode_info.season_number, episode_info.absolute_number
            if (ep := _match_by_index(episode_info, *indices)) is not None:
                ep.reload()
                return ep

            # Try for all seasons
            for season in series.seasons:
                indices = season.season_number, episode_info.absolute_number
                if (ep := _match_by_index(episode_info, *indices)) is not None:
                    ep.reload()
                    return ep

        # If title match is disabled, cannot identify
        if not title_match:
            return _find_episode_as_movie(episode_info)

        # Try every episode
        for season in series.seasons:
            season.reload()
            for episode in season.episodes:
                if ((episode_info.tmdb_id and episode_info.tmdb_id == episode.id)
                    or episode_info.full_title.matches(episode.name)):
                    episode.reload()
                    return episode

        return _find_episode_as_movie(episode_info)


    @catch_and_log('Error setting episode IDs')
    def set_episode_ids(self,
            library_name: Any,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
            *,
            log: Logger = log,
        ) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo
        objects. For TMDb, this does nothing, as TMDb cannot provide any
        useful episode ID's.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo for the entry.
            infos: List of EpisodeInfo objects to update.
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


    def __determine_best_image(self,
            images: list[TMDbStill],
            *,
            is_source_image: bool = True,
            skip_localized: bool = False,
        ) -> Optional[TMDbStill]:
        """
        Determine the best image and return it's contents from within
        the database return JSON.

        Args:
            images: The results from the database. Each entry is a new
                image to be considered.
            is_source_image: (Keyword only) Whether the images being
                selected are source images or not. If True, then images
                must meet the minimum resolution requirements.
            skip_localized: (Keyword only) Whether to skip localized
                images.

        Args:
            The "best" image for title card creation. This is determined
            using the images dimensions. Priority given to largest
            image. None if there are no valid images.
        """

        # Pick the best image based on image dimensions, and then vote average
        best_image = {'index': 0, 'pixels': 0, 'score': 0}
        valid_image = False
        for index, image in enumerate(images):
            # Get image dimensions
            width, height = image.width, image.height

            # If source image selection, check dimensions and localization
            if is_source_image:
                if (width < self.minimum_source_width
                    or height < self.minimum_source_height):
                    continue
                if skip_localized and image.iso_639_1 is not None:
                    continue

            # If the image has valid dimensions,get pixel count and vote average
            valid_image = True
            pixels = height * width
            score = image.vote_average

            # Priority 1 is image size, priority 2 is vote average/score
            if (pixels > best_image['pixels'] or (pixels == best_image['pixels']
                and score > best_image['score'])):
                best_image = {'index': index, 'pixels': pixels, 'score': score}

        return images[best_image['index']] if valid_image else None


    @catch_and_log('Error getting all source images', default=[])
    def get_all_source_images(self,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            *,
            match_title: bool = True,
            log: Logger = log,
        ) -> list[TMDbStill]:
        """
        Get all source images for the requested entry.

        Args:
            series_info: SeriesInfo for this entry.
            episode_info: EpisodeInfo for this entry.
            match_title:  Whether to require the episode title
                to match when querying TMDb.
            log: Logger for all log messages.

        Returns:
            List of tmdbapis.objs.image.Still objects. If the episode is
            not found on TMDb, then an empty list is returned.

        Raises:
            HTTPException (404): The given Series+Episode is not found
                on TMDb.
        """

        # Get Episode object for this episode
        episode = self.__find_episode(
            series_info, episode_info, match_title, log=log,
        )
        if episode is None:
            raise HTTPException(
                status_code=404,
                detail=f'"{series_info}" {episode_info} not found on TMDb'
            )

        # Episode found on TMDb, get images/backdrops based on episode/movie
        if hasattr(episode, 'stills'):
            images = episode.stills
        else:
            images = episode.backdrops

        return images # type: ignore


    @catch_and_log('Error getting all logos', default=None)
    def get_all_logos(self,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> Optional[list[TMDbStill]]:
        """
        Get all logos for the requested series.

        Args:
            series_info: SeriesInfo for this entry.
            log: Logger for all log messages.

        Returns:
            List of `tmdbapis.objs.image.Still` objects. If the series
            is not found on TMDb, then None is returned.

        Raises:
            HTTPException (404) if the given Series is not found on TMDb
        """

        # Get the series for this logo, exit if series or logos DNE
        try:
            if not series_info.tmdb_id:
                raise NotFound
            series = self.api.tv_show(series_info.tmdb_id)
        except NotFound:
            log.debug(f'Series {series_info} not found on TMDb')
            return None

        # Blacklist if there are no logos
        if len(series.logos) == 0:
            log.info(f'Series {series_info} has no logos')
            return None

        # Series found on TMDb, return all logos (sorted by quality)
        return sorted(series.logos, key=self.__sort_asset, reverse=True)


    @catch_and_log('Error getting all backdrops', default=None)
    def get_all_backdrops(self,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> Optional[list[TMDbStill]]:
        """
        Get all backdrops for the requested series.

        Args:
            series_info: SeriesInfo for this entry.
            log: Logger for all log messages.

        Returns:
            List of `tmdbapis.objs.image.Still` objects. If the series
            is not found on TMDb, then None is returned.

        Raises:
            HTTPException (404) if the given Series is not found on TMDb
        """

        # Get the series, exit if series or backdrops DNE
        try:
            if not series_info.tmdb_id:
                raise NotFound
            series = self.api.tv_show(series_info.tmdb_id)
        except NotFound as exc:
            raise HTTPException(
                status_code=404,
                detail=f'Series {series_info} not found on TMDb',
            ) from exc

        # Blacklist if there are no backdrops
        if len(series.backdrops) == 0:
            log.info(f'Series {series_info} has no backdrops')
            return []

        # Series found on TMDb, return all backdrops
        return series.backdrops


    @catch_and_log('Error getting source image', default=None)
    def get_source_image(self,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            *,
            match_title: bool = True,
            skip_localized_images: bool = False,
            raise_exc: bool = True,
            log: Logger = log,
        ) -> Optional[str]:
        """
        Get the best source image for the requested entry.

        Args:
            series_info: SeriesInfo for this entry.
            episode_info: EpisodeInfo for this entry.
            match_title:  Whether to require the episode title
                to match when querying TMDb.
            skip_localized_images: Whether to skip images with
                a non-null language code - i.e. skipping localized
                images.
            raise_exc: Whether to raise any HTTPExceptions that arise.
            log: Logger for all log messages.

        Returns:
            URL to the 'best' source image for the requested entry. None
            if no images are available.
        """

        # Get all images for this episode
        try:
            all_images = self.get_all_source_images(
                series_info, episode_info, match_title=match_title, log=log,
            )
        # Some error occurred, raise if indicated, otherwise return None
        except HTTPException as exc:
            if raise_exc:
                raise exc
            return None

        # Exit if no images for this Episode
        if not all_images:
            log.debug(f'TMDb has no images for "{series_info}" {episode_info}')
            return None

        # Get the best image for this Episode
        log.trace(f'TMDb has {len(all_images)} images for "{series_info}" '
                  f'{episode_info}')
        kwargs = {
            'is_source_image': True,
            'skip_localized':skip_localized_images
        }
        if (best_image := self.__determine_best_image(all_images, **kwargs)):
            return best_image.url

        log.debug(f'TMDb images for "{series_info}" {episode_info} do not meet '
                  f'dimensional requirements')
        return None


    def __is_generic_title(self,
            title: str,
            language_code: str,
            episode_info: EpisodeInfo,
        ) -> bool:
        """
        Determine whether the given title is a generic translation of
        "Episode (x)" for the indicated language.

        Args:
            title: The translated title.
            language_code: The language code of the translation.
            episode_info: The EpisodeInfo for this title.

        Returns:
            True if the title is a generic translation, False otherwise.
        """

        # Assume non-generic if the code isn't pre-mapped
        if not (generic := self.GENERIC_TITLE_FORMATS.get(language_code, None)):
            return False

        # Format with this episode, return whether this matches the translation
        if episode_info.absolute_number is not None:
            # Check against episode and absolute number
            return title in (
                generic.format(number=episode_info.episode_number),
                generic.format(number=episode_info.absolute_number),
            )

        # Only check against episode number (no absolute)
        return title == generic.format(number=episode_info.episode_number)


    @catch_and_log('Error getting episode title', default=None)
    def get_episode_title(self,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            language_code: str = 'en-US',
            *,
            log: Logger = log,
        ) -> Optional[str]:
        """
        Get the episode title for the given entry for the given language.

        Args:
            series_info: SeriesInfo for the entry.
            episode_info: EpisodeInfo for the entry.
            language_code: The language code for the desired title.
            log: Logger for all log messages.

        Args:
            The episode title, None if it cannot be found.
        """

        # Get episode
        episode = self.__find_episode(series_info, episode_info, log=log)
        if episode is None:
            log.debug(f'{series_info} {episode_info} not found - skipping')
            return None

        # Parse the ISO-3166-1 and ISO-639-1 codes from the given language code
        if '-' in language_code:
            lc_639, lc_3166 = language_code.split('-', maxsplit=1)
            lc_3166 = lc_3166.upper()
        else:
            lc_639, lc_3166 = language_code, None

        # Look for this translation
        for translation in episode.translations:
            if (lc_639 == translation.iso_639_1
                and (not lc_3166 or lc_3166 == translation.iso_3166_1)):
                # If the title translation is blank (i.e. non-existent)
                if hasattr(translation, 'name'):
                    title = translation.name
                else:
                    title = translation.title
                if not title:
                    break

                # If translation is generic, blacklist and skip
                if self.__is_generic_title(title, language_code, episode_info):
                    log.debug(f'Generic title "{title}" detected for '
                              f'{episode_info}')
                    return None

                return title

        return None


    @catch_and_log('Error getting series logo', default=None)
    def get_series_logo(self, series_info: SeriesInfo) -> Optional[str]:
        """
        Get the best logo for the given series.

        Args:
            series_info: Series to get the logo of.

        Returns:
            URL to the 'best' logo for the given series, and None if no
            images  are available.
        """

        # Get the series for this logo, exit if series or logos DNE
        try:
            if not series_info.tmdb_id:
                raise NotFound
            series = self.api.tv_show(series_info.tmdb_id)
        except NotFound:
            return None

        # Blacklist if there are no logos
        if len(series.logos) == 0:
            return None

        # Get the best logo
        best, best_priority = None, 999
        for logo in series.logos:
            # Skip logos with unindicated languages
            if logo.iso_639_1 not in self.language_priority:
                continue

            # Get relative priority of this logo's language
            priority = self.language_priority.index(logo.iso_639_1)

            # Skip this logo if the language priority is less than the current
            # best. Highest priority is index 0, so use > for lower priority
            if priority > best_priority:
                continue
            # New logo is higher priority, use always
            if priority < best_priority:
                best = logo
                best_priority = priority
            # Same priority, compare sizes
            elif priority == best_priority:
                # SVG logos are infinite size
                if logo.url.endswith('.svg') and not best.url.endswith('.svg'):
                    best = logo
                    best_priority = priority
                elif (best is None
                    or logo.width * logo.height > best.width * best.height):
                    best = logo
                    best_priority = priority

        # No valid image found, blacklist and exit
        if best is None:
            return None

        return best.url


    @catch_and_log('Error setting series backdrop', default=None)
    def get_series_backdrop(self,
            series_info: SeriesInfo,
            *,
            skip_localized_images: bool = False,
            raise_exc: bool = True
        ) -> Optional[str]:
        """
        Get the best backdrop for the given series.

        Args:
            series_info: Series to get the logo of.
            skip_localized_images: Whether to skip images with a non-
                null language code.
            raise_exc: Whether to raise any HTTPExceptions that arise.

        Returns:
            URL to the 'best' backdrop for the given series, and None if
            no  images are available.

        Raises:
            HTTPException (404): The Series is not found on TMDb.
        """

        # Get the series for this backdrop, exit if series or backdrop DNE
        try:
            if not series_info.tmdb_id:
                raise NotFound
            series = self.api.tv_show(series_info.tmdb_id)
        except NotFound as exc:
            if raise_exc:
                raise HTTPException(
                    status_code=404,
                    detail=f'"{series_info}" not found on TMDb'
                ) from exc
            return None

        # Blacklist if there are no backdrops
        if len(series.backdrops) == 0:
            return None

        # Find and return best image
        best_image = self.__determine_best_image(
            series.backdrops,
            is_source_image=True,
            skip_localized=skip_localized_images,
        )

        if best_image:
            return best_image.url

        return None


    @catch_and_log('Error getting series poster', default=None)
    def get_series_poster(self,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> Optional[str]:
        """
        Get the best poster for the given series.

        Args:
            series_info: Series to get the poster of.
            log: Logger for all log messages.

        Returns:
            URL to the 'best' poster for the given series, and None if
            no images are available.
        """

        # Get the series for this logo, exit if series or posters DNE
        try:
            if not series_info.tmdb_id:
                raise NotFound
            series = self.api.tv_show(series_info.tmdb_id)
        except NotFound:
            log.debug(f'Cannot find {series_info} on TMDb')
            return None

        posters: list[Poster] = series.posters
        if not posters:
            return None

        return sorted(
            series.posters,
            key=self.__sort_asset,
            reverse=True
        )[0].url
