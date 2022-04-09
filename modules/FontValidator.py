from pathlib import Path

from fontTools.ttLib import TTFont
from yaml import safe_load, dump

from modules.Debug import log

class FontValidator:
    """
    This class describes a font validator. A FontValidator takes font files and
    can indicate whether that font contains all the characters for some strings
    (titles).
    """

    """File to the font validation map that persists between runs"""
    FONT_VALIDATION_MAP = Path(__file__).parent / '.objects' / 'fvm.yml'

    def __init__(self) -> None:
        """
        Constructs a new instance. This creates the parent directory for the 
        temporary font map if it exists, and reads the font map if it exists.
        """

        # Attept to read existing font file if it exists
        if self.FONT_VALIDATION_MAP.exists():
            with self.FONT_VALIDATION_MAP.open('r') as file_handle:
                self.__fonts = safe_load(file_handle)['fonts']
        else:
            # Create parent directories if necessary
            self.FONT_VALIDATION_MAP.parent.mkdir(parents=True, exist_ok=True)
            self.__fonts = {}

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


    def __set_character(self, font_filepath: str, character: str,
                        status: bool) -> None:
        """
        Set the given character for the given font to the given status, then
        write the updated font map to file.
        
        :param      font_filepath:  Filepath to the font being validated against
        :param      character:      The character whose status is being set.
        :param      status:         Whether the given font has the given
                                    character.
        """

        # Set the given status within the map
        if font_filepath in self.__fonts:
            self.__fonts[font_filepath][character] = status
        else:
            self.__fonts[font_filepath] = {
                character: status, ' ': True,
            }

        # Write updated map to file
        with self.FONT_VALIDATION_MAP.open('w') as file_handle:
            dump({'fonts': self.__fonts}, file_handle, allow_unicode=True)


    def __has_character(self, font_filepath: str, character: str) -> bool:
        """
        Determines whether the given character exists in the given Font. 
        
        :param      font_filepath:  Filepath to the font being validated against
        :param      title:          The Title being validated.
        
        :returns:   True if the given character exists in the given font, False
                    otherwise.
        """

        # If this font and character has been checked, return that
        if (status := self.__fonts.get(font_filepath, {}).get(character, None)):
            return status

        # Get the ordinal value of this character
        glyph = ord(character)

        # Go through each table in this font, return True if in a cmap
        for table in TTFont(font_filepath)['cmap'].tables:
            if glyph in table.cmap:
                # Update map for this character, return True
                self.__set_character(font_filepath, character, True)
                return True

        # Update map for this character, return False
        self.__set_character(font_filepath, character, False)
        
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

