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

        # Establish directory bases
        self.source_base = self.preferences.source_directory
        self.archive_base = self.preferences.archive_directory

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


    def read_show_source(self) -> None:
        """
        Reads all source files known to this manager. This reads Episode objects
        for all Show and ShowArchives, and also looks for multipart episodes.
        """

        # Read source files for Show objects
        for show in tqdm(self.shows, desc='Reading source files',**TQDM_KWARGS):
            show.read_source()
            show.find_multipart_episodes()

        # Read source files for ShowSummary objects
        for archive in tqdm(self.archives, desc='Reading archive source files',
                            **TQDM_KWARGS):
            archive.read_source()
            archive.find_multipart_episodes()


    def check_tmdb_for_translations(self) -> None:
        """Query TMDb for all translated episode titles (if indicated)."""

        # If the TMDbInterface isn't enabled, skip
        if not self.tmdb_interface:
            return None

        # For each show in the Manager, add translation
        for show in (pbar := tqdm(self.shows, **TQDM_KWARGS)):
            pbar.set_description(f'Adding translations for '
                                 f'"{show.series_info.short_name}"')
            show.add_translations(self.tmdb_interface)


    def check_sonarr_for_new_episodes(self) -> None:
        """
        Query Sonarr to see if any new episodes exist for every show known to
        this manager.
        """

        # If Sonarr is globally disabled, skip
        if not self.preferences.use_sonarr:
            return None

        # Go through each show in the Manager and query Sonarr
        for show in tqdm(self.shows + self.archives, desc='Querying Sonarr',
                         **TQDM_KWARGS):
            show.query_sonarr(self.sonarr_interface)


    def select_source_images(self) -> None:
        """
        Select and download the source images for every show known to this
        manager. For each show, this called Show.select_source_images().
        """

        # Go through each show and download source images
        for show in (pbar := tqdm(self.shows, **TQDM_KWARGS)):
            # Update progress bar
            pbar.set_description(f'Selecting sources for '
                                 f'"{show.series_info.short_name}"')

            # Select source images from Plex and/or TMDb
            interfaces = {'plex_interface': None, 'tmdb_interface': None}
            if self.preferences.use_plex:
                interfaces['plex_interface'] = self.plex_interface
            if self.preferences.use_tmdb:
                interfaces['tmdb_interface'] = self.tmdb_interface

            # Pass enabled interfaces
            show.select_source_images(**interfaces)


    def create_missing_title_cards(self) -> None:
        """
        Creates all missing title cards for every show known to this Manager.
        For each show, this calls Show.create_missing_title_cards().
        """

        # Go through every show in the Manager, create cards
        for show in (pbar := tqdm(self.shows, **TQDM_KWARGS)):
            # Update progress bar
            pbar.set_description(f'Creating Title Cards for '
                                 f'"{show.series_info.short_name}"')

            # Create cards
            show.create_missing_title_cards()

    
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
        for show in (pbar := tqdm(self.shows, **TQDM_KWARGS)):
            # Update progress bar
            pbar.set_description(f'Updating Plex for '
                                 f'"{show.series_info.short_name}"')

            show.update_plex(self.plex_interface)


    def update_archive(self) -> None:
        """
        Update the title card archives for every show known to the manager. This
        calls ShowArchive.update_archive() if archives are globally enabled.
        """

        # If archives are globally disabled, skip
        if not self.preferences.create_archive:
            return None

        for show_archive in (pbar := tqdm(self.archives, **TQDM_KWARGS)):
            # Update progress bar
            pbar.set_description(f'Updating archive for '
                                 f'"{show_archive.series_info.short_name}"')
            
            show_archive.update_archive()


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
            # Update progress bar
            pbar.set_description(f'Creating ShowSummary for "'
                                 f'{show_archive.series_info.short_name}"')

            # If TMDb is globally enabled, pass the interface along
            if self.preferences.use_tmdb:
                show_archive.create_summary(self.tmdb_interface)
            else:
                show_archive.create_summary()


    def run(self) -> None:
        """Run the manager and exit."""
        
        self.create_shows()
        self.read_show_source()
        self.check_sonarr_for_new_episodes()
        self.check_tmdb_for_translations()
        self.select_source_images()
        self.create_missing_title_cards()
        self.update_plex()
        self.update_archive()
        self.create_summaries()


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
                if not episode.source.exists():
                    if str(episode) not in show_dict:
                        show_dict[str(episode)] = {}
                    show_dict[str(episode)]['source'] = episode.source.name

                # If destination card doesn't exist, add to report
                if (episode.destination != None
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

        