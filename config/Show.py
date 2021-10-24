from csv import reader
from pathlib import Path
from xml.etree.ElementTree import parse

from DataFileInterface import DataFileInterface
from TitleCard import TitleCard
from TitleCardProfile import TitleCardProfile
from TitleCardMaker import TitleCardMaker

class Show:
    """
    This class describes a show.
    """

    def __init__(self, base_source: Path, archive_directory: Path,
                 libraries: dict, show_element: 'Element') -> None:

        # Parse <name> attribute
        self.name = show_element.attrib['name']

        # Parse <seasons> attribute
        self.season_count = int(show_element.attrib['seasons'])

        # Parse <library> attribute, match it to the path from the library dict
        self.media_directory = Path(libraries[show_element.attrib['library']]) / self.name

        # Parse <font> tag (if present) - supported fonts are `convert -list font`
        font = show_element.find('font')
        self.font = TitleCardMaker.TITLE_DEFAULT_FONT if font is None else font.text

        # Parse <font> tag's <color> attribute (if present)
        if font is None:
            self.font_color = TitleCardMaker.TITLE_DEFAULT_COLOR
        else:
            try:
                self.font_color = font.attrib['color']
            except KeyError:
                self.font_color = TitleCardMaker.TITLE_DEFAULT_COLOR

        # Parse <season_map> tag (if present) - default is 1:Season 1, 2:Season 2, etc.
        self.season_map = {n: f'Season {n}' for n in range(1, self.season_count+1)}
        self.season_map.update({0: 'SPECIALS'})
        for season in show_element.findall('season_map/'):
            self.season_map.update({
                int(season.attrib['number']): season.attrib['name']
            })

       # Parse <profile> tag (if present) into a Profile object
        self.profile = TitleCardProfile(
            show_element.find('profile'), archive_directory,
            self.font, self.font_color, self.season_map,
        )

        # Initialize the data file interface
        self._file_interface(base_source / self.name / DataFileInterface.GENERIC_DATA_FILE_NAME)

        # Set base archive directory
        self.archive_directory = archive_directory

        # Create empty data list until a read is initated
        self.title_cards = []


    def __repr__(self) -> str:
        """
        Returns a unambiguous string representation of the object (for debug).
        
        :returns:   String representation of the object.
        """

        return f'<Show object for "{self.name}" media at "{self.media_directory.resolve()}">'


    def __iter__(self) -> 'Iterable':
        """
        Creates an iterator for this container.
        
        :returns:   The iterator.
        :rtype:     { return_type_description }
        """

        yield from self.title_cards


    def read_source_data(self) -> None:
        """
        Reads the data CSV for a specific show, storing TitleCard objects for that row
        in self.title_cards.
        
        :param      file:  The file to read
        
        :returns:   List of dictionaries with an entry for each row in the source CSV.
                    Each dictionary has keys for output path, title lines, season, and
                    episode numbers.
        """

        for data_row in self._file_interface.read():
            self.title_cards.append(
                TitleCard(
                    row,
                    self.media_directory,
                    self.source_directory,
                    self.profile
                )
            )


    def create_missing_title_cards(self) -> None:
        """
        Creates missing title cards.
        
        :returns:   { description_of_the_return_value }
        :rtype:     None
        """

        for title_card in self:
            title_card.create()


