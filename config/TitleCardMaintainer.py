from pathlib import Path
from xml.etree.ElementTree import parse

from Debug import *
from Show import Show

class TitleCardMaintainer:
    def __init__(self, config_xml: Path, source_directory: Path,
                 archive_directory: Path) -> None:

        """
        Constructs a new instance.
        
        :param      config_xml:        The configuration xml
        :type       config_xml:        Path
        :param      source_directory:  The source directory
        :type       source_directory:  Path
        """
        
        # Initialize shows to an empty dict, then attempt to read from existing pickle
        self.shows = {}
        self.source_directory = source_directory
        self.archive_directory = archive_directory

        # ...
        self._config_xml = config_xml
        self.config = None
        self.libraries = {}

        self.read_config()
        self.create_shows()
        self.read_show_data()


    def __contains__(self, show_name: str) -> bool:
        """
        { function_description }
        
        :param      show_name:  The show name
        :type       show_name:  str
        
        :returns:   { description_of_the_return_value }
        :rtype:     bool
        """

        return show_name in self.shows


    def __getitem__(self, show_name: str) -> Show:
        """
        { function_description }
        
        :param      show_name:  The show name
        :type       show_name:  str
        
        :returns:   { description_of_the_return_value }
        :rtype:     Show
        """

        return self.shows[show_name]


    def read_config(self) -> None:
        """
        { function_description }
        
        :returns:   { description_of_the_return_value }
        :rtype:     None
        """

        # Parse the XML file into an ElementTree
        self.config = parse(self._config_xml.resolve())

        # Read all specified libraries
        self.libraries = {e.attrib['name']: e.text for e in self.config.findall('library')}


    def create_shows(self) -> None:
        """
        Reads a configuration.
        
        :returns:   { description_of_the_return_value }
        :rtype:     { return_type_description }
        """

        self.shows = {}
        for show_element in self.config.findall('show'):
            show_object = Show(
                self.source_directory,
                self.archive_directory,
                self.libraries,
                show_element,
            )
            self.shows.update({show_object.name: show_object})


    def read_show_data(self) -> None:
        """
        Reads a show data.
        
        :returns:   { description_of_the_return_value }
        :rtype:     None
        """

        for _, show in self.shows.items():
            try:
                show.read_source_data()
            except:
                error(f'Show {show} does not have an associated source data file.')


    def create_missing_title_cards(self, show_name: str=None) -> None:
        """
        Create missing title cards. If show_name is provided, only that show's
        title cards are created; otherwise all shows.
        
        :returns:   { description_of_the_return_value }
        :rtype:     None
        """

        if show_name is None:
            for _, show in self.shows.items():
                info(f'Creating Title Cards for {show.name}')
                show.create_missing_title_cards()
        else:
            if show_name in self:
                self[show_name].create_missing_title_cards()
            else:
                error(f'Show "{show_name}" does not have an associated Show object.')

