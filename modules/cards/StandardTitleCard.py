from pathlib import Path
from typing import TYPE_CHECKING, Optional

from modules.BaseCardType import (
    BaseCardType, ImageMagickCommands, Extra, CardDescription
)
from modules.Debug import log
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


class StandardTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces the 'generic'
    title cards based on Reddit user /u/UniversalPolymath. This card
    supports customization of every aspect of the card, but does not
    use any arbitrary data.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Standard',
        identifier='standard',
        example='/internal_assets/cards/standard.jpg',
        creators=['/u/UniversalPolymath', 'CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is <c>#CFCFCF</c>.'
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.'
            ),
            Extra(
                name='Episode Text Vertical Shift',
                identifier='episode_text_vertical_shift',
                description=(
                    'Additional vertical shift to apply to the season and '
                    'episode text. Default is <v>0</v>.'
                ),
            ),
            Extra(
                name='Stroke Text Color',
                identifier='stroke_color',
                description='Color to use for the title text stroke',
                tooltip='Default is <c>black</c>.'
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
                tooltip='Default is <v>•</v>.'
            ),
            Extra(
                name='Gradient Omission',
                identifier='omit_gradient',
                description='Whether to omit the gradient overlay',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v>, text '
                    'may appear less legible on brighter images.'
                ),
            ),
        ], description=[
            'The most "generic" type of title card.',
            'This card features center-aligned season, episode, and title text.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 32,
        'max_line_count': 4,
        'style': 'bottom',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Sequel-Neue.otf').resolve())
    TITLE_COLOR = '#EBEBEB'
    FONT_REPLACEMENTS = {
        '[': '(', ']': ')', '(': '[', ')': ']', '―': '-', '…': '...', '“': '"'
    }

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'standard'

    """Default fonts and color for series count text"""
    SEASON_COUNT_FONT = REF_DIRECTORY / 'Proxima Nova Semibold.otf'
    EPISODE_COUNT_FONT = REF_DIRECTORY / 'Proxima Nova Regular.otf'
    SERIES_COUNT_TEXT_COLOR = '#CFCFCF'

    """Source path for the gradient image"""
    __GRADIENT_IMAGE = REF_DIRECTORY / 'GRADIENT.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_file', 'font_interline_spacing', 'font_interword_spacing',
        'font_kerning', 'font_size', 'font_stroke_width', 'font_vertical_shift',
        'episode_text_color', 'omit_gradient', 'stroke_color', 'separator',
        'episode_text_font_size', 'episode_text_vertical_shift',
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
            font_stroke_width: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            separator: str = '•',
            stroke_color: str = 'black',
            episode_text_color: str = SERIES_COUNT_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            episode_text_vertical_shift: int = 0,
            omit_gradient: bool = False,
            preferences: Optional['Preferences'] = None,
            **unused,
        ) -> None:
        """Construct a new instance of this card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text
        self.hide_episode_text = hide_episode_text

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_kerning = font_kerning
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.separator = separator
        self.omit_gradient = omit_gradient
        self.stroke_color = stroke_color
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.episode_text_vertical_shift = episode_text_vertical_shift


    @property
    def index_commands(self) -> ImageMagickCommands:
        """Subcommand for adding the index text to the image."""

        # All text hidden, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Base commands
        size = 67.75 * self.episode_text_font_size
        base_commands = [
            f'-background transparent',
            f'-kerning 5.42',
            f'-pointsize {size:.2f}',
            f'-interword-spacing 14.5',
            f'-gravity north',
        ]

        # Sub-command for adding season/episode text
        y = 1555 + self.episode_text_vertical_shift
        if self.hide_season_text:
            return [
                *base_commands,
                f'-font "{self.EPISODE_COUNT_FONT.resolve()}"',
                f'-fill black',
                f'-stroke black',
                f'-strokewidth 6',
                f'-annotate +0{y:+} "{self.episode_text}"',
                f'-fill "{self.episode_text_color}"',
                f'-stroke "{self.episode_text_color}"',
                f'-strokewidth 0.75',
                f'-annotate +0{y:+} "{self.episode_text}"',
            ]

        if self.hide_episode_text:
            return [
                *base_commands,
                # Black stroke behind primary text
                f'-fill black',
                f'-stroke black',
                f'-strokewidth 6',
                # Add season text
                f'-font "{self.SEASON_COUNT_FONT.resolve()}"',
                f'-annotate +0{y:+} "{self.season_text}"',
                # Primary text
                f'-fill "{self.episode_text_color}"',
                f'-stroke "{self.episode_text_color}"',
                f'-strokewidth 0.75',
                # Add season text
                f'-annotate +0{y:+} "{self.season_text}"',
            ]

        return [
            *base_commands,
            f'-gravity center',
            # Black stroke behind primary text
            f'\( -fill black',
            f'-stroke black',
            f'-strokewidth 6',
            # Add season text
            f'-font "{self.SEASON_COUNT_FONT.resolve()}"',
            f'label:"{self.season_text} {self.separator}"',
            # Add episode text
            f'-font "{self.EPISODE_COUNT_FONT.resolve()}"',
            f'label:"{self.episode_text}"',
            # Combine season+episode text into one "image"
            f'+smush 25 \)',
            # Add season+episode text "image" to source image
            f'-gravity north',
            f'-geometry +0{y:+}',
            f'-composite',
            # Primary text
            f'-gravity center',
            f'\( -fill "{self.episode_text_color}"',
            f'-stroke "{self.episode_text_color}"',
            f'-strokewidth 0.75',
            # Add season text
            f'-font "{self.SEASON_COUNT_FONT.resolve()}"',
            f'label:"{self.season_text} {self.separator}"',
            # Add episode text
            f'-font "{self.EPISODE_COUNT_FONT.resolve()}"',
            f'label:"{self.episode_text}"',
            f'+smush 30 \)',
            # Add text to source image
            f'-gravity north',
            f'-geometry +0{y+2:+}',
            f'-composite',
        ]


    @property
    def black_title_commands(self) -> ImageMagickCommands:
        """Subcommand to add the black stroke behind the title text."""

        # Stroke disabled, return empty command
        if self.font_stroke_width == 0:
            return []

        stroke_width = 3.0 * self.font_stroke_width
        vertical_shift = 245 + self.font_vertical_shift

        return [
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width}',
            f'-annotate +0+{vertical_shift} "{self.title_text}"',
        ]


    @staticmethod
    def modify_extras(
            extras: dict,
            custom_font: bool,
            custom_season_titles: bool,
        ) -> None:
        """
        Modify the given extras based on whether font or season titles
        are custom.

        Args:
            extras: Dictionary to modify.
            custom_font: Whether the font are custom.
            custom_season_titles: Whether the season titles are custom.
        """

        # Generic font, reset custom episode text color
        if not custom_font:
            if 'episode_text_color' in extras:
                extras['episode_text_color'] = \
                    StandardTitleCard.SERIES_COUNT_TEXT_COLOR
            if 'episode_text_font_size' in extras:
                extras['episode_text_font_size'] = 1.0
            if 'episode_text_vertical_shift' in extras:
                extras['episode_text_vertical_shift'] = 0
            if 'stroke_color' in extras:
                extras['stroke_color'] = 'black'


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        custom_extras = (
            ('episode_text_color' in extras
                and extras['episode_text_color'] != \
                    StandardTitleCard.SERIES_COUNT_TEXT_COLOR)
            or ('episode_text_font_size' in extras
                and extras['episode_text_font_size'] != 1.0)
            or ('episode_text_vertical_shift' in extras
                and extras['episode_text_vertical_shift'] != 0)
            or ('stroke_color' in extras
                and extras['stroke_color'] != 'black')
        )

        return custom_extras or StandardTitleCard._is_custom_font(font)


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> bool:
        """
        Determine whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        standard_etf = StandardTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # Font customizations
        font_size = 157.41 * self.font_size
        interline_spacing = -22 + self.font_interline_spacing
        interword_spacing = 50 + self.font_interword_spacing
        kerning = -1.25 * self.font_kerning
        vertical_shift = 245 + self.font_vertical_shift

        # Sub-command to optionally add gradient
        gradient_command = []
        if not self.omit_gradient:
            gradient_command = [
                f'"{self.__GRADIENT_IMAGE.resolve()}"',
                f'-composite',
            ]

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and optionally blur source image
            *self.resize_and_style,
            # Overlay gradient
            *gradient_command,
            # Global title text options
            f'-gravity south',
            f'-font "{self.font_file}"',
            f'-kerning {kerning}',
            f'-interword-spacing {interword_spacing}',
            f'-interline-spacing {interline_spacing}',
            f'-pointsize {font_size}',
            # Black stroke behind title text
            *self.black_title_commands,
            # Title text
            f'-fill "{self.font_color}"',
            f'-annotate +0+{vertical_shift} "{self.title_text}"',
            # Add episode or season+episode "image"
            *self.index_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
