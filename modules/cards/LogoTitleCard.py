from pathlib import Path
from typing import TYPE_CHECKING, Optional

from modules.BaseCardType import BaseCardType, ImageMagickCommands
from modules.CleanPath import CleanPath
from modules.Debug import log

if TYPE_CHECKING:
    from modules.PreferenceParser import PreferenceParser
    from modules.Font import Font


class LogoTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces logo-centric
    title cards, primarily for the purpose of reality TV shows.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 32,   # Character count to begin splitting titles
        'max_line_count': 2,    # Maximum number of lines a title can take up
        'top_heavy': False,     # This class uses bottom heavy titling
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

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Logo Style'

    """Default fonts and color for series count text"""
    SEASON_COUNT_FONT = REF_DIRECTORY / 'Proxima Nova Semibold.otf'
    EPISODE_COUNT_FONT = REF_DIRECTORY / 'Proxima Nova Regular.otf'
    SERIES_COUNT_TEXT_COLOR = '#CFCFCF'

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
            season_number: int = 1,
            episode_number: int = 1,
            blur: bool = False,
            grayscale: bool = False,
            logo: Optional[str] = None,
            background: str = 'black',
            episode_text_color: str = SERIES_COUNT_TEXT_COLOR,
            episode_text_vertical_shift: int = 0,
            logo_size: float = 1.0,
            logo_vertical_shift: int = 0,
            separator: str = '•',
            stroke_color: str = 'black',
            omit_gradient: bool = True,
            use_background_image: bool = False,
            blur_only_image: bool = False,
            preferences: Optional['PreferenceParser'] = None,
            **unused,
        ) -> None:
        """
        Construct a new instance of this card.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Look for logo if it's a format string
        if logo is None:
            self.logo = None
        else:
            try:
                logo = logo.format(season_number=season_number,
                                   episode_number=episode_number)
                self.logo = Path(CleanPath(logo).sanitize())
            except Exception as e:
                self.valid = False
                log.exception(f'Invalid logo file "{logo}"')

        # Get source file if indicated
        self.use_background_image = use_background_image
        self.blur_only_image = blur_only_image
        self.source_file = source_file
        if self.use_background_image and self.source_file is None:
            log.error(f'Source file must be provided if using a background '
                      f'image')
            self.valid = False

        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text.upper())
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())
        self.hide_season_text = hide_season_text or len(season_text) == 0
        self.hide_episode_text = hide_episode_text or len(episode_text) == 0

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

        return custom_extras or LogoTitleCard._is_custom_font(font)


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

        if not self.logo or not self.logo.exists():
            log.error(f'Logo file not specified or does not exist')
            return None

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
