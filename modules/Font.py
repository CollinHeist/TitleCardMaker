from pathlib import Path
from re import compile as re_compile

from modules.Debug import log
import modules.global_objects as global_objects
from modules.YamlReader import YamlReader

class Font(YamlReader):
    """
    This class describes a font and all of its configurable attributes.
    Notably, it's color, size, file, replacements, case function,
    vertical offset,  interline spacing, kerning, and stroke width.
    """

    """Valid YAML attributes to customize a font"""
    VALID_ATTRIBUTES = (
        'validate', 'color', 'size', 'file', 'case', 'replacements',
        'vertical_shift', 'interline_spacing', 'kerning', 'stroke_width',
    )

    """Compiled regex to identify percentage values for scalars"""
    _PERCENT_REGEX = re_compile(r'^-?\d+\.?\d*%$')
    _PERCENT_REGEX_POSITIVE = re_compile(r'^\d+\.?\d*%$')

    __slots__ = (
        '__card_class', '__series_info', '__validator', '__validate', 'color',
        'size', 'file', 'replacements', 'delete_missing', 'case_name', 'case',
        'vertical_shift', 'interline_spacing', 'kerning', 'stroke_width',
    )


    def __init__(self, yaml: dict, card_class: 'CardType',
            series_info: 'SeriesInfo') -> None:
        """
        Construct a new instance of a Font.

        Args:
            yaml: 'font' dictionary from a series YAML file.
            card_class:  CardType subclass to get default values from.
            series_info: Associated SeriesInfo (for logging).
        """

        # Initialize parent YamlReader
        super().__init__(yaml)

        # Store arguments
        self.__card_class = card_class
        self.__series_info = series_info

        # Use the global FontValidator object
        self.__validator = global_objects.fv

        # Set generic font attributes
        self.reset()

        # Parse YAML, update attributes and validity
        self.__parse_attributes()


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'<Font for series "{self.__series_info}">'


    @property
    def custom_hash(self) -> str:
        """Custom string to hash for this object for record keeping"""

        font_file_name = Path(self.file).name

        return (f'{self.color}|{self.size}|{font_file_name}|{self.replacements}'
                f'|{self.case_name}|{self.vertical_shift}'
                f'|{self.interline_spacing}|{self.kerning}|{self.stroke_width}')


    def __error(self,
            attribute: str,
            value: str,
            description: Optional[str] = None) -> None:
        """
        Print an error message for the given attribute of the given
        value. Also sets the valid attribute of this object to False.

        Args:
            attribute: Font attribute that is incorrect.
            value: Value of attribute that is incorrect.
            description: Optional description for why the given value is
                wrong.
        """

        description_tag = f' - {description}' if description else ''
        log.error(f'Font {attribute} "{value}" of series {self.__series_info} '
                  f'is invalid{description_tag}')
        self.valid = False


    def __parse_attributes(self) -> None:
        """Parse this object's YAML and update the validity and attributes."""

        # Whether to validate for this font
        if (value := self._get('validate', type_=bool)) is not None:
            self.__validate = value

        # Case
        if (value := self._get('case', type_=self.TYPE_LOWER_STR)) is not None:
            if value in self.__card_class.CASE_FUNCTIONS:
                self.case_name = value
                self.case = self.__card_class.CASE_FUNCTIONS[value]
            else:
                self.__error('case', value, 'unrecognized value')

        # Color
        if (value := self._get('color', type_=str)) is not None:
            self.color = value

        # File
        if (value := self._get('file', type_=Path)) is not None:
            # If specified as direct path, check for existance
            if value.exists():
                self.file = str(value.resolve())
                self.replacements = {}
            # If specified indirectly (or DNE), glob for any extension
            elif len(matches := tuple(value.parent.glob(f'{value.name}*'))) ==1:
                self.file = str(matches[0].resolve())
                self.replacements = {}
            else:
                self.__error('file', value, 'no font file found')

        # Replacements and delete_missing
        if (value := self._get('replacements', type_=dict)) is not None:
            # Convert each replacement to string, exit if impossible
            self.delete_missing = bool(value.pop('delete_missing', True))
            self.replacements = {}
            for in_, out_ in value.items():
                try:
                    self.replacements[str(in_)] = str(out_)
                except Exception:
                    self.__error('replacements', value,
                                f'bad replacement for "{in_}"')

        # Size
        if (value := self._get('size', type_=str)) is not None:
            if bool(self._PERCENT_REGEX_POSITIVE.match(value)):
                self.size = float(value[:-1]) / 100.0
            else:
                self.__error('size', value, 'specify as "x%')                

        # Vertical shift
        if (value := self._get('vertical_shift', type_=int)) is not None:
            if isinstance(value, int):
                self.vertical_shift = value
            else:
                self.__error('vertical_shift', value, 'must be integer')

        # Interline spacing
        if (value := self._get('interline_spacing', type_=int)) is not None:
            if isinstance(value, int):
                self.interline_spacing = value
            else:
                self.__error('interline_spacing', value, 'must be integer')

        # Kerning
        if (value := self._get('kerning', type_=str)) is not None:
            if bool(self._PERCENT_REGEX.match(value)):
                self.kerning = float(value[:-1]) / 100.0
            else:
                self.__error('kerning', value, 'specify as "x%"')

        # Stroke width
        if (value := self._get('stroke_width', type_=str)) is not None:
            if bool(self._PERCENT_REGEX_POSITIVE.match(value)):
                self.stroke_width = float(value[:-1]) / 100.0
            else:
                self.__error('stroke_width', value, 'specify as "x%"')


    def reset(self) -> None:
        """Reset this object's attributes to its default values."""

        # Whether to validate for this font
        self.__validate = global_objects.pp.validate_fonts

        # Default itle card characteristics and font values
        self.color = self.__card_class.TITLE_COLOR
        self.size = 1.0
        self.file = self.__card_class.TITLE_FONT
        self.replacements = self.__card_class.FONT_REPLACEMENTS
        self.delete_missing = True
        self.case_name = self.__card_class.DEFAULT_FONT_CASE
        self.case = self.__card_class.CASE_FUNCTIONS[self.case_name]
        self.vertical_shift = 0
        self.interline_spacing = 0
        self.kerning = 1.0
        self.stroke_width = 1.0


    def get_attributes(self) -> dict[str, Any]:
        """
        Return a dictionary of attributes for this font to be unpacked.

        Returns:
            Dictionary of attributes whose keys are 'title_color',
            'font_size', 'font', 'vertical_shift', 'interline_spacing',
            'kerning', and 'stroke_width'.
        """

        return {
            'title_color': self.color,
            'font_size': self.size,
            'font': self.file,
            'vertical_shift': self.vertical_shift,
            'interline_spacing': self.interline_spacing,
            'kerning': self.kerning,
            'stroke_width': self.stroke_width,
        }


    def validate_title(self, title: str) -> tuple[str, bool]:
        """
        Return whether all the characters of the given title are valid
        for this font. This uses this object's FontValidator object.

        Args:
            title: The title (string) being validated.

        Returns:
            Tuple of the modified title, and whether the title is now
            valid. The title is only modified if missing deletion is
            enabled (and applied); validity is True if all the
            characters of the given title are contained within this
            font, or if validation is not enabled and is False
            otherwise.
        """

        # Validate title against this font
        valid = self.__validator.validate_title(self.file, title)

        # If invalid, and missing characters are set to be deleted, modify title
        if not valid and self.delete_missing:
            # Delete each missing character from title
            for missing in self.__validator.get_missing_characters(self.file):
                title = title.replace(missing, '')

            # Return modified title, and title is now guaranteed to be valid
            return title, True

        # If validation isn't enabled, ignore result and return True
        return title, (valid if self.__validate else True)