from pathlib import Path
from typing import TYPE_CHECKING, Optional

from modules.BaseCardType import (
    BaseCardType,
    CardDescription,
    Extra,
    ImageMagickCommands,
)
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


class FadeTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards
    featuring a fade overlay showcasing a source image in 4:3 aspect
    ratio. The base idea for this card comes from Yozora.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Fade',
        identifier='fade',
        example='/internal_assets/cards/fade.jpg',
        creators=['Yozora', 'CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to use for the episode text',
                tooltip='Default is <c>rgb(163, 163, 163)</c>.',
                default='rgb(163, 163, 163)',
            ),
        ],
        description=[
            'Modification of the Standard style that is intended to be used '
            'for 4:3 aspect-ratio source images.', 'A logo can also be placed '
            'above the title text.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'fade'
    FONT_REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 13,
        'max_line_count': 5,
        'style': 'top',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((FONT_REF_DIRECTORY / 'Sequel-Neue.otf').resolve())
    TITLE_COLOR = 'white'
    FONT_REPLACEMENTS = {
        '[': '(', ']': ')', '(': '[', ')': ']', '―': '-', '…': '...', '“': '"'
    }

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'EPISODE {episode_number}'
    EPISODE_TEXT_COLOR = 'rgb(163, 163, 163)'
    EPISODE_TEXT_FONT = FONT_REF_DIRECTORY / 'Proxima Nova Semibold.otf'

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = True

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = '4x3 Fade Style'

    __OVERLAY = REF_DIRECTORY / 'gradient_fade.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'index_text', 'font_file',
        'font_size', 'font_color', 'font_interline_spacing',
        'font_interword_spacing', 'font_kerning', 'font_vertical_shift', 'logo',
        'episode_text_color',
    )

    def __init__(self,
            source_file: Path,
            card_file: Path,
            title_text: str,
            season_text: str,
            episode_text: str,
            hide_season_text: bool = False,
            hide_episode_text: bool = False,
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            logo_file: Optional[Path] = None,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            separator: str = '•',
            preferences: Optional['Preferences'] = None,
            **unused,
        ) -> None:
        """
        Construct a new instance of this Card.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store indicated files
        self.source_file = source_file
        self.output_file = card_file
        self.logo = logo_file

        # Store attributes of the text
        self.title_text = self.image_magick.escape_chars(title_text)
        if hide_season_text and hide_episode_text:
            index_text = ''
        elif hide_season_text:
            index_text = episode_text
        elif hide_episode_text:
            index_text = season_text
        else:
            index_text = f'{season_text} {separator} {episode_text}'
        self.index_text = self.image_magick.escape_chars(index_text)

        # Font customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_vertical_shift = font_vertical_shift

        # Extras
        self.episode_text_color = episode_text_color


    @property
    def add_logo(self) -> ImageMagickCommands:
        """Subcommand to add the logo file to the source image."""

        # No logo indicated, return blank command
        if self.logo is None or not self.logo.exists():
            return []

        return [
            f'\( "{self.logo.resolve()}"',
            f'-resize 900x',
            f'-resize x500\> \)',
            f'-gravity west -geometry +100-550',
            f'-composite',
        ]


    @property
    def add_title_text(self) -> ImageMagickCommands:
        """Subcommand to add the title text to the source image."""

        # No title, return blank command
        if len(self.title_text) == 0:
            return []

        size = 115 * self.font_size
        interline_spacing = -20 + self.font_interline_spacing
        kerning = 5 * self.font_kerning
        vertical_shift = 800 + self.font_vertical_shift

        return [
            f'-gravity northwest',
            f'-font "{self.font_file}"',
            f'-pointsize {size}',
            f'-kerning {kerning}',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-fill "{self.font_color}"',
            f'-annotate +100+{vertical_shift} "{self.title_text}"',
        ]


    @property
    def add_index_text(self) -> ImageMagickCommands:
        """Subcommand to add the index text to the source image."""

        # No season or episode text, return blank command
        if len(self.index_text) == 0:
            return []

        return [
            f'-gravity northwest',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-pointsize 65',
            f'-kerning 5',
            f'-fill "{self.episode_text_color}"',
            f'-annotate +105+725 "{self.index_text}"',
        ]


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determine whether the given arguments represent a custom font
        for this card.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        custom_extras = (
            ('episode_text_color' in extras
                and extras['episode_text_color'] != FadeTitleCard.EPISODE_TEXT_COLOR)
        )

        return (custom_extras
            or ((font.color != FadeTitleCard.TITLE_COLOR)
            or  (font.file != FadeTitleCard.TITLE_FONT)
            or  (font.interline_spacing != 0)
            or  (font.interword_spacing != 0)
            or  (font.kerning != 1.0)
            or  (font.size != 1.0)
            or  (font.vertical_shift != 0))
        )


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> bool:
        """
        Determine whether the given attributes constitute custom or
        genericseason titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if the episode map or episode text format is custom,
            False otherwise.
        """

        standard_etf = FadeTitleCard.EPISODE_TEXT_FORMAT

        return (custom_episode_map or (episode_text_format != standard_etf))


    def create(self) -> None:
        """Create the title card as defined by this object."""

        command = ' '.join([
            f'convert',
            # Create blank transparent image for composite sequencing
            f'-size "{self.TITLE_CARD_SIZE}"',
            f'xc:None',
            # Resize source to subsection of card
            f'\( "{self.source_file.resolve()}"',
            f'-resize x1525',
            *self.style,
            f'\)',
            # Compose source onto proper place on canvas (100px from right)
            f'-gravity east',
            f'-geometry +100+0',
            f'-composite',
            # Overlay gradient frame
            f'"{self.__OVERLAY.resolve()}"',
            f'-composite',
            # Overlay logo if indicated
            *self.add_logo,
            # Add title and index text
            *self.add_index_text,
            *self.add_title_text,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
