from pathlib import Path
from time import sleep
from xml.etree.ElementTree import parse, ParseError

from modules.Debug import *
from modules.Show import Show
from modules.ShowArchive import ShowArchive

class Manager:
    """
    This class describes a title card manager. The manager is used to control
    title card and archive creation/management from a high level.
    """

    def __init__(self, config: str, source_directory: str, archive_directory: str,
                 sonarr_interface: 'SonarrInterface',
                 database_interface: 'DatabaseInterface',
                 plex_interface: 'PlexInterface') -> None:

        # Setup Path for the config file
        self.__config_file = Path(config)
        self.config = parse(self.__config_file.resolve())

        # Read all specified libraries
        self.libraries = {
            e.attrib['name']: Path(e.text) for e in self.config.findall('library')
        }   

        # Establish directory bases
        self.source_base = Path(source_directory)
        self.archive_base = Path(archive_directory) if archive_directory else None

        # Assign each interface
        self.sonarr_interface = sonarr_interface
        self.database_interface = database_interface
        self.plex_interface = plex_interface

        # Setup blank show dictionary
        self.shows = {}
        self.archives = {}


    def __repr__(self) -> str:
        """
        Returns a unambiguous string representation of the object (for debug...).
        
        :returns:   String representation of the object.
        """

        return (f'<TitleCardManager(config={self.config}, source_directory='
            f'{self.source_base}, sonarr_interface={self.sonarr_interface}, '
            f'database_interface={self.database_interface}, shows={self.shows}>'
        )


    def create_shows(self) -> None:
        """
        Creates Show objects for each <show> element in this object's config file.
        """

        # Re-parse config file
        try:
            self.config = parse(self.__config_file.resolve())
        except ParseError:
            error(f'Config file has typo - cannot parse')
            return
        
        # Store object under each show's full name in the shows dictionary
        for show_element in self.config.findall('show'):
            # Ensure this show's library exists in the library map, if not error and skip
            library = show_element.attrib['library']
            if library not in self.libraries:
                error(f'Library "{library}" does not have an associated <library> element')
                continue

            # Create a show object for this element
            show_object = Show(
                show_element,
                self.source_base,
                self.libraries[library],
                show_element.attrib['library'],
            )

            # If this show object already exists, skip
            if show_object.full_name in self.shows:
                continue

            self.shows[show_object.full_name] = show_object

            # If an archive is not specified, skip
            if not self.archive_base:
                continue

            self.archives[show_object.full_name] = ShowArchive(
                self.archive_base,
                show_element,
                self.source_base,
                self.libraries[library],
            )


    def read_show_source(self) -> None:
        """
        Reads all source files known to this manager. This calls
        `Show.read_source()`.
        """

        for _, show in self.shows.items():
            show.read_source()

        for _, archive in self.archives.items():
            archive.read_source()


    def check_sonarr_for_new_episodes(self) -> None:
        """
        Query Sonarr to see if any new episodes exist for every show
        known to this manager. This calls
        `Show.check_sonarr_for_new_epsiodes()`.
        
        :param      show_full_name: The show's full name
        """
        
        for _, show in self.shows.items():
            show.check_sonarr_for_new_episodes(self.sonarr_interface)


    def create_missing_title_cards(self) -> None:
        """
        Creates all missing title cards for every show known to this
        manager. For each show, if any new title cards are created, it's
        Plex metadata is updated. This calls `Show.create_missing_title_cards()`.
        """

        for _, show in self.shows.items():
            # A show that created new cards will return True
            if show.create_missing_title_cards(self.database_interface):
                self.plex_interface.refresh_metadata(show.library, show.full_name)


    def update_archive(self) -> None:
        """
        Update the title card archives for every show known to this object.
        This calls `Show.update_archive()`.
        
        :param      show_full_name: The shows full name.
        """

        for _, show in self.archives.items():
            show.update_archive(self.database_interface)


    def create_summaries(self) -> None:
        """
        Creates summaries.
        """

        for _, show in self.archives.items():
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

        