from dataclasses import dataclass
from math import tan, pi as PI
from pathlib import Path
from random import choice as random_choice, randint
from re import IGNORECASE, compile as re_compile
from typing import TYPE_CHECKING, Iterable, Literal, Optional

from modules.BaseCardType import (
    BaseCardType, CardDescription, Coordinate, ImageMagickCommands, Extra,
)
from modules.Debug import log
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


TextPosition = Literal['upper left', 'upper right', 'lower left', 'lower right']

@dataclass(repr=False)
class Polygon:
    """
    A drawable SVG polgyon which is comprised of four Coordinate
    corners.
    """

    c0: Coordinate
    c1: Coordinate
    c2: Coordinate
    c3: Coordinate


    def __str__(self) -> str:
        return f'polygon {self.c0} {self.c1} {self.c2} {self.c3}'


    def draw(self) -> str:
        """
        Draw this polygon. Should be contained in a parent `-draw`
        command.
        """

        return str(self)


    @property
    def in_bounds(self) -> bool:
        """
        Whether this polygon is fully contained in the bounds of the
        Title Card canvas.
        """

        return (
            0 <= self.c0.x <= BaseCardType.WIDTH
            and 0 <= self.c1.x <= BaseCardType.WIDTH
            and 0 <= self.c2.x <= BaseCardType.WIDTH
            and 0 <= self.c3.x <= BaseCardType.WIDTH
            and 0 <= self.c0.y <= BaseCardType.HEIGHT
            and 0 <= self.c1.y <= BaseCardType.HEIGHT
            and 0 <= self.c2.y <= BaseCardType.HEIGHT
            and 0 <= self.c3.y <= BaseCardType.HEIGHT
        )


