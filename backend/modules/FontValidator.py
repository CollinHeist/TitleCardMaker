from fontTools.ttLib import TTFont
from tinydb import where

from modules.Debug import log
from modules.PersistentDatabase import PersistentDatabase


class FontValidator:
    """
    This class describes a font validator. A FontValidator takes font
    files and can indicate whether that font contains all the characters
    for some strings (titles).
    """

    """File to the font character validation database"""
    CHARACTER_DATABASE = 'fvm.json'


    def __init__(self) -> None:
        """
        Constructs a new instance. This reads the font validation map if
        it exists, and creates the file if it does not.
        """

        # Create/read font validation database
        self.__db = PersistentDatabase(self.CHARACTER_DATABASE)


    def __has_character(self, font_filepath: str, character: str) -> bool:
        """
        Determines whether the given character exists in the given Font.

        Args:
            font_filepath: Filepath to the font being validated against
            character: Character being checked.

        Returns:
            True if the given character exists in the given font, False
            otherwise.
        """

        # All fonts have spaces
        if character == ' ':
            return True

        # If character has been checked, return status
        if self.__db.contains((where('file') == font_filepath) &
                              (where('character') == character)):
            return self.__db.get((where('file') == font_filepath) &
                                 (where('character') == character))['status']

        # Get the ordinal value of this character
        glyph = ord(character)

        # Go through each table in this font, return True if in a cmap
        for table in TTFont(font_filepath, fontNumber=0)['cmap'].tables:
            if glyph in table.cmap:
                # Update map for this character, return True
                self.__db.insert({
                    'file': font_filepath,
                    'character': character,
                    'status': True
                })

                return True

        # Update map for this character, return False
        self.__db.insert({
            'file': font_filepath, 'character': character, 'status': False
        })

        return False


    def validate_title(self, font_filepath: str, title: str) -> bool:
        """
        Validate the given Title, returning whether all characters are
        contained within the given Font.

        Args:
            font_filepath: Filepath to the font being validated against
            title: The title being validated.

        Returns:
            True if all characters in the title are found within the
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
                log.warning(f'Character "{char}" missing from "{font_filepath}"')

        return all(has_characters)


    def get_missing_characters(self, font_filepath: str) -> set[str]:
        """
        Get a set of all (known) missing characters for the given font.

        Args:
            font_filepath: Filepath to the font being evaluated.

        Returns:
            Set of all characters present in this object's database that
            are marked as missing for the given font.
        """

        # Get all missing entries
        missing = self.__db.search(
            (where('file') == font_filepath)
            & (where('status') == False) # noqa: E712 # pylint: disable=singleton-comparison
        )

        # Return set of just characters from entries
        return {entry['character'] for entry in missing}
