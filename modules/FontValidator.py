from pathlib import Path

from fontTools.ttLib import TTFont
from tinydb import TinyDB, where

from modules.Debug import log

class FontValidator:
    """
    This class describes a font validator. A FontValidator takes font files and
    can indicate whether that font contains all the characters for some strings
    (titles).
    """

    """File to the font character validation database"""
    CHARACTER_DATABASE = Path(__file__).parent / '.objects' / 'fvm.json'
    

    def __init__(self) -> None:
        """
        Constructs a new instance. This creates the parent directory for the 
        temporary validation database if it does not exist, and reads it if it
        does.
        """

        # Create/read font validation database
        self.CHARACTER_DATABASE.parent.mkdir(parents=True, exist_ok=True)
        self.__db = TinyDB(self.CHARACTER_DATABASE)

        # List of missing characters that have already been warned
        self.__warned = []


    def __warn_missing(self, char: str, font_filepath: str) -> None:
        """
        Warn a given character is missing from a given font, but only if it 
        hasn't already been warned.
        
        :param      char:           The missing character
        :param      font_filepath:  Filepath to the relevant font.
        """

        # If this character (for this font) has already been warned, return
        if (key := f'{char}-{font_filepath}') in self.__warned:
            return None

        # Character (and font) hasn't been warned yet - warn and add to list
        log.warning(f'Character "{char}" missing from "{font_filepath}"')
        self.__warned.append(key)


    def __has_character(self, font_filepath: str, character: str) -> bool:
        """
        Determines whether the given character exists in the given Font. 
        
        :param      font_filepath:  Filepath to the font being validated against
        :param      character:      Character being checked.
        
        :returns:   True if the given character exists in the given font, False
                    otherwise.
        """

        # All fonts have spaces
        if character == ' ':
            return True

        # If character has been checked, return status
        if self.__db.contains((where('file') == font_filepath) &
                              (where('character') == character)):
            # Get entry, return status
            return self.__db.get((where('file') == font_filepath) &
                                 (where('character') == character))['status']

        # Get the ordinal value of this character
        glyph = ord(character)

        # Go through each table in this font, return True if in a cmap
        for table in TTFont(font_filepath, fontNumber=0)['cmap'].tables:
            if glyph in table.cmap:
                # Update map for this character, return True
                self.__db.insert({
                    'file': font_filepath, 'character': character, 'status':True
                })

                return True

        # Update map for this character, return False
        self.__db.insert({
            'file': font_filepath, 'character': character, 'status': False
        })

        return False


    def validate_title(self, font_filepath: str, title: str) -> bool:
        """
        Validate the given Title, returning whether all characters are contained
        within the given Font.
        
        :param      font_filepath:  Filepath to the font being validated against
        :param      title:          The title being validated.
        
        :returns:   True if all characters in the title are found within the
                    given font, False otherwise.
        """

        # Map __has_character() to all characters in the title
        has_characters = tuple(map(
            lambda char: self.__has_character(font_filepath, char),
            (title := title.replace('\n', ''))
        ))

        # Log all missing characters
        for char, has_character in zip(title, has_characters):
            if not has_character:
                self.__warn_missing(char, font_filepath)

        return all(has_characters)

