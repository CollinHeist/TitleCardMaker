from pathlib import Path
from subprocess import run

from modules.Debug import *
from modules.preferences import *

class FontValidator:
    """
    This class describes a font validator.
    """

    def __init__(self, font) -> None:
        """

        """

        pass

    def exists(self) -> bool:
        """

        """

        pass

    def has_all_characters(self, *args, **kwargs) -> bool:
        """
        Determines if characters.
        
        :param      args:    The arguments
        :type       args:    list
        :param      kwargs:  The keywords arguments
        :type       kwargs:  dictionary
        
        :returns:   True if characters, False otherwise.
        :rtype:     bool
        """
        
        pass


    def is_valid_font(self, font: str) -> bool:
        """
        Determines whether the specified font is a valid font for ImageMagick commands.
        
        :param      font:   The font being checked. Either a font name or filepath
                            to a font file
        
        :returns:   True if the specified font is valid font, False otherwise.
        """

        # If the font given is a file, no need to check ImageMagick's list
        if Path(font).exists():
            return True

        # Query ImageMagick for font list, then grep just the font name
        command = 'convert -list font | grep "Font: "'

        font_list = self.image_magick.run_get_stdout(command, capture_output=True).split('\n')

        # Check the given font against all fonts returned
        for font_string in font_list:
            if font in findall(': (.*)', font_string):
                return True

        return False