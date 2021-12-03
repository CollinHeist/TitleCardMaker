from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from xml.etree.ElementTree import parse, ParseError

from Debug import *
from Show import Show
from ShowArchive import ShowArchive

class TitleCardManager:
    """
    This class describes a title card manager. The manager is used to manage
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

        # Establish source base
        self.source_base = Path(source_directory)
        self.archive_base = Path(archive_directory)

        # Intialize each interface
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
        
        # Store Show object under each show's full name in the shows dictionary
        for show_element in self.config.findall('show'):
            show_object = Show(
                show_element,
                self.source_base,
                self.libraries[show_element.attrib['library']],
            )

            archive_object = ShowArchive(
                self.archive_base,
                show_element,
                self.source_base,
                self.libraries[show_element.attrib['library']],
            )

            if show_object.full_name in self.shows:
                continue

            self.shows[show_object.full_name] = show_object
            self.archives[show_object.full_name] = archive_object


    def read_show_source(self) -> None:
        """
        Reads all source files known to this manager. This calls
        `Show.read_source()`.
        """

        for _, show in self.shows.items():
            show.read_source()


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
            status = show.create_missing_title_cards(self.database_interface)
            
            # If a new title card was created, update Plex
            if status == show.CREATED_NEW_TITLE_CARDS:
                self.plex_interface.refresh_metadata(show.library, show.full_name)


    def update_archive(self) -> None:
        """
        Update the title card archives for every show known to this object.
        This calls `Show.update_archive()`.
        
        :param      show_full_name:  The show full name
        """

        for _, show in self.archives.items():
            show.update_archive(self.database_interface)


    def main_loop(self, interval: int=600) -> None:
        """
        Infinite loop meant to be the entrypoint of this class. All primary
        methods are called at the given interval. Multithreading is not used,
        so there is no guarantee these methods will be executed in time.

        The following functions are executed in the following order:

        `create_shows()`
        `read_show_source()`
        `check_sonarr_for_new_episodes()`
        `create_missing_title_cards()`
        `update_archive()`.

        And these are executed immediately upon call (waiting `interval` seconds
        after that first execution).
        
        :param      interval:   The interval, in seconds, to wait between
                                instances of execution.
        """

        # Execute everything before waiting
        self.create_shows()
        self.read_show_source()
        self.check_sonarr_for_new_episodes()
        self.create_missing_title_cards()
        self.update_archive()

        # Infinite loop 
        last_execution = datetime.now()
        while True:
            if datetime.now() - last_execution >= timedelta(seconds=interval):
                self.create_shows()
                self.read_show_source()
                self.check_sonarr_for_new_episodes()
                self.create_missing_title_cards()
                self.update_archive()
                last_execution = datetime.now()

            # Calculate how long to sleep
            wait_time = interval - (datetime.now() - last_execution).seconds
            sleep(max(wait_time, 0))

        