from pathlib import Path
from typing import TYPE_CHECKING, Optional

from modules.BaseCardType import BaseCardType, ImageMagickCommands

if TYPE_CHECKING:
    from modules.Font import Font


class StandardTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces the 'generic'
    title cards based on Reddit user /u/UniversalPolymath. This card
    supports customization of every aspect of the card, but does not
    use any arbitrary data.
    """

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
            omit_gradient: bool = False,
            preferences: Optional['Preferences'] = None, # type: ignore
            **unused,
        ) -> None:
        """Construct a new instance of this card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text.upper())
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())
        self.hide_season_text = hide_season_text or len(season_text) == 0
        self.hide_episode_text = hide_episode_text or len(episode_text) == 0

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


    @property
    def index_commands(self) -> ImageMagickCommands:
        """Subcommand for adding the index text to the image."""

        if self.hide_season_text and self.hide_episode_text:
            return []

        # Sub-command for adding season/episode text
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
                f'-fill "{self.episode_text_color}"',
                f'-stroke "{self.episode_text_color}"',
                f'-strokewidth 0.75',
                f'-annotate +0+697.2 "{self.episode_text}"',
            ]

        if self.hide_episode_text:
            return [
                # Global text effects
                f'-background transparent',
                f'-gravity center',
                f'-kerning 5.42',
                f'-pointsize 67.75',
                f'-interword-spacing 14.5',
                # Black stroke behind primary text
                f'-fill black',
                f'-stroke black',
                f'-strokewidth 6',
                # Add season text
                f'-font "{self.SEASON_COUNT_FONT.resolve()}"',
                f'-annotate +0+697.2 "{self.season_text}"',
                # Primary text
                f'-fill "{self.episode_text_color}"',
                f'-stroke "{self.episode_text_color}"',
                f'-strokewidth 0.75',
                # Add season text
                f'-annotate +0+697.2 "{self.season_text}"',
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
            f'-geometry +0+697.2',
            f'-composite',
        ]


    @property
    def black_title_commands(self) -> ImageMagickCommands:
        """
        Subcommands for adding the black stroke behind the title text.
        """

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

        return ((font.color != StandardTitleCard.TITLE_COLOR)
            or (font.file != StandardTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
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
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
