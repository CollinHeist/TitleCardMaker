from pathlib import Path
from typing import Optional

from modules.BaseCardType import BaseCardType, ImageMagickCommands


class WhiteBorderTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards based on
    the Standard card type, but including a white border to match the
    style of Musikmann2000's Posters.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'white_border'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 30,   # Character count to begin splitting titles
        'max_line_count': 3,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses top heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Arial_Bold.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = TITLE_COLOR
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Arial.ttf'

    """Default stroke color"""
    STROKE_COLOR = 'black'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'White Border Style'

    """White border frame image to overlay"""
    FRAME_IMAGE = REF_DIRECTORY / 'border.png'

    """Gradient image to overlay"""
    __GRADIENT_IMAGE = REF_DIRECTORY.parent / 'GRADIENT.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text',
        'font_color', 'font_file', 'font_interline_spacing', 'font_kerning',
        'font_size', 'font_stroke_width', 'font_vertical_shift', 'stroke_color',
        'episode_text_color', 'font_interword_spacing', 'separator',
        'omit_gradient',
    )

    def __init__(self, *,
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
            episode_text_color: str = TITLE_COLOR,
            omit_gradient: bool = False,
            separator: str = '•',
            stroke_color: str = STROKE_COLOR,
            preferences: Optional['Preferences'] = None, # type: ignore
            **unused,
        ) -> None:
        """
        Construct a new instance of this Card.
        """

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
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.episode_text_color = episode_text_color
        self.omit_gradient = omit_gradient
        self.separator = separator
        self.stroke_color = stroke_color


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """
        Subcommand for adding title text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # No title text
        if len(self.title_text) == 0:
            return []

        vertical_shift = 250 + self.font_vertical_shift

        return [
            # Global text effects
            f'-gravity south',
            f'-font "{self.font_file}"',
            f'-pointsize {160 * self.font_size}',
            f'-kerning {-1 * self.font_kerning}',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            # Black stroke behind primary text
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {4 * self.font_stroke_width}',
            f'-annotate +0+{vertical_shift} "{self.title_text}"',
            # Primary text
            f'-fill "{self.font_color}"',
            f'-annotate +0+{vertical_shift} "{self.title_text}"',
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """
        Subcommand for adding index text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        if self.hide_season_text and self.hide_episode_text:
            return []
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = (
                f'{self.season_text} {self.separator} {self.episode_text}'
            )

        return [
            # Global text effects
            f'-background transparent',
            f'-gravity south',
            f'-kerning 4',
            f'-pointsize 62.5',
            f'-interword-spacing 14.5',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            # Black stroke behind primary text
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 6',
            f'-annotate +0+162 "{index_text}"',
            # Primary text
            f'-fill "{self.episode_text_color}"',
            f'-stroke "{self.episode_text_color}"',
            f'-strokewidth 0.75',
            f'-annotate +0+162 "{index_text}"',
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

        # Generic font, reset episode text and box colors
        if not custom_font:
            if 'episode_text_color' in extras:
                extras['episode_text_color'] =\
                    WhiteBorderTitleCard.EPISODE_TEXT_COLOR
            if 'stroke_color' in extras:
                extras['stroke_color'] = WhiteBorderTitleCard.STROKE_COLOR


    @staticmethod
    def is_custom_font(font: 'Font') -> bool: # type: ignore
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.color != WhiteBorderTitleCard.TITLE_COLOR)
            or (font.file != WhiteBorderTitleCard.TITLE_FONT)
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

        standard_etf = WhiteBorderTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # Command to add the gradient overlay if indicated
        gradient_command = []
        if not self.omit_gradient:
            gradient_command = [
                f'"{self.__GRADIENT_IMAGE.resolve()}"',
                f'-composite',
            ]

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Fit within frame
            f'-gravity center',
            f'-resize "{self.WIDTH-(25 * 2)}x{self.HEIGHT - (25 * 2)}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            # Overlay gradient
            *gradient_command,
            # Add remaining sub-components
            *self.title_text_commands,
            *self.index_text_commands,
            # Overlay frame
            f'"{self.FRAME_IMAGE.resolve()}"',
            f'-composite',
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
