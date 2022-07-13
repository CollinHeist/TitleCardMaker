from yaml import dump
from tqdm import tqdm

from modules.Debug import log, TQDM_KWARGS
from modules.PlexInterface import PlexInterface
import modules.global_objects as global_objects
from modules.Show import Show
from modules.ShowArchive import ShowArchive
from modules.SonarrInterface import SonarrInterface
from modules.TMDbInterface import TMDbInterface

class Manager:
    """
    This class describes a title card manager. The Manager is used to control
    title card and archive creation/management from a high level, and is meant
    to be the main entry point of the program.
    """

    def __init__(self) -> None:
        """
        Constructs a new instance of the Manager. This uses the global
        PreferenceParser object in preferences, and optionally creates
        interfaces as indicated by that parser.
        """

        # Get the global preferences
        self.preferences = global_objects.pp

        # Optionally assign PlexInterface
        self.plex_interface = None
        if global_objects.pp.use_plex:
            self.plex_interface = PlexInterface(
                url=self.preferences.plex_url,
                x_plex_token=self.preferences.plex_token,
            )

        # Optionally assign SonarrInterface
        self.sonarr_interface = None
        if self.preferences.use_sonarr:
            self.sonarr_interface = SonarrInterface(
                url=self.preferences.sonarr_url,
                api_key=self.preferences.sonarr_api_key,
            )

        # Optionally assign TMDbInterface
        self.tmdb_interface = None
        if self.preferences.use_tmdb:
            self.tmdb_interface = TMDbInterface(self.preferences.tmdb_api_key)

        # Setup blank show and archive lists
        self.shows = []
        self.archives = []


    def create_shows(self) -> None:
        """
        Create Show and ShowArchive objects for each series YAML files known to
        the global PreferenceParser. This updates the Manager's show and
        archives lists.
        """

        # Reset this Manager's list of Show and ShowArchive objects
        self.shows = []
        self.archives = []

        # Go through each Series YAML file
        log.info(f'Starting to read series YAML files..')
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


    def set_show_ids(self) -> None:
        """Set the series ID's of each Show known to this Manager"""

        # If neither Sonarr nor TMDb are enabled, skip
        if not self.sonarr_interface and not self.tmdb_interface:
            return None

        # For each show in the Manager, set series IDs
        log.info(f"Starting to set show ID's..")
        for show in tqdm(self.shows + self.archives, desc='Setting series IDs',
                         **TQDM_KWARGS):
            # Select interfaces based on what's enabled
            show.set_series_ids(self.sonarr_interface, self.tmdb_interface)


    def read_show_source(self) -> None:
        """
        Reads all source files known to this manager. This reads Episode objects
        for all Show and ShowArchives, and also looks for multipart episodes.
        """

        # Read source files for Show objects
        log.info(f'Starting to read source files..')
        for show in tqdm(self.shows, desc='Reading source files',**TQDM_KWARGS):
            show.read_source()
            show.find_multipart_episodes()

        # Read source files for ShowSummary objects
        for archive in tqdm(self.archives, desc='Reading archive source files',
                            **TQDM_KWARGS):
            archive.read_source()
            archive.find_multipart_episodes()


    def add_new_episodes(self) -> None:
        """Add any new episodes to this Manager's shows."""

        # If Sonarr, Plex, and TMDb are disabled, exit
        if (not self.sonarr_interface and not self.plex_interface
            and not self.tmdb_interface):
            return None

        # For each show in the Manager, look for new episodes using any of the
        # possible interfaces
        log.info(f'Starting to add new episodes..')
        for show in tqdm(self.shows + self.archives, desc='Adding new episodes',
                         **TQDM_KWARGS):
            show.add_new_episodes(
                self.sonarr_interface, self.plex_interface, self.tmdb_interface
            )


    def set_episode_ids(self) -> None:
        """Set all episode ID's for all shows known to this manager."""

        # If Sonarr, Plex, and TMDb are disabled, exit
        if (not self.sonarr_interface and not self.plex_interface
            and not self.tmdb_interface):
            return None

        # For each show in the Manager, set IDs for every episode
        log.info(f"Starting to set episode ID's..")
        for show in (pbar := tqdm(self.shows + self.archives, **TQDM_KWARGS)):
            # Update progress bar
            pbar.set_description(f'Selecting episode IDs for '
                                 f'"{show.series_info.short_name}"')

            show.set_episode_ids(
                self.sonarr_interface, self.plex_interface, self.tmdb_interface
            )


    def add_translations(self) -> None:
        """Query TMDb for all translated episode titles (if indicated)."""

        # If the TMDbInterface isn't enabled, skip
        if not self.tmdb_interface:
            return None

        # For each show in the Manager, add translation
        log.info(f'Starting to add translations..')
        for show in (pbar := tqdm(self.shows, **TQDM_KWARGS)):
            pbar.set_description(f'Adding translations for '
                                 f'"{show.series_info.short_name}"')
            show.add_translations(self.tmdb_interface)


    def download_logos(self) -> None:
        """Download logo files for all shows known to this manager."""

        # If the TMDbInterface isn't enabled, skip
        if not self.tmdb_interface:
            return None

        # For each show in the Manager, download a logo
        log.info(f'Starting to download logos..')
        for show in (pbar := tqdm(self.shows + self.archives,
                                  desc='Downloading logos', **TQDM_KWARGS)):
            show.download_logo(self.tmdb_interface)


    def select_source_images(self) -> None:
        """
        Select and download the source images for every show known to this
        manager. For each show, this called Show.select_source_images().
        """

        # Go through each show and download source images
        log.info(f'Starting to select source images..')
        for show in (pbar := tqdm(self.shows, **TQDM_KWARGS)):
            # Update progress bar
            pbar.set_description(f'Selecting sources for '
                                 f'"{show.series_info.short_name}"')

            # Select source images from Plex and/or TMDb
            show.select_source_images(self.plex_interface, self.tmdb_interface)


    def create_missing_title_cards(self) -> None:
        """
        Creates all missing title cards for every show known to this Manager.
        For each show, this calls Show.create_missing_title_cards().
        """

        # Go through every show in the Manager, create cards
        log.info(f'Starting to create missing title cards..')
        for show in (pbar := tqdm(self.shows, **TQDM_KWARGS)):
            # Update progress bar
            pbar.set_description(f'Creating Title Cards for '
                                 f'"{show.series_info.short_name}"')

            # Create cards
            show.create_missing_title_cards()


    def create_season_posters(self) -> None:
        """Create season posters for all shows known to this Manager."""

        # For each show in the Manager, create its posters
        log.info(f'Starting to create season posters..')
        for show in (pbar := tqdm(self.shows + self.archives,
                                 desc='Creating season posters',**TQDM_KWARGS)):
            show.create_season_posters()

    
    def update_plex(self) -> None:
        """
        Update Plex for all cards for every show known to this Manager. This 
        only executes if Plex is globally enabled. For each show, this calls
        Show.update_plex().
        """

        # If Plex isn't enabled, return
        if not self.preferences.use_plex:
            return None

        # Go through each show in the Manager, update Plex
        log.info(f'Starting to update Plex..')
        for show in (pbar := tqdm(self.shows, **TQDM_KWARGS)):
            # Update progress bar
            pbar.set_description(f'Updating Plex for '
                                 f'"{show.series_info.short_name}"')

            show.update_plex(self.plex_interface)


    def update_archive(self) -> None:
        """
        Update the title card archives for every show known to the manager.
        """

        # If archives are globally disabled, skip
        if not self.preferences.create_archive:
            return None

        # Update each archive
        log.info(f'Starting to update archives..')
        for show_archive in (pbar := tqdm(self.archives, **TQDM_KWARGS)):
            # Update progress bar
            pbar.set_description(f'Updating archive for '
                                 f'"{show_archive.series_info.short_name}"')
            
            show_archive.create_missing_title_cards()


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
        log.info(f'Starting to create summaries..')
        for show_archive in (pbar := tqdm(self.archives, **TQDM_KWARGS)):
            # Update progress bar
            pbar.set_description(f'Creating ShowSummary for "'
                                 f'{show_archive.series_info.short_name}"')

            show_archive.create_summary()


    def run(self) -> None:
        """Run the manager and exit."""
        
        self.create_shows()
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


    @staticmethod
    def remake_cards(rating_keys: list[int]) -> None:
        """
        Remake the title cards associated with the given list of rating keys.
        These keys are used to identify their corresponding episodes within
        Plex.
        
        :param      rating_keys:    List of rating keys corresponding to
                                    Episodes to update the cards of.
        """
        
        # Get the global preferences, exit if Plex is not enabled
        preference_parser = global_objects.pp
        if not preference_parser.use_plex:
            log.error(f'Cannot remake card if Plex is not enabled')
            return None

        # Construct PlexInterface
        plex_interface = PlexInterface(
            url=preference_parser.plex_url,
            x_plex_token=preference_parser.plex_token,
        )

        # If TMDb is globally enabled, construct that interface
        tmdb_interface = None
        if preference_parser.use_tmdb:
            tmdb_interface = TMDbInterface(preference_parser.tmdb_api_key)

        # Get details for each rating key, removing 
        entry_list = []
        for key in rating_keys:
            if (details := plex_interface.get_episode_details(key)) is None:
                log.error(f'Cannot remake card, episode not found')
            else:
                entry_list.append(details)

        # Go through every series in all series YAML files
        found = set()
        for show in preference_parser.iterate_series_files():
            # If no more entries, exit
            if len(entry_list) == 0:
                break

            # Check if this show is one of the entries to update
            for index, (series_info, episode_info, library_name) \
                in enumerate(entry_list):
                # Skip entries already found
                if index in found:
                    continue

                # Match the library and series name
                full_match_name = show.series_info.full_match_name
                if (show.valid
                    and show.library_name == library_name
                    and full_match_name == series_info.full_match_name):
                    log.info(f'Remaking "{series_info}" {episode_info} within '
                             f'library "{library_name}"')
                    # Read this show's source
                    show.read_source()

                    # Remake card
                    show.remake_card(episode_info,plex_interface,tmdb_interface)
                    found.add(index)

        # Warn for all entries not found
        for index, (series_info, episode_info, library_name) \
            in enumerate(entry_list):
            if index not in found:
                log.warning(f'Cannot update card for "{series_info}" '
                            f'{episode_info} within library "{library_name}" - '
                            f'no matching YAML entry was found')


    def report_missing(self, file: 'Path') -> None:
        """Report all missing assets for Shows known to the Manager."""

        missing = {}
        # Go through each show
        for show in self.shows:
            show_dict = {}
            # Go through each episode for this show, add missing source/cards
            for _, episode in show.episodes.items():
                # Don't report special content as missing
                if episode.episode_info.season_number == 0:
                    continue

                # If source file doesn't exist, add to report
                if (show.card_class.USES_UNIQUE_SOURCES
                    and not episode.source.exists()):
                    if str(episode) not in show_dict:
                        show_dict[str(episode)] = {}
                    show_dict[str(episode)]['source'] = episode.source.name

                # If destination card doesn't exist, add to report
                if (episode.destination is not None
                    and not episode.destination.exists()):
                    if str(episode) not in show_dict:
                        show_dict[str(episode)] = {}
                    show_dict[str(episode)]['card'] = episode.destination.name

            # Report missing logo if archives and summaries are enabled
            if (show.archive and self.preferences.create_summaries
                and not show.logo.exists()):
                show_dict['logo'] = show.logo.name

            # Report missing backdrop if art style is used
            if (show.watched_style == 'art' or show.unwatched_style == 'art'
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

        log.info(f'Wrote missing assets to "{file.name}"')

        