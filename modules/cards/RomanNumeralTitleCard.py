from collections import namedtuple
from pathlib import Path
from random import choice
from re import compile as re_compile
from typing import Any, Optional

from modules.BaseCardType import BaseCardType
from modules.Debug import log

SeriesExtra = Optional

Position = namedtuple('Position', ('location', 'offset', 'rotation'))

class Offset:
    """
    This class defines an Offset of x/y to be utilized for placing
    season text around roman numerals.
    """

    """Regex to match signed float offsets from an ImageMagick offset string"""
    OFFSET_REGEX = re_compile(r'([-+]\d+.?\d*)([-+]\d+.?\d*)')

    def __init__(self, offset_str: str=None, *,
            x: float=None, y: float=None) -> None:
        """
        Initialize an Offset object with the given ImageMagick offset
        string. For example, Offset('+20-10') indicates a 20 pixel
        positive X offset, and a 10 pixel negative Y offset.

        This can be initialized with offset string or x/y coordinates.

        Args:
            offset_str: ImageMagick offset string.
            x: (Keyword) X offset to initialize this object with.
            y: (Keyword) Y offset to initialize this object with.
        """

        # Initialize with offset string
        if offset_str is not None:
            self.x, self.y = map(
                float, self.OFFSET_REGEX.match(offset_str).groups()
            )
        else:
            self.x, self.y = float(x), float(y)

    def __repr__(self) -> str:
        return f'<Offset {self.x=}, {self.y=}>'

    def __str__(self) -> str:
        return f'{self.x:+}{self.y:+}'

    def __add__(self, other: 'Offset') -> None:
        """
        Add an offset to this object, returning a new object.

        Args:
            other: Offset to add to this object.
        """

        return Offset(x=self.x + other.x, y=self.y + other.y)

    def __iadd__(self, other: 'Offset') -> 'Offset':
        """
        Adjust this object by the given offset. For example:

        >>> o = Offset('+10+30')
        >>> o += Offset('-10-30')
        >>> repr(o)
        '<Offset self.x=0.0, self.y=0.0>'

        Args:
            other: Offset to adjust this object by.
        """

        self.x += other.x
        self.y += other.y

        return self

    def __mul__(self, scalar: float) -> 'Offset':
        """
        Scale this object's offsets by the given scalar, returning a new
        object.

        Args:
            scalar: Scalar multiple to scale this offset by.
        """

        return Offset(x=self.x*scalar, y=self.y*scalar)

    def __imul__(self, scalar: float) -> 'Offset':
        """
        Scale this object's offsets by the given scalar. For example:

        >>> o = Offset('+100+50')
        >>> o *= 0.5
        >>> repr(o)
        '<Offset self.x=50.0, self.y=25.0>'

        Args:
            scalar: Scalar multiple to adjust this object by.
        """

        self.x *= scalar
        self.y *= scalar

        return self

"""
Lists of all possible Positions for season text around each possible
roma numeral.
"""
POSITIONS: dict[str, list[Position]] = {
    'I': [
        Position('Below', Offset('+0+425'), '0x0'),
        Position('Above', Offset('+0-360'), '0x0'),
        Position('Lower', Offset('+0+300'), '0x0'),
        Position('Upper', Offset('+0-250'), '0x0'),
        Position('Left', Offset('-75+0'), '-90x-90'),
        Position('Right', Offset('+75+0'), '90x90'),
    ], 'V': [
        Position('Inside', Offset('+0-275'), '0x0'),
        Position('Above', Offset('+0-365'), '0x0'),
        Position('Lower', Offset('+0+315'), '0x0'),
        Position('Lower Left', Offset('-185+350'), '0x0'),
        Position('Lower Right', Offset('+175+350'), '0x0'),
        Position('Lower Right Rotated', Offset('+90+280'), '-67x-67'),
        Position('Lower Left Rotated', Offset('-120+260'), '67x67'),
        Position('Upper Left', Offset('-270-370'), '0x0'),
        Position('Upper Right', Offset('+280-370'), '0x0'),
    ], 'X': [
        Position('Upper Right', Offset('+230-360'), '0x0'),
        Position('Upper Left', Offset('-230-360'), '0x0'),
        Position('Lower Right', Offset('+240+425'), '0x0'),
        Position('Lower Left', Offset('-240+425'), '0x0'),
        Position('Lower Middle', Offset('+0+325'), '0x0'),
        Position('Right Rotated', Offset('+175+150'), '55x55'),
    ], 'L': [
        Position('Below', Offset('+0+425'), '0x0'),
        Position('Top Left', Offset('-110-365'), '0x0'),
        Position('Left', Offset('-190+0'), '-90x-90'),
        Position('Right', Offset('-45+0'), '90x90'),
    ], 'C': [
        Position('Above', Offset('+0-375'), '0x0'),
        Position('Below', Offset('+0+425'), '0x0'),
        Position('Left', Offset('-365+0'), '-90x-90'),
        Position('Center', Offset('+0+0'), '0x0'),
    ], 'D': [
        Position('Above', Offset('+0-375'), '0x0'),
        Position('Below', Offset('+0+425'), '0x0'),
        Position('Left', Offset('-325+0'), '-90x-90'),
        Position('Right', Offset('+400+0'), '90x90'),
        Position('Center', Offset('+0+0'), '0x0'),
        Position('Above Left', Offset('-240-355'), '0x0'),
        Position('Below Left', Offset('-240+425'), '0x0'),
    ], 'M': [
        Position('Above', Offset('+0-300'), '0x0'),
        Position('Below', Offset('+0+300'), '0x0'),
        Position('Below Left', Offset('-350+425'), '0x0'),
        Position('Below Right', Offset('+340+425'), '0x0'),
        Position('Upper Left', Offset('-145-180'), '59x59'),
        Position('Left', Offset('-375+0'), '-88x-88'),
        Position('Right', Offset('+395+0'), '88x88'),
    ]
}

