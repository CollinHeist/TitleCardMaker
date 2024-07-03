from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from modules.BaseCardType import BaseCardType

if TYPE_CHECKING:
    from modules.PreferenceParser import PreferenceParser
    from modules.Font import Font


class TextlessTitleCard(BaseCardType):
    """
    This class describes a type of CardType that does not modify the
    source image in anyway, only optionally blurring it. No text of any
    kind is added.
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

    """Don't require source images to work w/ importing"""
    USES_SOURCE_IMAGES = False # Set as False; if required then caught by model

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Textless Version'

    __slots__ = ('source_file', 'output_file')


    def __init__(self,
            source_file: Path,
            card_file: Path,
            blur: bool = False,
            grayscale: bool = False,
            preferences: Optional['PreferenceParser'] = None,
            **unused,
        ) -> None:
        """Construct a new instance of this card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store input/output files
        self.source_file = source_file
        self.output_file = card_file


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> Literal[False]:
        """
        Determines whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            False, as fonts are not customizable with this card.
        """

        return False


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> Literal[False]:
        """
        Determines whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            False, as season titles are not customizable with this card.
        """

        return False


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        if (self.source_file and isinstance(self.source_file, Path)
            and self.source_file.exists()):
            add_source = [f'"{self.source_file.resolve()}"']
        else:
            add_source = [
                f'-size {self.TITLE_CARD_SIZE}',
                f'xc:None',
            ]

        command = ' '.join([
            f'convert',
            *add_source,
            *self.resize_and_style,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
