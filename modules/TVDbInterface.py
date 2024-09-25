from datetime import datetime, timedelta
from typing import Any, Literal, Optional, TypedDict
from urllib.parse import quote as url_quote, urlencode

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
from modules.WebInterface import WebInterface


ArtType = Literal[
    'banner', 'poster', 'background', 'icon', 'season', 'clearart', 'logo'
]
LanguageCode = Literal[
    'ara', 'ces', 'dan', 'deu', 'ell', 'eng', 'fra', 'ita', 'kor', 'nld', 'pol',
    'por', 'pt', 'rus', 'spa', 'swe', 'tur', 'zho', 'zhtw',
]
OrderType = Literal[ # Called season-type in TVDb API docs
    'absolute', 'alternate', 'default', 'dvd', 'official', 'regional'
]
SourceName = Literal[
    'EIDR', 'Facebook', 'IMDB', 'Instagram', 'Official Website',
    'TheMovieDB.com', 'Twitter',
]

class TVDbRemoteID(TypedDict):
    id: str
    type: int
    sourceName: SourceName

class TVDbSearchResult(TypedDict):
    objectID: str
    aliases: list[str]
    country: str
    id: str
    image_url: str
    name: str
    first_air_time: str
    overview: str
    primary_language: str
    primary_type: Literal['movie', 'series']
    status: Literal['Continuing', 'Ended', 'Released', 'Upcoming']
    type: Literal['series']
    tvdb_id: str
    year: str
    slug: str
    overviews: dict[str, str]
    translations: dict[str, str]
    network: str
    remote_ids: list[TVDbRemoteID]
    thumbnail: str

class TVDbArtwork(TypedDict):
    id: int
    image: str
    thumbnail: str
    language: str
    type: int # 1: Banner, 2: Poster, 5: Square Icon, 23: Clear Logo
    score: int
    width: int
    height: int
    includesText: bool
    thumbnailWidth: int
    thumbnailHeight: int
    updatedAt: int
    status: dict
    tagOptions: None

# class TVDbSeriesArtwork(TypedDict):
#     id: int
#     name: str
#     slug: str
#     image: str
#     nameTranslations: list[str]
#     overviewTranslations: list[str]
#     aliases: list[dict[str, str]]
#     firstAired: str # yyyy-mm-dd
#     lastAired: str # yyyy-mm-dd
#     nextAired: str # yyyy-mm-dd
#     score: int
#     status: dict
#     originalCountry: str
#     originalLanguage: str
#     isOrderRandomized: bool
#     lastUpdated: str # yyyy-mm-dd hh:mm:ss
#     averageRuntime: int
#     episodes: None
#     overview: str
#     year: str
#     artworks: list[TVDbArtwork]

class TVDbEpisode(TypedDict):
    id: int
    seriesId: int
    name: str
    aired: str
    runtime: int
    nameTranslations: list[str]
    overview: str
    overviewTranslations: list[str]
    image: str
    imageType: int
    isMovie: Literal[0, 1]
    number: int
    seasonNumber: int
    lastUpdated: str
    finaleType: Optional[Literal['series']]
    year: str

class TVDbEpisodes(TypedDict):
    series: Any # TVDbSeries
    episodes: list[TVDbEpisode]


