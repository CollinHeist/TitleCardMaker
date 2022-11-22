from yaml import dump
from tqdm import tqdm
from typing import Iterable

from modules.Debug import log, TQDM_KWARGS
from modules.PlexInterface import PlexInterface
import modules.global_objects as global_objects
from modules.Show import Show
from modules.ShowArchive import ShowArchive
from modules.SonarrInterface import SonarrInterface
from modules.TautulliInterface import TautulliInterface
from modules.TMDbInterface import TMDbInterface

class Manager:
    """
    This class describes a title card manager. The Manager is used to control
    title card and archive creation/management from a high level, and is meant
    to be the main entry point of the program.
    """

    """Default execution mode for Manager.run()"""
    DEFAULT_EXECUTION_MODE = 'serial'
    
    """Valid execution modes for Manager.run()"""
    VALID_EXECUTION_MODES = ('serial', 'batch')


    def __init__(self, check_tautulli: bool=True) -> None:
        """
        Constructs a new instance of the Manager. This uses the global
        PreferenceParser object in preferences, and optionally creates
        interfaces as indicated by that parser.

        Args:
            check_tautulli: Whether to check Tautulli integration (for fast
                start).
        """

        # Get the global preferences
        self.preferences = global_objects.pp

        # Optionally integrate with Tautulli
        if check_tautulli and self.preferences.use_tautulli:
            TautulliInterface(
                **self.preferences.tautulli_interface_args
            ).integrate()
            
        # Optionally assign PlexInterface
        self.plex_interface = None
        if self.preferences.use_plex:
            self.plex_interface = PlexInterface(
                **self.preferences.plex_interface_kwargs
            )

        # Optionally assign SonarrInterface(s)
        self.sonarr_interfaces = []
        if self.preferences.use_sonarr:
            self.sonarr_interfaces = [
                SonarrInterface(**kw) for kw in self.preferences.sonarr_kwargs
            ]

        # Optionally assign TMDbInterface
        self.tmdb_interface = None
        if self.preferences.use_tmdb:
            self.tmdb_interface = TMDbInterface(
                **self.preferences.tmdb_interface_kwargs,
            )

        # Setup blank show and archive lists
        self.shows = []
        self.archives = []


    def notify(message: str) -> callable:
        """
        Return a decorator that notifies the given message when the decorated
        function starts executing. Only notify if the global execution mode is
        batch. Logging is done in info level.

        Args:
            message: Message to log.

        Returns:
            Wrapped decorator.
        """

        def decorator(function: callable) -> callable:
            def inner(*args, **kwargs):
                if global_objects.pp.execution_mode == 'batch':
                    log.info(message)

                return function(*args, **kwargs)
            return inner
        return decorator


    def sync_series_files(self) -> None:
        """Update the series YAML files for either Sonarr or Plex."""

        # If neither Sonarr or Plex are enabled, skip
        if not self.preferences.use_sonarr and not self.preferences.use_plex:
            return None

        # Always notify the user
        log.info('Starting to sync to series YAML files..')

        if (self.preferences.use_sonarr
            and len(self.preferences.sonarr_yaml_writers) > 0):
            for writer, update_args in zip(self.preferences.sonarr_yaml_writers,
                                    self.preferences.sonarr_yaml_update_args):
                writer.update_from_sonarr(self.sonarr_interface, **update_args)

        if (self.preferences.use_plex
            and len(self.preferences.plex_yaml_writers) > 0):
            for writer, update_args in zip(self.preferences.plex_yaml_writers,
                                        self.preferences.plex_yaml_update_args):
                writer.update_from_plex(self.plex_interface, **update_args)
        

    @notify('Starting to read series YAML files..')
    def create_shows(self) -> None:
        """
        Create Show and ShowArchive objects for each series YAML files known to
        the global PreferenceParser. This updates the Manager's show and
        archives lists.
        """

        # Go through each Series YAML file
        for show in self.preferences.iterate_series_files():
            # Skip shows whose YAML was invalid
            if not show.valid:
                log.warning(f'Skipping series {show}')
                continue
                
            self.shows.append(show)
            
            # If archives are disabled globally, or for this show - skip 
            if not self.preferences.create_archive or not show.archive:
                continue

            self.archives.append(
                ShowArchive(self.preferences.archive_directory, show)
            )


    @notify('Starting to assign interfaces..')
    def assign_interfaces(self) -> None:
        """
        
        """

        # Assign interfaces for each show
        for show in tqdm(self.shows + self.archives, desc='Assign interfaces',
                         **TQDM_KWARGS):
            show.assign_interfaces(
                self.plex_interface, self.sonarr_interfaces, self.tmdb_interface
            )

    
    @notify("Starting to set show ID's..")
    def set_show_ids(self) -> None:
        """Set the series ID's of each Show known to this Manager"""

        # If neither Sonarr nor TMDb are enabled, skip
        if not self.preferences.use_sonarr and not self.preferences.use_tmdb:
            return None

        # For each show in the Manager, set series IDs
        for show in tqdm(self.shows + self.archives, desc='Setting series IDs',
                         **TQDM_KWARGS):
            # Select interfaces based on what's enabled
            show.set_series_ids(self.sonarr_interfaces, self.tmdb_interface)


    @notify('Starting to read source files..')
    def read_show_source(self) -> None:
        """
        Reads all source files known to this manager. This reads Episode objects
        for all Show and ShowArchives, and also looks for multipart episodes.
        """

        # Read source files for Show objects
        for show in (pbar := tqdm(self.shows + self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Reading source files for {show}')

            show.read_source()
            show.find_multipart_episodes()


    @notify('Starting to add new episodes..')
    def add_new_episodes(self) -> None:
        """Add any new episodes to this Manager's shows."""

        # If Sonarr, Plex, and TMDb are disabled, exit
        if (not self.preferences.use_sonarr and not self.preferences.use_tmdb
            and not self.preferences.use_plex):
            return None

        # For each show in the Manager, look for new episodes using any of the
        # possible interfaces
        for show in (pbar := tqdm(self.shows + self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Adding new episodes for {show}')

            show.add_new_episodes(
                self.sonarr_interface, self.plex_interface, self.tmdb_interface
            )


    @notify("Starting to set episode ID's..")
    def set_episode_ids(self) -> None:
        """Set all episode ID's for all shows known to this manager."""

        # If Sonarr, Plex, and TMDb are disabled, exit
        if (not self.preferences.use_sonarr and not self.preferences.use_tmdb
            and not self.preferences.use_plex):
            return None

        # For each show in the Manager, set IDs for every episode
        for show in (pbar := tqdm(self.shows + self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Setting episode IDs for {show}')

            show.set_episode_ids(
                self.sonarr_interface, self.plex_interface, self.tmdb_interface
            )


    @notify('Starting to add translations..')
    def add_translations(self) -> None:
        """Query TMDb for all translated episode titles (if indicated)."""

        # If the TMDbInterface isn't enabled, skip
        if not self.preferences.use_tmdb:
            return None

        # For each show in the Manager, add translation
        for show in (pbar := tqdm(self.shows + self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Adding translations for {show}')

            show.add_translations(self.tmdb_interface)


    @notify('Starting to download logos..')
    def download_logos(self) -> None:
        """Download logo files for all shows known to this manager."""

        # If the TMDbInterface isn't enabled, skip
        if not self.preferences.use_tmdb:
            return None

        # For each show in the Manager, download a logo
        for show in (pbar := tqdm(self.shows + self.archives,
                                  #desc='Downloading logos',
                                  **TQDM_KWARGS)):
            pbar.set_description(f'Downloading logo for {show}')

            show.download_logo(self.tmdb_interface)


    @notify('Starting to select source images..')
    def select_source_images(self) -> None:
        """
        Select and download the source images for every show known to this
        manager. For each show, this called Show.select_source_images().
        """

        # If Plex and TMDb aren't enabled, skip
        if not self.preferences.use_plex and not self.preferences.use_tmdb:
            return None

        # Go through each show and download source images
        for show in (pbar := tqdm(self.shows + self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Selecting sources for {show}')

            show.select_source_images(self.plex_interface, self.tmdb_interface)


    @notify('Starting to create missing title cards..')
    def create_missing_title_cards(self) -> None:
        """
        Creates all missing title cards for every show known to this Manager.
        For each show, this calls Show.create_missing_title_cards().
        """

        # Go through every show in the Manager, create cards
        for show in (pbar := tqdm(self.shows, **TQDM_KWARGS)):
            pbar.set_description(f'Creating cards for {show}')

            show.create_missing_title_cards()


    @notify('Starting to create season posters..')
    def create_season_posters(self) -> None:
        """Create season posters for all shows known to this Manager."""

        # For each show in the Manager, create its posters
        for show in tqdm(self.shows + self.archives,
                         desc='Creating season posters',**TQDM_KWARGS):
            show.create_season_posters()

    
    @notify('Starting to update Plex..')
    def update_plex(self) -> None:
        """
        Update Plex for all cards for every show known to this Manager. This 
        only executes if Plex is globally enabled. For each show, this calls
        Show.update_plex().
        """

        # If Plex isn't enabled, skip
        if not self.preferences.use_plex:
            return None

        # Go through each show in the Manager, update Plex
        for show in (pbar := tqdm(self.shows, **TQDM_KWARGS)):
            pbar.set_description(f'Updating Plex for {show}')

            show.update_plex(self.plex_interface)


    @notify('Starting to update archives..')
    def update_archive(self) -> None:
        """
        Update the title card archives for every show known to the manager.
        """

        # If archives are globally disabled, skip
        if not self.preferences.create_archive:
            return None

        # Update each archive
        for show_archive in (pbar := tqdm(self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Updating archive for {show_archive}')
            
            show_archive.create_missing_title_cards()


    @notify('Starting to create summaries..')
    def create_summaries(self) -> None:
        """
        Creates summaries for every ShowArchive known to this manager. This
        calls ShowArchive.create_summary() if summaries are globally enabled.
        """

        # If summaries aren't enabled, skip
        if (not self.preferences.create_archive
            or not self.preferences.create_summaries):
            return None

        # Go through each archive and create summaries
        for show_archive in (pbar := tqdm(self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Creating Summary for {show_archive}')

            show_archive.create_summary()


    def __run(self, *, serial: bool=False) -> None:
        """
        Run the Manager. If serial execution is not indicated, then sync is run
        and Show/ShowArchive objects are created.
        
        Args:
            serial: (Keyword only) Whether execution is serial.
        """
        
        # If serial, don't update series files or create shows
        if not serial:
            self.sync_series_files()
            self.create_shows()

        # Always execute these, even in serial mode
        self.set_show_ids()
        self.read_show_source()
        self.add_new_episodes()
        self.set_episode_ids()
        self.add_translations()
        self.download_logos()
        self.select_source_images()
        self.create_missing_title_cards()
        self.create_season_posters()
        self.update_plex()
        self.update_archive()
        self.create_summaries()


    def __run_serially(self) -> None:
        """Run the Manager, executing each step for each show at a time."""

        # Sync YAML files
        self.sync_series_files()

        # Go through each Series YAML file, creating Show/ShowArchive objects
        for show in self.preferences.iterate_series_files():
            # Skip shows whose YAML was invalid
            if not show.valid:
                log.warning(f'Skipping series {show}')
                continue

            # Create ShowArchive object if archive enabled globally + show
            self.shows = [show]
            if self.preferences.create_archive and show.archive:
                archive = ShowArchive(self.preferences.archive_directory, show)
                self.archives = [archive]

            # Run all functions on this series
            self.__run(serial=True)


    def run(self) -> None:
        """Run the Manager either in either serial or batch mode"""

        if self.preferences.execution_mode == 'serial':
            self.__run_serially()
        elif self.preferences.execution_mode == 'batch':
            self.__run()


    def remake_cards(self, rating_keys: Iterable[int]) -> None:
        """
        Remake the title cards associated with the given list of rating keys.
        These keys are used to identify their corresponding episodes within
        Plex.
        
        Args:
            rating_keys: List of Plex rating keys corresponding to Episodes to
                update the cards of.
        """
        
        # Exit if Plex is not enabled
        if not self.preferences.use_plex:
            log.error(f'Cannot remake card if Plex is not enabled')
            return None

        # Get details for each rating key from Plex
        entry_list = []
        for key in rating_keys:
            if len(details := self.plex_interface.get_episode_details(key)) ==0:
                log.error(f'Cannot remake cards, no episodes found')
            else:
                log.debug(f'{len(details)} items associated with rating key {key}')
                entry_list += details

        # Go through every series in all series YAML files
        found = set()
        for show in self.preferences.iterate_series_files():
            # If no more entries, exit
            if len(entry_list) == 0:
                break

            # Check if this show is one of the entries to update
            is_found = False
            for index, (series_info, episode_info, library_name) \
                in enumerate(entry_list):
                # Match the library and series name
                full_match_name = show.series_info.full_match_name
                if (show.valid
                    and show.library_name == library_name
                    and full_match_name == series_info.full_match_name):
                    self.shows = [show]
                    self.__run(serial=True)
                    is_found = True
                    break

            # If an entry was found, delete from list 
            if is_found:
                del entry_list[index]

        # Warn for all entries not found
        for index, (series_info, episode_info, library_name) \
            in enumerate(entry_list):
            if index not in found:
                log.warning(f'Cannot update card for "{series_info}" '
                            f'{episode_info} within library "{library_name}" - '
                            f'no matching YAML entry was found')


    def report_missing(self, file: 'Path') -> None:
        """Report all missing assets for Shows known to the Manager."""

        # Serial mode won't have an accurate show list
        if self.preferences.execution_mode == 'serial':
            self.create_shows()
            self.read_show_source()

        missing = {}
        # Go through each show
        for show in self.shows:
            show_dict = {}
            # Go through each episode for this show, add missing source/cards
            for _, episode in show.episodes.items():
                # Don't report special content as missing
                if episode.episode_info.season_number == 0:
                    continue

                # Add key for this episode
                key = str(episode)
                show_dict[key] = {}

                # If source file doesn't exist, add to report
                if (show.card_class.USES_UNIQUE_SOURCES
                    and not episode.source.exists()):
                    show_dict[key]['source'] = episode.source.name

                # If destination card doesn't exist, add to report
                if (episode.destination is not None
                    and not episode.destination.exists()):
                    show_dict[key]['card'] = episode.destination.name

                # If translation is requested and doesn't exist, add
                missing_translations = [
                    translation['key'] for translation in show.title_languages
                    if not episode.key_is_specified(translation['key'])
                ]
                if len(missing_translations) > 0:
                    show_dict[key]['translations'] = missing_translations

                # Delete entry if no missing assets
                if len(show_dict[key]) == 0:
                    del show_dict[key]

            # Report missing logo if archives and summaries are enabled
            if (show.archive and self.preferences.create_summaries
                and not show.logo.exists()):
                show_dict['logo'] = show.logo.name

            # Report missing backdrop if art style is used
            if ((show.style_set.watched_style_is_art or
                show.style_set.unwatched_style_is_art)
                and not show.backdrop.exists()):
                show_dict['backdrop'] = show.backdrop.name

            # If this show is missing at least one thing, add to missing dict
            if len(show_dict.keys()) > 0:
                missing[str(show)] = show_dict

        # Create parent directories if necessary
        file.parent.mkdir(parents=True, exist_ok=True)

        # Write updated data with this entry added
        with file.open('w', encoding='utf-8') as file_handle:
            dump(missing, file_handle, allow_unicode=True, width=160)

        log.info(f'Wrote missing assets to "{file.resolve()}"')