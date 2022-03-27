from yaml import dump
from tqdm import tqdm

from modules.Debug import log
from modules.PlexInterface import PlexInterface
import modules.preferences as global_preferences
from modules.Show import Show
from modules.ShowArchive import ShowArchive
from modules.SonarrInterface import SonarrInterface
from modules.TMDbInterface import TMDbInterface

class Manager:
    """
    This class describes a title card manager. The manager is used to control
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
        self.preferences = global_preferences.pp

        # Establish directory bases
        self.source_base = self.preferences.source_directory
        self.archive_base = self.preferences.archive_directory

        # Optionally assign PlexInterface
        self.plex_interface = None
        if global_preferences.pp.use_plex:
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

            # If archives are disabled globally, or for this show.. skip 
            if not self.preferences.create_archive or not show.archive:
                continue

            self.archives.append(
                ShowArchive(self.preferences.archive_directory, show)
            )


    def check_tmdb_for_translations(self) -> None:
        """Query TMDb for all translated episode titles (if indicated)."""

        # If the TMDbInterface isn't enabled, skip
        if not self.tmdb_interface:
            return None

        # For each show in the Manager, add translation
        modified = False
        for show in (pbar := tqdm(self.shows)):
            pbar.set_description(f'Adding translations for '
                                 f'"{show.series_info.short_name}"')
            modified |= show.add_translations(self.tmdb_interface)


    def read_show_source(self) -> None:
        """
        Reads all source files known to this manager. This reads Episode objects
        for all Show and ShowArchives, and also looks for multipart episodes.
        """

        for show in tqdm(self.shows, desc='Reading source files'):
            show.read_source()
            show.find_multipart_episodes()

        for archive in tqdm(self.archives, desc='Reading archive source files'):
            archive.read_source()
            archive.find_multipart_episodes()


    def check_sonarr_for_new_episodes(self) -> None:
        """
        Query Sonarr to see if any new episodes exist for every show known to
        this manager.
        """

        # If sonarr is globally disabled, skip
        if not self.preferences.use_sonarr:
            return None

        for show in tqdm(self.shows, desc='Querying Sonarr'):
            show.check_sonarr_for_new_episodes(self.sonarr_interface)


    def create_missing_title_cards(self) -> None:
        """
        Creates all missing title cards for every show known to this manager.
        For each show, if any new title cards are created, it's Plex metadata is
        updated (if enabled). This calls Show.create_missing_title_cards().
        """

        for show in (pbar := tqdm(self.shows)):
            # Update progress bar
            pbar.set_description(f'Creating Title Cards for '
                                 f'"{show.series_info.short_name}"')

            # Pass the TMDbInterface to the show if globally enabled
            if self.preferences.use_tmdb and self.preferences.use_sonarr:
                created = show.create_missing_title_cards(
                    self.tmdb_interface, self.sonarr_interface
                )
            elif self.preferences.use_tmdb:
                created = show.create_missing_title_cards(self.tmdb_interface)
            else:
                created = show.create_missing_title_cards()

            # If a card was created and a plex interface is globally enabled
            if created and self.preferences.use_plex:
                self.plex_interface.refresh_metadata(
                    show.library_name,
                    show.series_info
                )


    def update_archive(self) -> None:
        """
        Update the title card archives for every show known to the manager. This
        calls ShowArchive.update_archive() if archives are globally enabled.
        """

        # If archives are globally disabled, skip
        if not self.preferences.create_archive:
            return None

        for show_archive in (pbar := tqdm(self.archives)):
            # Update progress bar
            pbar.set_description(f'Updating archive for '
                                 f'"{show_archive.series_info.short_name}"')

            # Depending on which interfaces are enabled, pass those along
            if self.preferences.use_tmdb and self.preferences.use_sonarr:
                show_archive.update_archive(
                    self.tmdb_interface, self.sonarr_interface
                )
            elif self.preferences.use_tmdb:
                show_archive.update_archive(self.tmdb_interface)
            else:
                show_archive.update_archive()


    def create_summaries(self) -> None:
        """
        Creates summaries for every ShowArchive known to this manager. This
        calls ShowArchive.create_summary()` if summaries are globally enabled.
        """

        if not self.preferences.create_summaries:
            return None

        for show_archive in (pbar := tqdm(self.archives)):
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
        self.read_show_source()
        self.check_tmdb_for_translations()
        self.read_show_source()
        self.create_missing_title_cards()
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
                if not episode.source.exists():
                    show_dict[str(episode)] = {}
                    show_dict[str(episode)]['source'] = episode.source.name
                if (episode.destination != None
                    and not episode.destination.exists()):
                    show_dict[str(episode)]['card'] = episode.destination.name

            if not show.logo.exists():
                show_dict['logo'] = show.logo.name

            if len(show_dict.keys()) > 0:
                missing[str(show)] = show_dict

        # Create parent directories if necessary
        file.parent.mkdir(parents=True, exist_ok=True)

        # Write updated data with this entry added
        with file.open('w') as file_handle:
            dump(missing, file_handle, allow_unicode=True, width=120)

        log.info(f'Wrote missing assets to "{file.name}"')



        