class RomanNumeralTitleCard(BaseCardType):
    """
    This class defines a type of CardType that produces imageless title
    cards with roman numeral text behind the central title. The style is
    inspired from the official Devilman Crybaby title cards.

    If enabled, season text is randomly placed around fixed positions on
    the roman numerals. 
    """

    """API Parameters"""
    API_DETAILS = {
        'name': 'Roman Numeral',
        'example': '/assets/cards/roman.jpg',
        'creators': ['CollinHeist'],
        'source': 'local',
        'supports_custom_fonts': False,
        'supports_custom_seasons': True,
        'supported_extras': [
            {'name': 'Background Color',
             'identifier': 'background',
             'description': 'Background color to utilize for the card'},
            {'name': 'Roman Numeral Color',
             'identifier': 'roman_numeral_color',
             'description': 'Color to utilize for the roman numerals'},
        ], 'description': [
            'Imageless title cards featuring large roman numerals indicating the episode number just behind the title.',
            'This style of title card is based off the official Devilman Crybaby title cards.',
            'Season text, if enabled, is placed at deterministic locations around the roman numerals.',
        ],
    }

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'roman'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 26,   # Character count to begin splitting titles
        'max_line_count': 5,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses bottom heavy titling
    }

    """Default font and text color for episode title text"""
    TITLE_FONT = str((REF_DIRECTORY / 'flanker-griffo.otf').resolve())
    TITLE_COLOR = 'white'

    """Default characters to replace in the generic font"""
    FONT_REPLACEMENTS = {}

    """Default episode text format for this class"""
    EPISODE_TEXT_FORMAT = '{episode_number}'
    GENERIC_EPISODE_TEXT_FORMATS = (
        EPISODE_TEXT_FORMAT, '{abs_number}',
    )

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Whether this CardType uses unique source images"""
    USES_UNIQUE_SOURCES = False

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Roman Numeral Style'

    """Blur profile for this card is 1/3 the radius of the standard blur"""
    BLUR_PROFILE = '0x30'

    """Default fonts and color for series count text"""
    BACKGROUND_COLOR = 'black'
    ROMAN_NUMERAL_FONT = REF_DIRECTORY / 'sinete-regular.otf'
    ROMAN_NUMERAL_TEXT_COLOR = '#AE2317'
    SEASON_TEXT_COLOR = 'rgb(200, 200, 200)'

    """Maximum possible roman numeral (as overline'd characters are invalid)"""
    MAX_ROMAN_NUMERAL = 3999

    """Maximum number of attempts for season text placement (if overlapping)"""
    SEASON_TEXT_PLACEMENT_ATTEMPS = 10

    __slots__ = (
        'output_file', 'title', 'season_text', 'hide_season', 'title_color',
        'background', 'blur', 'roman_numeral_color', 'roman_numeral',
        '__roman_text_scalar', '__roman_numeral_lines', 'rotation', 'offset',
    )

    def __init__(self, output_file: Path, title: str, season_text: str, 
            episode_text: str, hide_season: bool, title_color: str,
            episode_number: int=1,
            blur: bool=False,
            grayscale: bool=False,
            background: SeriesExtra[str]=BACKGROUND_COLOR, 
            roman_numeral_color: SeriesExtra[str]=ROMAN_NUMERAL_TEXT_COLOR,
            **unused) -> None:
        """
        Construct a new instance of this card.

        Args:
            output_file: Output file.
            title: Episode title.
            episode_text: The episode text to parse the roman numeral
                from.
            episode_number: Episode number for the roman numerals.
            title_color: Color to use for the episode title.
            blur: Whether to blur the source image.
            grayscale: Whether to make the source image grayscale.
            background: Color for the background.
            roman_numeral_color: Color for the roman numerals.
            unused: Unused arguments.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        # Store object attributes
        self.output_file = output_file
        self.title = self.image_magick.escape_chars(title)
        self.title_color = title_color
        self.background = background
        self.roman_numeral_color = roman_numeral_color

        # Try and parse roman digit from the episode text, if cannot be done,
        # just use actual episode number
        digit = int(episode_text) if episode_text.isdigit() else episode_number
        self.__assign_roman_numeral(digit)

        # Select roman numeral for season text
        self.season_text = season_text.strip().upper()
        self.hide_season = hide_season or (len(self.season_text) == 0)

        # Rotation and offset attributes to be determined later
        self.rotation, self.offset = None, None


    def __assign_roman_numeral(self, number: int) -> None:
        """
        Convert the given number to a roman numeral, update the scalar
        and text attributes of this object.

        Args:
            number: The number to become the roman numeral.
        """

        # Limit to maximum possible roman numeral
        if number > self.MAX_ROMAN_NUMERAL:
            log.warning(f'Numbers larger than {self.MAX_ROMAN_NUMERAL:,} cannot'
                        f' be represented as roman numerals')
            number = self.MAX_ROMAN_NUMERAL

        # Index-sorted places -> roman numerals
        m_text = ['', 'M', 'MM', 'MMM']
        c_text = ['', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM']
        x_text = ['', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC']
        i_text = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX']

        # Get each places' roman numeral
        thousands = m_text[number // 1000]
        hundreds = c_text[(number % 1000) // 100]
        tens = x_text[(number % 100) // 10]
        ones = i_text[number % 10]

        numeral = (thousands + hundreds + tens + ones).strip()

        # Split roman numerals that are longer than 6 chars into two lines
        if len(numeral) >= 5:
            self.__roman_numeral_lines = 2
            roman_text = [numeral[:len(numeral)//2], numeral[len(numeral)//2:]]
        else:
            self.__roman_numeral_lines = 1
            roman_text = [numeral]

        # Update scalar for this text
        self.__assign_roman_scalar(roman_text)

        # Assign combined roman numeral text
        self.roman_numeral = '\n'.join(roman_text)


    def __assign_roman_scalar(self, roman_text: list[str]) -> None:
        """
        Assign the roman text scalar for this text based on the widest
        line of the given roman numeral text.

        Args:
            roman_text: List of strings, where each entry is a new line
                in the roman numeral string.
        """

        # Width of each roman numeral
        widths = {
            'I': 364, 'V': 782, 'X': 727, 'L': 599,
            'C': 779, 'D': 856, 'M': 1004,
        }

        # Get max width of all lines
        max_width = max(sum(widths[ch] for ch in line) for line in roman_text)

        # Get width of output title card for comparison
        card_width = int(self.TITLE_CARD_SIZE.split('x')[0])

        # Scale roman numeral text if line width is larger than card (+margin)
        if max_width > (card_width - 100):
            self.__roman_text_scalar = (card_width - 100) / max_width
        else:
            self.__roman_text_scalar = 1.0


    def create_roman_numeral_command(self, roman_numeral: str) -> list[str]:
        """
        Subcommand to add roman numerals to the image.

        Returns:
            List of ImageMagick commands.
        """

        # Scale font size and interline spacing of roman text
        font_size = 1250 * self.__roman_text_scalar
        interline_spacing = -400 * self.__roman_text_scalar

        return [
            f'-font "{self.ROMAN_NUMERAL_FONT.resolve()}"',
            f'-fill "{self.roman_numeral_color}"',
            f'-pointsize {font_size}',
            f'-gravity center',
            f'-interline-spacing {interline_spacing}',
            f'-annotate +0-30 "{roman_numeral}"',
        ]


    def create_season_text_command(self, rotation: str, offset: str)->list[str]:
        """
        Generate the ImageMagick commands necessary to create season
        text at the given rotation and offset.

        Args:
            rotation: Rotation (string) to utilize. Should be like
                "90x90".
            offset: Offset (string, not Object) to utilize relative to
                the center of the canvas. Should be like "+100-300".

        Returns:
            List of ImageMagick commands.
        """

        if self.hide_season or rotation is None or offset is None:
            return []

        # Override font color only if a custom background color was specified
        if self.background != self.BACKGROUND_COLOR:
            color = self.title_color
        else:
            color = self.SEASON_TEXT_COLOR

        return [
            f'-size "{self.TITLE_CARD_SIZE}"',
            f'-gravity center',
            f'-font "{self.TITLE_FONT}"',
            f'-fill "{color}"',
            f'-pointsize 50',
            f'+interword-spacing',
            f'-annotate {rotation}{offset} "{self.season_text}"',
        ]


    @property
    def title_text_command(self) -> list[str]:
        """
        Subcommand to add title text to the image.

        Returns:
            List of ImageMagick commands.
        """

        return [
            f'-font "{self.TITLE_FONT}"',
            f'-pointsize 150',
            f'-interword-spacing 40',
            f'-interline-spacing 0',
            f'-fill "{self.title_color}"',            
            f'-annotate +0+0 "{self.title}"',
        ]


    def randomize_season_text_position(self) -> tuple[str, Offset]:
        """
        Select a random roman numeral and position for season text
        placement.

        Returns:
            Tuple of the rotation string and the final Offset of the
            randomly selected position.
        """

        # Select random roman numeral and position on that numeral
        random_index = choice(range(len(self.roman_numeral)))
        if self.roman_numeral[random_index] == '\n': random_index -= 1
        random_letter = self.roman_numeral[random_index]
        random_position = choice(POSITIONS[random_letter])

        # Offset of season text - center of roman numerals is +0-30
        offset = Offset('+0-30')

        # If the roman numeral has multiple lines, adjust accordingly
        if self.__roman_numeral_lines > 1:
            # Determine whether on the top/bottom of the roman numeral text
            top, bottom = self.roman_numeral.split('\n')
            on_top = random_index < len(top)
            line = top if on_top else bottom

            # Shift offset down/up if on top/bottom
            amount = (425 * self.__roman_text_scalar) * (-1 if on_top else 1)
            offset += Offset(x=0, y=amount)

            # Calculate widths only against relevant line
            adjusted_index = random_index - (0 if on_top else len(top)+1)
            left_text = line[:adjusted_index]
            right_text = line[adjusted_index+1:]
            numeral_command = self.create_roman_numeral_command(line)
        # Single line, no vertical offset necessary
        else:
            left_text = self.roman_numeral[:random_index]
            right_text = self.roman_numeral[random_index+1:]
            numeral_command = self.create_roman_numeral_command(
                self.roman_numeral
            )

        # Get width of whole line
        total_width, _ = self.get_text_dimensions(numeral_command,
                                                  width='sum', height='max')

        # Get width of line to the left of the selected numeral
        left_width = 0
        if len(left_text) > 0:
            left_width, _ = self.get_text_dimensions(
                self.create_roman_numeral_command(left_text),
                width='sum', height='max'
            )

        # Get width of line to the right of the selected numeral
        right_width = 0
        if len(right_text) > 0:
            right_width, _ = self.get_text_dimensions(
                self.create_roman_numeral_command(right_text),
                width='sum', height='max'
            )

        # Determine necesary offset by position within the line
        on_right = left_width > right_width
        amount = (left_width if on_right else right_width) \
            - (total_width / 2) \
            + ((total_width - left_width - right_width) / 2)
        amount *= (1 if on_right else -1)

        # Adjust offset horizontally by position in the line
        offset += Offset(x=amount, y=0)

        # Adjust offset from center of letter to randomly selected position
        offset += (random_position.offset * self.__roman_text_scalar)

        return random_position.rotation, offset


    def place_season_text(self) -> None:
        """
        Determine the final placement for season text on this image.
        This  randomly selects letters/positions until they do not
        overlap the title, or until the maximum number of attempts has
        been reached (very unlikely).

        When finished, the value of this object's rotation and offset
        attributes are set.
        """

        # If season titles are hidden, exit
        if self.hide_season:
            return None

        # Get boundaries of title text
        width, height = self.get_text_dimensions(self.title_text_command,
                                                 width='width', height='sum')
        box0 = {
            'start_x': -width/2  + 3200/2,
            'start_y': -height/2 + 1800/2,
            'end_x':    width/2  + 3200/2,
            'end_y':    height/2 + 1800/2,
        }

        # Inner function to randomize position and determine if overlapping
        def select_position() -> bool:
            """
            Select a random position for season text.

            Returns:
                True if the selected position is invalid (i.e. overlaps
                the title, or extends beyond the bounds of the card).
                False otherwise.
            """

            # Select random position and get it's associated offset
            rotation, offset = self.randomize_season_text_position()
            self.rotation, self.offset = rotation, offset

            # Get dimensions of season text
            season_width, season_height = self.get_text_dimensions(
                self.create_season_text_command(rotation, offset),
                width='max', height='max'
            )

            # Modify dimensions or add margin based on rotation of text
            margin = 0
            # If not rotated, no margin necessary
            if rotation == '0x0':
                pass
            # If rotated 90 degrees, then swap width/height of text
            elif rotation in ('90x90', '-90x-90'):
                season_width, season_height = season_height, season_width
            # If rotated, but not at 90 degrees, then add margin based on max
            # dimension - this is equivalent to expanding the bounds of the text
            # box by the maximum possible error in the dimensions of the text
            else:
                # Worst case is a _nearly_ 90 degree rotation with large delta
                # between width/height; in which case the width would be off by
                # the height/2 (in either direction), and the height off by
                # width/2 (in either direction)
                max_error = abs(season_width - season_height)
                margin = max_error / 2

            # Get boundaries of season text
            box1 = {
                'start_x': offset.x - season_width/2  + 3200/2 - margin,
                'start_y': offset.y - season_height/2 + 1800/2 - margin,
                'end_x': offset.x   + season_width/2  + 3200/2 + margin,
                'end_y': offset.y   + season_height/2 + 1800/2 + margin,
            }

            # If outside the bounds of the image, return invalid
            if (box1['start_x'] < 0 or box1['start_x'] > 3200
                or box1['end_x'] < 0 or box1['end_x'] > 3200
                or box1['start_y'] < 0 or box1['start_y'] > 1800
                or box1['end_y'] < 0 or box1['end_y'] > 1800):
                return True

            # Return whether the bounds of the season text overlap the title 
            return (box0['start_x'] < box1['end_x']  # Box0 left before Box1 right
                and box0['end_x'] > box1['start_x']  # Box0 right after Box1 left
                and box0['start_y'] < box1['end_y']  # Box0 top before Box1 bottom
                and box0['end_y'] > box1['start_y']) # Box0 bottom after Box1 top

        # Attempt position selection until not overlapping, or out of attemps
        attempts_left = self.SEASON_TEXT_PLACEMENT_ATTEMPS
        while (attempts_left := attempts_left-1) > 0 and select_position(): pass


    @staticmethod
    def modify_extras(
            extras: dict[str, Any],
            custom_font: bool,
            custom_season_titles: bool) -> None:
        """
        Modify the given extras base on whether font or season titles
        are custom.

        Args:
            extras: Dictionary to modify.
            custom_font: Whether the font are custom.
            custom_season_titles: Whether the season titles are custom.
        """

        # Generic font, reset roman numeral color and background
        if not custom_font:
            if 'background' in extras:
                extras['background'] = RomanNumeralTitleCard.BACKGROUND_COLOR
            if 'roman_numeral_color' in extras:
                extras['roman_numeral_color'] =\
                    RomanNumeralTitleCard.ROMAN_NUMERAL_TEXT_COLOR


    @staticmethod
    def is_custom_font(font: 'Font') -> bool:
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.

        Returns:
            False, as custom fonts aren't used.
        """

        return ((font.color != RomanNumeralTitleCard.TITLE_COLOR))


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool, episode_text_format: str) -> bool:
        """
        Determine whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if the episode map or episode text format is custom,
            False otherwise.
        """

        standard_etfs = RomanNumeralTitleCard.GENERIC_EPISODE_TEXT_FORMATS

        return (custom_episode_map 
                or episode_text_format not in standard_etfs)


    def create(self):
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # Determine placement of season text
        self.place_season_text()

        command = ' '.join([
            f'convert',
            # Create fixed color background
            f'-size "{self.TITLE_CARD_SIZE}"',
            f'xc:"{self.background}"',
            # Overlay roman numerals
            *self.create_roman_numeral_command(self.roman_numeral),
            # Overlay season text
            *self.create_season_text_command(self.rotation, self.offset),
            # Apply any set style modifiers
            *self.style,
            # Overlay title text
            *self.title_text_command,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)