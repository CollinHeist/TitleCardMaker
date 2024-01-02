from math import cos, sin, pi
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from modules.BaseCardType import (
    BaseCardType, Coordinate, ImageMagickCommands, Extra, CardDescription, Line,
)
from modules.Debug import log

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
        supports_custom_seasons=True,
        supported_extras=[
            
        ],
        description=[
            'A title card similiar to the Shape card, but features a bar '
            '"graph" or progress bar which can be used to indicate total series'
            'progress.',
        ],
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'inset'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 30,   # Character count to begin splitting titles
        'max_line_count': 3,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses top heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'HelveticaNeue-BoldItalic.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'source'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = 'skyblue'
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'HelveticaNeue-BoldItalic.ttf'
    EPISODE_TEXT_FORMAT = '{episode_number} / {season_episode_max}'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Graph Style'

    """Implementation details"""
    GRAPH_COLOR = 'SteelBlue1'
    GRAPH_FILL_SCALE = 0.6
    GRAPH_INSET = 75
    GRAPH_RADIUS = 175
    BACKGROUND_GRAPH_COLOR = 'rgba(140,140,140,0.5)'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'episode_text',
        'hide_episode_text', 'font_color', 'font_interline_spacing',
        'font_interword_spacing', 'font_file', 'font_kerning', 'font_size',
        'font_vertical_shift', 'graph_background_color', 'graph_color',
        'graph_inset', 'graph_radius', 'graph_width', 'fill_scale',
        'percentage', 'text_position',
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
            graph_width: float = 1.0,
            fill_scale: float = GRAPH_FILL_SCALE,
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
        self.episode_text = self.image_magick.escape_chars(episode_text)
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
        self.graph_background_color = graph_background_color
        self.graph_color = graph_color
        self.graph_inset = graph_inset
        self.graph_radius = graph_radius
        self.graph_width = graph_width
        self.fill_scale = fill_scale
        self.percentage = percentage
        self.text_position: TextPosition = text_position


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

        graph_width = 25 * self.graph_width

        return [
            # Draw container ring
            f'-fill none',
            f'-stroke "{self.graph_background_color}"',
            f'-strokewidth {graph_width:.1f}',
            f'-draw "translate {x},{y}',
            *SvgCircle(
                radius=self.graph_radius,
                fill_percentage=1.0,
            ).draw_commands,
            f'"',
            # Draw filled in ring
            f'-stroke "{self.graph_color}"',
            f'-strokewidth {graph_width * self.fill_scale:.1f}',
            f'-draw "translate {x},{y}',
            *SvgCircle(
                radius=self.graph_radius,
                fill_percentage=self.percentage,
            ).draw_commands,
            f'"',
        ]


    @property
    def divider_commands(self) -> ImageMagickCommands:
        """
        Subcommand to draw the divider between the nominator and
        denominator.
        """

        # Determine coordinates of the lower left of the divider
        internal_offset = 85 * (self.graph_radius / 175)
        if 'left' in self.text_position:
            sx = self.graph_inset + internal_offset
        else:
            sx = self.WIDTH - (2 * self.graph_radius) \
                - self.graph_inset + internal_offset
        if 'upper' in self.text_position:
            sy = self.graph_inset + (2 * self.graph_radius) - internal_offset
        elif 'lower' in self.text_position:
            sy = self.HEIGHT - self.graph_inset - internal_offset
        else:
            sy = (self.HEIGHT / 2) + self.graph_radius - internal_offset
        start = Coordinate(sx, sy)

        # Determine coordinates of the top right of the divider
        if 'left' in self.text_position:
            ex = self.graph_inset + (2 * self.graph_radius) - internal_offset
        else:
            ex = self.WIDTH - self.graph_inset - internal_offset
        if 'upper' in self.text_position:
            ey = self.graph_inset + internal_offset
        elif 'lower' in self.text_position:
            ey = self.HEIGHT - self.graph_inset - (2 * self.graph_radius) \
                + internal_offset
        else:
            ey = (self.HEIGHT / 2) - self.graph_radius + internal_offset
        end = Coordinate(ex, ey)

        return [
            f'-fill none',
            f'-stroke "white"',
            # f'-stroke "{self.BACKGROUND_GRAPH_COLOR}"',
            f'-strokewidth 8',
            Line(start, end).draw(),
        ]


    @property
    def fraction_commands(self) -> ImageMagickCommands:
        """Subcommand to draw the numerator and denominator."""

        # Parse numerator and denominator from episode text
        if '/' in self.episode_text:
            numerator, denominator = map(str.strip, self.episode_text.split('/', maxsplit=1))
        else:
            numerator, denominator = '-', self.episode_text

        # Determine coordinates of the positioning
        if 'left' in self.text_position:
            num_x = self.WIDTH - self.graph_inset - self.graph_radius
            den_x = self.graph_inset + self.graph_radius
        else:
            num_x = self.graph_inset + self.graph_radius
            den_x = self.WIDTH - self.graph_inset - self.graph_radius
        if 'upper' in self.text_position:
            num_y = self.HEIGHT - self.graph_inset - self.graph_radius + 10
            den_y = self.graph_inset + self.graph_radius + 10
        elif 'lower' in self.text_position:
            num_y = self.graph_inset + self.graph_radius - 10
            den_y = self.HEIGHT - self.graph_inset - self.graph_radius - 10
        else:
            num_y = self.HEIGHT / 2
            den_y = self.HEIGHT / 2

        # Base commands for both numerator and denominator
        base_commands = [
            f'-background None',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-stroke none',
            f'-strokewidth 0',
            f'-pointsize 75',
        ]

        return [
            # Add numerator
            f'-gravity southeast',
            *self.add_drop_shadow(
                [
                    *base_commands,
                    f'-fill "{self.graph_color}"',
                    f'label:"{numerator}"',
                ],
                '95x2+10+10',
                num_x, num_y,
            ),
            # Add denominator
            f'-gravity northwest',
            *self.add_drop_shadow(
                [
                    *base_commands,
                    f'-fill "white"',
                    f'label:"{denominator}"',
                ],
                '95x2+10+10',
                den_x, den_y,
            ),
        ]


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # If no title text, return empty commands
        if len(self.title_text) == 0:
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
                    f'-interword-spacing {15 + self.font_interword_spacing}',
                    f'-kerning {1 * self.font_kerning:.2f}',
                    f'label:"{self.title_text}"',
                ],
                shadow=f'95x2+10+10',
                x=x, y=y,
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

        return (custom_extras
            or ((font.color != GraphTitleCard.TITLE_COLOR)
            or (font.file != GraphTitleCard.TITLE_FONT)
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
            # Add each component of the image
            # Draw the graph
            *self.graph_commands,
            # Draw divider
            *self.divider_commands,
            *self.fraction_commands,
            # Add title text
            *self.title_text_commands,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
