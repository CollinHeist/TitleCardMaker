from pathlib import Path
from string import whitespace
from typing import Iterable

from fontTools.ttLib import TTFont


class FontValidator:
    """
    This class describes a font validator. A FontValidator takes font
    files and can indicate whether that font contains all the characters
    for some strings (titles).
    """

    """File to the font character validation database"""
    CHARACTER_DATABASE = 'fvm.json'


    def __init__(self, font_file: Path) -> None:
        """
        Constructs a new instance. This reads the font validation map if
        it exists, and creates the file if it does not.
        """

        # Create/read font validation database
        self._file = font_file
        self._font = TTFont(font_file, fontNumber=0)


    def __contains__(self, chars: Iterable[str]) -> bool:
        """
        Evaluate whether the given string of characters exist in this
        object's Font.

        Args:
            chars: Characters being evaluated.

        Returns:
            True if all characters in chars are contained in this Font.
        """

        for char in chars:
            # All whitespace is valid
            if char in whitespace:
                continue

            # Check all tables
            ord_char = ord(char)
            for table in self._font['cmap'].tables:
                # Check character is in cmap
                if ord_char not in table.cmap:
                    return False

                # Check glyph has boundaires (i.e. is not blank)
                try:
                    glyph = self._font['glyf'][table.cmap[ord_char]]
                    if not hasattr(glyph, 'xMin'):
                        return False
                except KeyError:
                    continue

        return True


    def get_missing_characters(self, chars: Iterable[str]) -> set[str]:
        """
        Get all the missing characters from the given chars.

        Args:
            chars: Characters to evluate

        Returns:
            Set of all characters present in this object's database that
            are marked as missing for the given font.
        """

        return {char for char in chars if char not in self}
