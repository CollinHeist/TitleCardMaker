from pathlib import Path
from re import match
from typing import TYPE_CHECKING, Literal, Optional

from modules.BaseCardType import (
    BaseCardType, ImageMagickCommands, Extra, CardDescription
)
from modules.Debug import log

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font
    from modules.EpisodeInfo2 import EpisodeInfo


TextPosition = Literal[
    'upper left', 'upper right',
    'left', 'right',
    'lower left', 'lower right',
]
SeasonTextPosition = Literal['above', 'below']


class ShapeTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards styled
    ...
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
                tooltip='Defaults to match the shape color.',
            ), Extra(
                name='Hide Shape',
                identifier='hide_shape',
                description='Whether to hide the shape',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is '
                    '<v>False</v>.'
                ),
            ), Extra(
                name='Italize Season Text',
                identifier='italicize_season_text',
                description='Whether to italicize the season text',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is '
                    '<v>False</v>.'
                ),
            ), Extra(
                name='Season Text Font Size',
                identifier='season_text_font_size',
                description='Size adjustment for the season text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
            ), Extra(
                name='Season Text Position',
                identifier='season_text_position',
                description=(
                    'Where to position the season text relative to the title '
                    'text'
                ), tooltip=(
                    'Either <v>above</v> or <v>below</v>. Default is '
                    '<v>below</v>.'
                ),
            ), Extra(
                name='Shape Color',
                identifier='shape_color',
                description='Color of the shape',
                tooltip='Default is <v>gold1</v>.',
            ), Extra(
                name='Shape Inset',
                identifier='shape_inset',
                description='How far to inset the shape from the edges.',
                tooltip=(
                    'Number ≥<v>0.0</v>. Default is <v>75</v>. Unit is pixels.'
                ),
            ), Extra(
                name='Shape Side Length',
                identifier='shape_side_length',
                description='How long each side of the shape is.',
                tooltip=(
                    'Number ≥<v>50.0</v>. Default is <v>200</v>. Unit is pixels.'
                ),
            ), Extra(
                name='Shape Width',
                identifier='shape_width',
                description='Width of the shape',
                tooltip=(
                    'Number ><v>0.0</v>. Default is <v>10</v>. Unit is pixels.'
                ),
            ), Extra(
                name='Stroke Text Color',
                identifier='stroke_color',
                description='Color to use for the text stroke',
            ), Extra(
                name='Text Position',
                identifier='text_position',
                description='Where on the image to position the text',
                tooltip=(
                    'Either <v>upper left</v>, <v>upper right</v>, <v>left</v>,'
                    ' <v>right</v>, <v>lower left</v>, or <v>lower right</v>. '
                    'Default is <v>lower left</v>.'
                ),
            ), Extra(
                name='Gradient Omission',
                identifier='omit_gradient',
                description='Whether to omit the gradient overlay',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v>, text '
                    'may appear less legible on brighter images.'
                ),
            ),
        ], description=[
            'A title card featuring a diamond shape surrounding the text. The '
            'shape is interesected by the title text.',
            'This card allows the text (and shape) to be positioned at various '
            'points around the image.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'shape'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 32,   # Character count to begin splitting titles
        'max_line_count': 1,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses top heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Golca Extra Bold.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'source'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = 'rgb(255, 215, 0)' # gold1
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Golca Bold.ttf'
    EPISODE_TEXT_FONT_ITALIC = REF_DIRECTORY / 'Golca Bold Italic.ttf'
    EPISODE_TEXT_FORMAT = '{episode_number}.'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Shape Style'

    """Implementation details"""
    SHAPE_COLOR = EPISODE_TEXT_COLOR
    SHAPE_INSET = 75        # How far from each edge to offset the shape
    SHAPE_SIDE_LENGTH = 200 # How long each side of the shape is
    SHAPE_WIDTH = 8         # Width of the shape

    """Gradient image"""
    GRADIENT = REF_DIRECTORY.parent / 'overline' / 'small_gradient.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'hide_season_text', 'font_color', 'font_interline_spacing',
        'font_interword_spacing', 'font_file', 'font_kerning', 'font_size',
        'font_stroke_width', 'font_vertical_shift', 'season_text_color',
        'season_text_font_size', 'hide_shape', 'italicize_season_text',
        'omit_gradient', 'season_text_position', 'shape_color', 'shape_inset',
        'shape_side_length', 'shape_width', 'stroke_color', 'text_position',
        '__title_height',
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
            shape_color: str = SHAPE_COLOR,
            shape_inset: int = SHAPE_INSET,
            shape_side_length: int = SHAPE_SIDE_LENGTH,
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
        self.shape_color = shape_color
        self.shape_inset = int(shape_inset)
        self.shape_side_length = shape_side_length
        self.shape_width = shape_width
        self.stroke_color = stroke_color
        self.text_position: TextPosition = text_position

        # Implementation variables
        self.__title_height = None


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

        interline_spacing = 0 + self.font_interline_spacing
        size = 125 * self.font_size
        stroke_width = 4.0 * self.font_stroke_width

        return [
            f'-font "{self.font_file}"',
            f'-interline-spacing {interline_spacing}',
            f'-pointsize {size:.1f}',
            f'-fill "{self.font_color}"',
            f'+stroke',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width:.1f}',
            f'-gravity {gravity}',
            # f'-undercolor "rgba(12,12,12,0.5)"',
            f'-annotate {x:+.0f}{y:+.0f}',
        ]


    @property
    def _title_text_height(self) -> int:
        """
        
        """

        if len(self.title_text) == 0:
            return 0

        # Use value if already computed
        if self.__title_height is not None:
            return self.__title_height

        # Determine and store height
        self.__title_height =  self.image_magick.get_text_dimensions(
            self._base_title_text_commands() + [f'"{self.title_text}"'],
            width='max',
            height='sum',
        )[1] + 10 # 10px margin

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
            if (number := match(r'(\d+)\.?', first_word)):
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
            y = (self.HEIGHT / 2) - self.shape_inset - self.shape_side_length
        else:
            y = 0
        y += self.font_vertical_shift

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
        y += title_height - 10 # 10px margin

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
    def _left_shape_commands(self) -> ImageMagickCommands:
        """Subcommands to add the shape on the left of the image."""

        # Determine the length of the line
        line_length = self.shape_side_length \
            - (self._title_text_height / 2) - 10 # 10px margin

        # Starting y translation is based on text position
        if 'upper' in self.text_position:
            translation = self.shape_inset + (2 * self.shape_side_length)
        elif 'lower' in self.text_position:
            translation = self.HEIGHT - self.shape_inset
        else:
            translation = (self.HEIGHT / 2) + self.shape_side_length

        return [
            # Translate in from left side (y based on text position)
            f'"translate {self.shape_inset},{translation:.0f}',
            # Begin shape starting on left corner
            f'path \'M 0,-{self.shape_side_length}',
            # Draw up to top corner
            f'l {self.shape_side_length},-{self.shape_side_length}',
            # Draw down to right corner; x/y is cut off by text
            f'l {line_length},{line_length}',
            # Move back to left corner
            f'M 0,-{self.shape_side_length}',
            # Draw to bottom corner
            f'l {self.shape_side_length},{self.shape_side_length}',
            # Draw up to right corner; x/y is cut off by text
            f'l {line_length},-{line_length}',
            f'\'"'
        ]


    @property
    def _right_shape_commands(self) -> ImageMagickCommands:
        """Subcommands to add the shape on the right of the image."""

        line_length = self.shape_side_length \
            - (self._title_text_height / 2) - 10 # 10px margin

        # Starting y translation is based on text position
        if 'upper' in self.text_position:
            translation = self.shape_inset + (2 * self.shape_side_length)
        elif 'lower' in self.text_position:
            translation = self.HEIGHT - self.shape_inset
        else:
            translation = self.HEIGHT / 2 + self.shape_side_length

        return [
            # Translate in from right side (y based on text position)
            f'"translate {self.WIDTH - self.shape_inset},{translation:.0f}',
            # Begin shape starting on right corner
            f'path \'M 0,-{self.shape_side_length}',
            # Draw up to top corner
            f'l -{self.shape_side_length},-{self.shape_side_length}',
            # Draw down to left corner; x/y is cut off by text
            f'l -{line_length},{line_length}',
            # Move back to left corner
            f'M 0,-{self.shape_side_length}',
            # Draw to bottom corner
            f'l -{self.shape_side_length},{self.shape_side_length}',
            # Draw up to left corner; x/y is cut off by text
            f'l -{line_length},-{line_length}',
            f'\'"'
        ]


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

        return [
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
    def is_custom_font(font: 'Font') -> bool:
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.color != ShapeTitleCard.TITLE_COLOR)
            or (font.file != ShapeTitleCard.TITLE_FONT)
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

        standard_etf = ShapeTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


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
            *self.title_text_commands,
            *self.index_text_commands,
            *self.shape_commands,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
