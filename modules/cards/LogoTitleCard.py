from pathlib import Path
from typing import Optional

from modules.BaseCardType import (
    BaseCardType, ImageMagickCommands, Extra, CardDescription
)


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
        source='local',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
            ), Extra(
                name='Background Color or Image',
                identifier='background',
                description='Background color or image to use behind the logo',
            ), Extra(
                name='Stroke Text Color',
                identifier='stroke_color',
                description='Color to use for the text stroke',
            ), Extra(
                name='Gradient Omission',
                identifier='omit_gradient',
                description='Whether to omit the gradient overlay from the card',
            ), Extra(
                name='Background Image Enabling',
                identifier='use_background_image',
                description='Whether "background" is an image (instead of a color)',
            ), Extra(
                name='Blur Image Only',
                identifier='blur_only_image',
                description='Whether to only blur the background image - and not the logo - when blurring and using a background image',
            ),
        ], description=[
            'Variation of the Standard title card featuring a central logo.',
            'This card is intended to be used for very "spoilery" series, such as Reality TV shows.',
            'The background of this card can either be a solid color or an image.',
            'If a background image is desired, it is recommended to use an Art Un/Watched Style.',
        ]
    )
    # pylint: enable=line-too-long

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

    """Paths to intermediate files that are deleted after the card is created"""
    __RESIZED_LOGO = BaseCardType.TEMP_DIR / 'resized_logo.png'

    """Source path for the gradient image overlayed over all title cards"""
    __GRADIENT_IMAGE = REF_DIRECTORY / 'GRADIENT.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_file', 'font_kerning', 'font_interline_spacing', 'font_size',
        'font_stroke_width',  'font_vertical_shift', 'separator', 'logo',
        'omit_gradient', 'background', 'stroke_color', 'use_background_image',
        'blur_only_image',
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
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_stroke_width: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            logo_file: Optional[Path] = None,
            background: str = 'black',
            separator: str = '•',
            stroke_color: str = 'black',
            omit_gradient: bool = True,
            use_background_image: bool = False,
            blur_only_image: bool = False,
            preferences: Optional['Preferences'] = None, # type: ignore
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
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.omit_gradient = omit_gradient
        self.background = background
        self.separator = separator
        self.stroke_color = stroke_color


    def resize_logo(self) -> Path:
        """
        Resize the logo into at most a 1875x1030 bounding box.

        Returns:
            Path to the created image.
        """

        command = ' '.join([
            f'convert',
            f'"{self.logo.resolve()}"',
            f'-resize x1030',
            f'-resize 1875x1030\>',
            f'"{self.__RESIZED_LOGO.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__RESIZED_LOGO


    @property
    def index_commands(self) -> ImageMagickCommands:
        """
        Subcommand for adding the index text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # All index text is disabled, return blank command
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Only add season text
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
                f'-annotate +0+697.2 "{self.season_text}"',
                f'-fill "{self.SERIES_COUNT_TEXT_COLOR}"',
                f'-stroke "{self.SERIES_COUNT_TEXT_COLOR}"',
                f'-strokewidth 0.75',
                f'-annotate +0+697.2 "{self.episode_text}"',
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
                f'-annotate +0+697.2 "{self.episode_text}"',
                f'-fill "{self.SERIES_COUNT_TEXT_COLOR}"',
                f'-stroke "{self.SERIES_COUNT_TEXT_COLOR}"',
                f'-strokewidth 0.75',
                f'-annotate +0+697.2 "{self.episode_text}"',
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
            f'-geometry +0+697.2',
            f'-composite',
            # Primary text
            f'\( -fill "{self.SERIES_COUNT_TEXT_COLOR}"',
            f'-stroke "{self.SERIES_COUNT_TEXT_COLOR}"',
            f'-strokewidth 0.75',
            # Add season text
            f'-font "{self.SEASON_COUNT_FONT.resolve()}"',
            f'label:"{self.season_text} {self.separator}"',
            # Add episode text
            f'-font "{self.EPISODE_COUNT_FONT.resolve()}"',
            f'label:"{self.episode_text}"',
            f'+smush 30 \)',
            # Add text to source image
            f'-geometry +0+697.2',
            f'-composite',
        ]


    @staticmethod
    def is_custom_font(font: 'Font') -> bool: # type: ignore
        """
        Determines whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.color != LogoTitleCard.TITLE_COLOR)
            or (font.file != LogoTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
            or (font.stroke_width != 1.0)
            or (font.vertical_shift != 0)
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

        # Resize logo, get resized height to determine offset
        resized_logo = self.resize_logo()
        _, height = self.image_magick.get_image_dimensions(resized_logo)
        offset = 60 + ((1030 - height) // 2)

        # Font customizations
        vertical_shift = 245 + self.font_vertical_shift
        font_size = 157.41 * self.font_size
        interline_spacing = -22 + self.font_interline_spacing
        kerning = -1.25 * self.font_kerning
        stroke_width = 3.0 * self.font_stroke_width

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
            # Overlay resized logo
            f'"{resized_logo.resolve()}"',
            f'-gravity north',
            f'-geometry "+0+{offset}"',
            f'-composite',
            # Optionally overlay gradient
            *gradient_command,
            # Apply style that is applicable to entire image
            *style_command,
            # Global title text options
            f'-gravity south',
            f'-font "{self.font_file}"',
            f'-kerning {kerning}',
            f'-interword-spacing 50',
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
            # Add episode or season+episode "image"
            *self.index_commands,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        # Delete resized logo
        self.image_magick.delete_intermediate_images(resized_logo)
