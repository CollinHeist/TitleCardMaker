from pathlib import Path

from plexapi.server import PlexServer, NotFound, Unauthorized
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential
from tinydb import TinyDB, where
from tqdm import tqdm

from modules.Debug import log, TQDM_KWARGS
import modules.global_objects as global_objects
from modules.EpisodeInfo import EpisodeInfo
from modules.SeriesInfo import SeriesInfo
from modules.WebInterface import WebInterface

class PlexInterface:
    """
    This class describes an interface to Plex for the purpose of pulling in new
    title card images.
    """

    """Directory for all temporary objects"""
    TEMP_DIR = Path(__file__).parent / '.objects'

    """Filepath to the database of each episode's loaded card characteristics"""
    LOADED_DB = TEMP_DIR / 'loaded.json'

    """Filepath to the database of the loaded season poster characteristics"""
    LOADED_POSTERS_DB = TEMP_DIR / 'loaded_posters.json'

    """How many failed episodes result in skipping a series"""
    SKIP_SERIES_THRESHOLD = 3


    def __init__(self, url: str, x_plex_token: str=None,
                 verify_ssl: bool=True) -> None:
        """
        Constructs a new instance of a Plex Interface.
        
        Args:
            url: URL of plex server.
            x_plex_token: X-Plex Token for sending API requests to Plex.
            verify_ssl: Whether to verify SSL requests when querying Plex.
        """

        # Get global PreferenceParser and MediaInfoSet objects
        self.preferences = global_objects.pp
        self.info_set = global_objects.info_set

        # Create Session for caching HTTP responses
        self.__session = WebInterface('Plex', verify_ssl).session

        # Create PlexServer object with these arguments
        try:
            self.__token = x_plex_token
            self.__server = PlexServer(url, x_plex_token, self.__session)
        except Unauthorized:
            log.critical(f'Invalid Plex Token "{x_plex_token}"')
            exit(1)
        
        # Create/read loaded card database
        self.__db = TinyDB(self.LOADED_DB)
        self.__posters = TinyDB(self.LOADED_POSTERS_DB)

        # List of "not found" warned series
        self.__warned = set()


    def __get_condition(self, library_name: str, series_info: 'SeriesInfo',
                        episode: 'Episode'=None) -> 'QueryInstance':
        """
        Get the tinydb query condition for the given entry.
        
        :param      library_name:   The name of the library containing the
                                    series to get the details of.
        :param      series_info:    The series to get the details of.
        :param      episode:        Optional Episode object to get details of.
        
        :returns:   The condition that matches the given library, series, and
                    Episode season+episode number if provided.
        """

        # If no episode was given, get condition for entire series
        if episode is None:
            return (
                (where('library') == library_name) &
                (where('series') == series_info.full_name)
            )

        return (
            (where('library') == library_name) &
            (where('series') == series_info.full_name) &
            (where('season') == episode.episode_info.season_number) &
            (where('episode') == episode.episode_info.episode_number)
        )


    def __get_loaded_episode(self, loaded_series: [dict],
                             episode: 'Episode') -> dict:
        """
        Get the loaded details of the given Episode from the given list of
        loaded series details.
        
        :param      loaded_series:  Filtered List from the loaded database to
                                    look through.
        :param      episode:        The Episode to get the details of.

        :returns:   Loaded details for the specified episode. None if an episode
                    of that index DNE in the given list.
        """
        
        for entry in loaded_series:
            if (entry['season'] == episode.episode_info.season_number and
                entry['episode'] == episode.episode_info.episode_number):
                return entry

        return None


    def __filter_loaded_cards(self, library_name: str, series_info:'SeriesInfo',
                              episode_map: dict) -> dict:
        """
        Filter the given episode map and remove all Episode objects without
        created cards, or whose card's filesizes matches that of the already
        uploaded card.
            
        :param      library_name:   Name of the library containing this series.
        :param      series_info:    SeriesInfo object for these episodes.
        :param      episode_map:    Dictionary of Episode objects to filter.
        
        :returns:   Filtered episode map. Episodes without existing cards, or
                    whose existing card filesizes' match those already loaded
                    are removed.
        """

        # Get all loaded details for this series
        series=self.__db.search(self.__get_condition(library_name, series_info))

        filtered = {}
        for key, episode in episode_map.items():
            # Filter out episodes without cards
            if not episode.destination or not episode.destination.exists():
                continue

            # If no cards have been loaded, add all episodes with cards
            if not series:
                filtered[key] = episode
                continue

            # Get current details of this episode
            found = False
            if (entry := self.__get_loaded_episode(series, episode)):
                # Episode found, check filesize
                found = True
                if entry['filesize'] != episode.destination.stat().st_size:
                    filtered[key] = episode

            # If this episode has never been loaded, add
            if not found:
                filtered[key] = episode

        return filtered
    

    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32))
    def __get_library(self, library_name: str) -> 'Library':
        """
        Get the Library object under the given name.
        
        :param      library_name:   The name of the library to get.

        :returns:   The Library object if found, None otherwise.
        """

        try:
            return self.__server.library.section(library_name)
        except NotFound:
            log.error(f'Library "{library_name}" was not found in Plex')
            return None


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32))
    def __get_series(self, library: 'Library',
                     series_info: 'SeriesInfo') -> 'Show':
        """
        Get the Series object from within the given Library associated with the
        given SeriesInfo. This tries to match by TVDb ID, TMDb ID, name, and
        finally full name.
        
        :param      library:    The Library object to search for within Plex.
        
        :returns:   The Series associated with this SeriesInfo object.
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

        # Try by full name
        try:
            return library.get(series_info.full_name)
        except NotFound:
            pass

        # Try by name and match the year
        try:
            if (ser := library.get(series_info.name)).year == series_info.year:
                return ser
            raise NotFound
        except NotFound:
            key = f'{library.title}-{series_info.full_name}'
            if key not in self.__warned:
                log.warning(f'Series "{series_info}" was not found under '
                            f'library "{library.title}" in Plex')
                self.__warned.add(key)
            
            return None


    def get_library_paths(self, filter_libraries: list[str]=[]) ->dict[str:str]:
        """
        Get all libraries and their associated base directories.

        Args:
            filer_libraries: List of library names to filter the return by.

        Returns:
            Dictionary whose keys are the library names, and whose values are
            the paths to that library's base directory. If the library has
            multiple directories, the first one is returned.
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

            # Add library's corresponding (first) path to the dictionary
            all_libraries[library.title] = library.locations[0]

        return all_libraries
    

    def get_all_series(self, filter_libraries: list[str]=[]
                       ) -> list[tuple[SeriesInfo, str, str]]: 
        """
        Get all series within Plex, as filtered by the given libraries.

        Args:
            filter_libraries: Optional list of library names to filter returned
                list by. If provided, only series that are within a given
                library are returned.

        Returns:
           List of tuples whose elements are the SeriesInfo of the series, the 
            path (string) it is located, and its corresponding library name.
        """

        # Go through every library in this server
        all_series = []
        for library in self.__server.library.sections():
            # Skip non-TV libraries
            if library.type != 'show':
                continue

            # If filtering, skip unspecified libraries
            if (len(filter_libraries) > 0
                and library.title not in filter_libraries):
                continue

            # Get all Shows in this library
            for show in library.all():
                # Skip show if has no year
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

                # Create SeriesInfo object for this show
                series_info = SeriesInfo(
                    show.title,
                    show.year,
                    **ids,
                )

                # Add to returned list
                all_series.append(
                    (series_info, show.locations[0], library.title)
                )

        return all_series
    
    
    def get_all_episodes(self, library_name: str,
                         series_info: SeriesInfo) -> list[EpisodeInfo]:
        """
        Gets all episode info for the given series. Only episodes that have 
        already aired are returned.
        
        :param      library_name:   The name of the library containing the
                                    series.
        :param      series_info:    Series to get the episodes of.
        
        :returns:   List of EpisodeInfo objects for this series.
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
                title_match=False,
                queried_plex=True,
            )

            # Add to list
            if episode_info is not None:
                all_episodes.append(episode_info)

        return all_episodes


    def has_series(self, library_name: str, series_info: 'SeriesInfo') -> bool:
        """
        Determine whether the given series is present within Plex.
        
        :param      library_name:   The name of the library potentially
                                    containing the series.
        :param      series_info:    The series to update.
        
        :returns:   True if the series is present within Plex.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return False

        # If the given series cannot be found in this library, exit
        return self.__get_series(library, series_info) is not None


    def update_watched_statuses(self, library_name: str,
                                series_info: 'SeriesInfo', episode_map: dict,
                                watched_style: str, unwatched_style: str)->None:
        """
        Modify the Episode objects according to the watched status of the
        corresponding episodes within Plex, and the spoil status of the object.
        If a loaded card needs its spoiler status changed, the card is deleted
        and the loaded map is forced to reload that card.
        
        :param      library_name:   The name of the library containing the
                                    series to update.
        :param      series_info:    The series to update.
        :param      episode_map:    Dictionary of episode keys to Episode
                                    objects to modify.
        :param      watched_style:  Desired card style of watched episodes.
        :param      unwatched:      Desired card style of unwatched episodes.
        """

        # If no episodes, or unwatched setting is ignored, exit
        if len(episode_map) == 0:
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Get loaded characteristics of the series
        loaded_series = self.__db.search(
            self.__get_condition(library_name, series_info)
        )

        # Go through each episode within Plex and update Episode spoiler status
        for plex_episode in series.episodes():
            # If this Plex episode doesn't have Episode object(?) skip
            ep_key = f'{plex_episode.parentIndex}-{plex_episode.index}'
            if not (episode := episode_map.get(ep_key)):
                continue
            
            # Set Episode watched/spoil statuses
            episode.update_statuses(plex_episode.isWatched, watched_style,
                                    unwatched_style)

            # Get loaded card characteristics for this episode
            details = self.__get_loaded_episode(loaded_series, episode)
            loaded = (details is not None)
            spoiler_status = details['spoiler'] if loaded else None

            # Delete and reset card if current spoiler type doesnt match
            delete_and_reset = ((episode.spoil_type != spoiler_status)
                                and spoiler_status)

            # Delete card, reset size in loaded map to force reload
            if delete_and_reset and loaded:
                episode.delete_card()
                log.debug(f'Deleted card for "{series_info}" {episode}, '
                          f'updating spoil status')
                self.__db.update(
                    {'filesize': 0},
                    self.__get_condition(library_name, series_info, episode)
                )


    def set_episode_ids(self, library_name: str, series_info: SeriesInfo,
                        infos: list[EpisodeInfo]) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo objects. This
        sets the Sonarr and TVDb ID's for each episode. As a byproduct, this
        also updates the series ID's for the SeriesInfo object
        
        :param      library_name:   Name of the library the series is under.
        :param      series_info:    SeriesInfo for the entry.
        :param      infos:          List of EpisodeInfo objects to update.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        for info in infos:
            # Skip if EpisodeInfo already has IMDb, and TVDb ID's
            if info.queried_plex or info.has_ids('imdb_id', 'tvdb_id'):
                continue

            # Get episode from Plex
            info.queried_plex = True
            try:
                plex_episode = series.episode(
                    season=info.season_number,
                    episode=info.episode_number,
                )
                
                # Set the ID's for this object
                for guid in plex_episode.guids:
                    if 'tvdb://' in guid.id:
                        info.set_tvdb_id(guid.id[len('tvdb://'):])
                    elif 'imdb://' in guid.id:
                        info.set_imdb_id(guid.id[len('imdb://'):])
                    elif 'tmdb://' in guid.id:
                        info.set_tmdb_id(guid.id[len('tmdb://'):])
            except NotFound:
                continue


    def get_source_image(self, library_name: str, series_info: 'SeriesInfo',
                         episode_info: EpisodeInfo) -> str:
        """
        Get the source image (i.e. the URL to the existing thumbnail) for the
        given episode within Plex.
        
        :param      library_name:   Name of the library the series is under.
        :param      series_info:    The series to get the thumbnail of.
        :param      episode_info:   The episode to get the thumbnail of.
        
        :returns:   URL to the thumbnail of the given Episode. None if the
                    episode DNE.
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

            return (f'{self.__server._baseurl}{plex_episode.thumb}'
                    f'?X-Plex-Token={self.__token}')
        except NotFound:
            # Episode DNE in Plex, return
            return None


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32),
           before_sleep=lambda _:log.warning('Cannot upload image, retrying..'))
    def __retry_upload(self, plex_object: 'Episode', filepath: Path) -> None:
        """
        Upload the given poster to the given Episode, retrying if it fails.
        
        :param      plex_object:    The plexapi object to upload the file to.
        :param      filepath:       Filepath to the poster to upload.
        """

        plex_object.uploadPoster(filepath=filepath)


    def set_title_cards_for_series(self, library_name: str, 
                                   series_info: 'SeriesInfo',
                                   episode_map: dict) -> None:
        """
        Set the title cards for the given series. This only updates episodes
        that have title cards, and those episodes whose card filesizes are
        different than what has been set previously.
        
        :param      library_name:   The name of the library containing the
                                    series to update.
        :param      series_info:    The series to update.
        :param      episode_map:    Dictionary of episode keys to Episode
                                    objects to update the cards of.
        """

        # Filter episodes without cards, or whose cards have not changed
        filtered_episodes = self.__filter_loaded_cards(
            library_name,
            series_info,
            episode_map
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
            
            # Upload card to Plex, optionally remove Overlay label
            try:
                self.__retry_upload(pl_episode, episode.destination.resolve())
                loaded_count += 1
                
                # If overlay integration is enabled, remove "Overlay" label
                if self.preferences.integrate_with_pmm_overlays:
                    pl_episode.removeLabel(['Overlay'])
            except Exception as e:
                error_count += 1
                log.warning(f'Unable to upload {episode.destination.resolve()} '
                            f'to {series_info}')
                continue
            
            # Update the loaded map with this card's size
            size = episode.destination.stat().st_size
            series_name = series_info.full_name

            # Update/add loaded map with this entry
            self.__db.upsert({
                'library': library_name,
                'series': series_info.full_name,
                'season': episode.episode_info.season_number,
                'episode': episode.episode_info.episode_number,
                'filesize': size,
                'spoiler': episode.spoil_type,
            }, self.__get_condition(library_name, series_info, episode))
                
        # Log load operations to user
        if loaded_count > 0:
            log.info(f'Loaded {loaded_count} cards for "{series_info}"')


    def set_season_poster(self, library_name: str,
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

            # Upload this poster
            try:
                self.__retry_upload(season, poster)
                loaded_count += 1
            except Exception:
                continue

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


    def get_episode_details(self, rating_key: int) -> tuple[SeriesInfo,
                                                            EpisodeInfo, str]:
        """
        Get all details for the episode indicated by the given Plex rating key.
        
        :param      rating_key: Rating key used to fetch the item within Plex.
        
        :returns:   Tuple of the SeriesInfo, EpisodeInfo, and the library name
                    corresponding to the given episode.
        """

        try:
            # Get the episode for this key
            episode = self.__server.fetchItem(rating_key)

            # Make sure result is an episode
            if episode.TYPE != 'episode':
                log.error(f'Item {episode} is not an Episode')
                raise NotFound

            series = self.__server.fetchItem(episode.grandparentKey)

            return (
                SeriesInfo(episode.grandparentTitle, series.year),
                EpisodeInfo(episode.title, episode.parentIndex, episode.index),
                episode.librarySectionTitle,
            )
        except NotFound:
            log.error(f'No item with ratingKey={rating_key} exists')
            return None


    def remove_records(self, library_name: str, series_info: SeriesInfo) ->None:
        """
        Remove all records for the given library and series from the loaded
        database.
        
        :param      library_name:   The name of the library containing the
                                    series whose records are being removed.
        :param      series_info:    SeriesInfo whose records are being removed.
        """

        # Get condition to find records matching this library + series
        condition = self.__get_condition(library_name, series_info)

        # Delete records matching this condition
        records = self.__db.remove(condition)

        # Log actions to user
        log.info(f'Deleted {len(records)} records')

        