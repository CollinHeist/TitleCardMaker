from pathlib import Path
from re import findall

from modules.BaseCardType import BaseCardType
from modules.Debug import log

class TextlessTitleCard(BaseCardType):
    """
    This class describes a type of CardType that does not modify the source
    image in anyway, only optionally blurring it. No text of any kind is added.
    """

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 999,  # Character count to begin splitting titles
        'max_line_count': 1,    # Maximum number of lines a title can take up
        'top_heavy': False,     # This class uses bottom heavy titling
    }

    """Font case for this card is entirely blank"""
    DEFAULT_FONT_CASE = 'blank'

    """Default episode text format string, can be overwritten by each class"""
    EPISODE_TEXT_FORMAT = ''

    """Characteristics of the default title font"""
    TITLE_FONT = ''
    TITLE_COLOR = ''
    FONT_REPLACEMENTS = {}

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = False

    """Label to archive cards under"""
    ARCHIVE_NAME = 'Textless Version'

    __slots__ = ('source_file', 'output_file', 'blur')


    def __init__(self, source: Path, output_file: Path, blur: bool=False,
                 **kwargs) -> None:
        """
        Initialize the TitleCardMaker object. This primarily just stores
        instance variables for later use in `create()`. If the provided font
        does not have a character in the title text, a space is used instead.

        Args:
            source: Source image.
            output_file: Output file.
            blur: Whether to blur the source image.
            kwargs: Unused arguments to permit general calls for any CardType.
        """
        
        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__()

        # Store arguments as attributes
        self.source_file = source
        self.output_file = output_file
        self.blur = blur


    def _resize_and_blur(self) -> Path:
        """
        Resize the source image, optionally blurring. Write the resulting image
        to the output filepath.
        
        Returns:
            Path to the created image (the output file).
        """

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            f'+profile "*"',
            f'-gravity center',
            f'-resize "{self.TITLE_CARD_SIZE}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output_file


    @staticmethod
    def is_custom_font(font: 'Font') -> bool:
        """
        Determines whether the given font characteristics constitute a default
        or custom font.
        
        Args:
            font: The Font being evaluated.
        
        Returns:
            False, as fonts are not customizable with this card.
        """

        return False


    @staticmethod
    def is_custom_season_titles(custom_episode_map: bool, 
                                episode_text_format: str) -> bool:
        """
        Determines whether the given attributes constitute custom or generic
        season titles.
        
        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.
        
        Returns:
            False, as season titles are not customizable with this card.
        """

        return False


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this object's
        defined title card.
        """
        
        # Only ImageMagick call is resizing and an optional blur
        self._resize_and_blur()