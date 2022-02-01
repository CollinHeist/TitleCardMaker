from modules.Debug import *
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
        Constructs a new instance of the manager. This uses the global
        `PreferenceParser` object in `preferences`, and optionally creates
        interfaces as indicated by that parser.
        """

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


    def __repr__(self) -> str:
        """
        Returns a unambiguous string representation of the object.
        
        :returns:   String representation of the object.
        """

        return (f'<TitleCardManager(config={self.config}, source_directory='
            f'{self.source_base}, sonarr_interface={self.sonarr_interface}, '
            f'tmdb_interface={self.tmdb_interface}, shows={self.shows}>'
        )


    def create_shows(self) -> None:
        """
        Create `Show` and `ShowArchive` objects for each series entry found
        known to the global `PreferenceParser`. This updates the `shows` and
        `archives` lists with these objects.
        """

        self.shows = []
        self.archives = []
        for show in self.preferences.iterate_series_files():
            # Skip shows whose YAML was invalid
            if not show.valid:
                error(f'Skipping series "{show.name}"')
                continue

            self.shows.append(show)

            # If archives are disabled globally, or for this show.. skip 
            if not self.preferences.create_archive or not show.archive:
                continue

            self.archives.append(
                ShowArchive(
                    self.preferences.archive_directory,
                    show,
                )
            )


    def read_show_source(self) -> None:
        """
        Reads all source files known to this manager. This calls `read_source()`
        on all show and archive objects.
        """

        for show in self.shows:
            if self.sonarr_interface:
                show.read_source(self.sonarr_interface)
            else:
                show.read_source()

        for archive in self.archives:
            archive.read_source()


    def check_sonarr_for_new_episodes(self) -> None:
        """
        Query Sonarr to see if any new episodes exist for every show
        known to this manager. This calls
        `Show.check_sonarr_for_new_epsiodes()`.
        
        :param      show_full_name: The show's full name
        """

        # If sonarr is globally disabled, skip
        if not self.preferences.use_sonarr:
            return None

        for show in self.shows:
            show.check_sonarr_for_new_episodes(self.sonarr_interface)


    def create_missing_title_cards(self) -> None:
        """
        Creates all missing title cards for every show known to this manager.
        For each show, if any new title cards are created, it's Plex metadata is
        updated (if enabled). This calls `Show.create_missing_title_cards()`
        """

        for show in self.shows:
            # Pass the TMDbInterface to the show if globally enabled
            if self.preferences.use_tmdb:
                created = show.create_missing_title_cards(self.tmdb_interface)
            else:
                created = show.create_missing_title_cards()

            # If a card was created and a plex interface is globally enabled
            if created and self.preferences.use_plex:
                self.plex_interface.refresh_metadata(show.library_name, show.full_name)


    def update_archive(self) -> None:
        """
        Update the title card archives for every show known to the manager. This
        calls `ShowArchive.update_archive()` if archives are globally enabled.
        """

        # If archives are globally disabled, skip
        if not self.preferences.create_archive:
            return None

        for show in self.archives:
            if self.preferences.use_tmdb:
                show.update_archive(self.tmdb_interface)
            else:
                show.update_archive()


    def create_summaries(self) -> None:
        """
        Creates summaries for every `ShowArchive` known to this manager. This
        calls `ShowArchive.create_summary()` if summaries are globally enabled.
        """

        if not self.preferences.create_summaries:
            return None

        for show in self.archives:
            show.create_summary()


    def run(self) -> None:
        """
        Run the manager and exit.

        The following functions are executed in the following order:

        `create_shows()`
        `read_show_source()`
        `check_sonarr_for_new_episodes()`
        `create_missing_title_cards()`
        `update_archive()`
        `create_summaries()`
        """

        # Execute everything before waiting
        self.create_shows()
        self.read_show_source()
        self.check_sonarr_for_new_episodes()
        self.create_missing_title_cards()
        self.update_archive()
        self.create_summaries()

        