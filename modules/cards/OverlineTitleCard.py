from pathlib import Path
from typing import Literal, Optional

from modules.BaseCardType import (
    BaseCardType, ImageMagickCommands, Extra, CardDescription
)
from modules.ImageMagickInterface import Dimensions


class Coordinate:
    """Class that defines a single Coordinate on an x/y plane."""
    __slots__ = ('x', 'y')

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __str__(self) -> str:
        return f'{self.x:.0f},{self.y:.0f}'


class Rectangle:
    """Class that defines movable SVG rectangle."""
    __slots__ = ('start', 'end')

    def __init__(self, start: Coordinate, end: Coordinate) -> None:
        self.start = start
        self.end = end

    def __str__(self) -> str:
        return f'rectangle {str(self.start)},{str(self.end)}'

    def draw(self) -> str:
        """Draw this Rectangle"""
        return f'-draw "{str(self)}"'


class OverlineTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards featuring
    a thin line over (or under) the title text. This line is
    interesected by the episode text, and can be recolored.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Overline',
        identifier='overline',
        example='/internal_assets/cards/overline.jpg',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Defaults to match the Font color',
            ), Extra(
                name='Line Color',
                identifier='line_color',
                description='Color of the line',
                tooltip='Defaults to match the episode text or Font color',
            ), Extra(
                name='Line Position',
                identifier='line_position',
                description='Position of the line and episode text',
                tooltip=(
                    'Either <v>top</v> or <v>bottom</v>. Defaults to <v>top</v>.'
                ),
            ), Extra(
                name='Line Width',
                identifier='line_width',
                description='Thickness of the line',
                tooltip=(
                    'Thickness of the line. Default is <v>7</v>. Unit is '
                    'pixels.'
                ),
            ), Extra(
                name='Line Toggle',
                identifier='hide_line',
                description='Whether to hide the line completely',
                tooltip='Either <v>True</v> or <v>False</v>.'
            ), Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
            ), Extra(
                name='Gradient Omission',
                identifier='omit_gradient',
                description='Whether to omit the gradient overlay',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v>, text '
                    'may appear less legible on brighter images.'
                ),
            )
        ], description=[
            'Simple Title Card with title and episode text at the bottom of '
            'image, and a thin line positioned above (or below) the title '
            'text.', 'The line (and episode text) can be repositioned and '
            'colored separately.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'overline'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 30,   # Character count to begin splitting titles
        'max_line_count': 2,    # Maximum number of lines a title can take up
        'top_heavy': False,      # This class uses top heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'HelveticaNeueMedium.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = TITLE_COLOR
    EPISODE_TEXT_FONT = (
        BaseCardType.BASE_REF_DIRECTORY / 'Proxima Nova Semibold.otf'
    )

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Overline Style'

    """How thick the line is (in pixels)"""
    LINE_THICKNESS = 7

    """Gradient to overlay"""
    GRADIENT_IMAGE = REF_DIRECTORY / 'small_gradient.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_file',
        'font_size', 'font_color', 'font_interline_spacing',
        'font_interword_spacing', 'font_kerning', 'font_stroke_width',
        'font_vertical_shift', 'episode_text_color', 'line_color', 'hide_line',
        'line_position', 'line_width', 'omit_gradient', 'separator',
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
            episode_text_color: str = EPISODE_TEXT_COLOR,
            hide_line: bool = False,
            line_color: str = TITLE_COLOR,
            line_position: Literal['top', 'bottom'] = 'top',
            line_width: int = LINE_THICKNESS,
            omit_gradient: bool = False,
            separator: str = '-',
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
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text
        self.hide_episode_text = hide_episode_text

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
        self.hide_line = hide_line
        self.line_color = line_color
        self.line_position = line_position
        self.line_width = line_width
        self.omit_gradient = omit_gradient
        self.separator = separator


    @property
    def gradient_commands(self) -> ImageMagickCommands:
        """
        Subcommand to add the gradient overlay to the source image.

        Returns:
            List of ImageMagick commands.
        """

        if self.omit_gradient:
            return []

        return [
            f'"{self.GRADIENT_IMAGE.resolve()}"',
            f'-composite',
        ]


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """
        Subcommand for adding title text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # No title text, or not being shown
        if len(self.title_text) == 0:
            return []

        # Position of the text is based on where the line is
        vertical_position = self.font_vertical_shift
        if self.line_position == 'top':
            vertical_position += 70
        else:
            vertical_position += 110

        # Font characteristics
        size = 55 * self.font_size
        interline_spacing = 25 + self.font_interline_spacing
        interword_spacing = 50 + self.font_interword_spacing
        kerning = -2 * self.font_kerning
        stroke_width = 5 * self.font_stroke_width

        return [
            f'-density 200',
            f'-gravity south',
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {size}',
            f'-strokewidth {stroke_width}',
            f'-stroke black',
            f'-kerning {kerning}',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {interword_spacing}',
            f'-annotate +0+{vertical_position} "{self.title_text}"',
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """
        Subcommands for adding index text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # If not showing index text, return
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Set index text based on which text is hidden/not
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text} {self.separator} {self.episode_text}'

        # Determine vertical position based on which element this text is
        vertical_shift = self.font_vertical_shift
        if self.line_position == 'top':
            vertical_shift += 232
        else:
            vertical_shift += 65

        return [
            f'-density 200',
            # f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-font "{self.REF_DIRECTORY.parent / "Proxima Nova Semibold.otf"}"',
            f'-fill "{self.episode_text_color}"',
            f'-strokewidth 2',
            f'-pointsize 22',
            f'-interword-spacing 18',
            f'-annotate +0+{vertical_shift} "{index_text}"'
        ]


    def line_commands(self,
            title_text_dimensions: Dimensions,
            index_text_dimensions: Dimensions,
        ) -> ImageMagickCommands:
        """
        Subcommands to add the over/underline to the image.

        Args:
            title_text_dimensions: Dimensions of the title text.
            index_text_dimensions: Dimensions of the index text.

        Returns:
            List of ImageMagick commands.
        """

        # Line is not being shown, skip
        if self.hide_line:
            return []

        # Determine starting vertical offset of the lines
        vertical_position = self.font_vertical_shift
        if self.line_position == 'top':
            vertical_position += 265
        else:
            vertical_position += 98
        vertical_position = self.HEIGHT - vertical_position

        # If index text is gone, draw singular rectangle
        if self.hide_season_text and self.hide_episode_text:
            right_rectangle = Rectangle(Coordinate(0, 0), Coordinate(0, 0))
            left_rectangle = Rectangle(
                Coordinate(
                    (self.WIDTH / 2) - (title_text_dimensions.width / 2) + 30,
                    vertical_position - (self.line_width / 2)
                ),
                Coordinate(
                    (self.WIDTH / 2) + (title_text_dimensions.width / 2) - 30,
                    vertical_position + (self.line_width / 2),
                )
            )
        else:
            # Create left rectangle
            left_rectangle = Rectangle(
                Coordinate(
                    (self.WIDTH / 2) - (title_text_dimensions.width / 2) + 30,
                    vertical_position - (self.line_width / 2),
                ),
                Coordinate(
                    (self.WIDTH / 2) - (index_text_dimensions.width / 2),
                    vertical_position + (self.line_width / 2),
                )
            )

            # Create right rectangle
            right_rectangle = Rectangle(
                Coordinate(
                    (self.WIDTH / 2) + (index_text_dimensions.width / 2),
                    vertical_position - (self.line_width / 2),
                ),
                Coordinate(
                    (self.WIDTH / 2) + (title_text_dimensions.width / 2) - 30,
                    vertical_position + (self.line_width / 2),
                )
            )

            # Draw nothing if either rectangle would invert or is too short
            if (left_rectangle.start.x > left_rectangle.end.x
                or right_rectangle.start.x > right_rectangle.end.x
                or left_rectangle.end.x - left_rectangle.start.x < 20
                or right_rectangle.end.x - right_rectangle.start.x < 20):
                return []

        return [
            f'-fill "{self.line_color}"',
            f'-stroke black',
            f'-strokewidth 2',
            left_rectangle.draw(),
            right_rectangle.draw(),
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
                    OverlineTitleCard.EPISODE_TEXT_COLOR
            if 'line_color' in extras:
                extras['line_color'] = OverlineTitleCard.TITLE_COLOR


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

        return ((font.color != OverlineTitleCard.TITLE_COLOR)
            or (font.file != OverlineTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
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

        standard_etf = OverlineTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # Get the dimensions of the title and index text
        title_text_dimensions = self.image_magick.get_text_dimensions(
            self.title_text_commands, width='max', height='sum',
        )
        index_text_dimensions = self.image_magick.get_text_dimensions(
            self.index_text_commands, width='max', height='sum',
        )

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Add gradient overlay
            *self.gradient_commands,
            # Add text
            *self.title_text_commands,
            *self.index_text_commands,
            # Add line
            *self.line_commands(title_text_dimensions, index_text_dimensions),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
