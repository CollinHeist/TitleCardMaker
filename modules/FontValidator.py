from pathlib import Path

from fontTools.ttLib import TTFont
from yaml import safe_load, dump

from modules.Debug import log

class FontValidator():

    FONT_VALIDATION_MAP = Path(__file__).parent / '.objects' / 'fvm.yml'

    def __init__(self) -> None:
        """
        Constructs a new instance. This creates the parent directory for the 
        temporary font map if it exists, and reads the font map if possible.
        """

        # Attept to read existing font file if it exists
        if self.FONT_VALIDATION_MAP.exists():
            with self.FONT_VALIDATION_MAP.open('r') as file_handle:
                self.__fonts = safe_load(file_handle)['fonts']
        else:
            # Create parent directories if necessary
            self.FONT_VALIDATION_MAP.parent.mkdir(parents=True, exist_ok=True)
            self.__fonts = {}


    def __set_character(self, font_key: str, character: str,
                        status: bool) -> None:
        """
        Set the given character for the given font to the given status, then
        write the updated font map to file.
        
        :param      font_key:   The font key
        :param      character:  The character
        :param      status:     The status
        """

        # Set the given status within the map
        if font_key in self.__fonts:
            self.__fonts[font_key][character] = status
        else:
            self.__fonts[font_key] = {character: status}

        # Write updated map to file
        with self.FONT_VALIDATION_MAP.open('w') as file_handle:
            dump({'fonts': self.__fonts}, file_handle, allow_unicode=True)


    def __has_character(self, font: Path, character: str) -> bool:
        """
        Determines whether the given character exists in the given font. 
        
        :param      font:   Path to the font file being validated.
        :param      title:  The Title being validated.
        
        :returns:   True if the given character exists in the given font, False
                    otherwise.
        """

        # Get the key for this font, and ordinal value of this character
        font_key = str(font.resolve())
        glyph = ord(character)

        # If this font and character has been checked, return that
        if (font_key in self.__fonts
            and character in self.__fonts[font_key]):
            return self.__fonts[font_key][character]

        # Go through each table in this font, return True if in a cmap
        for table in TTFont(font.resolve())['cmap'].tables:
            if glyph in table.cmap:
                # Update map for this character, return True
                self.__set_character(font_key, character, True)
                return True

        # Update map for this character, return False
        self.__set_character(font_key, character, False)
        log.debug(f'Character "{character}"" not in font "{font_key}"')
        return False


    def validate_title(self, font: Path, title: 'Title') -> bool:
        """
        Validate the given Title, returning whether all characters are contained
        within the given font.
        
        :param      font:   Path to the font file being validated.
        :param      title:  The Title being validated.
        
        :returns:   True if all characters in the title are found within the
                    given font, False otherwise.
        """

        # Map __has_character() to all characters in the title
        has_characters = map(
            lambda char: self.__has_character(font, char),
            title.full_title
        )

        return all(has_characters)


    def validate_episode_titles(self, font: Path,
                                datafile_interface: 'DataFileInterface') ->bool:
        """

        """

        invalid = False
        for data in datafile_interface.read():
            invalid |= not self.validate_title(font, data['episode_info'].title)

        return not invalid



# from yaml import safe_load
# from pathlib import Path

# with Path('data.yml').open('r') as fh:
#     yaml = safe_load(fh)

# all_titles = ''
# for season_key, season in yaml['data'].items():
#     for episode_number, episode in season.items():
#         all_titles += episode['title']

# alpha = 'abcdefghijklmnopqrstuvwxyz'

# missing = set(all_titles)-set(alpha)-set(alpha.upper())
# print(''.join(missing))
