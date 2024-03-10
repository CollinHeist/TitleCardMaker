from pathlib import Path
from typing import TYPE_CHECKING, Optional

from modules.BaseCardType import (
    BaseCardType, ImageMagickCommands, Extra, CardDescription
)
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


class LogoTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces logo-centric
    title cards, primarily for the purpose of reality TV shows.
    """

    """API Parameters"""
    # pylint: disable=line-too-long
    API_DETAILS = CardDescription(
        name='Logo',
        identifier='logo',
        example='/internal_assets/cards/logo.jpg',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Logo Size',
                identifier='logo_size',
                description='How much to scale the size of the logo',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.'
            ),
            Extra(
                name='Logo Vertical Shift',
                identifier='logo_vertical_shift',
                description='Vertical shift to apply to the logo',
                tooltip=(
                    'Positive values to shift the logo down, negative values to'
                    'shift it up. Default is <v>0.0</v>. Unit is pixels.'
                ),
            ),
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is <c>#CFCFCF</c>.'
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
                name='Background Color',
                identifier='background',
                description='Background color to use behind the logo',
                tooltip=(
                    'Ignored if a background image is used. Default is '
                    '<c>black</c>.'
                ),
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
                tooltip='Default is <v>•</v>.'
            ),
            Extra(
                name='Background Image Enabling',
                identifier='use_background_image',
                description='Whether to use a background image (not color)',
                tooltip=(
                    'Either <v>True</v>, or <v>False</v>. Default is '
                    '<v>False</v>.'
                ),
            ),
            Extra(
                name='Stroke Text Color',
                identifier='stroke_color',
                description='Color to use for the text stroke',
                tooltip='Default is <c>black</c>.'
            ),
            Extra(
                name='Gradient Omission',
                identifier='omit_gradient',
                description='Whether to omit the gradient overlay',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v>, text '
                    'may appear less legible on brighter images. Default is '
                    '<v>False</v>.'
                ),
            ),
            Extra(
                name='Blur Image Only',
                identifier='blur_only_image',
                description='Whether to only blur the background image',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v>, the '
                    'logo is not blurred. Default is <v>False</v>.'
                ),
            ),
        ],
        description=[
            'Variation of the Standard title card featuring a central logo.',
            'This card is intended to be used for very "spoilery" series, such '
            'as Reality TV shows.', 'The background of this card can either be '
            'a solid color or an image.', 'If a background image is desired, it'
            ' is recommended to use an Art Un/Watched Style.',
        ]
    )
    # pylint: enable=line-too-long

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 32,
        'max_line_count': 2,
        'style': 'bottom',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Sequel-Neue.otf').resolve())
    TITLE_COLOR = '#EBEBEB'
    FONT_REPLACEMENTS = {
        '[': '(', ']': ')', '(': '[', ')': ']', '―': '-', '…': '...'
    }

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Whether this CardType uses unique source images"""
    USES_UNIQUE_SOURCES = False

    """Whether this class uses Source Images at all"""
    USES_SOURCE_IMAGES = False # Set as False; if required then caught by model

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Logo Style'

    """Default fonts and color for series count text"""
    SEASON_COUNT_FONT = REF_DIRECTORY / 'Proxima Nova Semibold.otf'
    EPISODE_COUNT_FONT = REF_DIRECTORY / 'Proxima Nova Regular.otf'
    SERIES_COUNT_TEXT_COLOR = '#CFCFCF'

    """Paths to intermediate files that are deleted after the card is created"""
    __RESIZED_LOGO = BaseCardType.TEMP_DIR / 'resized_logo.png'

    """Source path for the gradient image overlayed over all title cards"""
    __GRADIENT_IMAGE = REF_DIRECTORY / 'GRADIENT.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_file', 'font_kerning', 'font_interline_spacing',
        'font_interword_spacing', 'font_size', 'font_stroke_width',
        'font_vertical_shift', 'separator', 'logo', 'logo_size',
        'logo_vertical_shift', 'omit_gradient', 'background', 'stroke_color',
        'use_background_image', 'blur_only_image', 'episode_text_color',
        'episode_text_vertical_shift'
    )

    def __init__(self,
            card_file: Path,
            title_text: str,
            season_text: str,
            episode_text: str,
            source_file: Optional[Path] = None,
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
            background: str = 'black',
            blur_only_image: bool = False,
            episode_text_color: str = SERIES_COUNT_TEXT_COLOR,
            episode_text_vertical_shift: int = 0,
            logo_file: Optional[Path] = None,
            logo_size: float = 1.0,
            logo_vertical_shift: int = 0,
            omit_gradient: bool = True,
            separator: str = '•',
            stroke_color: str = 'black',
            use_background_image: bool = False,
            preferences: Optional['Preferences'] = None,
            **unused,
        ) -> None:
        """
        Construct a new instance of this card.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Get source file if indicated
        self.use_background_image = use_background_image
        self.blur_only_image = blur_only_image
        self.logo = logo_file
        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text
        self.hide_episode_text = hide_episode_text

        # Font attributes
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.background = background
        self.episode_text_color = episode_text_color
        self.episode_text_vertical_shift = episode_text_vertical_shift
        self.omit_gradient = omit_gradient
        self.logo_size = logo_size
        self.logo_vertical_shift = logo_vertical_shift
        self.separator = separator
        self.stroke_color = stroke_color


    @property
    def logo_commands(self) -> ImageMagickCommands:
        """Subcommands to add the logo to the Card."""

        # Post-resize max dimensions of the logo
        max_width = 1875 * self.logo_size
        max_height = 1030 * self.logo_size

        # Determine current dimensions of the logo
        current_width, current_height = self.image_magick.get_image_dimensions(
            self.logo
        )

        # Determine dimensions post-resizing
        scale = max_height / current_height  # -resize x{max_height}
        if current_width * scale > max_width:# -resize {max_width}x{max_height}>
            scale = max_width / current_width

        # Resize logo, get resized height to determine offset
        offset = 60 + ((1030 - (current_height * scale)) // 2) \
            + self.logo_vertical_shift

        return [
            f'-gravity north',
            f'\( "{self.logo.resolve()}"',
            f'-resize x{max_height}',
            f'-resize {max_width}x{max_height}\>',
            f'\) -geometry +0{offset:+}',
            f'-composite',
        ]


    @property
    def index_commands(self) -> ImageMagickCommands:
        """Subcommand for adding the index text to the source image."""

        # All index text is disabled, return blank command
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Only add season text
        y = 697.2 + self.episode_text_vertical_shift
        if self.hide_episode_text:
            return [
                f'-kerning 5.42',
                f'-pointsize 67.75',
                f'-interword-spacing 14.5',
                f'-font "{self.SEASON_COUNT_FONT.resolve()}"',
                f'-gravity center',
                f'-fill black',
                f'-stroke black',
                f'-strokewidth 6',
                f'-annotate +0{y:+} "{self.season_text}"',
                f'-fill "{self.episode_text_color}"',
                f'-stroke "{self.episode_text_color}"',
                f'-strokewidth 0.75',
                f'-annotate +0{y:+} "{self.episode_text}"',
            ]

        # Only add episode text
        if self.hide_season_text:
            return [
                f'-kerning 5.42',
                f'-pointsize 67.75',
                f'-interword-spacing 14.5',
                f'-font "{self.EPISODE_COUNT_FONT.resolve()}"',
                f'-gravity center',
                f'-fill black',
                f'-stroke black',
                f'-strokewidth 6',
                f'-annotate +0{y:+} "{self.episode_text}"',
                f'-fill "{self.episode_text_color}"',
                f'-stroke "{self.episode_text_color}"',
                f'-strokewidth 0.75',
                f'-annotate +0{y:+} "{self.episode_text}"',
            ]

        return [
            # Global text effects
            f'-background transparent',
            f'-gravity center',
            f'-kerning 5.42',
            f'-pointsize 67.75',
            f'-interword-spacing 14.5',
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
            f'-geometry +0{y:+}',
            f'-composite',
            # Primary text
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
            f'-geometry +0{y:+}',
            f'-composite',
        ]


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the title text to the image."""

        # No title text, return empty commands
        if not self.title_text:
            return []

        # Font customizations
        vertical_shift = 245 + self.font_vertical_shift
        font_size = 157.41 * self.font_size
        interline_spacing = -22 + self.font_interline_spacing
        interword_spacing = 50 + self.font_interword_spacing
        kerning = -1.25 * self.font_kerning
        stroke_width = 3.0 * self.font_stroke_width

        return [
            # Global title text options
            f'-gravity south',
            f'-font "{self.font_file}"',
            f'-kerning {kerning}',
            f'-interword-spacing {interword_spacing}',
            f'-interline-spacing {interline_spacing}',
            f'-pointsize {font_size}',
            # Stroke behind title text
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width}',
            f'-annotate +0+{vertical_shift} "{self.title_text}"',
            # Title text
            f'-fill "{self.font_color}"',
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

        if not custom_font:
            if 'episode_text_color' in extras:
                extras['episode_text_color'] =\
                    LogoTitleCard.SERIES_COUNT_TEXT_COLOR
            if 'episode_text_vertical_shift' in extras:
                extras['episode_text_vertical_shift'] = 0
            if 'stroke_color' in extras:
                extras['stroke_color'] = 'black'


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determines whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        custom_extras = (
            ('episode_text_color' in extras
                and extras['episode_text_color'] != 0)
            or ('episode_text_vertical_shift' in extras
                and extras['episode_text_vertical_shift'] != 0)
            or ('stroke_color' in extras
                and extras['stroke_color'] != 'black')
        )

        return (custom_extras
            or ((font.color != LogoTitleCard.TITLE_COLOR)
            or (font.file != LogoTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
            or (font.stroke_width != 1.0)
            or (font.vertical_shift != 0))
        )


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> bool:
        """
        Determines whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        standard_etf = LogoTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # Sub-command to add source file or create colored background
        if self.use_background_image:
            blur_command = ''
            if self.blur and self.blur_only_image:
                blur_command = f'-blur {self.BLUR_PROFILE}'
            background_command = [
                f'"{self.source_file.resolve()}"',
                *self.resize,
                blur_command,
            ]
        else:
            background_command = [
                f'-set colorspace sRGB',
                f'-size "{self.TITLE_CARD_SIZE}"',
                f'xc:"{self.background}"',
            ]

        # Sub-command to optionally add gradient
        gradient_command = []
        if not self.omit_gradient:
            gradient_command = [
                f'"{self.__GRADIENT_IMAGE.resolve()}"',
                f'-composite',
            ]

        # Sub-command to style the overall image if indicated
        style_command = []
        if self.blur_only_image and self.grayscale:
            style_command = [
                f'-colorspace gray',
                f'-set colorspace sRGB',
            ]
        elif not self.blur_only_image:
            style_command = self.style

        command = ' '.join([
            f'convert',
            # Add background image or color
            *background_command,
            # Overlay logo
            *self.logo_commands,
            # Optionally overlay gradient
            *gradient_command,
            # Apply style that is applicable to entire image
            *style_command,
            # Title text
            *self.title_text_commands,
            # Add episode or season+episode "image"
            *self.index_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
