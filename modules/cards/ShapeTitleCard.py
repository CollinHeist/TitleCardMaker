from math import asin, cos
from pathlib import Path
from random import choice as random_choice
from re import match as re_match
from typing import TYPE_CHECKING, Literal, Optional, get_args as get_type_args

from modules.BaseCardType import (
    BaseCardType, Coordinate, ImageMagickCommands, Extra, CardDescription
)
from modules.Debug import log
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


Shape = Literal['circle', 'diamond', 'square', 'down triangle', 'up triangle']
RandomShapeRegex = (
    r'random\[\s*((circle|diamond|square|down triangle|up triangle)'
    r'\s*(,\s*(circle|diamond|square|down triangle|up triangle))*)\]'
)
SeasonTextPosition = Literal['above', 'below']
TextPosition = Literal[
    'upper left', 'upper right',
    'left', 'right',
    'lower left', 'lower right',
]


class ShapeTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards featuring
    an adjustable shape surrounding the text. The shape is intersected
    by the title text. This card allows the text (and shape) to be
    positioned at various points around the image.

    Each shape is drawn as follows:
    Circle: 1 -> 2; 3 -> 4
        *  *
     *        *
    1          2
    3          4
     *        *
        *  *
    Diamond: 1 -> 2 -> 3; 1 -> 4 -> 3.
          2
        *   *
      *       *
    1           3
      *       *
        *   *
          4
    Square: 1 -> 2 -> 3 -> 4; 1 -> 5 -> 6
    2 * * * * * 3
    *           *
    *           4
    *           6
    *           *
    1 * * * * * 5
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Shape',
        identifier='shape',
        example='/internal_assets/cards/shape.jpg',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Season Text Color',
                identifier='season_text_color',
                description='Color of the season text',
                tooltip='Defaults is to match the shape color.',
            ),
            Extra(
                name='Hide Shape',
                identifier='hide_shape',
                description='Whether to hide the shape',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is '
                    '<v>False</v>.'
                ),
            ),
            Extra(
                name='Italize Season Text',
                identifier='italicize_season_text',
                description='Whether to italicize the season text',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is '
                    '<v>False</v>.'
                ),
            ),
            Extra(
                name='Season Text Font Size',
                identifier='season_text_font_size',
                description='Size adjustment for the season text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
            ),
            Extra(
                name='Season Text Position',
                identifier='season_text_position',
                description=(
                    'Where to position the season text relative to the title '
                    'text'
                ), tooltip=(
                    'Either <v>above</v> or <v>below</v>. Default is '
                    '<v>below</v>.'
                ),
            ),
            Extra(
                name='Shape',
                identifier='shape',
                description='Which shape to add to the image',
                tooltip=(
                    'Either <v>circle</v>, <v>diamond</v>, <v>square</v>, '
                    '<v>down triangle</v>, or <v>up triangle</v>. Can also be '
                    'randomized by specifying as <v>random[shape1, shape2, '
                    'etc.]</v> - i.e. <v>random[circle, diamond]</v> to '
                    'randomly select one of those shapes. Default is '
                    '<v>diamond</v>.'
                ),
            ),
            Extra(
                name='Shape Color',
                identifier='shape_color',
                description='Color of the shape',
                tooltip='Default is <c>skyblue</c>.',
            ),
            Extra(
                name='Shape Inset',
                identifier='shape_inset',
                description='How far to inset the shape from the edges',
                tooltip=(
                    'Number between <v>0</v> and <v>1800</v>. Default is '
                    '<v>75</v>. Unit is pixels.'
                ),
            ),
            Extra(
                name='Shape Size',
                identifier='shape_size',
                description='How much to scale the length of the shape',
                tooltip=(
                    'Number ≥<v>0.3</v>. Values greater than <v>1.0</v> will '
                    'increase the size of the shape; values less than '
                    '<v>1.0</v> will descrease it. Default is <v>1.0</v>.'
                ),
            ),
            Extra(
                name='Shape Width',
                identifier='shape_width',
                description='Width of the shape',
                tooltip=(
                    'Number ><v>0.0</v>. Default is <v>10</v>. Unit is pixels.'
                ),
            ),
            Extra(
                name='Shape Stroke Width',
                identifier='shape_stroke_width',
                description='Width of the stroke around the shape',
                tooltip='Number ≥<v>0</v>. Default is <v>0</v> (no stroke).',
            ),
            Extra(
                name='Shape Stroke Color',
                identifier='shape_stroke_color',
                description='Color of the shape stroke',
                tooltip=(
                    'Only visible if the shape stroke width is greater than 0. '
                    'Default is <c>black</c>.'
                ),
            ),
            Extra(
                name='Stroke Text Color',
                identifier='stroke_color',
                description='Color to use for the text stroke',
                tooltip='Default is <c>black</c>.'
            ),
            Extra(
                name='Text Position',
                identifier='text_position',
                description='Where on the image to position the text',
                tooltip=(
                    'Either <v>upper left</v>, <v>upper right</v>, <v>left</v>,'
                    ' <v>right</v>, <v>lower left</v>, or <v>lower right</v>. '
                    'Default is <v>lower left</v>.'
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
        ], description=[
            'A title card featuring a customizable shape which surrounds the '
            'text.', 'The shape itself, along with the text are completely '
            'customizable in color, size, and position.'
        ],
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'shape'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 32,
        'max_line_count': 3,
        'style': 'top',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Golca Extra Bold.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'source'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = 'skyblue' # gold1
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Golca Bold.ttf'
    EPISODE_TEXT_FONT_ITALIC = REF_DIRECTORY / 'Golca Bold Italic.ttf'
    EPISODE_TEXT_FORMAT = '{episode_number}.'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Shape Style'

    """Implementation details"""
    DEFAULT_SHAPE: Shape = 'diamond'
    SHAPE_COLOR = EPISODE_TEXT_COLOR
    SHAPE_STROKE_COLOR = 'black'
    SHAPE_INSET = 75
    SHAPE_WIDTH = 8
    DEFAULT_LENGTHS: dict[Shape, int] = {
        'circle': 175,
        'diamond': 200,
        'down triangle': 225,
        'square': 150,
        'up triangle': 225,
    }

    """Gradient image"""
    GRADIENT = REF_DIRECTORY.parent / 'overline' / 'small_gradient.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'hide_season_text', 'font_color', 'font_interline_spacing',
        'font_interword_spacing', 'font_file', 'font_kerning', 'font_size',
        'font_stroke_width', 'font_vertical_shift', 'season_text_color',
        'season_text_font_size', 'hide_shape', 'italicize_season_text',
        'omit_gradient', 'season_text_position', 'shape', 'shape_color',
        'shape_inset', 'shape_side_length', 'shape_stroke_color',
        'shape_stroke_width', 'shape_width', 'stroke_color', 'text_position',
        '__title_width', '__title_height', '__line_count',
    )


    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title_text: str,
            season_text: str,
            hide_season_text: bool = False,
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
            hide_shape: bool = False,
            italicize_season_text: bool = False,
            omit_gradient: bool = False,
            season_text_color : str = EPISODE_TEXT_COLOR,
            season_text_font_size: float = 1.0,
            season_text_position: SeasonTextPosition = 'below',
            shape: str = DEFAULT_SHAPE,
            shape_color: str = SHAPE_COLOR,
            shape_inset: int = SHAPE_INSET,
            shape_size: float = 1.0,
            shape_stroke_color: str = SHAPE_STROKE_COLOR,
            shape_stroke_width: float = 0.0,
            shape_width: int = SHAPE_WIDTH,
            stroke_color: str = 'black',
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
        self.season_text = self.image_magick.escape_chars(season_text)
        self.hide_season_text = hide_season_text

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
        self.hide_shape = hide_shape
        self.italicize_season_text = italicize_season_text
        self.omit_gradient = omit_gradient
        self.season_text_color = season_text_color
        self.season_text_font_size = season_text_font_size
        self.season_text_position: SeasonTextPosition = season_text_position
        self.shape: Shape = self.__select_shape(shape)
        self.shape_color = shape_color
        self.shape_inset = shape_inset
        self.shape_side_length = self.DEFAULT_LENGTHS[self.shape] * shape_size
        self.shape_stroke_color = shape_stroke_color
        self.shape_stroke_width = shape_stroke_width
        self.shape_width = shape_width
        self.stroke_color = stroke_color
        self.text_position: TextPosition = text_position

        # Scale side length by for multiline titles
        self.__line_count = len(title_text.split('\n'))
        if self.__line_count > 1:
            self.shape_side_length *= 1.0 + (0.25 * (self.__line_count - 1))

        # Implementation variables
        self.__title_width = None
        self.__title_height = None


    def __select_shape(self, shape_str: str, /) -> Shape:
        """
        Determine a shape from the given string. This will parse random
        shape strings, as well as explicit ones. For example:

        >>> self.__select_shape('random')
        'down triangle' # Randomly selected from all available shapes
        >>> self.__select_shape('random[circle, triangle]')
        'circle' # Has 50% chance to choose circle or triangle
        >>> self.__select_shape('triangle')
        'triangle'

        Args:
            shape_str: Shape string to parse for shapes.

        Returns:
            Selected shape as indicated or randomly selected.
        """

        # If just "random", pick any
        if shape_str == 'random':
            return random_choice(get_type_args(Shape))

        # If shape is randomized, replace with random shape
        if re_match(RandomShapeRegex, shape_str):
            return random_choice(tuple(map(
                str.strip,
                re_match(RandomShapeRegex, shape_str).group(1).split(',')
            )))

        return shape_str


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


    def _base_title_text_commands(self,
            x: int = 300,
            y: int = 200,
            gravity: str = 'west',
        ) -> ImageMagickCommands:
        """
        Subcommands for adding title text to an image.

        Args:
            x: X-position where the title text should be positioned at.
            y: Y-position where the title text should be positioned at.
            gravity: Gravity to utilize for text annotation.

        Returns:
            List of ImageMagick commands.
        """

        if len(self.title_text) == 0:
            return []

        interline_spacing = -20 + self.font_interline_spacing
        size = 125 * self.font_size
        stroke_width = 4.0 * self.font_stroke_width

        return [
            f'-font "{self.font_file}"',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-pointsize {size:.1f}',
            f'-fill "{self.font_color}"',
            f'+stroke',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width:.1f}',
            f'-gravity {gravity}',
            f'-annotate {x:+.0f}{y:+.0f}',
        ]


    @property
    def _title_text_width(self) -> int:
        """The width of the title text. Only calculated once."""

        # No title text, width of 0
        if len(self.title_text) == 0:
            return 0

        # Value is not computed, calculate in `_title_text_height` call
        if self.__title_width is None:
            _ = self._title_text_height

        return self.__title_width


    @property
    def _title_text_height(self) -> int:
        """The height of the title text. Only calculated once."""

        # No title text, height of 0
        if len(self.title_text) == 0:
            return 0

        # Use value if already computed
        if self.__title_height is not None:
            return self.__title_height

        # Determine and store height
        w, h = self.image_magick.get_text_dimensions(
            self._base_title_text_commands() + [f'"{self.title_text}"'],
            width='max',
            height='sum',
        )
        self.__title_width = w
        self.__title_height = h + 10 # 10px margin

        return self.__title_height


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # If no title text, return empty commands
        if len(self.title_text) == 0:
            return []

        # Determine text to center around within shape
        if self.text_position.endswith('left'):
            # If first word is a number - e.g. `14. `, then center that
            first_word = self.title_text.split(' ', maxsplit=1)[0]
            if (number := re_match(r'(\d+)\.?', first_word)):
                center_text = number.group(1)
            # First word is not number, center around first letter
            else:
                center_text = self.title_text[0]
        elif self.text_position.endswith('middle'):
            center_text = self.title_text
        else:
            center_text = self.title_text[-1]

        # Get width of centering text
        width, _ = self.image_magick.get_text_dimensions(
            self._base_title_text_commands() + [f'"{center_text}"'],
            width='max', height='sum',
        )

        # Determine gravity and x placement
        if 'left' in self.text_position:
            gravity = 'west'
            x = self.shape_inset + self.shape_side_length - (width / 2)
        else:
            gravity = 'east'
            x = +self.shape_inset + self.shape_side_length - (width / 2)

        # Determine y placement
        if 'upper' in self.text_position:
            y = -(self.HEIGHT / 2) + self.shape_inset + self.shape_side_length
        elif 'lower' in self.text_position:
            y = +(self.HEIGHT / 2) - self.shape_inset - self.shape_side_length
        else:
            y = 0
        y += -5 + self.font_vertical_shift

        return [
            *self._base_title_text_commands(x, y, gravity),
            f'"{self.title_text}"',
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the index text."""

        # No index text, return empty commands
        if self.hide_season_text:
            return []

        # Utilize height of the title text to determine positioning
        title_height = self._title_text_height / 2

        # Determine gravity and x position
        if 'left' in self.text_position:
            if self.season_text_position == 'above':
                gravity = 'southwest'
            else:
                gravity = 'northwest'
        else:
            if self.season_text_position == 'above':
                gravity = 'southeast'
            else:
                gravity = 'northeast'
        x = self.shape_inset + (self.shape_side_length * 2) \
            - title_height + 20 # 20px margin

        # Adjust x positioning based on shape
        if self.shape == 'circle':
            x += 60 * self.__line_count
        elif self.shape == 'square':
            x += 90 * self.__line_count
        elif self.shape == 'down triangle': # TODO calculate w/ trig
            x += title_height - 20 # Remove previous offset
            dx = -130 if 'below' in self.season_text_position else -10
            dx *= self.shape_side_length / self.DEFAULT_LENGTHS[self.shape]
            x += dx
        elif self.shape == 'up triangle': # TODO calculate w/ trig
            x += title_height - 20 # Remove previous offset
            dx = -10 if 'below' in self.season_text_position else -130
            dx *= self.shape_side_length / self.DEFAULT_LENGTHS[self.shape]
            x += dx

        # Determine y position
        if 'upper' in self.text_position:
            if self.season_text_position == 'above':
                y = self.HEIGHT - self.shape_inset - self.shape_side_length
            else:
                y = self.shape_inset + self.shape_side_length
        elif 'lower' in self.text_position:
            if self.season_text_position == 'above':
                y = self.shape_inset + self.shape_side_length
            else:
                y = self.HEIGHT - self.shape_inset - self.shape_side_length
        else:
            y = self.HEIGHT / 2
        y += -5 + self.font_vertical_shift + title_height - 10 # 10px margin

        # Font characteristics
        size = 75 * self.season_text_font_size
        if self.italicize_season_text:
            file = self.EPISODE_TEXT_FONT_ITALIC.resolve()
        else:
            file = self.EPISODE_TEXT_FONT.resolve()

        return [
            f'-font "{file}"',
            f'-pointsize {size}',
            f'-fill "{self.season_text_color}"',
            f'-strokewidth 2',
            f'-gravity {gravity}',
            f'-annotate {x:+.0f}{y:+.0f} "{self.season_text}"',
        ]


    @property
    def _line_length(self) -> float:
        """
        The effective shape line length. This acounts for very short
        titles.
        """

        if self._title_text_width < self.shape_side_length:
            return self.shape_side_length

        # Normal length titles, truncate based on height of title text; +margin
        return self.shape_side_length - (self._title_text_height / 2) - 10


    @property
    def __left_shape_translation(self) -> Coordinate:
        """
        The coordinate to translate to the starting position of all left
        shapes. This is one of the following positions (based on the
        text position).

        - - -      - - -      - - -
        - - -      - - -      - - -
        o - -      - - -      - - -

        - - -      - - -      - - -
        - - -      - - -      - - -
        o - -      - - -      - - -

        - - -      - - -      - - -
        - - -      - - -      - - -
        o - -      - - -      - - -
        """

        x = self.shape_inset

        if 'upper' in self.text_position:
            return Coordinate(x, self.shape_inset + (2 * self.shape_side_length))
        if 'lower' in self.text_position:
            return Coordinate(x, self.HEIGHT - self.shape_inset)

        return Coordinate(x, (self.HEIGHT / 2) + self.shape_side_length)


    @property
    def __right_shape_translation(self) -> Coordinate:
        """
        The coordinate to translate to the starting position of all
        right shapes. This is one of the following positions (based on
        the text position).

        - - -      - - -      - - -
        - - -      - - -      - - -
        - - -      - - -      - - o

        - - -      - - -      - - -
        - - -      - - -      - - -
        - - -      - - -      - - o

        - - -      - - -      - - -
        - - -      - - -      - - -
        - - -      - - -      - - o
        """

        x = self.WIDTH - self.shape_inset

        if 'upper' in self.text_position:
            return Coordinate(x, self.shape_inset + (2 *self.shape_side_length))
        if 'lower' in self.text_position:
            return Coordinate(x, self.HEIGHT - self.shape_inset)

        return Coordinate(x, (self.HEIGHT / 2) +  self.shape_side_length)


    @property
    def __left_circle(self) -> ImageMagickCommands:
        """Subcommands to add a circle shape to the left of the image."""

        radius = self.shape_side_length
        if self._title_text_width < radius:
            x, y = 2 * radius, 0 # 180 degrees
        else:
            y = self._title_text_height / 2 + 10
            theta = asin(y / radius)            # ϴ = asin(y / r)
            x = radius + (radius * cos(theta))  # x = r * cos(ϴ)

        return [
            # Translate in from left side (y based on text position)
            f'"translate {self.__left_shape_translation}',
            # Begin shape starting on left corner
            f'path \'M 0,-{radius}',
            # Draw top arc
            f'a {radius},{radius} 0 0 1 {x:+.1f},-{y:.1f}',
            # Move back to left corner
            f'M 0,-{radius}',
            # Draw bottom arc
            f'a {radius},{radius} 0 0 0 {x:+.1f},+{y:.1f}',
            f'\'"'
        ]


    @property
    def __right_circle(self) -> ImageMagickCommands:
        """Subcommands to add a circle shape to the right of the image."""

        radius = self.shape_side_length
        if self._title_text_width < radius:
            x, y = 2 * radius, 0 # 180 degrees
        else:
            y = self._title_text_height / 2 + 10
            theta = asin(y / radius)            # ϴ = asin(y / r)
            x = radius + (radius * cos(theta))  # x = r * cos(ϴ)

        return [
            # Translate in from left side (y based on text position)
            f'"translate {self.__right_shape_translation}',
            # Begin shape starting on left corner
            f'path \'M 0,-{radius}',
            # Draw top arc
            f'a {radius},{radius} 0 0 0 -{x:.1f},-{y:.1f}',
            # Move back to left corner
            f'M 0,-{radius}',
            # Draw bottom arc
            f'a {radius},{radius} 0 0 1 -{x:.1f},+{y:.1f}',
            f'\'"'
        ]


    @property
    def __left_diamond(self) -> ImageMagickCommands:
        """
        ImageMagick commands to draw a diamond shape on the left of the
        image.
        """

        return [
            # Translate in from left side (y based on text position)
            f'"translate {self.__left_shape_translation}',
            # Begin shape starting on left corner
            f'path \'M 0,-{self.shape_side_length}',
            # Draw up to top corner
            f'l {self.shape_side_length},-{self.shape_side_length}',
            # Draw down to right corner; x/y is cut off by text
            f'l {self._line_length},{self._line_length}',
            # Move back to left corner
            f'M 0,-{self.shape_side_length}',
            # Draw to bottom corner
            f'l {self.shape_side_length},{self.shape_side_length}',
            # Draw up to right corner; x/y is cut off by text
            f'l {self._line_length},-{self._line_length}',
            f'\'"'
        ]


    @property
    def __right_diamond(self) -> ImageMagickCommands:
        """
        ImageMagick commands to draw a diamond shape on the right of the
        image.
        """

        return [
            # Translate in from right side (y based on text position)
            f'"translate {self.__right_shape_translation}',
            # Begin shape starting on right corner
            f'path \'M 0,-{self.shape_side_length}',
            # Draw up to top corner
            f'l -{self.shape_side_length},-{self.shape_side_length}',
            # Draw down to left corner; x/y is cut off by text
            f'l -{self._line_length},{self._line_length}',
            # Move back to left corner
            f'M 0,-{self.shape_side_length}',
            # Draw to bottom corner
            f'l -{self.shape_side_length},{self.shape_side_length}',
            # Draw up to left corner; x/y is cut off by text
            f'l -{self._line_length},-{self._line_length}',
            f'\'"'
        ]


    @property
    def __left_square(self) -> ImageMagickCommands:
        """"""

        return [
            # Translate in from left side (y based on text position)
            f'"translate {self.__left_shape_translation}',
            # Begin shape starting on lower left corner
            f'path \'M 0,0',
            # Draw up to top left corner
            f'l 0,-{self.shape_side_length * 2}',
            # Draw to the top right corner
            f'l {self.shape_side_length * 2},0',
            # Draw down to right middle; y is cut off by text
            f'l 0,{self._line_length}',
            # Move back to lower left corner
            f'M 0,0',
            # Draw to lower right corner
            f'l {self.shape_side_length * 2},0',
            # Draw up to right middle; y is cut off by text
            f'l 0,-{self._line_length}',
            f'\'"'
        ]


    @property
    def __right_square(self) -> ImageMagickCommands:
        """"""

        return [
            # Translate in from left side (y based on text position)
            f'"translate {self.__right_shape_translation}',
            # Begin shape starting on lower left corner
            f'path \'M 0,0',
            # Draw up to top right corner
            f'l 0,-{self.shape_side_length * 2}',
            # Draw to the top left corner
            f'l -{self.shape_side_length * 2},0',
            # Draw down to left middle; y is cut off by text
            f'l 0,{self._line_length}',
            # Move back to lower right corner
            f'M 0,0',
            # Draw to lower left corner
            f'l -{self.shape_side_length * 2},0',
            # Draw up to left middle; y is cut off by text
            f'l 0,-{self._line_length}',
            f'\'"'
        ]


    @property
    def __left_down_triangle(self) -> ImageMagickCommands:
        """
             l
           +----/
           |   /
        2l |  /
           | /
           +
        """

        # Determine the length of the line
        # Very short title lines, do not truncate side
        if self._title_text_width < self.shape_side_length:
            ratio = 1 / 2
        # Normal length titles, truncate based on height of title text
        else:
            ratio = (
                (self.shape_side_length - ((self._title_text_height / 2) + 10))
                / (2 * self.shape_side_length)
            )

        # Ratio of sides stays equivalent for like-triangles
        # Determine end coordinate by length ratio of end hypotenuse
        x = self.shape_side_length * ratio
        y = 2 * self.shape_side_length * ratio

        return [
            # Translate in from left side (y based on text position)
            f'"translate {self.__left_shape_translation}',
            # Begin shape starting on top left corner
            f'path \'M 0,-{2 * self.shape_side_length}',
            # Draw to the top right corner
            f'l +{self.shape_side_length * 2},0',
            # Draw down to the bottom middle; y is cut off
            f'l -{x:.1f},{y:+.1f}',
            # Move back to the top left corner
            f'M 0,-{2 * self.shape_side_length}',
            # Draw down to the bottom middle
            f'l {self.shape_side_length},{2 * self.shape_side_length}',
            # Draw up to the top right; y is cut off
            f'l {x:+.1f},-{y:.1f}',
            f'\'"'
        ]


    @property
    def __right_down_triangle(self) -> ImageMagickCommands:
        """
          l
        \----+
         \   |
          \  | 2l
           \ |
             +
        """

        # Determine the length of the line
        # Very short title lines, do not truncate side
        if self._title_text_width < self.shape_side_length:
            ratio = 1 / 2
        # Normal length titles, truncate based on height of title text
        else:
            ratio = (
                (self.shape_side_length - ((self._title_text_height / 2) + 10))
                / (2 * self.shape_side_length)
            )

        # Ratio of sides stays equivalent for like-triangles
        # Determine end coordinate by length ratio of end hypotenuse
        x = self.shape_side_length * ratio
        y = 2 * self.shape_side_length * ratio

        return [
            # Translate in from right side (y based on text position)
            f'"translate {self.__right_shape_translation}',
            # Begin shape starting on top right corner
            f'path \'M 0,-{2 * self.shape_side_length}',
            # Draw to the top left corner
            f'l -{self.shape_side_length * 2},0',
            # Draw down to the bottom middle; y is cut off
            f'l +{x:.1f},+{y:.1f}',
            # Move back to the top right corner
            f'M 0,-{2 * self.shape_side_length}',
            # Draw down to the bottom middle
            f'l -{self.shape_side_length},+{2 * self.shape_side_length}',
            # Draw up to the top left; y is cut off
            f'l -{x:.1f},-{y:.1f}',
            f'\'"'
        ]


    @property
    def __left_up_triangle(self) -> ImageMagickCommands:
        """
           +
           | \
        2l |  \
           |   \
           +----\
             l
        """

        # Determine the length of the line
        # Very short title lines, do not truncate side
        if self._title_text_width < self.shape_side_length:
            ratio = 1 / 2
        # Normal length titles, truncate based on height of title text
        else:
            ratio = (
                (self.shape_side_length - ((self._title_text_height / 2) + 10))
                / (2 * self.shape_side_length)
            )

        # Ratio of sides stays equivalent for like-triangles
        # Determine end coordinate by length ratio of end hypotenuse
        x = self.shape_side_length * ratio
        y = 2 * self.shape_side_length * ratio

        return [
            # Translate in from left side (y based on text position)
            f'"translate {self.__left_shape_translation}',
            # Begin shape starting on bottom left corner
            f'path \'M 0,0',
            # Draw to the bottom right corner
            f'l +{self.shape_side_length * 2},0',
            # Draw up to the bottom middle; y is cut off
            f'l -{x:.1f},-{y:.1f}',
            # Move back to the bottom left corner
            f'M 0,0',
            # Draw up to the top middle
            f'l {self.shape_side_length},-{2 * self.shape_side_length}',
            # Draw down to the bottom right; y is cut off
            f'l {x:+.1f},+{y:.1f}',
            f'\'"'
        ]


    @property
    def __right_up_triangle(self) -> ImageMagickCommands:
        """
           +
           | \
        2l |  \
           |   \
           +----\
             l
        """

        # Determine the length of the line
        # Very short title lines, do not truncate side
        if self._title_text_width < self.shape_side_length:
            ratio = 1 / 2
        # Normal length titles, truncate based on height of title text
        else:
            ratio = (
                (self.shape_side_length - ((self._title_text_height / 2) + 10))
                / (2 * self.shape_side_length)
            )

        # Ratio of sides stays equivalent for like-triangles
        # Determine end coordinate by length ratio of end hypotenuse
        x = self.shape_side_length * ratio
        y = 2 * self.shape_side_length * ratio

        return [
            # Translate in from right side
            f'"translate {self.__right_shape_translation}',
            # Begin shape starting on bottom right corner
            f'path \'M 0,0',
            # Draw to the bottom left corner
            f'l -{self.shape_side_length * 2},0',
            # Draw up to the bottom middle; y is cut off
            f'l +{x:.1f},-{y:.1f}',
            # Move back to the bottom right corner
            f'M 0,0',
            # Draw up to the top middle
            f'l -{self.shape_side_length},-{2 * self.shape_side_length}',
            # Draw down to the bottom left; y is cut off
            f'l -{x:.1f},+{y:.1f}',
            f'\'"'
        ]


    @property
    def _left_shape_commands(self) -> ImageMagickCommands:
        """Subcommands to add the shape on the left side of the image."""

        if self.shape == 'circle':
            return self.__left_circle
        if self.shape == 'diamond':
            return self.__left_diamond
        if self.shape == 'square':
            return self.__left_square
        if self.shape == 'down triangle':
            return self.__left_down_triangle
        if self.shape == 'up triangle':
            return self.__left_up_triangle

        return []


    @property
    def _right_shape_commands(self) -> ImageMagickCommands:
        """Subcommands to add the shape on the right of the image."""

        if self.shape == 'circle':
            return self.__right_circle
        if self.shape == 'diamond':
            return self.__right_diamond
        if self.shape == 'square':
            return self.__right_square
        if self.shape == 'down triangle':
            return self.__right_down_triangle
        if self.shape == 'up triangle':
            return self.__right_up_triangle

        return []


    @property
    def shape_commands(self) -> ImageMagickCommands:
        """Subcommands to add the shape to the image."""

        # Shape is hidden, return empty commands
        if self.hide_shape:
            return []

        # Determine shape command set based on text position
        if 'left' in self.text_position:
            shape_commands = self._left_shape_commands
        else:
            shape_commands = self._right_shape_commands

        stroke_commands = []
        if self.shape_stroke_width > 0:
            stroke_commands = [
                f'-fill none',
                f'-stroke "{self.shape_stroke_color}"',
                f'-strokewidth {self.shape_width + self.shape_stroke_width}',
                f'-draw',
                *shape_commands,
            ]

        return [
            *stroke_commands,
            f'-fill none',
            f'-stroke "{self.shape_color}"',
            f'-strokewidth {self.shape_width}',
            # Begin shape SVG
            f'-draw',
            *shape_commands,
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
            if 'season_text_color' in extras:
                extras['season_text_color'] = ShapeTitleCard.EPISODE_TEXT_COLOR
            if 'season_text_font_size' in extras:
                extras['season_text_font_size'] = 1.0
            if 'shape_color' in extras:
                extras['shape_color'] = ShapeTitleCard.SHAPE_COLOR
            if 'stroke_color' in extras:
                extras['stroke_color'] = 'black'


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
            ('season_text_color' in extras
             and extras['season_text_color'] != ShapeTitleCard.EPISODE_TEXT_COLOR)
            or ('season_text_font_size' in extras
                and extras['season_text_font_size'] != 1.0)
            or ('shape_color' in extras
                and extras['shape_color'] != ShapeTitleCard.SHAPE_COLOR)
            or ('stroke_color' in extras
                and extras['stroke_color'] != 'black')
        )

        return custom_extras or ShapeTitleCard._is_custom_font(font)

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

        return (
            custom_episode_map
            or episode_text_format.upper() != \
                ShapeTitleCard.EPISODE_TEXT_FORMAT.upper()
        )


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Overlay gradient
            *self.gradient_commands,
            # Add each component of the image
            *self.shape_commands,
            *self.title_text_commands,
            *self.index_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
