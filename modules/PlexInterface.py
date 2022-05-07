from pathlib import Path

from plexapi.server import PlexServer, NotFound
from tqdm import tqdm
from yaml import safe_load, dump

from modules.Debug import log, TQDM_KWARGS

class PlexInterface:
    """
    This class describes an interface to Plex for the purpose of pulling in new
    title card images.

    Get the plex token from this webpage:
    https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
    """

    """Directory for all temporary objects"""
    TEMP_DIR = Path(__file__).parent / '.objects'

    """Filepath to the map of each episode's loaded card size (from os.stat)"""
    LOADED_CARDS = TEMP_DIR / 'loaded_cards.yml'

    """Action to take for unwatched episodes"""
    VALID_UNWATCHED_ACTIONS = ('ignore', 'blur', 'art', 'blur_all', 'art_all')
    DEFAULT_UNWATCHED_ACTION = 'ignore'


    def __init__(self, url: str, x_plex_token: str=None) -> None:
        """
        Constructs a new instance of a Plex Interface.
        
        :param      url:            The url at which Plex is hosted.
        :param      x_plex_token:   The x plex token for sending API requests to
                                    if the host device is untrusted.
        """

        # Create PlexServer object with these arguments
        self.__server = PlexServer(url, x_plex_token)

        # Read map of show name, key, and file size (in bytes)
        if self.LOADED_CARDS.exists():
            try:
                with self.LOADED_CARDS.open('r', encoding='utf-8') as fh:
                    self.__loaded = self.__update_loaded(safe_load(fh)['sizes'])

                # Write updated loaded map to file
                self.__write_loaded()
            except Exception as e:
                log.debug(f'Error reading loaded card map - {e}')
                self.__loaded = {}
        else:
            # Create parent directories if necessary
            self.LOADED_CARDS.parent.mkdir(parents=True, exist_ok=True)
            self.__loaded = {}


    def __write_loaded(self) -> None:
        """Write the loaded dictionary to file."""

        # Write updated loaded map to file
        with self.LOADED_CARDS.open('w', encoding='utf-8') as file_handle:
            dump({'sizes': self.__loaded}, file_handle, allow_unicode=True)


    def __update_loaded(self, yaml: dict) -> dict:
        """
        Update the loaded dictionary from old style to new. This keeps old
        filesizes and adds spoiler attribute for each card.
        
        :param      yaml:   The YAML of the loaded file to update.
        
        :returns:   Modified YAML with each 'old' entry converted.
        """

        # Go through each item one-by-one, update to new format
        for library_name, library in yaml.items():
            for series_name, series in library.items():
                for episode_key, loaded in series.items():
                    if isinstance(loaded, int):
                        yaml[library_name][series_name][episode_key] = \
                            {'filesize': loaded, 'spoiler': 'spoiled'}

        return yaml


    def __get_loaded_details(self, library_name: str, series_info: 'SeriesInfo',
                             episode: 'Episode') -> dict:
        """
        Get the loaded dictionary details for the specified entry.
        
        :param      library_name:   The name of the library containing the
                                    series to get the details of.
        :param      series_info:    The series to get the details of.
        :param      episode:        The Episode object to get the details of.
        
        :returns:   The loaded details with keys 'filesize' and 'spoiler'. Empty
                    dictionary if the specified entry DNE.
        """

        # If this library hasn't been loaded, return 
        if not (library := self.__loaded[library_name]):
            return {}

        # If this series hasn't been loaded, return
        if not (series := library.get(series_info.full_name)):
            return {}

        # Return contents for this episode (or blank)
        return series.get(episode.episode_info.key, {})


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

        filtered = {}
        for key, episode in episode_map.items():
            # Filter out episodes without cards
            if not episode.destination or not episode.destination.exists():
                continue

            # If this library is new, don't filter
            if not (library_loaded := self.__loaded.get(library_name, {})):
                filtered[key] = episode
                continue

            # Check if this episode matches what was loaded for this series
            if (show_loaded := library_loaded.get(series_info.full_name, {})):
                # Get the previously loaded filesize (or 0 if never loaded)
                ep_loaded = show_loaded.get(episode.episode_info.key, {})
                old_size = ep_loaded.get('filesize', 0)

                # If new or different card, don't filter
                if (not old_size
                    or episode.destination.stat().st_size != old_size):
                    filtered[key] = episode
            else:
                # If series has never been loaded before, don't filter
                filtered[key] = episode

        return filtered
    

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


    def __get_series(self, library: 'Library',
                     series_info: 'SeriesInfo') -> 'Show':
        """
        Get the Series object from within the given Library associated with the
        given SeriesInfo. This tries to match by TVDb ID, TMDb ID, name, and
        finally full name.
        
        :param      library:    The Library object to search for within Plex.
        
        :returns:   The Series associated with this SeriesInfo object.
        """

        # Try by TVDb ID
        try:
            if series_info.tvdb_id != None:
                return library.getGuid(f'tvdb://{series_info.tvdb_id}')
        except NotFound:
            pass

        # Try by TMDb ID
        try:
            if series_info.tmdb_id != None:
                return library.getGuid(f'tmdb://{series_info.tmdb_id}')
        except NotFound:
            pass

        # Try by name
        try:
            return library.get(series_info.name)
        except NotFound:
            pass

        # Try by full name
        try:
            return library.get(series_info.full_name)
        except NotFound:
            log.warning(f'Series "{series_info}" was not found under library '
                        f'"{library.title}" in Plex')
            return None


    def modify_unwatched_episodes(self, library_name: str,
                                  series_info: 'SeriesInfo',
                                  episode_map: dict, unwatched: str) -> None:
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
        :param      unwatched:      How to treat unwatched episodes.
        """

        # Validate unwatched action
        if (unwatched := unwatched.lower()) not in self.VALID_UNWATCHED_ACTIONS:
            raise ValueError(f'Invalid unwatched action "{unwatched}"')

        # If no episodes, or unwatched setting is ignored, exit
        if len(episode_map) == 0:
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # General spoil characteristics
        all_spoiler_free = unwatched in ('art_all', 'blur_all')
        all_spoiler = unwatched == 'ignore'
        if unwatched == 'ignore':
            spoil_type = 'spoiled'
        else:
            spoil_type = 'art' if 'art' in unwatched else 'blur'

        # Go through each episode within Plex and update Episode spoiler status
        for plex_episode in series.episodes():
            # If this Plex episode doesn't have Episode object(?) skip
            ep_key = f'{plex_episode.parentIndex}-{plex_episode.index}'
            if not (episode := episode_map.get(ep_key)):
                continue

            # Spoil characteristics for this card            
            spoiler_free = (unwatched != 'ignore'
                            and not plex_episode.isWatched)
            spoiler = plex_episode.isWatched and not all_spoiler_free

            # Get loaded card characteristics for this episode
            loaded = self.__get_loaded_details(library_name,series_info,episode)
            spoiler_status = loaded.get('spoiler')

            # If episode needs to be spoiler-free
            if all_spoiler_free or spoiler_free:
                # Update episode source
                episode.make_spoiler_free(unwatched)

                # If loaded card is spoiler, or wrong style
                if (spoiler_status == 'spoiled'
                    or spoiler_status != spoil_type):
                    # Delete card, reset size in loaded map to force reload
                    episode.delete_card()
                    self.__loaded[library_name][series_info.full_name]\
                        [ep_key]['filesize'] = 0
                    log.debug(f'Deleted card for {series_info} {episode} - want'
                              f' spoiler-free card')
                continue

            # If episode needs to be a spoiler and has been loaded already
            if (all_spoiler or spoiler) and spoiler_status != 'spoiled':
                # Delete card, reset size in loaded map to force reload
                episode.delete_card()
                self.__loaded[library_name][series_info.full_name]\
                    [ep_key]['filesize'] = 0
                log.debug(f'Deleted card for {series_info} {episode} - want'
                          f' spoiler card')

        # Write updated loaded map to file
        self.__write_loaded()


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
        for episode in (pbar := tqdm(series.episodes(), **TQDM_KWARGS)):
            # Skip episodes that aren't in list of cards to update
            ep_key = f'{episode.parentIndex}-{episode.index}'
            if ep_key not in filtered_episodes:
                continue

            # Update progress bar
            pbar.set_description(f'Updating {episode.seasonEpisode.upper()}')
            
            # Upload card to Plex
            card_file = filtered_episodes[ep_key].destination
            try:
                episode.uploadPoster(filepath=card_file.resolve())
            except Exception as e:
                log.error(f'Unable to upload {card_file} to {series_info} - '
                          f'Plex returned "{e}"')
                continue
            
            # Update the loaded map with this card's size
            size = card_file.stat().st_size
            series_name = series_info.full_name

            # Update loaded map with this entry
            ep_stats = {'filesize': size,
                        'spoiler': filtered_episodes[ep_key]._spoil_type}
            if library_name in self.__loaded:
                if series_name in self.__loaded[library_name]:
                    self.__loaded[library_name][series_name][ep_key] = ep_stats
                else:
                    self.__loaded[library_name][series_name] = {ep_key:ep_stats}
            else:
                self.__loaded[library_name] = {series_name: {ep_key: ep_stats}}

        # Write updated loaded map to file
        self.__write_loaded()

        