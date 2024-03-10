from collections import namedtuple
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional, Union

from modules.BaseCardType import (
    BaseCardType, ImageMagickCommands, Extra, CardDescription, Shadow
)
from modules.Debug import log
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


DarkenOption = Union[Literal['all', 'box'], bool]
BoxCoordinates = namedtuple('BoxCoordinates', ('x0', 'y0', 'x1', 'y1'))


class LandscapeTitleCard(BaseCardType):
    """
    This class defines a type of CardType that produces title-centric
    cards that do not feature any index text (i.e. season or episode
    text). The title is prominently featured in the center of the image,
    and is intended for landscape-centric images (hence the name) such
    as Planet Earth - as it well likely cover faces in a "typical"
    image. A bounding box around the title can be added/adjusted via
    extras.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Landscape',
        identifier='landscape',
        example='/internal_assets/cards/landscape.jpg',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=False,
        supported_extras=[
            Extra(
                name='Box Toggle',
                identifier='add_bounding_box',
                description='Whether to add a bounding box around the title text',
                tooltip=(
                    'Either <v>True</v>, or <v>False</v>. Default is '
                    '<v>True</v>.'
                ),
            ),
            Extra(
                name='Box Color',
                identifier='box_color',
                description='Color of the bounding box around the title text',
                tooltip='Default is to match the Font color.',
            ),
            Extra(
                name='Box Adjustments',
                identifier='box_adjustments',
                description='Manual adjustments to the bounds of the bounding box',
                tooltip=(
                    'Specifiy as <v>{top} {right} {bottom} {left}</v> - e.g. '
                    '<v>-20 10 0 5</v>. Positive values move that face out, '
                    'negative values move the face in. Default is '
                    '<v>0 0 0 0</v>. Unit is pixels.'
                ),
            ),
            Extra(
                name='Box Width',
                identifier='box_width',
                description='Thickness of the bounding box',
                tooltip=(
                    'Number ><v>0</v>. Default is <v>10</v>. Unit is pixels.'
                ),
            ),
            Extra(
                name='Image Darkening',
                identifier='darken',
                description='Whether to dark all or parts of the image',
                tooltip=(
                    'Either <v>all</v> to darken the entire image, <v>box</v> '
                    'to darken only the bounding box, or <v>False</v> to not'
                    'darken the image at all. This is to improve text '
                    'legibility on very bright images. Default is <v>box</v>.'
                ),
            ),
            Extra(
                name='Shadow Color',
                identifier='shadow_color',
                description='Color of the text drop shadow.',
                tooltip='Default is <c>black</c>.',
            ),
        ],
        description=[
            'Title-centric title cards that do not feature any text except a '
            'title.', 'These cards are intended for landscape-centric images.',
            'A bounding box around the title text can be added and adjusted '
            'via extras.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'landscape'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 15,
        'max_line_count': 5,
        'style': 'top',
    }

    """Default font and text color for episode title text"""
    TITLE_FONT = str((REF_DIRECTORY / 'Geometos.ttf').resolve())
    TITLE_COLOR = 'white'

    """Default characters to replace in the generic font"""
    FONT_REPLACEMENTS = {}

    """Default episode text format for this class"""
    EPISODE_TEXT_FORMAT = ''

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = False

    """Whether this CardType uses unique source images"""
    USES_UNIQUE_SOURCES = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Landscape Style'

    """Additional spacing (in pixels) between bounding box and title text"""
    BOUNDING_BOX_SPACING = 150
    """Default box width (in pixels)"""
    BOX_WIDTH = 10
    """Color for darkening is black at 30% transparency"""
    DARKEN_COLOR = '#00000030'
    """Color of the drop shadow"""
    SHADOW_COLOR = 'black'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'font_color', 'font_file',
        'font_interline_spacing', 'font_interword_spacing', 'font_kerning',
        'font_size', 'font_vertical_shift', 'add_bounding_box',
        'box_adjustments', 'box_color', 'box_width', 'darken', 'shadow_color',
    )

    def __init__(self,
            source_file: Path,
            card_file: Path,
            title_text: str,
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_size: float = 1.0,
            font_kerning: float = 1.0,
            font_vertical_shift: float = 0,
            blur: bool = False,
            grayscale: bool = False,
            add_bounding_box: bool = True,
            box_adjustments: tuple[int, int, int, int] = (0, 0, 0, 0),
            box_color: str = TITLE_COLOR,
            box_width: int = BOX_WIDTH,
            darken: DarkenOption = 'box',
            shadow_color: str = SHADOW_COLOR,
            preferences: Optional['Preferences'] = None,
            **unused,
        ) ->None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store object attributes
        self.source_file = source_file
        self.output_file = card_file
        self.title_text = self.image_magick.escape_chars(title_text)

        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_size = font_size
        self.font_kerning = font_kerning
        self.font_vertical_shift = font_vertical_shift

        # Store extras
        self.add_bounding_box = add_bounding_box
        self.box_adjustments = box_adjustments
        self.box_color = box_color
        self.box_width = box_width
        self.darken = darken
        self.shadow_color = shadow_color


    def darken_commands(self,
            coordinates: BoxCoordinates,
        ) -> ImageMagickCommands:
        """
        Subcommand to darken the image if indicated.

        Args:
            coordinates: Tuple of coordinates to that indicate where to
                darken.

        Returns:
            List of ImageMagick commands.
        """

        # Don't darken if blurring or not enabled
        if self.blur or not self.darken:
            return []

        # Darken only the bounding box coorindates
        if self.darken == 'box':
            x_start, y_start, x_end, y_end = coordinates

            return [
                f'-fill "{self.DARKEN_COLOR}"',
                f'-draw "rectangle {x_start},{y_start},{x_end},{y_end}"',
            ]

        return [
            # Create image the size of the title card filled with darken color
            f'\( -size "{self.TITLE_CARD_SIZE}"',
            f'xc:"{self.DARKEN_COLOR}" \)',
            # Compose atop of source image
            f'-gravity center',
            f'-composite',
        ]


    def __add_no_title(self) -> None:
        """Only resize and apply style to this source image."""

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            *self.resize_and_style,
            *self.darken_commands((0, 0, 0, 0)),
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)


    @property
    def bounding_box_coordinates(self) -> BoxCoordinates:
        """The coordinates of the bounding box around the title."""

        # If no bounding box indicated, return blank command
        if not self.add_bounding_box:
            return BoxCoordinates(0, 0, 0, 0)

        font_size = 150 * self.font_size
        interline_spacing = 60 + self.font_interline_spacing
        interword_spacing = 40 + self.font_interword_spacing
        kerning = 40 * self.font_kerning

        # Text-relevant commands
        text_command = [
            f'-font "{self.font_file}"',
            f'-gravity center',
            f'-pointsize {font_size:.1f}',
            f'-interline-spacing {interline_spacing:.1f}',
            f'-interword-spacing {interword_spacing:.1f}',
            f'-kerning {kerning:.2f}',
            f'-fill "{self.font_color}"',
            f'label:"{self.title_text}"',
        ]

        # Get dimensions of text - since text is stacked, do max/sum operations
        width, height = self.image_magick.get_text_dimensions(
            text_command,
            interline_spacing=interline_spacing,
            line_count=len(self.title_text.splitlines()),
            width='max', height='sum'
        )

        # Get start coordinates of the bounding box
        x_start, x_end = (self.WIDTH - width) / 2, (self.WIDTH + width) / 2
        y_start, y_end = (self.HEIGHT - height) / 2, (self.HEIGHT + height) / 2
        y_end -= 35 # Additional offset necessary for asymmetrical text bounds

        # Shift y coordinates by vertical shift
        y_start += self.font_vertical_shift
        y_end += self.font_vertical_shift

        # Adjust corodinates by spacing and manual adjustments
        x_start -= self.BOUNDING_BOX_SPACING + self.box_adjustments[3]
        x_end   += self.BOUNDING_BOX_SPACING + self.box_adjustments[1]
        y_start -= self.BOUNDING_BOX_SPACING + self.box_adjustments[0]
        y_end   += self.BOUNDING_BOX_SPACING + self.box_adjustments[2]

        return BoxCoordinates(x_start, y_start, x_end, y_end)


    def add_bounding_box_commands(self,
            coordinates: BoxCoordinates,
        ) -> ImageMagickCommands:
        """
        Subcommand to add the bounding box around the title text.

        Args:
            coordinates: Tuple of coordinates to that indicate where to
                darken.

        Returns:
            List of ImageMagick commands.
        """

        # No bounding box, return empty command
        if not self.add_bounding_box:
            return []

        x_start, y_start, x_end, y_end = coordinates

        return self.add_drop_shadow(
            [
                f'-size {self.TITLE_CARD_SIZE}',
                f'xc:None',
                f'-fill transparent',
                f'-strokewidth {self.box_width}',
                f'-stroke "{self.box_color}"',
                f'-draw "rectangle {x_start},{y_start},{x_end},{y_end}"',
            ],
            Shadow(opacity=85, sigma=3, x=10, y=10),
            x=0, y=0,
            shadow_color=self.shadow_color,
        )


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the title text to the image."""

        font_size = 150 * self.font_size
        interline_spacing = 60 + self.font_interline_spacing
        interword_spacing = 40 + self.font_interword_spacing
        kerning = 40 * self.font_kerning

        return self.add_drop_shadow(
            [
                f'-font "{self.font_file}"',
                f'-gravity center',
                f'-pointsize {font_size:.1f}',
                f'-interline-spacing {interline_spacing:.1f}',
                f'-interword-spacing {interword_spacing:.1f}',
                f'-kerning {kerning:.2f}',
                f'-fill "{self.font_color}"',
                f'label:"{self.title_text}"',
            ],
            Shadow(opacity=85, sigma=3, x=10, y=10),
            x=0, y=self.font_vertical_shift,
            shadow_color=self.shadow_color,
        )


    @staticmethod
    def modify_extras(
            extras: dict,
            custom_font: bool,
            custom_season_titles: bool,
        ) -> None:
        """
        Modify the given extras base on whether font or season titles
        are custom.

        Args:
            extras: Dictionary to modify.
            custom_font: Whether the font are custom.
            custom_season_titles: Whether the season titles are custom.
        """

        # Generic font, reset box adjustments and coloring
        if not custom_font:
            if 'box_adjustments' in extras:
                extras['box_adjustments'] = '0 0 0 0'
            if 'box_color' in extras:
                extras['box_color'] = LandscapeTitleCard.TITLE_COLOR


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            True if the given font is custom, False otherwise.
        """

        custom_extras = (
            ('box_adjustments' in extras
                and extras['box_adjustments'] != '0 0 0 0')
            or ('box_color' in extras
                and extras['box_color'] != LandscapeTitleCard.TITLE_COLOR)
        )

        return (custom_extras
            or ((font.color != LandscapeTitleCard.TITLE_COLOR)
            or (font.file != LandscapeTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0))
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
            False, as season titles aren't used.
        """

        return False


    def create(self):
        """Create this object's defined Title Card."""

        # If title is 0-length, just stylize
        if len(self.title_text) == 0:
            self.__add_no_title()
            return None

        # Get coordinates for bounding box
        bounding_box = self.bounding_box_coordinates

        # Generate command to create card
        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply any style modifiers
            *self.resize_and_style,
            # Add box or image darkening
            *self.darken_commands(bounding_box),
            # Add title text
            *self.title_text_commands,
            # Optionally add bounding box
            *self.add_bounding_box_commands(bounding_box),
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
        return None
