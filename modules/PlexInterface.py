from pathlib import Path

from plexapi.server import PlexServer, NotFound
from tqdm import tqdm
from yaml import safe_load, dump

from modules.Debug import log

class PlexInterface:
    """
    This class describes an interface to Plex for the purpose of pulling in new
    title card images.

    Get the plex token from this webpage:
    https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
    """

    """Filepath to the map of each episode's loaded card size (from os.stat)"""
    LOADED_CARDS = Path(__file__).parent / '.objects' / 'loaded_cards.yml'


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
                    self.__loaded = safe_load(fh)['sizes']
            except Exception as e:
                log.debug(f'Error reading loaded card map - {e}')
                self.__loaded = {}
        else:
            # Create parent directories if necessary
            self.LOADED_CARDS.parent.mkdir(parents=True, exist_ok=True)
            self.__loaded = {}


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
                old_size = show_loaded.get(episode.episode_info.key, 0)

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
            log.error(f'Library "{library}" was not found in Plex')
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
        :param      episodes:       Dictionary of episode keys to Episode
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

        # If no episodes, or the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # Exit if the given series cannot be found in this library
        if not (series := self.__get_series(library, series_info)):
            return None

        # Go through each episode within Plex, set title cards
        for episode in (pbar := tqdm(series.episodes(), leave=False)):
            # Update progress bar
            pbar.set_description(f'Updating {episode.seasonEpisode.upper()}')

            # If this Plex episode is among the list of cards to update
            ep_key = f'{episode.parentIndex}-{episode.index}'
            if ep_key in filtered_episodes:
                # Upload card to Plex
                card_file = filtered_episodes[ep_key].destination
                episode.uploadPoster(filepath=card_file.resolve())
                
                # Update the loaded map with this card's size
                size = card_file.stat().st_size
                series_name = series_info.full_name

                # Update loaded map with this entry
                if library_name in self.__loaded:
                    if series_name in self.__loaded[library_name]:
                        self.__loaded[library_name][series_name][ep_key] = size
                    else:
                        self.__loaded[library_name][series_name] = {ep_key:size}
                else:
                    self.__loaded[library_name] = {series_name: {ep_key: size}}

        # Write updated loaded map to file
        with self.LOADED_CARDS.open('w', encoding='utf-8') as file_handle:
            dump({'sizes': self.__loaded}, file_handle, allow_unicode=True)

        