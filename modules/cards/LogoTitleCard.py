from pathlib import Path
from typing import Optional

from modules.BaseCardType import BaseCardType
from modules.CleanPath import CleanPath
from modules.Debug import log

SeriesExtra = Optional

class LogoTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces logo-centric
    title cards, primarily for the purpose of reality TV shows.
    """

    """API Parameters"""
    API_DETAILS = {
        'name': 'Logo',
        'example': '/assets/cards/logo.jpg',
        'creators': ['CollinHeist'],
        'source': 'local',
        'supports_custom_fonts': True,
        'supports_custom_seasons': True,
        'supported_extras': [
            {'name': 'Logo File',
             'identifier': 'logo',
             'description': 'Logo file to place in the center of the title card'},
            {'name': 'Separator Character',
             'identifier': 'separator',
             'description': 'Character to separate season and episode text'},
            {'name': 'Background Color',
             'identifier': 'background',
             'description': 'Background color to utilize'},
            {'name': 'Stroke Text Color',
             'identifier': 'stroke_color',
             'description': 'Custom color to use for the stroke on the title text'},
            {'name': 'Gradient Omission',
             'identifier': 'omit_gradient',
             'description': 'Whether to omit the gradient overlay from the card'},
        ], 'description': [
            'Image-less variation of the Standard title card featuring a logo and solid background instead of a source image.',
            'This card is intended to be used for very "spoilery" series, such as Reality TV shows.',
        ],
    }

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
        'source_file', 'output_file', 'title', 'season_text', 'episode_text',
        'font', 'font_size', 'title_color', 'hide_season', 'separator', 'blur',
        'vertical_shift',  'interline_spacing', 'kerning', 'stroke_width',
        'logo', 'omit_gradient', 'background', 'stroke_color',
        'hide_episode_text',
    )

    def __init__(self,
            card_file: Path,
            title: str,
            season_text: str,
            episode_text: str,
            hide_season_text: bool = False,
            hide_episode_text: bool = False,
            font_file: str = TITLE_FONT,
            font_color: str = TITLE_COLOR,
            font_size: float = 1.0,
            font_kerning: float = 1.0,
            font_interline_spacing: int = 0,
            font_stroke_width: float = 1.0,
            font_vertical_shift: int = 0,
            season_number: int = 1,
            episode_number: int = 1,
            blur: bool = False,
            grayscale: bool = False,
            logo: SeriesExtra[str] = None,
            separator: SeriesExtra[str] = '•', 
            background: SeriesExtra[str] = 'black',
            stroke_color: SeriesExtra[str] = 'black',
            omit_gradient: SeriesExtra[bool] = True,
            preferences: 'Preferences' = None,
            **unused) -> None:
        """
        Construct a new instance of this card.

        Args:
            output_file: Output file.
            title: Episode title.
            season_text: Text to use as season count text. Ignored if
                hide_season is True.
            episode_text: Text to use as episode count text.
            hide_season: Whether to omit the season text (and joining
                character) from the title card completely.
            font: Font to use for the episode title.
            title_color: Color to use for the episode title.
            interline_spacing: Pixels to adjust title interline spacing.
            stroke_width: Scalar to apply to stroke of title text.
            kerning: Scalar to apply to kerning of the title text.
            font_size: Scalar to apply to the title font size.
            vertical_shift: Pixels to adjust title vertical shift by.
            season_number: Season number for logo-file formatting.
            episode_number: Episode number for logo-file formatting.
            blur: Whether to blur the source image.
            grayscale: Whether to make the source image grayscale.
            logo: Filepath (or file format) to the logo file.
            separator: Character to use to separate season/episode text.
            background: Backround color.
            omit_gradient: Whether to omit the gradient overlay.
            stroke_color: Color to use for the back-stroke color.
            unused: Unused arguments.
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
                log.exception(f'Invalid logo file "{logo}"', e)

        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title = self.image_magick.escape_chars(title)
        self.season_text = self.image_magick.escape_chars(season_text.upper())
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())
        self.hide_season = hide_season_text
        self.hide_episode_text = hide_episode_text

        # Font attributes
        self.font = font_file
        self.font_size = font_size
        self.title_color = font_color
        self.vertical_shift = font_vertical_shift
        self.interline_spacing = font_interline_spacing
        self.kerning = font_kerning
        self.stroke_width = font_stroke_width

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
    def index_command(self) -> list[str]:
        """
        Subcommand for adding the index text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # All index text is disabled, return blank command
        if self.hide_season and self.hide_episode_text:
            return []
        
        # Only add season text
        if self.hide_episode_text:
            return [
                f'-kerning 5.42',       
                f'-pointsize 67.75',
                f'-interword-spacing 14.5',
                # Add season text
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
        if self.hide_season:
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
    def is_custom_font(font: 'Font') -> bool:
        """
        Determines whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.file != LogoTitleCard.TITLE_FONT)
            or (font.size != 1.0)
            or (font.color != LogoTitleCard.TITLE_COLOR)
            or (font.replacements != LogoTitleCard.FONT_REPLACEMENTS)
            or (font.vertical_shift != 0)
            or (font.interline_spacing != 0)
            or (font.kerning != 1.0)
            or (font.stroke_width != 1.0))


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
            True if custom season titles are indicated, False otherwise.
        """

        standard_etf = LogoTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map or
                episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # Skip card if logo doesn't exist
        if self.logo is None:
            log.error(f'Logo file not specified')
            return None
        elif not self.logo.exists():
            log.error(f'Logo file "{self.logo.resolve()}" does not exist')
            return None

        # Resize logo, get resized height to determine offset
        resized_logo = self.resize_logo()
        _, height = self.get_image_dimensions(resized_logo)
        offset = 60 + ((1030 - height) // 2)

        # Font customizations
        vertical_shift = 245 + self.vertical_shift
        font_size = 157.41 * self.font_size
        interline_spacing = -22 + self.interline_spacing
        kerning = -1.25 * self.kerning
        stroke_width = 3.0 * self.stroke_width

        # Sub-command to optionally add gradient
        gradient_command = []
        if not self.omit_gradient:
            gradient_command = [
                f'"{self.__GRADIENT_IMAGE.resolve()}"',
                f'-composite',
            ]

        command = ' '.join([
            f'convert',
            f'-set colorspace sRGB',
            # Crate canvas of static background color
            f'-size "{self.TITLE_CARD_SIZE}"',
            f'xc:"{self.background}"',
            # Overlay resized logo
            f'"{resized_logo.resolve()}"',
            f'-gravity north',
            f'-geometry "+0+{offset}"',
            f'-composite',
            # Optionally overlay logo
            *gradient_command,
            # Resize and optionally blur source image
            *self.resize_and_style,
            # Global title text options
            f'-gravity south',
            f'-font "{self.font}"',                     
            f'-kerning {kerning}',
            f'-interword-spacing 50',
            f'-interline-spacing {interline_spacing}',
            f'-pointsize {font_size}',
            # Stroke behind title text
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width}',
            f'-annotate +0+{vertical_shift} "{self.title}"',
            # Title text
            f'-fill "{self.title_color}"',
            f'-annotate +0+{vertical_shift} "{self.title}"',
            # Add episode or season+episode "image"
            *self.index_command,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        # Delete resized logo
        self.image_magick.delete_intermediate_images(resized_logo)