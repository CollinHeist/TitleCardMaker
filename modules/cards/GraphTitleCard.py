from math import cos, sin, pi
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from modules.BaseCardType import (
    BaseCardType, Coordinate, ImageMagickCommands, Extra, CardDescription, Line,
)
from modules.Debug import log
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


TextPosition = Literal[
    'upper left', 'upper right',
    'left', 'right',
    'lower left', 'lower right',
]


class SvgCircle:
    """Class definition of a circle which can be drawn as an SVG."""

    __slots__  = ('radius', 'percentage')

    def __init__(self,
            *,
            radius: int,
            fill_percentage: float,
        ) -> None:
        """
        Initialize this circle.

        Args:
            radius: Radius of the circle.
            fill_percentage: Percentage of the circle that is filled.
        """

        self.radius = radius
        self.percentage = fill_percentage


    def _angle_to_coordinate(self, angle: float, /) -> tuple[float, float]:
        """
        Convert the given angle to X/Y coordinates.

        Args:
            angle: Angle (in degrees) to convert.

        Returns:
            Tuple of the X and Y coordinates equivalent to the given
            angle.
        """

        angle_radians = angle * pi / 180.0
        adjustment = -self.radius if angle > 180 else self.radius

        # Non-standard x/y conversion because it 0deg is top of the circle
        return (
            self.radius * sin(angle_radians),
            # Relative to center of circle, adjust to top
            -self.radius * cos(angle_radians) + adjustment,
        )


    @property
    def draw_commands(self) -> ImageMagickCommands:
        """ImageMagick commands to draw this Circle."""

        # Starting in bottom left corner; shift to middle top
        positioning = f'M {self.radius},-{2 * self.radius}'

        # Less than 50% filled; only draw singular arc
        x, y = self._angle_to_coordinate(360 * self.percentage)
        if self.percentage <= 0.5:
            return [
                # Start path
                f'path \'',
                positioning,
                # Draw arc
                f'a {self.radius},{self.radius} 0 0 1 {x:+.1f},{y:+.1f}',
                # End path
                f'\'',
            ]

        return [
            # Start path
            f'path \'',
            positioning,
            # Draw full arc half
            f'a {self.radius},{self.radius} 0 0 1 {0:+.1f},{2 * self.radius}',
            # Draw partial arc
            f'a {self.radius},{self.radius} 0 0 1 {x:+.1f},{y:+.1f}',
            # End path
            f'\'',
        ]


class GraphTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards with a
    progress bar or "graph" which can be used to indicate total Series
    progress.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Graph',
        identifier='graph',
        example='/internal_assets/cards/graph.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=False,
        supported_extras=[
            Extra(
                name='Graph Background Color',
                identifier='graph_background_color',
                description='Background color of the graph',
                tooltip='Default is <c>rgba(140,140,140,0.5)</c>.',
            ),
            Extra(
                name='Graph Color',
                identifier='graph_color',
                description='Color of the filled-in portion of the graph',
                tooltip='Default is <c>rgb(99,184,255)</c>.' # SteelBlue1
            ),
            Extra(
                name='Graph Inset',
                identifier='graph_inset',
                description='How far to inset the graph from the edges',
                tooltip=(
                    'Number between <v>0.0</v> and <v>1800</v>. Default is '
                    '<v>75</v>. Unit is pixels.'
                ),
            ),
            Extra(
                name='Graph Radius',
                identifier='graph_radius',
                description='Radius of the graph',
                tooltip=(
                    'Number between <v>0</v> and <v>900</v>. Default is '
                    '<v>175</v>. Unit is pixels.'
                ),
            ),
            Extra(
                name='Graph Text Font Size',
                identifier='graph_text_font_size',
                description='Size adjustment for the graph text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
            ),
            Extra(
                name='Graph Width',
                identifier='graph_width',
                description='The width of the graph',
                tooltip=(
                    'Number between <v>2</v> and the graph radius. Default is '
                    '<v>25</v>. Unit is pixels.'
                )
            ),
            Extra(
                name='Fill Scale',
                identifier='fill_scale',
                description='Scale for how wide the filled graph should appear',
                tooltip=(
                    'Number between <v>0.0</v> and <v>1.0</v>. Default is '
                    '<v>0.6</v>.'
                ),
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
                name='Text Position',
                identifier='text_position',
                description='Where on the image to position the graph and text',
                tooltip=(
                    'Either <v>upper left</v>, <v>upper right</v>, <v>left</v>,'
                    ' <v>right</v>, <v>lower left</v>, or <v>lower right</v>. '
                    'Default is <v>lower left</v>.'
                ),
            ),
        ],
        description=[
            'A title card similiar to the Shape card, but features a bar '
            '"graph" or progress bar which can be used to indicate total series'
            ' progress.', 'The progress is parsed from the Episode Text, which '
            'defaults to "{episode_number} / {season_episode_max}" to display '
            'the progress within each season.',
        ],
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'inset'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 35,
        'max_line_count': 3,
        'style': 'top',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'HelveticaNeue-BoldItalic.ttf').resolve())
    TITLE_COLOR = 'rgb(247, 247, 247)'
    DEFAULT_FONT_CASE = 'source'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'HelveticaNeue-BoldItalic.ttf'
    EPISODE_TEXT_FORMAT = '{episode_number} / {season_episode_max}'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = False

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Graph Style'

    """Implementation details"""
    BACKGROUND_GRAPH_COLOR = 'rgba(140,140,140,0.5)'
    GRAPH_COLOR = 'SteelBlue1' # 'rgb(77,178,136)'
    GRAPH_FILL_SCALE = 0.6
    GRAPH_INSET = 75
    GRAPH_RADIUS = 175
    GRAPH_WIDTH = 25

    """Gradient image"""
    GRADIENT = REF_DIRECTORY.parent / 'overline' / 'small_gradient.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'numerator', 'denominator',
        'hide_episode_text', 'font_color', 'font_interline_spacing',
        'font_interword_spacing', 'font_file', 'font_kerning', 'font_size',
        'font_vertical_shift', 'episode_text_font_size',
        'graph_background_color', 'graph_color', 'graph_inset', 'graph_radius',
        'graph_width', 'fill_scale', 'omit_gradient', 'percentage',
        'text_position',
    )


    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title_text: str,
            episode_text: str,
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
            graph_background_color: str = BACKGROUND_GRAPH_COLOR,
            graph_color: str = GRAPH_COLOR,
            graph_inset: int = GRAPH_INSET,
            graph_radius: int = GRAPH_RADIUS,
            graph_text_font_size: float = 1.0,
            graph_width: int = GRAPH_WIDTH,
            fill_scale: float = GRAPH_FILL_SCALE,
            omit_gradient: bool = False,
            percentage: float = 0.75,
            text_position: TextPosition = 'lower left',
            preferences: Optional['Preferences'] = None,
            **unused,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        if not hide_episode_text and '/' in episode_text:
            numerator, denominator = map(
                str.strip, episode_text.split('/', maxsplit=1)
            )
        else:
            numerator, denominator = '-', episode_text
        self.numerator = self.image_magick.escape_chars(numerator)
        self.denominator = self.image_magick.escape_chars(denominator)
        self.hide_episode_text = hide_episode_text

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_vertical_shift = font_vertical_shift

        # Extras
        self.episode_text_font_size = graph_text_font_size
        self.graph_background_color = graph_background_color
        self.graph_color = graph_color
        self.graph_inset = graph_inset
        self.graph_radius = graph_radius
        self.graph_width = graph_width
        self.fill_scale = fill_scale
        self.omit_gradient = omit_gradient
        self.percentage = float(percentage)
        self.text_position: TextPosition = text_position


    @property
    def gradient_commands(self) -> ImageMagickCommands:
        """
        Subcommand to overlay the gradient to this image. This rotates
        and repositions the gradient overlay based on the text position.
        """

        if self.omit_gradient:
            return []

        if 'lower' in self.text_position:
            rotation = 0
            geometry = '+0+0'
        elif 'upper' in self.text_position:
            rotation = 180
            geometry = '+0+0'
        elif 'left' in self.text_position:
            rotation = 90
            geometry = f'-{(self.WIDTH - self.HEIGHT) / 2}+0'
        else:
            rotation = 270
            geometry = f'+{(self.WIDTH - self.HEIGHT) / 2}+0'

        return [
            f'\( "{self.GRADIENT.resolve()}"',
            f'-rotate {rotation} \)',
            f'-geometry {geometry}',
            f'-composite',
        ]


    @property
    def graph_commands(self) -> ImageMagickCommands:
        """Subcommands to add the graph to the image."""

        # Determine x/y position of the lower left corner of the graph
        if 'left' in self.text_position:
            x = self.graph_inset
        else:
            x = self.WIDTH - self.graph_inset - (2 * self.graph_radius)
        if 'upper' in self.text_position:
            y = self.graph_inset + (2 * self.graph_radius)
        elif 'lower' in self.text_position:
            y = self.HEIGHT - self.graph_inset
        else:
            y = (self.HEIGHT / 2) + self.graph_radius

        return self.add_drop_shadow(
            [
                f'-size {self.TITLE_CARD_SIZE}',
                f'xc:none',
                # Draw container ring
                f'-fill none',
                f'-stroke "{self.graph_background_color}"',
                f'-strokewidth {self.graph_width:.1f}',
                f'-draw "translate {x},{y}',
                *SvgCircle(
                    radius=self.graph_radius,
                    fill_percentage=1.0,
                ).draw_commands,
                f'"',
                # Draw filled in ring
                f'-stroke "{self.graph_color}"',
                f'-strokewidth {self.graph_width * self.fill_scale:.1f}',
                f'-draw "translate {x},{y}',
                *SvgCircle(
                    radius=self.graph_radius,
                    fill_percentage=self.percentage,
                ).draw_commands,
                f'"',
            ],
            '95x2+4+4',
            0, 0,
        )


    @property
    def divider_commands(self) -> ImageMagickCommands:
        """
        Subcommand to draw the divider between the nominator and
        denominator.
        """

        if self.hide_episode_text:
            return []

        # Scale offset from graph sides by graph radius
        internal_offset = 85 * (self.graph_radius / self.GRAPH_RADIUS)

        # Determine coordinates of the lower left corner of the divider
        if 'left' in self.text_position:
            sx = self.graph_inset + internal_offset
        else:
            sx = self.WIDTH - (2 * self.graph_radius) \
                - self.graph_inset + internal_offset

        if (slant_mode := len(self.numerator) < 3 and len(self.denominator) <3):
            if 'upper' in self.text_position:
                sy = self.graph_inset + (2 * self.graph_radius) - internal_offset
            elif 'lower' in self.text_position:
                sy = self.HEIGHT - self.graph_inset - internal_offset
            else:
                sy = (self.HEIGHT / 2) + self.graph_radius - internal_offset
        else:
            if 'upper' in self.text_position:
                sy = self.graph_inset + self.graph_radius
            elif 'lower' in self.text_position:
                sy = self.HEIGHT - self.graph_inset - self.graph_radius
            else:
                sy = self.HEIGHT / 2
        start = Coordinate(sx, sy)

        # Determine coordinates of the top right of the divider
        if 'left' in self.text_position:
            ex = self.graph_inset + (2 * self.graph_radius) - internal_offset
        else:
            ex = self.WIDTH - self.graph_inset - internal_offset

        if slant_mode:
            if 'upper' in self.text_position:
                ey = self.graph_inset + internal_offset
            elif 'lower' in self.text_position:
                ey = self.HEIGHT - self.graph_inset - (2 * self.graph_radius) \
                    + internal_offset
            else:
                ey = (self.HEIGHT / 2) - self.graph_radius + internal_offset
        else:
            ey = sy
        end = Coordinate(ex, ey)

        # Use graph color if at 100%
        color = self.graph_color if self.percentage >= 1.0 else 'white'

        return self.add_drop_shadow(
            [
                f'-size {self.TITLE_CARD_SIZE}',
                f'xc:none',
                f'-fill none',
                f'-stroke "{color}"',
                # f'-stroke "{self.BACKGROUND_GRAPH_COLOR}"',
                f'-strokewidth 8',
                Line(start, end).draw(),
            ],
            '90x3+5+5', 0, 0,
        )


    @property
    def fraction_commands(self) -> ImageMagickCommands:
        """Subcommand to draw the numerator and denominator."""

        if self.hide_episode_text:
            return []

        # Determine gravity
        if (slant_mode := len(self.numerator) < 3 and len(self.denominator) <3):
            numerator_gravity = 'southeast'
            denominator_gravity = 'northwest'
        else:
            numerator_gravity = 'south'
            denominator_gravity = 'north'

        # Determine coordinates of the positioning
        if slant_mode:
            if 'left' in self.text_position:
                num_x = self.WIDTH - self.graph_inset - self.graph_radius
                den_x = self.graph_inset + self.graph_radius
            else:
                num_x = self.graph_inset + self.graph_radius
                den_x = self.WIDTH - self.graph_inset - self.graph_radius
        else:
            num_x = (self.WIDTH / 2) - self.graph_inset - self.graph_radius
            num_x *= -1 if 'left' in self.text_position else 1
            den_x = num_x

        # Determine y coordinate
        if 'upper' in self.text_position:
            num_y = self.HEIGHT - self.graph_inset - self.graph_radius + 10
            den_y = self.graph_inset + self.graph_radius + 10
        elif 'lower' in self.text_position:
            num_y = self.graph_inset + self.graph_radius - 10
            den_y = self.HEIGHT - self.graph_inset - self.graph_radius - 10
        else:
            num_y = self.HEIGHT / 2
            den_y = self.HEIGHT / 2

        # Color denominator if at 100%
        if self.numerator == self.denominator or self.percentage >= 1.0:
            denominator_color = self.graph_color
        else:
            denominator_color = 'white'

        # Base commands for both numerator and denominator
        base_commands = [
            f'-background None',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-stroke none',
            f'-strokewidth 0',
            f'-kerning {4.0 * self.episode_text_font_size:.2f}',
            f'-pointsize {70 * self.episode_text_font_size:.2f}'
        ]

        return [
            # Add numerator
            f'-gravity {numerator_gravity}',
            *self.add_drop_shadow(
                [
                    *base_commands,
                    f'-fill "{self.graph_color}"',
                    f'label:"{self.numerator}"',
                ],
                '95x2+8+8',
                num_x, num_y,
            ),
            # Add denominator
            f'-gravity {denominator_gravity}',
            *self.add_drop_shadow(
                [
                    *base_commands,
                    f'-fill "{denominator_color}"',
                    # f'-fill "{self.BACKGROUND_GRAPH_COLOR}"',
                    f'label:"{self.denominator}"',
                ],
                '95x2+8+8',
                den_x, den_y,
            ),
        ]


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # If no title text, return empty commands
        if not self.title_text:
            return []

        # Determine coordinates and gravity of the positioning
        if 'left' in self.text_position:
            x = self.graph_inset + (2 * self.graph_radius) + 50
            gravity = 'west'
        else:
            x = self.graph_inset + (2 * self.graph_radius) + 50
            gravity = 'east'
        if 'upper' in self.text_position:
            y = -(self.HEIGHT / 2) + self.graph_inset + self.graph_radius
        elif 'lower' in self.text_position:
            y = (self.HEIGHT / 2) - self.graph_inset - self.graph_radius
        else:
            y = 0

        return [
            f'-gravity {gravity}',
            *self.add_drop_shadow(
                [
                    f'-background None',
                    f'-font "{self.font_file}"',
                    f'-stroke none',
                    f'-strokewidth 0',
                    f'-fill "{self.font_color}"',
                    f'-pointsize {95 * self.font_size}',
                    f'-interline-spacing {-35 + self.font_interline_spacing}',
                    f'-interword-spacing {25 + self.font_interword_spacing}',
                    f'-kerning {2 * self.font_kerning:.2f}',
                    f'label:"{self.title_text}"',
                ],
                '95x2+8+8', x, y,
            ),
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
            if 'graph_background_color' in extras:
                extras['graph_background_color'] =\
                    GraphTitleCard.BACKGROUND_GRAPH_COLOR
            if 'graph_color' in extras:
                extras['graph_color'] = GraphTitleCard.GRAPH_COLOR


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
            ('graph_background_color' in extras
                and extras['graph_background_color'] != GraphTitleCard.BACKGROUND_GRAPH_COLOR)
            or ('graph_color' in extras
                and extras['graph_color'] != GraphTitleCard.GRAPH_COLOR)
        )

        return custom_extras or GraphTitleCard._is_custom_font(font)


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

        standard_etf = GraphTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """Create this object's defined Title Card."""

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            f'-density 100',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Overlay gradient
            *self.gradient_commands,
            # Draw the graph
            *self.graph_commands,
            # Draw divider
            *self.divider_commands,
            *self.fraction_commands,
            # Add title text
            *self.title_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
