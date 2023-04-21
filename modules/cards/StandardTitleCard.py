from pathlib import Path
from typing import Any, Optional

from modules.BaseCardType import BaseCardType
from modules.Debug import log

SeriesExtra = Optional

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
        example='/assets/cards/standard.jpg',
        creators=['/u/UniversalPolymath', 'CollinHeist'],
        source='local',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Stroke Text Color',
                identifier='stroke_color',
                description='Color to use for the text stroke',
            ), Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
            ), Extra(
                name='Gradient Omission',
                identifier='omit_gradient',
                description='Whether to omit the gradient overlay from the card',
            )
        ], description=[
            'The default title card style.',
            'This card features center-aligned season, episode, and title text.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 32,   # Character count to begin splitting titles
        'max_line_count': 3,    # Maximum number of lines a title can take up
        'top_heavy': False,     # This class uses bottom heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Sequel-Neue.otf').resolve())
    TITLE_COLOR = '#EBEBEB'
    FONT_REPLACEMENTS = {'[': '(', ']': ')', '(': '[', ')': ']', '―': '-',
                         '…': '...', '“': '"'}

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'standard'

    """Default fonts and color for series count text"""
    SEASON_COUNT_FONT = REF_DIRECTORY / 'Proxima Nova Semibold.otf'
    EPISODE_COUNT_FONT = REF_DIRECTORY / 'Proxima Nova Regular.otf'
    SERIES_COUNT_TEXT_COLOR = '#CFCFCF'

    """Source path for the gradient image overlayed over all title cards"""
    __GRADIENT_IMAGE = REF_DIRECTORY / 'GRADIENT.png'

    __slots__ = (
        'source_file', 'output_file', 'title', 'season_text', 'episode_text',
        'font', 'font_size', 'title_color', 'hide_season', 'separator',
        'vertical_shift', 'interline_spacing', 'kerning', 'stroke_width',
        'omit_gradient', 'stroke_color',
    )

    def __init__(self,
            source_file: Path,
            card_file: Path,
            title: str,
            season_text: str,
            episode_text: str,
            hide_season_text: bool = False,
            font_file: str = TITLE_FONT,
            font_color: str = TITLE_COLOR,
            font_size: float = 1.0,
            font_interline_spacing: int = 0,
            font_kerning: float = 1.0,
            font_stroke_width: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            separator: SeriesExtra[str] = '•',
            stroke_color: SeriesExtra[str] = 'black',
            omit_gradient: SeriesExtra[bool] = False,
            preferences: 'Preferences' = None,
            **unused) -> None:
        """
        Construct a new instance of this card.

        Args:
            source: Source image to base the card on.
            output_file: Output file where to create the card.
            title: Title text to add to created card.
            season_text: Season text to add to created card.
            episode_text: Episode text to add to created card.
            font: Font name or path (as string) to use for episode title.
            font_size: Scalar to apply to title font size.
            title_color: Color to use for title text.
            hide_season: Whether to ignore season_text.
            vertical_shift: Pixel count to adjust the title vertical
                offset by.
            interline_spacing: Pixel count to adjust title interline
                spacing by.
            kerning: Scalar to apply to kerning of the title text.
            stroke_width: Scalar to apply to black stroke.
            blur: Whether to blur the source image.
            grayscale: Whether to make the source image grayscale.
            separator: Character to use to separate season/episode text.
            omit_gradient: Whether to omit the gradient overlay.
            stroke_color: Color to use for the back-stroke color.
            unused: Unused arguments.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title = self.image_magick.escape_chars(title)
        self.season_text = self.image_magick.escape_chars(season_text.upper())
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())

        # Font/card customizations
        self.font = font_file
        self.font_size = font_size
        self.title_color = font_color
        self.hide_season = hide_season_text
        self.vertical_shift = font_vertical_shift
        self.interline_spacing = font_interline_spacing
        self.kerning = font_kerning
        self.stroke_width = font_stroke_width

        # Optional extras
        self.separator = separator
        self.omit_gradient = omit_gradient
        self.stroke_color = stroke_color


    @property
    def index_command(self) -> list[str]:
        """
        Subcommand for adding the index text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # Sub-command for adding season/episode text
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
        else:
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


    @property
    def black_title_command(self) -> list[str]:
        """
        Subcommand for adding the black stroke behind the title text.

        Returns:
            List of ImageMagick commands.
        """

        # Stroke disabled, return empty command
        if self.stroke_width == 0:
            return []

        vertical_shift = 245 + self.vertical_shift
        stroke_width = 3.0 * self.stroke_width

        return [
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width}',
            f'-annotate +0+{vertical_shift} "{self.title}"',
        ]


    @staticmethod
    def modify_extras(extras: dict[str, Any], custom_font: bool,
                      custom_season_titles: bool) -> None:
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
            if 'stroke_color' in extras:
                extras['stroke_color'] = 'black'


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

        return ((font.file != StandardTitleCard.TITLE_FONT)
            or (font.size != 1.0)
            or (font.color != StandardTitleCard.TITLE_COLOR)
            or (font.vertical_shift != 0)
            or (font.interline_spacing != 0)
            or (font.kerning != 1.0)
            or (font.stroke_width != 1.0))


    @staticmethod
    def is_custom_season_titles(custom_episode_map: bool, 
                                episode_text_format: str) -> bool:
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

        return (custom_episode_map or
                episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # Font customizations
        vertical_shift = 245 + self.vertical_shift
        font_size = 157.41 * self.font_size
        interline_spacing = -22 + self.interline_spacing
        kerning = -1.25 * self.kerning

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
            f'-font "{self.font}"',                     
            f'-kerning {kerning}',
            f'-interword-spacing 50',
            f'-interline-spacing {interline_spacing}',
            f'-pointsize {font_size}',
            # Black stroke behind title text
            *self.black_title_command,
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