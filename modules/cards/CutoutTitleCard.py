from pathlib import Path
from typing import Optional

from modules.BaseCardType import BaseCardType, ImageMagickCommands
from modules.Debug import log

SeriesExtra = Optional

class CutoutTitleCard(BaseCardType):
    """
    This class describes a type of CardType that is very loosely based
    off of /u/Phendrena's Willow title card set. These cards feature a
    solid color overlay with the episode text cutout to reveal the
    source image.
    """

    """API Parameters"""
    API_DETAILS = {
        'name': 'Cutout',
        'example': '/assets/cards/cutout.jpg',
        'creators': ['/u/Phendrena', 'CollinHeist'],
        'source': 'local',
        'supports_custom_fonts': True,
        'supports_custom_seasons': False,
        'supported_extras': [
            {'name': 'Overlay Color',
             'identifier': 'overlay_color',
             'description': 'Color of the solid overlay to cut text out of'},
            {'name': 'Edge Blurring',
             'identifier': 'blur_edges',
             'description': 'Whether to blur the edges of the number cutout'},
        ], 'description': [
            'Title cards featuring a solid color overlay overlaying the source image.',
            'Written episode text cuts out the overlay to reveal the underlying source image.',
        ],
    }

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'cutout'
    OLIVIER_REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'olivier'
    SW_REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'star_wars'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 34,   # Character count to begin splitting titles
        'max_line_count': 3,    # Maximum number of lines a title can take up
        'top_heavy': False,     # This class uses bottom heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((OLIVIER_REF_DIRECTORY / 'Montserrat-Bold.ttf').resolve())
    TITLE_COLOR = 'white'
    FONT_REPLACEMENTS = {}

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = False

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Cutout Style'

    """Default fonts and color for series count text"""
    EPISODE_TEXT_FORMAT = '{episode_number_cardinal}'
    EPISODE_TEXT_FONT = SW_REF_DIRECTORY / 'HelveticaNeue-Bold.ttf'

    """Custom blur profile for the poster"""
    BLUR_PROFILE = '0x20'
    NUMBER_BLUR_PROFILE = '0x10'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'episode_text',
        'font_color', 'font_file', 'font_size', 'font_vertical_shift',
        'overlay_color', 'blur_edges',
    )

    def __init__(self,
            source_file: Path,
            card_file: Path,
            title_text: str,
            episode_text: str,
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            font_size: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            overlay_color: SeriesExtra[str] = 'black',
            blur_edges: SeriesExtra[bool] = False,
            preferences: 'Preferences' = None,
            **unused) -> None:
        """
        Construct a new instance of this Card.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        # Format episode text to split into 1/2 lines depending on word count
        self.title_text = self.image_magick.escape_chars(title_text)
        self.episode_text = self.image_magick.escape_chars(
            self._format_episode_text(episode_text).upper()
        )

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_size = font_size
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.overlay_color = overlay_color
        self.blur_edges = blur_edges


    def _format_episode_text(self, episode_text: str) -> str:
        """
        Format the given episode text into the appropriate multi-line
        string.

        Args:
            episode_text: Episode text to format.

        Returns:
            Formatted multi (or single) line episode text.
        """

        # Has and, split around that
        if ' and ' in episode_text:
            top, bottom = episode_text.split(' and ')
            return f'{top}\nand {bottom}'
        # Has more than three words, split in half
        elif len(episode_text.split(' ')) > 3:
            words = episode_text.split(' ')
            top, bottom = words[:len(words)//2], words[len(words)//2:]
            top, bottom = ' '.join(top), ' '.join(bottom)
            return f'{top}\n{words}'

        # Split about dash (likely a 10-100 number)
        return '\n'.join(episode_text.split('-'))


    @staticmethod
    def is_custom_font(font: 'Font') -> bool:
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.color != CutoutTitleCard.TITLE_COLOR)
            or (font.file != CutoutTitleCard.TITLE_FONT)
            or (font.size != 1.0)
            or (font.vertical_shift != 0)
        )


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
            True if custom season titles are indicated, False otherwise.
        """

        standard_etf = CutoutTitleCard.EPISODE_TEXT_FORMAT.upper()

        return episode_text_format.upper() != standard_etf


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        command = ' '.join([
            f'convert',
            f'-set colorspace sRGB',
            # Create solid-color overlay
            f'\( -size "{self.TITLE_CARD_SIZE}"',
            f'xc:"{self.overlay_color}" \)',
            # Resize and optionally blur source image
            f'\( "{self.source_file.resolve()}"',
            *self.resize_and_style,
            f'\)',
            # Create cutout of episode text
            f'\( -set colorspace sRGB',
            f'-background transparent',
            f'-density 200',
            f'-pointsize 500',
            f'-gravity center',
            f'-interline-spacing -300',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'+size',
            f'label:"{self.episode_text}"',
            # Resize with 100px margin on all sides
            f'-resize 3100x1700',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            f'-blur "{self.NUMBER_BLUR_PROFILE}" \)' if self.blur_edges else '\)',
            # Use masked alpha composition to combine images
            f'-gravity center',
            f'-composite',
            # Add title text
            f'-gravity south',
            f'-pointsize {50 * self.font_size}',
            f'+interline-spacing',
            f'-fill "{self.font_color}"',
            f'-font "{self.font_file}"',
            f'-annotate +0+{100 + self.font_vertical_shift} "{self.title_text}"',
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)