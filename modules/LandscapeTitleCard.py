from pathlib import Path

from modules.BaseCardType import BaseCardType
from modules.Debug import log

class LandscapeTitleCard(BaseCardType):
    """
    This class defines a type of CardType that produces un-imaged title cards
    with roman numeral text behind the central title. The style is inspired
    from the official Devilman Crybaby title cards.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'landscape'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 15,   # Character count to begin splitting titles
        'max_line_count': 5,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses bottom heavy titling
    }

    """Default font and text color for episode title text"""
    TITLE_FONT = str((REF_DIRECTORY / 'Geometos.ttf').resolve())
    TITLE_COLOR = 'white'

    """Default characters to replace in the generic font"""
    FONT_REPLACEMENTS = {}

    """Default episode text format for this class"""
    EPISODE_TEXT_FORMAT = ''

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = False

    """Whether this CardType uses unique source images"""
    USES_UNIQUE_SOURCES = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Landscape Style'

    __slots__ = ('source', 'output_file', 'title', 'font', 'font_size',
                 'title_color', 'interline_spacing', 'kerning', 'blur')


    def __init__(self, source: Path, output_file: Path, title: str, font: str,
                 font_size: float, title_color: str, blur: bool=False, 
                 interline_spacing: int=0, kerning: float=1.0, **kwargs) ->None:
        """
        Initialize this TitleCard object. This primarily just stores instance
        variables for later use in `create()`.

        Args:
            source: Source image to base the card on.
            output_file: Output file where to create the card.
            title: Title text to add to created card.
            font: Font name or path (as string) to use for episode title.
            font_size: Scalar to apply to title font size.
            title_color: Color to use for title text.
            blur: Whether to blur the source image.
            interline_spacing: Pixel count to adjust title interline spacing by.
            kerning: Scalar to apply to kerning of the title text.
            kwargs: Unused arguments.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__()

        # Store object attributes
        self.source = source
        self.output_file = output_file
        self.title = self.image_magick.escape_chars(title)
        self.font = font
        self.font_size = font_size
        self.title_color = title_color
        self.interline_spacing = interline_spacing
        self.kerning = kerning
        self.blur = blur


    def __add_no_title(self) -> None:
        """Only resize and blur this source."""

        # Command to resize and optionally blur the source
        command = ' '.join([
            f'convert "{self.source.resolve()}"',
            f'+profile "*"',
            f'-gravity center',
            f'-resize "{self.TITLE_CARD_SIZE}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)


    @staticmethod
    def is_custom_font(font: 'Font') -> bool:
        """
        Determine whether the given font characteristics constitute a default
        or custom font.
        
        Args:
            font: The Font being evaluated.
        
        Returns:
            True if the given font is custom, False otherwise.
        """

        return ((font.file != LandscapeTitleCard.TITLE_FONT)
            or (font.size != 1.0)
            or (font.color != LandscapeTitleCard.TITLE_COLOR)
            or (font.interline_spacing != 0)
            or (font.kerning != 1.0))


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

        # If title is 0-length, just optionally blur
        if len(self.title.strip()) == 0:
            self.__add_no_title()
            return None

        # Scale font size and interline spacing of roman text
        font_size = int(150 * self.font_size)
        interline_spacing = int(60 * self.interline_spacing)
        kerning = int(40 * self.kerning)
 
        # Generate command to create card
        command = ' '.join([
            f'convert "{self.source.resolve()}"',
            f'+profile "*"',
            f'-gravity center',
            # Resize source image
            f'-resize "{self.TITLE_CARD_SIZE}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            # Optionally blur
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            # Add title text
            f'\( -background None',
            f'-font "{self.font}"',
            f'-pointsize {font_size}',
            f'-gravity center',
            f'-interline-spacing {interline_spacing}',
            f'-kerning {kerning}',
            f'-interword-spacing 40',
            f'-fill "{self.title_color}"',
            f'label:"{self.title}"',
            # Create drop shadow of title text
            f'\( +clone',
            f'-background None',
            f'-shadow 80x3+10+10 \)',
            # Underlay drop shadow 
            f'+swap',
            f'-background None',
            f'-layers merge',
            f'+repage \)',
            # Add title image(s) to source
            f'-composite',
            f'"{self.output_file.resolve()}"',
        ])
        
        # Create the card
        self.image_magick.run(command)