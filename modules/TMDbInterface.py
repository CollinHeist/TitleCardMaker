from datetime import datetime, timedelta
from pathlib import Path
from tinydb import TinyDB, where

from tmdbapis import TMDbAPIs, NotFound, Unauthorized

from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo
import modules.global_objects as global_objects
from modules.SeriesInfo import SeriesInfo

class TMDbInterface:
    """
    This class defines an interface to TheMovieDatabase (TMDb). Once initialized 
    with a valid API key, the primary purpose of this class is to gather images
    for title cards, logos for summaries, or translations for titles.
    """

    """Default for how many failed requests lead to a blacklisted entry"""
    BLACKLIST_THRESHOLD = 5

    """Generic translated episode format strings for each language code"""
    GENERIC_TITLE_FORMATS = {
        'ar': r'الحلقة {number}',
        'cs': r'{number}. epizoda',
        'de': r'Episode {number}',
        'en': r'Episode {number}',
        'es': r'Episodio {number}',
        'fr': r'Épisode {number}',
        'he': r'פרק {number}',
        'hu': r'{number}. epizód',
        'id': r'Episode {number}',
        'it': r'Episodio {number}',
        'ja': r'第{number}話',
        'ko': r'에피소드 {number}',
        'pl': r'Odcinek {number}',
        'pt': r'Episódio {number}',
        'ro': r'Episodul {number}',
        'ru': r'Эпизод {number}',
        'sk': r'Epizóda {number}',
        'th': r'Episode {number}',
        'tr': r'{number}. Bölüm',
        'uk': r'Серія {number}',
        'vi': r'Episode {number}',
        'zh': r'第 {number} 集',
    }

    """Filename for where to store blacklisted entries"""
    __BLACKLIST_DB = Path(__file__).parent / '.objects' / 'tmdb_blacklist.json'

    """Filename where mappings of series full titles to TMDB ids is stored"""
    __ID_DB = Path(__file__).parent / '.objects' / 'tmdb_ids.json'


    def __init__(self, api_key: str) -> None:
        """
        Constructs a new instance of an interface to TheMovieDB.
        
        :param      api_key:    The api key to communicate with TMDb.
        """

        # Store global objects
        self.preferences = global_objects.pp
        self.info_set = global_objects.info_set

        # Create/read blacklist database
        self.__blacklist = TinyDB(self.__BLACKLIST_DB)

        # Create/read series ID database
        self.__id_map = TinyDB(self.__ID_DB)
        
        # Create API object, validate key
        try:
            self.api = TMDbAPIs(api_key)
        except Unauthorized:
            log.critical(f'TMDb API key "{api_key}" is invalid')
            exit(1)


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'<TMDbInterface {self.api=}>'


    def __get_condition(self, query_type: str, series_info: SeriesInfo,
                        episode_info: EpisodeInfo=None) -> 'QueryInstance':
        """
        Get the tinydb query condition for the given query.
        
        :param      query_type:     The type of request being updated.
        :param      series_info:    SeriesInfo for the request.
        :param      episode_info:   EpisodeInfo for the request.
        
        :returns:   The condition that matches the given query type, series, and
                    Episode season+episode number and episode.
        """

        # Logo and backdrop queries don't use episode index
        if query_type in ('logo', 'backdrop'):
            return (
                (where('query') == query_type) &
                (where('series') == series_info.full_name)
            )

        # Query by series name and episode index
        return (
            (where('query') == query_type) &
            (where('series') == series_info.full_name) &
            (where('season') == episode_info.season_number) &
            (where('episode') == episode_info.episode_number)
        )


    def __update_blacklist(self, series_info: SeriesInfo,
                           episode_info: EpisodeInfo, query_type: str) -> None:
        """
        Adds the given request to the blacklist; indicating that this exact
        request shouldn't be queried to TMDb for another day. Write the updated
        blacklist to file
        
        :param      series_info:    SeriesInfo for the request.
        :param      episode_info:   EpisodeInfo for the request.
        :param      query_type:     The type of request being updated.
        """

        # Get the entry for this request
        condition = self.__get_condition(query_type, series_info, episode_info)
        entry = self.__blacklist.get(condition)

        # If previously indexed and next has passed, increase count and set next
        later = (datetime.now() + timedelta(days=1)).timestamp()

        # If this entry exists, check that next has passed
        if entry is not None:
            if datetime.now().timestamp() >= entry['next']:
                self.__blacklist.update(
                    {'failures': entry['failures']+1, 'next': later},
                    condition
                )
        else:
            if query_type in ('logo', 'backdrop'):
                self.__blacklist.insert({
                    'query': query_type,
                    'series': series_info.full_name,
                    'failures': 1,
                    'next': later,    
                })
            else:
                self.__blacklist.insert({
                    'query': query_type,
                    'series': series_info.full_name,
                    'season': episode_info.season_number,
                    'episode': episode_info.episode_number,
                    'failures': 1,
                    'next': later,
                })


    def __is_blacklisted(self, series_info: SeriesInfo,
                         episode_info: EpisodeInfo, query_type: str) -> bool:
        """
        Determines if the specified entry is in the blacklist (i.e. should
        not bother querying TMDb.
        
        :param      series_info:    SeriesInfo for the entry.
        :param      episode_info:   EpisodeInfo for the entry.
        :param      query_type:     The type of request being checked.
        
        :returns:   True if the entry is blacklisted, False otherwise.
        """

        # Get the blacklist entry for this request
        entry = self.__blacklist.get(
            self.__get_condition(query_type, series_info, episode_info)
        )

        # If request DNE, not blacklisted
        if entry is None:
            return False

        # If too many failures, blacklisted
        if entry['failures'] > self.preferences.tmdb_retry_count:
            return True

        # If next hasn't passed, treat as temporary blacklist
        return datetime.now().timestamp() < entry['next']


    def is_permanently_blacklisted(self, series_info: SeriesInfo,
                                   episode_info: EpisodeInfo,
                                   query_type: str='image') -> bool:
        """
        Determines if permanently blacklisted.
        
        :param      series_info:   The series information
        :param      episode_info:  The episode information
        
        :returns:   True if permanently blacklisted, False otherwise.
        """

        # Get the blacklist entry for this request
        entry = self.__blacklist.get(
            self.__get_condition(query_type, series_info, episode_info)
        )

        # If request hasn't been blacklisted, not blacklisted
        if entry is None:
            return False

        # If too many failures, blacklisted
        return entry['failures'] > self.preferences.tmdb_retry_count


    def set_series_ids(self, series_info: SeriesInfo) -> None:
        """
        Set the TMDb and TVDb ID's for the given SeriesInfo object.
        
        :param      series_info:    SeriesInfo to update.
        """

        # TMDb can set the TMDb, TVDb, and IMDb ID's - exit if all defined
        if series_info.has_ids('tmdb_id', 'tvdb_id', 'imdb_id'):
            return None

        # If TVDb ID is available and is mapped, set that ID
        if (series_info.tvdb_id and
            (val := self.__id_map.get(where('tvdb_id') == series_info.tvdb_id))):
            series_info.set_tmdb_id(val['tmdb_id'])
            return None

        # If already mapped, set that ID
        if (entry := self.__id_map.get(where('name') == series_info.full_name)):
            series_info.set_tvdb_id(entry['tmdb_id'])
            series_info.set_tmdb_id(entry['tmdb_id'])
            return None

        # Try and find by TMDb ID first
        found = False
        if not found and series_info.has_id('tmdb_id'):
            try:
                results = [self.api.tv_show(series_info.tmdb_id)]
                found = True
            except NotFound:
                pass

        # Find by TVDb ID
        if not found and series_info.has_id('tvdb_id'):
            try:
                results = self.api.find_by_id(
                    tvdb_id=series_info.tvdb_id
                ).tv_results
                found = len(results) > 0
            except NotFound:
                pass

        # Find by IMDb ID
        if not found and series_info.has_id('imdb_id'):
            try:
                results = self.api.find_by_id(
                    imdb_id=series_info.imdb_id
                ).tv_results
                found = len(results) > 0
            except NotFound:
                pass

        # Find by series name + year
        if not found:
            try:
                # Search by name+year, and exclude adult content
                results = self.api.tv_search(series_info.name, False,
                                             series_info.year)
                found = results.total_results > 0
            except NotFound:
                pass

        # If found, update ID's
        if found:
            result = results[0]
            # Series always have TMDb ID
            series_info.set_tmdb_id(result.id)

            # Series without IMDb ID have None in its place
            if (imdb_id := result.imdb_id) is not None:
                series_info.set_imdb_id(imdb_id)

            # Series without TVDB ID have 0 in its place
            if (tvdb_id := result.tvdb_id) != 0:
                series_info.set_tvdb_id(tvdb_id)
        else:
            log.warning(f'Series "{series_info}" not found on TMDb')


    def get_all_episodes(self, series_info: SeriesInfo) -> list[EpisodeInfo]:
        """
        Gets all episode info for the given series. Only episodes that have 
        already aired are returned.
        
        :param      series_info:    SeriesInfo for the entry.
        
        :returns:   List of EpisodeInfo objects for this series.
        """

        # Cannot query TMDb if no series TMDb ID 
        if series_info.tmdb_id is None:
            log.error(f'Cannot source episodes from TMDb for {series_info}')
            return []

        # Get all seasons on TMDb
        try:
            seasons = self.api.tv_show(series_info.tmdb_id).seasons
        except NotFound:
            log.error(f'Cannot source episodes from TMDb for {series_info}')
            return []

        # Go through each season, getting episodes from each
        all_episodes = []
        for season in seasons:
            # Load episodes, now iterate through them
            season.reload()
            for episode in season.episodes:
                # Skip episodes until 2 hours after airing
                if episode.air_date > datetime.now() + timedelta(hours=2):
                    continue

                # Create either a new EpisodeInfo or get from the MediaInfoSet
                episode.reload()
                episode_info = self.info_set.get_episode_info(
                    series_info,
                    episode.name,
                    season.season_number,
                    episode.episode_number,
                    tvdb_id=episode.tvdb_id if episode.tvdb_id != 0 else None,
                    imdb_id=None if episode.imdb_id is None else episode.imdb_id,
                    queried_tmdb=True,
                )

                # Create EpisodeInfo for this episode, add to list
                all_episodes.append(episode_info)

        return all_episodes


    def __find_episode(self, series_info: SeriesInfo,
                       episode_info: EpisodeInfo,
                       title_match: bool=True) ->'tmdbapis.objs.reload.Episode':
        """
        Finds the episode index for the given entry. Searching is done in the
        following priority:

        1. Episode TVDb ID
        2. Series TMDb ID and season+episode index with title match
        3. Series TMDb ID and season+absolute episode index with title match
        3. Series TMDb ID and title match on any episode
        
        :param      series_info:    The series information.
        :param      episode_info:   The episode information.
        :para       title_match:    Whether to require the title within
                                    episode_info to match the title on TMDb.
        
        :returns:   Dictionary of the index for the given entry. This dictionary
                    has keys 'season' and 'episode'. None if returned if the
                    entry cannot be found.
        """

        # Query with TVDb ID first
        if episode_info.has_id('tvdb_id'):
            try:
                results = self.api.find_by_id(tvdb_id=episode_info.tvdb_id)
                return results.tv_episode_results[0]
            except (NotFound, IndexError):
                pass

        # Query with IMDB ID
        if episode_info.has_id('imdb_id'):
            try:
                results = self.api.find_by_id(tvdb_id=episode_info.tvdb_id)
                return results.tv_episode_results[0]
            except (NotFound, IndexError):
                pass

        # If series TMDb ID is not present, exit
        if not series_info.has_id('tmdb_id'):
            return None

        # Verify series ID is valid
        try:
            series = self.api.tv_show(series_info.tmdb_id)
        except NotFound:
            return None

        def _match_by_index(episode_info, season_number, episode_number):
            try:
                episode = self.api.tv_episode(series_info.tmdb_id,
                                              season_number, episode_number)
                if ((title_match and episode_info.title.matches(episode.name))
                    or not title_match):
                    return episode
                return None
            except NotFound:
                return None

        # Try and match by index
        indices = episode_info.season_number, episode_info.episode_number
        if (episode := _match_by_index(episode_info, *indices)) is not None:
            return episode
        
        # Match by absolute number
        if episode_info.abs_number is not None:
            # Try for this season
            indices = episode_info.season_number, episode_info.abs_number
            if (ep := _match_by_index(episode_info, *indices)) is not None:
                return ep

            # Try for all seasons
            for season in series.seasons:
                indices = season.season_number, episode_info.abs_number
                if (ep := _match_by_index(episode_info, *indices)) is not None:
                    return ep
        
        # If title match is disabled, cannot identify
        if not title_match:
            return None

        # Try every episode
        for season in series.seasons:
            season.reload()
            for episode in season.episodes:
                if episode_info.title.matches(episode.name):
                    return episode

        return None


    def set_episode_ids(self, series_info: SeriesInfo,
                        infos: list[EpisodeInfo]) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo objects. For
        TMDb, this does nothing, as TMDb cannot provide any useful episode ID's.
        
        :param      series_info:    SeriesInfo for the entry.
        :param      infos:          List of EpisodeInfo objects to update.
        """

        return None


    def __determine_best_image(self, images: list['tmdbapis.objs.image.Still'],
                               source_image: bool=True) -> dict:
        """
        Determines the best image, returning it's contents from within the
        database return JSON.
        
        :param      images:         The results from the database. Each entry is
                                    a new image to be considered.
        :param      source_image:   Whether the images being selected are source
                                    images or not. If True, then images must
                                    meet the minimum resolution requirements.
        
        :returns:   The "best" image for title card creation. This is determined
                    using the images' dimensions. Priority given to largest
                    image. None if there are no valid images.
        """

        # Pick the best image based on image dimensions, and then vote average
        best_image = {'index': 0, 'pixels': 0, 'score': 0}
        valid_image = False
        for index, image in enumerate(images):
            # Get image dimensions
            width, height = image.width, image.height

            # If source image selection, check dimensions
            if (source_image and
                not self.preferences.meets_minimum_resolution(width, height)):
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


    def __is_generic_title(self, title: str, language_code: str,
                           episode_info: EpisodeInfo) -> bool:
        """
        Determine whether the given title is a generic translation of
        "Episode (x)" for the indicated language. 
        
        :param      title:          The translated title.
        :param      language_code:  The language code of the translation.
        :param      episode_info:   The EpisodeInfo for this title.
        
        :returns:   True if the title is a generic translation, False otherwise.
        """

        # Assume non-generic if the code isn't pre-mapped
        if not (generic := self.GENERIC_TITLE_FORMATS.get(language_code, None)):
            log.debug(f'Unrecognized language code "{language_code}"')
            return False

        # Format with this episode, return whether this matches the translation
        if episode_info.abs_number is not None:
            # Check against episode and absolute number
            return title in (
                generic.format(number=episode_info.episode_number),
                generic.format(number=episode_info.abs_number),
            )

        # Only check against episode number (no absolute)
        return title == generic.format(number=episode_info.episode_number)


    def get_source_image(self, series_info: SeriesInfo,
                         episode_info: EpisodeInfo,
                         title_match: bool=True) -> str:
        """
        Get the best source image for the requested entry. The URL of this image
        is returned.
        
        :param      series_info:    SeriesInfo for this entry.
        :param      episode_info:   EpisodeInfo for this entry.
        :param      title_match:    Whether to require the episode title to
                                    match when querying TMDb.
        
        :returns:   URL to the 'best' source image for the requested entry. None
                    if no images are available.
        """
        
        # Don't query the database if this episode is in the blacklist
        if self.__is_blacklisted(series_info, episode_info, 'image'):
            return None

        # Get Episode object for this episode
        episode = self.__find_episode(series_info, episode_info, title_match)
        if episode is None:
            log.debug(f'TMDb has no matching episode for "{series_info}" '
                      f'{episode_info}')
            self.__update_blacklist(series_info, episode_info, 'image')
            return None

        # Episode found on TMDb, exit if no backdrops for this episode
        episode.reload()
        if len(episode.stills) == 0:
            log.debug(f'TMDb has no images for "{series_info}" {episode_info}')
            self.__update_blacklist(series_info, episode_info, 'image')
            return None

        # Get the best image for this Episode
        if (best_image := self.__determine_best_image(episode.stills, True)):
            return best_image.url
        
        log.debug(f'TMDb images for "{series_info}" {episode_info} do not meet '
                  f'dimensional requirements')
        self.__update_blacklist(series_info, episode_info, 'image')
        return None


    def get_episode_title(self, series_info: SeriesInfo,
                          episode_info: EpisodeInfo,
                          language_code: str='en-US') -> str:
        """
        Get the episode title for the given entry for the given language.
        
        :param      series_info:    SeriesInfo for the entry.
        :param      episode_info:   EpisodeInfo for the entry.
        :param      language_code:  The language code for the desired title.
        
        :returns:   The episode title, None if the entry does not exist.
        """

        # Don't query the database if this episode is in the blacklist
        if self.__is_blacklisted(series_info, episode_info, 'title'):
            return None

        # Get episode
        episode = self.__find_episode(series_info, episode_info)
        if episode is None:
            self.__update_blacklist(series_info, episode_info, 'title')
            return None

        # Look for this translation
        for translation in episode.translations:
            if language_code in (translation.iso_3166_1, translation.iso_639_1):
                # If the title translation is blank (i.e. non-existant)
                title = translation.name
                if len(title) == 0:
                    break

                # If translation is generic, blacklist and skip
                if self.__is_generic_title(title, language_code, episode_info):
                    log.debug(f'Generic title "{title}" detected for '
                              f'{episode_info}')
                    self.__update_blacklist(series_info, episode_info, 'title')
                    return None

                return title


    def get_series_logo(self, series_info: SeriesInfo) -> str:
        """
        Get the 'best' logo for the given series.
        
        :param      series_info:    Series to get the logo of.
        
        :returns:   URL to the 'best' logo for the given series, and None if no
                    images are available.
        """

        # Don't query the database if this series' logo is blacklisted
        if self.__is_blacklisted(series_info, None, 'logo'):
            return None

        # Get the series for this logo, exit if series or logos DNE
        try:
            series = self.api.tv_show(series_info.tmdb_id)
        except NotFound:
            self.__update_blacklist(series_info, None, 'logo')
            return None

        # Blacklist if tthere are no logos
        if len(series.logos) == 0:
            self.__update_blacklist(series_info, None, 'logo')
            return None

        # Get the best logo
        best = series.logos[0]
        valid_image = False
        for logo in series.logos:
            # SVG images are always the best
            if logo.url.endswith('.svg'):
                return logo.url

            # Choose best based on pixel count
            valid_image = True
            if logo.width * logo.height > best.width * best.height:
                best = logo

        # No valid image found, blacklist and exit
        if not valid_image:
            self.__update_blacklist(series_info, None, 'logo')
            return None

        return best.url


    def get_series_backdrop(self, series_info: SeriesInfo) -> str:
        """
        Get the 'best' backdrop for the given series.
        
        :param      series_info:    Series to get the logo of.
        
        :returns:   URL to the 'best' backdrop for the given series, and None if
                    no images are available.
        """

        # Don't query the database if this episode is in the blacklist
        if self.__is_blacklisted(series_info, None, 'backdrop'):
            return None

        # Get the series for this backdrop, exit if series or backdrop DNE
        try:
            series = self.api.tv_show(series_info.tmdb_id)
        except NotFound:
            self.__update_blacklist(series_info, None, 'backdrop')
            return None

        # Blacklist if tthere are no backdrops
        if len(series.backdrops) == 0:
            self.__update_blacklist(series_info, None, 'backdrop')
            return None

        if (best_image := self.__determine_best_image(series.backdrops, True)):
            return best_image.url
        
        self.__update_blacklist(series_info, None, 'backdrop')
        return None


    @staticmethod
    def manually_download_season(api_key: str, title: str, year: int,
                                 season: int, episode_count: int,
                                 directory: Path) -> None:
        """
        Download episodes 1-episode_count of the requested season for the given
        show. They will be named as s{season}e{episode}.jpg.
        
        :param      api_key:        The api key for sending requsts to TMDb.
        :param      title:          The title of the requested show.
        :param      year:           The year of the requested show.
        :param      season:         The season to download.
        :param      episode_count:  The number of episodes to download
        :param      directory:      The directory to place the downloaded images
                                    in.
        """

        # Create a temporary interface object for this function
        dbi = TMDbInterface(api_key)

        # Create SeriesInfo and EpisodeInfo objects
        si = SeriesInfo(title, year)

        for episode in range(1, episode_count+1):
            ei = EpisodeInfo('', season, episode)
            image_url = dbi.get_source_image(si, ei, title_match=False)

            # If a valid URL was returned, download it
            if image_url:
                filename = f's{season}e{episode}.jpg'
                dbi.download_image(image_url, directory / filename)


    @staticmethod
    def delete_blacklist() -> None:
        """Delete the blacklist file referenced by this class."""

        TMDbInterface.__BLACKLIST_DB.unlink(missing_ok=True)
        log.info(f'Deleted blacklist file '
                 f'"{TMDbInterface.__BLACKLIST_DB.resolve()}"')

