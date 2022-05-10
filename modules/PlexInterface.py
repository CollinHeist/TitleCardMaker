from pathlib import Path

from plexapi.server import PlexServer, NotFound
from tinydb import TinyDB, where
from tqdm import tqdm
from yaml import safe_load

from modules.Debug import log, TQDM_KWARGS

class PlexInterface:
    """
    This class describes an interface to Plex for the purpose of pulling in new
    title card images.
    """

    """Directory for all temporary objects"""
    TEMP_DIR = Path(__file__).parent / '.objects'

    """Filepath to the database of each episode's loaded card characteristics"""
    LOADED_DB = TEMP_DIR / 'loaded.json'

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

        # Create/read loaded card database
        self.LOADED_DB.parent.mkdir(parents=True, exist_ok=True)
        self.__db = TinyDB(self.LOADED_DB)

        # Import old database if it exists
        self.__import_old_db()


    def __import_old_db(self) -> None:
        """
        Import old loaded database into new TinyDB. This reads the file and then
        deletes it.
        """

        # If old map doesn't exist, nothing to do
        if not (old_file := self.TEMP_DIR / 'loaded_cards.yml').exists():
            return None

        # Read old file
        try:
            with old_file.open('r', encoding='utf-8') as fh:
                old_yaml = safe_load(fh)['sizes']
        except Exception:
            return None

        # Go through each entry, adding to list to add to DB all-at-once
        entries = []
        for library_name, library in old_yaml.items():
            for series_name, series in library.items():
                for episode_key, filesize in series.items():
                    # Get DB-equivalent of this entry
                    season_num, episode_num = map(int, episode_key.split('-'))
                    entries.append({
                        'library': library_name,
                        'series': series_name,
                        'season': season_num,
                        'episode': episode_num,
                        'filesize': filesize,
                        'spoiler': 'spoiled',
                    })                    

        # Add entries to DB
        self.__db.insert_multiple(entries)

        # Delete old file
        old_file.unlink()


    def __get_condition(self, library_name: str, series_info: 'SeriesInfo',
                        episode: 'Episode') -> 'QueryInstance':
        """
        Get the tinydb query condition for the given entry.
        
        :param      library_name:   The name of the library containing the
                                    series to get the details of.
        :param      series_info:    The series to get the details of.
        :param      episode:        The Episode object to get the details of.
        
        :returns:   The condition that matches the given library, series, and
                    Episode season+episode number.
        """

        return (
            (where('library') == library_name) &
            (where('series') == series_info.full_name) &
            (where('season') == episode.episode_info.season_number) &
            (where('episode') == episode.episode_info.episode_number)
        )


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

            # Get current details of this episode
            details = self.__db.get(
                self.__get_condition(library_name, series_info, episode)
            )

            # If this episode has never been loaded, add
            if details == None:
                filtered[key] = episode
                continue

            # If the loaded filesize is different, add
            if details['filesize'] != episode.destination.stat().st_size:
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

            # Get loaded card characteristics for this episode, skip if unloaded
            condition = self.__get_condition(library_name, series_info, episode)
            if (loaded := self.__db.get(condition)) == None:
                continue

            # Spoil characteristics for this card            
            spoiler_free = (unwatched != 'ignore'
                            and not plex_episode.isWatched)
            spoiler = plex_episode.isWatched and not all_spoiler_free
            spoiler_status = loaded['spoiler']

            # If episode needs to be spoiler-free
            delete_and_reset = False
            if all_spoiler_free or spoiler_free:
                # Update episode source
                episode.make_spoiler_free(unwatched)

                # If loaded card is spoiler, or wrong style
                if (spoiler_status == 'spoiled'
                    or spoiler_status != spoil_type):
                    delete_and_reset = True
                    log.debug(f'Deleted card for "{series_info}" {episode}, '
                              f'want spoiler-free card')

            # If episode needs to be a spoiler and has been loaded already
            if (all_spoiler or spoiler) and spoiler_status != 'spoiled':
                delete_and_reset = True
                log.debug(f'Deleted card for "{series_info}" {episode}, want '
                          f'spoiler card')

            # Delete card, reset size in loaded map to force reload
            if delete_and_reset:
                episode.delete_card()
                self.__db.update({'filesize': 0}, condition)


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
        for pl_episode in (pbar := tqdm(series.episodes(), **TQDM_KWARGS)):
            # Skip episodes that aren't in list of cards to update
            ep_key = f'{pl_episode.parentIndex}-{pl_episode.index}'
            if not (episode := filtered_episodes.get(ep_key)):
                continue

            # Update progress bar
            pbar.set_description(f'Updating {pl_episode.seasonEpisode.upper()}')
            
            # Upload card to Plex
            try:
                pl_episode.uploadPoster(filepath=episode.destination.resolve())
            except Exception as e:
                log.error(f'Unable to upload {card_file} to {series_info} - '
                          f'Plex returned "{e}"')
                continue
            
            # Update the loaded map with this card's size
            size = episode.destination.stat().st_size
            series_name = series_info.full_name

            # Update loaded map with this entry
            condition = self.__get_condition(library_name, series_info, episode)
            loaded = self.__db.get(condition)
            if loaded:
                self.__db.update(
                    {'filesize': size, 'spoiler': episode._spoil_type},
                    condition
                )
            else:
                self.__db.insert({
                    'library': library_name,
                    'series': series_info.full_name,
                    'season': episode.episode_info.season,
                    'episode': episode.episode_info.episode,
                    'filesize': size,
                    'spoiler': episode._spoil_type,
                })

        