class TVDbInterface(EpisodeDataSource, WebInterface, Interface):
    """
    This class defines an interface to TheTV Database (TVDb). Once
    initialized  with a valid API key, the primary purpose of this class
    is to communicate with TVDb.
    """

    INTERFACE_TYPE: str = 'TVDb'

    """TVDb ID mappings for each type of artwork"""
    ARTWORK_TYPES: dict[ArtType, int] = {
        'banner': 1, 'poster': 2, 'background': 3, 'icon': 5, 'season': 7,
        'clearart': 22, 'logo': 23
    }

    """How episode airdates are written as strings"""
    EPISODE_AIRDATE_FORMAT = '%Y-%m-%d'

    """Series ID's that can be set by TMDb"""
    SERIES_IDS: set[str] = ('imdb_id', 'tmdb_id', 'tvdb_id')

    """Root URL of all API requests"""
    __ROOT_API_URL = 'https://api4.thetvdb.com/v4'

    """
    Auth tokens are valid for 1 month - per https://thetvdb.github.io/v4-api/).
    Refresh every 25 days to be sure
    """
    __TOKEN_DURATION = timedelta(days=25)


    def __init__(self,
            api_key: str,
            episode_ordering: OrderType = 'default',
            include_movies: bool = False,
            minimum_source_width: int = 0,
            minimum_source_height: int = 0,
            language_priority: list[LanguageCode] = ['eng'],
            *,
            interface_id: int = 0,
            log: Logger = log,
        ) -> None:
        """
        Construct a new instance of an interface to TVDb.

        Args:
            api_key: The API key to communicate with TVDb.
            episode_ordering: Which order of episode data to query.
            include_movies: Whether to include episodes which are movies
                in the episode data queries of this connection.
            minimum_source_width: Minimum width (in pixels) required for
                source images.
            minimum_source_height: Minimum height (in pixels) required
                for source images.
            language_priority: Priority which artwork should be
                evaluated at.
            log: Logger for all log messages.

        Raises:
            HTTPException (401): The API key is invalid.
        """

        super().__init__('TVDb', log=log)

        self.minimum_source_width = minimum_source_width
        self.minimum_source_height = minimum_source_height
        self.language_priority = language_priority
        self._interface_id = interface_id
        self._order_type: OrderType = episode_ordering
        self._include_movies = include_movies

        # Authenticate with TVDb, generate session token
        self.__api_key = api_key
        self.__token_expiration: Optional[datetime] = None
        self.__initialize_token(log=log) # This will initialize the interface


    def __generate_login_token(self, api_key: str, *, log: Logger = log) -> str:
        """
        Generate a login token which can be used for API requests with
        the given key.

        Args:
            api_key: The API key to communicate with TVDb.
            log: Logger for all log messages.

        Returns:
            Token which can be used in a simple OAuth `Bearer` field
            for API requests.

        Raises:
            Raises: HTTPException (401): The API key is invalid.
        """

        # Submit login request
        resp = self.session.post(
            url=f'{self.__ROOT_API_URL}/login',
            json={'apikey': api_key},
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            timeout=30,
        )
        json: dict = resp.json()

        if resp.status_code == 401:
            raise ValueError('API key is invalid')

        if (resp.status_code > 400
            or json.get('status') != 'success'
            or not json.get('data', {}).get('token')):
            log.debug(f'Authentication failed [{resp.status_code}] - {json}')
            raise ValueError('Unable to generate TVDb API token')

        return json['data']['token']


    def __initialize_token(self, *, log: Logger = log) -> None:
        """
        Initialize the session token for communicating with TVDb. This
        can also re-initialize an expired session. Once initialized,
        this sets this object's session headers to use the OAuth2 bearer
        token.

        Args:
            log: Logger for all log messages.

        Raises:
            HTTPException (401): The API key is invalid.
        """

        # Token has not yet expired, skip
        if (self.__token_expiration
            and datetime.now() > self.__token_expiration):
            return None

        # Token has expired, regenerate and update expiration
        try:
            token = self.__generate_login_token(self.__api_key, log=log)
            self.__token_expiration = datetime.now() + self.__TOKEN_DURATION
            self.activate()
        except ValueError:
            log.exception('Failed to authenticate with TVDb')
            self.active = False
            raise HTTPException(
                status_code=401,
                detail='Invalid API key',
            )

        # Set default headers on this object's session with new token
        self.session.headers = { # Pulled from tvdb_v4_official
            'Authorization': f'Bearer {token}',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }


    def __get_series_id(self, series_info: SeriesInfo) -> Optional[int]:
        """
        Get the TVDb ID of the given series. This looks up by database
        ID, if present, otherwise series name and year.

        Args:
            series_info: Series to search for.

        Returns:
            TVDb ID of the series. None if it cannot be found.
        """

        # If Series already has a TVDb ID, return
        if series_info.tvdb_id:
            return series_info.tvdb_id

        def _find(results: list[dict]) -> Optional[int]:
            """
            Search through the given results and return the TVDb ID of
            the first series.
            """

            if not isinstance(results, list):
                return None

            for result in results:
                if not isinstance(result, dict):
                    continue
                # Ignore movies
                if (id_ := result.get('series', {}).get('id')):
                    return id_

            return None

        # Search by IMDb or TMDb ID if present
        if series_info.has_id('imdb_id'):
            url = f'{self.__ROOT_API_URL}/search/remoteid/{series_info.imdb_id}'
            if (id_ := _find(self.get(url))):
                return id_
        if series_info.has_id('tmdb_id'):
            url = f'{self.__ROOT_API_URL}/search/remoteid/{series_info.tmdb_id}'
            if (id_ := _find(self.get(url))):
                return id_

        # Search by name and year
        params = urlencode({
            'query': series_info.name,
            'year': series_info.year,
            'type': 'series'
        })
        results: dict[list] = self.get(f'{self.__ROOT_API_URL}/search?{params}')
        if results.get('data'):
            return int(results.get('data')[0]['tvdb_id'])

        return None


    def __get_episode_id(self,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            *,
            log: Logger = log,
        ) -> Optional[int]:
        """
        Find the TVDb ID of the indicated episode.

        Args:
            series_info: Series associated with the given episode.
            episode_info: Episode whose ID is being queried.
            log: Logger for all log messages.

        Returns:
            TVDb ID of the indicated episode. None if the episode cannot
            be found.
        """

        if episode_info.tvdb_id:
            return episode_info.tvdb_id

        # Search by IMDb ID if present
        if episode_info.has_id('imdb_id'):
            url =f'{self.__ROOT_API_URL}/search/remoteid/{episode_info.imdb_id}'
            if isinstance((resp := self.get(url)), dict):
                for result in resp.get('data', []):
                    if (id_ := result.get('series', {}).get('id')):
                        return int(id_)
        # Cannot search episodes by TMDb ID for some reason; raises error
        # Cannot search by episode title; not supported via /search endpoint

        # If series has no TVDb ID, cannot identify episode
        if not (tvdb_id := self.__get_series_id(series_info)):
            return None

        # Generate query URL
        url = f'{self.__ROOT_API_URL}/series/{tvdb_id}/episodes/' \
            + f'{self._order_type}?season={episode_info.season_number}&' \
            + f'episodeNumber={episode_info.episode_number}'

        # Submit API request
        if not (results := self.get(url).get('data', {}).get('episodes')):
            log.debug(f'No associated episode {episode_info} on TVDb')
            return None

        return int(results[0]['id'])


    def __get_all_episodes(self, tvdb_id: int) -> list[TVDbEpisode]:
        """
        Get all the episodes (across all pages) for the series with the
        given TVDb ID.

        Args:
            tvdb_id: ID of the series whose episodes are being
                requested.

        Returns:
            List of all Episodes for the given series.
        """

        def _query_page(page: int, /) -> list[TVDbEpisode]:
            """Query the episodes on the given page number"""

            url = f'{self.__ROOT_API_URL}/series/{tvdb_id}/episodes' \
                + f'/{self._order_type}?page={page}'
            return self.get(url).get('data', {}).get('episodes', [])

        # Query first page of episodes
        page_number, last_length = 0, 0
        results = _query_page(page_number)

        # Default page size is 500; if an exact multiple of 500 episodes
        # were returned, query next page until no new episodes are
        # returned (in case there is an exact multiple of 500 episodes)
        while len(results) % 500 == 0 and len(results) != last_length:
            last_length = len(results)
            results += _query_page(page_number := page_number + 1)

        return results


    def __get_series_artwork(self,
            tvdb_id: int,
            language: str,
            art_type: ArtType,
        ) -> list[TVDbArtwork]:
        """
        Get all the artwork of the given type for the series with the
        given TVDb ID.

        Args:
            tvdb_id: TVDb ID of the series whose artwork is being
                requested.
            language: Language code of the artwork to request.
            art_type: Name of the type of art being requested.

        Returns:
            List of artwork.
        """

        url = f'{self.__ROOT_API_URL}/series/{tvdb_id}/artworks?lang={language}'

        return [
            art
            for art in self.get(url).get('data', {}).get('artworks')
            if art['type'] == self.ARTWORK_TYPES[art_type]
        ]


    def __get_best_artwork(self,
            tvdb_id: int,
            art_type: ArtType,
        ) -> Optional[str]:
        """
        Get the URL for the "best" artwork of the specified type.

        Args:
            tvdb_id: ID of the series whose artwork is being queried.
            art_type: Type of the artwork to query.

        Returns:
            URL to the highest resolution artwork of the specified type.
            None if there is no artwork.
        """

        artwork: list[TVDbArtwork] = []
        for language in self.language_priority:
            artwork += self.__get_series_artwork(tvdb_id, language, 'poster')

        if not artwork:
            log.debug(f'TVDb has no {art_type}s for TVDb {tvdb_id}')
            return None

        # Find best (valid) poster by pixel count, starting with the first one
        best = artwork[0]
        for art in artwork:
            if art['width'] * art['height'] > best['width'] * best['height']:
                best = art

        return best['image']


    def set_series_ids(self,
            library_name: str,
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

        # Exit if the series cannot be found on TVDb
        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return None
        series_info.set_tvdb_id(tvdb_id)

        # Use short mode so that characters and artwork are not returned
        remote_ids: list[TVDbRemoteID] = self.get(
            f'{self.__ROOT_API_URL}/series/{tvdb_id}/extended?short=true'
        ).get('data', {}).get('remoteIds', [])

        # Update any returned IDs
        for id_ in remote_ids:
            if id_['sourceName'] == 'IMDB':
                series_info.set_imdb_id(id_['id'])
            elif id_['sourceName'] == 'TheMovieDB.com':
                series_info.set_tmdb_id(id_['id'])

        return None


    def query_series(self,
            query: str,
            *,
            log: Logger = log,
        ) -> list[SearchResult]:
        """
        Search TVDb for any Series matching the given query.

        Args:
            query: Series name or substring to look up.
            log: Logger for all log messages.

        Returns:
            List of SearchResults for the given query.
        """

        results: list[TVDbSearchResult] = self.get(
            f'{self.__ROOT_API_URL}/search?query={url_quote(query)}'
        ).get('data', [])

        def _get_id(ids: list[TVDbRemoteID], source_name: str) -> Optional[str]:
            for id_ in ids:
                if id_['sourceName'] == source_name:
                    return id_['id']
            return None

        return [
            SearchResult(
                name=result['translations'].get('eng', result['name']),
                year=result['year'],
                poster=result['image_url'],
                overview=result.get('overview', 'No Overview'),
                ongoing=result.get('status') == 'Continuing',
                imdb_id=_get_id(result.get('remote_ids', []), 'IMDB'),
                tmdb_id=result['tvdb_id'],
            )
            for result in results
            if 'year' in result
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
            series_info: Series to get the episodes of.
            log: Logger for all log messages.

        Returns:
            List of EpisodeInfo objects and None (as watched statuses
            cannot be determined) for this series.
        """

        # Cannot query TVDb if no series TVDb ID
        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.error(f'Cannot source episodes from TVDb for {series_info}')
            return []

        return [
            (
                EpisodeInfo(
                    title=episode['name'],
                    season_number=episode['seasonNumber'],
                    episode_number=episode['number'],
                    absolute_number=episode['number'] if self._order_type == 'absolute' else None,
                    tvdb_id=episode['id'],
                    airdate=datetime.strptime(
                        episode['aired'], self.EPISODE_AIRDATE_FORMAT
                    ),
                ),
                WatchedStatus(self._interface_id)
            )
            for episode in self.__get_all_episodes(tvdb_id)
            if not episode['isMovie'] or self._include_movies
        ]


    def set_episode_ids(self,
            library_name: Any,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
            *,
            log: Logger = log,
        ) -> None:
        """
        Set all the ID's for the given list of EpisodeInfo objects. This
        can provide the IMDb, TMDb, or TVDb ID for each episode.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo for the entry.
            infos: List of EpisodeInfo objects to update.
            log: Logger for all log messages.
        """

        for episode_info in episode_infos:
            # Skip if has IMDb, TMDb, and TVDb IDs
            if episode_info.has_ids('imdb_id', 'tmdb_id', 'tvdb_id'):
                continue

            # Get and set the episode TVDb ID
            tvdb_id = self.__get_episode_id(series_info, episode_info, log=log)
            if tvdb_id is None:
                log.debug(f'Cannot find {series_info} {episode_info} on TVDb')
                continue
            episode_info.set_tvdb_id(tvdb_id)

            # Query extended info for this episode
            ids: list[TVDbRemoteID] = self.get(
                f'{self.__ROOT_API_URL}/episodes/{tvdb_id}/extended'
            ).get('data', {}).get('remoteIds', [])

            # Update all ID data for this episode
            for id_ in ids:
                if id_['sourceName'] == 'IMDB':
                    episode_info.set_imdb_id(id_['id'])
                elif id_['sourceName'] == 'TheMovieDB.com':
                    episode_info.set_tmdb_id(id_['id'])

        return None


    def get_all_logos(self,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> Optional[list[str]]:
        """
        Get all logos for the requested series.

        Args:
            series_info: SeriesInfo for this entry.
            log: Logger for all log messages.

        Returns:
            List of URLs of all logos corresponding to this Series. None
            if the Series cannot be found on TVDb.
        """

        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return None

        return [
            art['image']
            for language in self.language_priority
            for art in self.__get_series_artwork(tvdb_id, language, 'logo')
        ]


    def get_all_backdrops(self,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> Optional[list]:
        """
        Get all backdrops for the requested series.

        Args:
            series_info: SeriesInfo for this entry.
            log: Logger for all log messages.

        Returns:
            List of URLs to series backdrops. None if it cannot be
            found.
        """

        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return None

        return [
            art['image']
            for language in self.language_priority
            for art in self.__get_series_artwork(tvdb_id, language, 'background')
        ]


    def get_source_image(self,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            *,
            log: Logger = log,
        ) -> Optional[str]:
        """
        Get the source image for the requested episode.

        Args:
            series_info: SeriesInfo for this episode.
            episode_info: EpisodeInfo for this episode.
            log: Logger for all log messages.

        Returns:
            URL to the source image for the requested episode. None if
            no image is available.
        """

        tvdb_id = self.__get_episode_id(series_info, episode_info, log=log)
        if tvdb_id is None:
            log.warning(f'Cannot find {series_info} {episode_info} on TVDb')
            return None

        url = f'{self.__ROOT_API_URL}/episodes/{tvdb_id}/extended'

        return self.get(url).get('data', {}).get('image')


    def get_episode_title(self,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            language_code: LanguageCode = 'eng',
            *,
            log: Logger = log,
        ) -> Optional[str]:
        """
        Get the episode title for the episode in the given language.

        Args:
            series_info: SeriesInfo for the entry.
            episode_info: EpisodeInfo for the entry.
            language_code: The language code for the desired title.
            log: Logger for all log messages.

        Args:
            The episode title, None if it cannot be found.
        """

        # Find Episode ID, warn and exit if cannot be found
        tvdb_id = self.__get_episode_id(series_info, episode_info, log=log)
        if tvdb_id is None:
            log.warning(f'Cannot find {series_info} {episode_info} on TVDb')
            return None

        url = f'{self.__ROOT_API_URL}/episodes/{tvdb_id}/translations/' \
            + language_code

        return self.get(url).get('data', {}).get('name')


    def get_series_logo(self, series_info: SeriesInfo) -> Optional[str]:
        """
        Get the best logo for the given series.

        Args:
            series_info: Series to get the logo of.

        Returns:
            URL to the 'best' logo for the given series, and None if no
            images  are available.
        """

        # Find Series
        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return None

        return self.__get_best_artwork(tvdb_id, 'logo')


    def get_series_backdrop(self, series_info: SeriesInfo) -> Optional[str]:
        """
        Get the best backdrop for the given series.

        Args:
            series_info: Series to get the logo of.
            skip_localized_images: Whether to skip images with a non-
                null language code.
            raise_exc: Whether to raise any HTTPExceptions that arise.

        Returns:
            URL to the 'best' backdrop for the given series, and None if
            no images are available.
        """

        # Find Series
        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return None

        return self.__get_best_artwork(tvdb_id, 'banner')


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

        # Find Series
        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return None

        return self.__get_best_artwork(tvdb_id, 'poster')