class PolygonDistribution:
    """
    A class which defines some distribution of polygon definitions. This
    is initialized with a polygon string which can take one of the
    following forms:

    1. `random[sml]` - Indicates a randomized order of polygons in the
    given distrubution. `sml` can be any combination of `s` `m` and `l`,
    and indicates the relative frequency of that size. The size of each
    shape is randomly selected from the default distributions for that
    size.

    2. `random[100,200]` - Indicates a randomized order of polygons in
    the given distrubution and size. `100,200` can be any comma-
    separated integers which indicate the fixed size of that polygon.

    3. `random[10-50,100-400]` - Indicates a randomized order of
    polygons in the given distribution and size ranges. `10-50,100-400`
    can be any comma-separated range of integers which indicates the
    size of the polygon will be randomly selected between that range.

    4. `ssmmll` - Indicates a fixed order of polygons of randomized
    sizes. `ssmmll` can be any combination of `s` `m` and `l`, and
    indicates the size of that polygon. The exact size is randomly
    selected from the default distrubutions for that size.
    
    5. `50,200` - Indicates a fixed order of polygons of fixed size.
    `50,200` can be any comma-separated integers which indicate the size
    of those polygons.

    6. `10-50,100-400` - Indicates a fixed order of polygons of
    randomized sizes. `10-50,100-400` can be any comma-separated ranges
    of integers which indicates the size of the polygon will be randomly
    selected between that range.

    7. Any of patterns 4-6 can end in `+` to indicate that pattern
    should repeat until the edge of the Card.
    """

    """Default distrubution of polygon size ranges"""
    DEFAULT_SHAPE_SIZES = {
        's': [15, 40],
        'm': [50, 200],
        'l': [250, 500],
    }

    """Regex which indicates some randomized polygon strng"""
    _RANDOMIZED_POLYGONS_REGEX = re_compile(r'^random\[(.+)\]$', IGNORECASE)

    def __init__(self, polygons: str, /) -> None:
        """
        Initialize an object defined by the given distribution string.

        Args:
            polygons: Distribution definition. See class docstring for
                details.
        """

        self._str = polygons.lower()
        match = self._RANDOMIZED_POLYGONS_REGEX.match(self._str)

        self._distribution: Optional[Iterable[str]] = None
        self._order: Optional[Iterable[str]] = None
        self._sizes: dict[str, list[int]] = self.DEFAULT_SHAPE_SIZES
        self._repeating = False

        # Parse random pattern types[1-3]
        if match:
            random_str: str = match.group(1)

            # Distrubution type[1] - e.g. `random[ssmmll]`
            if all(char in 'sml' for char in random_str):
                self._distribution = random_str
                self._sizes = self.DEFAULT_SHAPE_SIZES
            # Distrubution type[3] - e.g. `random[20-50,100-500]`
            elif '-' in random_str:
                self._distribution = random_str.split(',')
                self._sizes = {
                    range_: list(map(int, range_.split('-')))
                    for range_ in self._distribution
                }
            # Distrubution type[2] - e.g. `random[20,500]`
            else:
                self._distribution = random_str.split(',')
                self._sizes = {
                    range_: [int(range_), int(range_)]
                    for range_ in self._distribution
                }
        # Fixed order pattern types[4-6]
        else:
            # Repeating pattern, set flag and remove + for order parsing
            if self._str.endswith('+'):
                self._repeating = True
                self._str = self._str.removesuffix('+')

            # Distribution type[4] - e.g. `ssmmll`
            if all(char in 'sml' for char in self._str):
                self._order = [char for char in self._str]
            # Distribution type[6] - e.g. `100-200,50-20`
            elif '-' in self._str:
                self._order = self._str.split(',')
                self._sizes = {
                    range_: list(map(int, range_.split('-')))
                    for range_ in self._order
                }
            # Distribution type[5] - e.g. `50,400`
            else:
                self._order = self._str.split(',')
                self._sizes = {
                    range_: [int(range_), int(range_)]
                    for range_ in self._order
                }


    def generate_coordinates(self,
            inset: int,
            inter_shape_spacing: int,
        ) -> list[Coordinate]:
        """
        Generate a list of Coordinates constrained by the given inset
        and spacing. The generated coordinates follow the definition
        used to initialize this object.

        Args:
            inset: How far from the edges of the image to start and end
                coordinate generation.
            inter_shape_spacing: Distance between sequential coordinate
                pairs.

        Returns:
            List of Coordinate pairs. Each two sequential Coordinates
            constitute the left and right bounds of a Polygon defined
            by the distribution string.
        """

        # Start from left-hand side
        x, coordinates = inset, [inset]

        # Randomized mode
        if self._distribution:
            # Generate left-right until reaching the edge of the image
            while x < BaseCardType.WIDTH - inset:
                # Select random object from distrubition
                size: str = random_choice(self._distribution)

                # Try and increment x by random width
                x += randint(
                    self._sizes[size][0],
                    min(
                        self._sizes[size][1],
                        BaseCardType.WIDTH - inset, # Max size possible
                    )
                )

                # Add polygon end to list of coordinates
                coordinates.append(x)

                # Increment x by spacing, add end coordinate to list
                x += inter_shape_spacing
                coordinates.append(x)

            return coordinates

        # Fixed order mode; iterate through specified order

        # If the pattern is repeating then repeat order arbitrarily many
        # times; exit condition will be the dimensions of the card
        order = (self._order * 100) if self._repeating else self._order

        for size in order:
            # If in a repeat pattern and out-of-bounds, exit order early
            if self._repeating and x > BaseCardType.WIDTH - inset:
                break

            x += randint(
                self._sizes[size][0],
                min(
                    self._sizes[size][1],
                    BaseCardType.WIDTH - inset, # Max size possible
                )
            )

            # Add polygon end to list of coordinates
            coordinates.append(x)

            # Increment x by spacing, add end coordinate to list
            x += inter_shape_spacing
            coordinates.append(x)

        return coordinates


class StripedTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards which
    feature a solid color overlay with stripes of rectangles "cut" out
    to expose the underlying Source Image.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Striped',
        identifier='striped',
        example='/internal_assets/cards/striped.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Stripe Angle',
                identifier='angle',
                description='Angle of the stripes',
                tooltip=(
                    'Value between <v>45</v> and <v>135</v>. <v>90</v> is '
                    'straight up. Default is <v>79.5</v>. Unit is degrees.'
                ),
            ),
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is <c>crimson</c>.',
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the season and episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
            ),
            Extra(
                name='Stripe Inset',
                identifier='inset',
                description='How far to inset the start and end of the stripes',
                tooltip=(
                    'Number between <v>0</v> and <v>1600</v>. Default is '
                    '<v>50</v>. Unit is pixels.'
                ),
            ),
            Extra(
                name='Inter-stripe Spacing',
                identifier='inter_stripe_spacing',
                description='Spacing between stripes',
                tooltip=(
                    'Number between <v>0</v> and <v>800</v>. Default is '
                    '<v>8</v>. Unit is pixels.'
                ),
            ),
            Extra(
                name='Overlay Color',
                identifier='overlay_color',
                description='Color of the overlay',
                tooltip='Default is <c>white</c>.',
            ),
            Extra(
                name='Stripe Definition',
                identifier='polygons',
                description='Format for the size and order of the stripes',
                tooltip=(
                    'See <a href="https://titlecardmaker.com/card_types/striped/#definition">'
                    'the documentation</a> for details. Default is '
                    '<v>random[ssmmmlll]</v>.'
                ),
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description=(
                    'Character that separates the season and episode text'
                ),
                tooltip='Default is <v> - </v>.'
            ),
            Extra(
                name='Text Position',
                identifier='text_position',
                description='Position of the text on the image',
                tooltip=(
                    'Either <v>upper left</v>, <v>upper right</v>, <v>lower '
                    'left</v>, or <v>lower right</v>. Default is <v>lower '
                    'left</v>.'
                ),
            ),
        ],
        description=[
            'Cards featuring a solid color overlay with stripes of rectangles '
            '"cut" out to expose the underlying image. By default the stripes '
            'are randomly placed and sized, but this can be adjusted with an '
            'extra.', 'The position of the text can also be adjusted to any of '
            'the four corners.'
        ],
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'shape'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 35,
        'max_line_count': 3,
        'style': 'bottom',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Golca Bold Italic.ttf').resolve())
    TITLE_COLOR = 'black'
    DEFAULT_FONT_CASE = 'source'
    FONT_REPLACEMENTS = {}
 
    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = 'crimson' # TITLE_COLOR
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Golca Bold Italic.ttf'
    EPISODE_TEXT_FORMAT = 'Episode {episode_number}'
    INDEX_TEXT_FONT = REF_DIRECTORY / 'Gotham-Medium.ttf'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Striped Style'

    """Implementation details"""
    DEFAULT_ANGLE = 79.5 # Degrees
    DEFAULT_INSET = 50
    DEFAULT_INTER_STRIPE_SPACING = 8
    DEFAULT_OVERLAY_COLOR = 'white'
    DEFAULT_POLYGON_STRING = 'random[ssmmmlll]'
    DEFAULT_TEXT_POSITION: TextPosition = 'lower left'
    _MIN_SHAPE_HEIGHT = BaseCardType.HEIGHT // 2


    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_interline_spacing', 'font_interword_spacing', 'font_file',
        'font_kerning', 'font_size', 'font_vertical_shift', 'angle',
        'episode_text_color', 'episode_text_font_size', 'inset',
        'inter_shape_spacing', 'overlay_color', 'polygon_distribution',
        'separator', 'text_position',
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
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            angle: float = DEFAULT_ANGLE,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            inset: int = DEFAULT_INSET,
            inter_stripe_spacing: int = DEFAULT_INTER_STRIPE_SPACING,
            overlay_color: str = DEFAULT_OVERLAY_COLOR,
            polygons: str = DEFAULT_POLYGON_STRING,
            separator: str = ' - ',
            text_position: TextPosition = DEFAULT_TEXT_POSITION,
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
        self.angle = angle
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.inset = inset
        self.inter_shape_spacing = inter_stripe_spacing
        self.overlay_color = overlay_color
        self.polygon_distribution = PolygonDistribution(polygons)
        self.separator = separator
        self.text_position: TextPosition = text_position


    @property
    def text_gravity(self) -> str:
        """Gravity attribute for all text."""

        return {
            'upper left': 'northwest',
            'upper right': 'northeast',
            'lower left': 'southwest',
            'lower right': 'southeast',
        }.get(self.text_position, 'southwest')


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # If no title text, return empty commands
        if not self.title_text:
            return []

        x, y = 50, 35 + self.font_vertical_shift

        return [
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {100 * self.font_size}',
            f'-interline-spacing {self.font_interline_spacing:+}',
            f'-interword-spacing {25 + self.font_interword_spacing:+}',
            f'-kerning {-2.0 * self.font_kerning}',
            f'-gravity {self.text_gravity}',
            f'-annotate {x:+}{y:+} "{self.title_text}"',
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommands to the season and episode text to the image."""

        # All text hidden, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Determine text to display
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text =f'{self.season_text}{self.separator}{self.episode_text}'

        # Get height of the title text
        _, height = self.image_magick.get_text_dimensions(
            self.title_text_commands,
            density=100,
            interline_spacing=self.font_interline_spacing,
            line_count=len(self.title_text.splitlines()),
        )

        x, y = 55, 50 + self.font_interline_spacing + height - 25

        return [
            f'-font "{self.EPISODE_TEXT_FONT}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize {45 * self.episode_text_font_size}',
            f'-kerning 1.0',
            f'-interword-spacing 10',
            f'-interline-spacing -10',
            f'-gravity {self.text_gravity}',
            f'-annotate {x:+}{y:+} "{index_text}"',
        ]


    def _create_polygons(self) -> list[Polygon]:
        """
        Create polygons which can be drawn on the image. These polygons
        are randomly generated and generally do not overlap the title
        or index text.

        Returns:
            List of Polygons to draw on the image.
        """

        # Generate all the coordinates which define the edges of each
        # polygon
        coordinates = self.polygon_distribution.generate_coordinates(
            self.inset, self.inter_shape_spacing
        )
        slope = tan(self.angle * PI / 180)

        def _x_at(y: float, b: float) -> float:
            """
            Get the x-coordinate for the slanted line with the given
            x-intercept at the given y-coordinate. This is derived from
            the point-slope equation.
            """

            return (y / slope) + b

        # Determine dimensions of text to adjust polygon boundaries
        title_width, title_height = self.image_magick.get_text_dimensions(
            self.title_text_commands,
            density=100,
            interline_spacing=self.font_interline_spacing,
            line_count=len(self.title_text.splitlines()),
        )
        index_width, index_height = self.image_magick.get_text_dimensions(
            self.index_text_commands,
        )
        text_width = max(title_width, index_width) + 50 # Text is 50px from edge
        text_height = title_height + index_height + self.font_vertical_shift +55

        # Generate list of polygons
        polygons: list[Polygon] = []
        # Iterate through polygons in pairs left -> right
        for b0, b1 in zip(coordinates[::2], coordinates[1::2]):
            # Default bounds of the randomly selected y-coordinate
            top_y_bound = self.inset
            bottom_y_bound = self.HEIGHT - self.inset

            # Limit bounds of y-coordinates to not overlap with text
            # log.debug(f'{b0} : {b1} | {_x_at(text_height, b0)} < {text_width}')
            if ((self.text_position == 'upper left'
                 and _x_at(text_height, b0) < text_width)
                or (self.text_position == 'upper right'
                    and _x_at(text_height, b1) > self.WIDTH - text_width)):
                top_y_bound = text_height
            elif ((self.text_position == 'lower left'
                   and _x_at(text_height, b0) < text_width)
                  or (self.text_position == 'lower right'
                      and _x_at(text_height, b1) > self.WIDTH - text_width)):
                bottom_y_bound = self.HEIGHT - text_height
                # log.debug(f'Limiting bottom_y to {text_height} from bottom')

            # Pick random y-coordinates for the top and bottom of the polygon
            top_y = randint(
                top_y_bound,
                (self.HEIGHT - self._MIN_SHAPE_HEIGHT) // 2,
            )
            bottom_y = randint(
                (self.HEIGHT // 2) + self._MIN_SHAPE_HEIGHT // 3,
                bottom_y_bound,
            )

            # For drawing the polygon, "invert" the y-coordinate used in
            # the x-coordinate calculation since the canvas 0 is at the
            # top of the image, not bottom
            polygon = Polygon(
                Coordinate(_x_at(self.HEIGHT - bottom_y, b0), bottom_y),
                Coordinate(_x_at(self.HEIGHT - bottom_y, b1), bottom_y),
                Coordinate(_x_at(self.HEIGHT - top_y, b1), top_y),
                Coordinate(_x_at(self.HEIGHT - top_y, b0), top_y),
            )
            if polygon.in_bounds:
                polygons.append(polygon)

        return polygons


    def _create_polygon_mask(self) -> Path:
        """
        Create an image which can be used as a composition mask. The
        mask is created by randomly generating polygons.

        Returns:
            Path to the created image. This is a placeholder image which
            should be deleted after Card creation is finished.
        """

        mask = self.image_magick.get_random_filename(self.source_file)

        command = ' '.join([
            f'convert',
            f'-size {self.WIDTH}x{self.HEIGHT}',
            # Alpha mask composition, non-polygons must be white
            f'xc:white',
            # Polygons (cutout) must be black
            f'-fill black',
            f'-draw "',
            # Add each polygon to the draw command
            *[polygon.draw() for polygon in self._create_polygons()],
            f'" "{mask.resolve()}"',
        ])
        self.image_magick.run(command)

        return mask


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
                extras['episode_text_color'] = StripedTitleCard.EPISODE_TEXT_COLOR
            if 'episode_text_font_size' in extras:
                extras['episode_text_font_size'] = 1.0


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
            ('episode_text_color' in extras
                and extras['episode_text_color'] != StripedTitleCard.EPISODE_TEXT_COLOR)
            or ('episode_text_font_size' in extras
                and extras['episode_text_font_size'] != 1.0)
        )

        return (custom_extras
            or ((font.color != StripedTitleCard.TITLE_COLOR)
            or (font.file != StripedTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
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

        return (custom_episode_map
                or episode_text_format.upper() != \
                    StripedTitleCard.EPISODE_TEXT_FORMAT.upper())


    @staticmethod
    def get_title_split_characteristics(
            characteristics: SplitCharacteristics,
            default_font_file: str,
            data: dict,
        ) -> SplitCharacteristics:
        """
        Get the title split characteristics for the card defined by the
        given card data. This modifies the style based on the indicated
        text position.

        Args:
            characteristics: Base split characteristics being modified
                for this card.
            default_font_file: Default font file for font size
                evaluation.
            data: Dictionary of card data to evaluate for any changes
                to the split characteristics.

        Returns:
            SplitCharacteristics object which defines how to split
            titles.
        """

        if 'text_position' in data:
            if 'upper' in data['text_position']:
                characteristics['style'] = 'top'
            else:
                characteristics['style'] = 'bottom'

        # Apply defaults
        return BaseCardType.get_title_split_characteristics(
            characteristics, default_font_file, data
        )


    def create(self) -> None:
        """Create this object's defined Title Card."""

        mask = self._create_polygon_mask()

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            f'-density 100',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Create mask
            f'\( -size "{self.TITLE_CARD_SIZE}"',
            f'xc:"{self.overlay_color}" \)',
            # Use mask composition
            f'"{mask.resolve()}"',
            f'-composite',
            # Add text
            *self.title_text_commands,
            *self.index_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        self.image_magick.delete_intermediate_images(mask)
