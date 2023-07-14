from pathlib import Path
from typing import Optional

from modules.BaseCardType import BaseCardType, CardDescription


class TextlessTitleCard(BaseCardType):
    """
    This class describes a type of CardType that does not modify the
    source image in anyway, only optionally blurring it. No text of any
    kind is added.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Textless',
        identifier='textless',
        example='/internal_assets/cards/textless.jpg',
        creators=['CollinHeist'],
        source='local',
        supports_custom_fonts=False,
        supports_custom_seasons=False,
        supported_extras=[],
        description=[
            'A card completely devoid of all text.',
            'This card is intended to easily enable users to have TCM manage '
            'non-TCM-created cards, as well as apply style modifiers (like '
            'blurring and grayscale) to images',
        ]
    )

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

    __slots__ = ('source_file', 'output_file')


    def __init__(self,
            source_file: Path,
            card_file: Path,
            blur: bool = False,
            grayscale: bool = False,
            preferences: Optional['Preferences'] = None, # type: ignore
            **unused,
        ) -> None:
        """
        Construct a new instance of this card.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store input/output files
        self.source_file = source_file
        self.output_file = card_file


    @staticmethod
    def is_custom_font(font: 'Font') -> bool: # type: ignore
        """
        Determines whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.

        Returns:
            False, as fonts are not customizable with this card.
        """

        return False


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool, episode_text_format: str) -> bool:
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

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            *self.resize_and_style,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
