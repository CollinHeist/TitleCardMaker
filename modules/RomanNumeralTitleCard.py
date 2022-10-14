from pathlib import Path

from modules.BaseCardType import BaseCardType
from modules.Debug import log

class RomanNumeralTitleCard(BaseCardType):
    """
    This class defines a type of CardType that produces un-imaged title cards
    with roman numeral text behind the central title. The style is inspired
    from the official Devilman Crybaby title cards.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'roman'

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

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = False

    """Whether this CardType uses unique source images"""
    USES_UNIQUE_SOURCES = False

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Roman Numeral Style'

    """Blur profile for this card is 1/3 the radius of the standard blur"""
    BLUR_PROFILE = '0x30'

    """Default fonts and color for series count text"""
    ROMAN_NUMERAL_FONT = REF_DIRECTORY / 'sinete-regular.otf'
    ROMAN_NUMERAL_TEXT_COLOR = '#AE2317'

    __slots__ = (
        'output_file', 'title', 'title_color', 'background', 'blur',
        'roman_numeral_color', 'roman_numeral', '__roman_text_scalar'
    )

    def __init__(self, output_file: Path, title: str, episode_text: str,
                 title_color: str, episode_number: int=1, blur: bool=False, 
                 grayscale: bool=False, background: str='black', 
                 roman_numeral_color: str=ROMAN_NUMERAL_TEXT_COLOR,
                 **kwargs) -> None:
        """
        Construct a new instance.
        
        Args:
            output_file: Output file.
            title: Episode title.
            episode_text: The episode text to parse the roman numeral from.
            episode_number: Episode number for the roman numerals.
            title_color: Color to use for the episode title.
            background: Color for the background.
            roman_numeral_color: Color for the roman numerals.
            blur: Whether to blur the source image.
            grayscale: Whether to make the source image grayscale.
            kwargs: Unused arguments.
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
        breakpoint()


    def __assign_roman_numeral(self, number: int) -> None:
        """
        Convert the given number to a roman numeral, update the scalar and text
        attributes of this object.
        
        Args:
            number: The number to become the roman numeral.
        """

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
            roman_text = [numeral[:len(numeral)//2], numeral[len(numeral)//2:]]
        else:
            roman_text = [numeral]

        # Update scalar for this text
        self.__assign_roman_scalar(roman_text)

        # Assign combined roman numeral text
        self.roman_numeral = '\n'.join(roman_text)


    def __assign_roman_scalar(self, roman_text: list[str]) -> None:
        """
        Assign the roman text scalar for this text based on the widest line of
        the given roman numeral text.
        
        Args:
            roman_text: List of strings, where each entry is a new line in the
                roman numeral string.
        """

        # Width of each roman numeral
        widths = {
            'I': 364, 'V': 782, 'X': 727, 'L': 599,
            'C': 779, 'D': 856, 'M': 1004
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


    @property
    def roman_numeral_command(self) -> list[str]:
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
            f'-annotate +0+0 "{self.roman_numeral}"',
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


    @staticmethod
    def is_custom_font(font: 'Font') -> bool:
        """
        Determine whether the given font characteristics constitute a default
        or custom font.
        
        Args:
            font: The Font being evaluated.
        
        Returns:
            False, as custom fonts aren't used.
        """

        return False


    @staticmethod
    def is_custom_season_titles(custom_episode_map: bool, 
                                episode_text_format: str) -> bool:
        """
        Determine whether the given attributes constitute custom or generic
        season titles.
        
        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.
        
        Returns:
            False, as season titles aren't used.
        """

        return False


    def create(self):
        """
        Make the necessary ImageMagick and system calls to create this object's
        defined title card.
        """
        
        command = ' '.join([
            f'convert',
            # Create fixed color background
            f'-size "{self.TITLE_CARD_SIZE}"',
            f'xc:"{self.background}"',
            # Overlay roman numerals
            *self.roman_numeral_command,
            # Optionally blur and apply grayscale
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            f'-colorspace gray' if self.grayscale else '',
            # Overlay title text
            *self.title_text_command,
            f'"{self.output_file.resolve()}"',
        ])
        
        self.image_magick.run(command)