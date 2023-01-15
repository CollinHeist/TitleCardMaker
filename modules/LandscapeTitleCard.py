from collections import namedtuple
from pathlib import Path
from typing import Any, Literal, Union

from modules.BaseCardType import BaseCardType
from modules.Debug import log

BoxCoordinates = namedtuple('BoxCoordinates', ('x0', 'y0', 'x1', 'y1'))
DarkenOption = Union[Literal['all', 'box'], bool]

class LandscapeTitleCard(BaseCardType):
    """
    This class defines a type of CardType that produces title-centric cards that
    do not feature any index text (i.e. season or episode text). The title is
    prominently featured in the center of the image, and is intended for 
    landscape-centric images (hence the name) such as Planet Earth - as it
    well likely cover faces in a "typical" image. A bounding box around the
    title can be added/adjusted via extras.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'landscape'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 15,   # Character count to begin splitting titles
        'max_line_count': 5,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses bottom heavy titling
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

    """Color for darkening is black at 30% transparency"""
    DARKEN_COLOR = '#00000030'

    __slots__ = (
        'source', 'output_file', 'title', 'font', 'font_size', 'title_color',
        'interline_spacing', 'kerning', 'vertical_shift', 'darken',
        'add_bounding_box', 'box_adjustments'
    )


    def __init__(self, source: Path, output_file: Path, title: str, font: str,
                 font_size: float, title_color: str,
                 interline_spacing: int=0,
                 kerning: float=1.0,
                 blur: bool=False,
                 grayscale: bool=False,
                 vertical_shift: float=0,
                 darken: DarkenOption=False,
                 add_bounding_box: bool=False,
                 box_adjustments: str=None,
                 **unused) ->None:
        """
        Initialize this TitleCard object. This primarily just stores instance
        variables for later use in `create()`.

        Args:
            source: Source image to base the card on.
            output_file: Output file where to create the card.
            title: Title text to add to created card.
            font: Font name or path (as string) to use for episode title.
            font_size: Scalar to apply to title font size.
            title_color: Color to use for title text.
            interline_spacing: Pixel count to adjust title interline spacing by.
            kerning: Scalar to apply to kerning of the title text.
            blur: Whether to blur the source image.
            grayscale: Whether to make the source image grayscale.
            vertical_shift: Vertical shift to apply to the title text.
            darken: (Extra) Whether to darken the image (if not blurred).
            add_bounding_box: (Extra) Whether to add a bounding box around the
                title text.
            box_adjustments: (Extra) How to adjust the bounds of the bounding
                box. Given as a string of pixels in clockwise order relative to
                the center. For example, "10 10 10 10" will expand the box by 10
                pixels in each direction.
            unused: Unused arguments.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        # Store object attributes
        self.source = source
        self.output_file = output_file
        self.title = self.image_magick.escape_chars(title)
        self.font = font
        self.font_size = font_size
        self.title_color = title_color
        self.interline_spacing = interline_spacing
        self.kerning = kerning
        self.vertical_shift = vertical_shift

        # Store extras
        self.add_bounding_box = add_bounding_box
        if isinstance(darken, str):
            try:
                er1 = '"darken" must be "all" or "box"'
                er2 = '"add_bounding_box" must be true if "darken" is "box"'
                assert (darken := str(darken).lower()) in ('all', 'box'), er1
                assert not (darken == 'box' and not self.add_bounding_box), er2
                self.darken = darken
            except Exception as e:
                log.error(f'Invalid extras - {e}')
                self.valid = False
                self.darken = False
        else:
            self.darken = bool(darken)

        # Parse box adjustments
        self.box_adjustments = (0, 0, 0, 0)
        if box_adjustments:
            # Verify adjustments are properly provided
            try:
                adjustments = box_adjustments.split(' ')
                self.box_adjustments = tuple(map(float, adjustments))
                error = ('must provide numeric adjustments for all sides like '
                         '"top right bottom left", e.g. "20 0 40 0"')
                assert len(self.box_adjustments) == 4, error
            # Invalid adjustments, log and mark invalid
            except Exception as e:
                log.error(f'Invalid box adjustments "{box_adjustments}" - {e}')
                self.box_adjustments = (0, 0, 0, 0)
                self.valid = False


    def darken_command(self, coordinates: BoxCoordinates) -> list[str]:
        """
        Subcommand to darken the image if indicated.

        Args:
            coordinates: Tuple of coordinates to that indicate where to darken.

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
            f'convert "{self.source.resolve()}"',
            *self.resize_and_style,
            *self.darken_command((0, 0, 0, 0)),
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)


    def get_bounding_box_coordinates(self, font_size: float,
                                     interline_spacing: float, kerning: float
                                     ) -> BoxCoordinates:
        """
        Get the coordinates of the bounding box around the title.

        Args:
            font_size: Font size.
            interline_spacing: Font interline spacing.
            kerning: Font kerning.

        Returns:
            Tuple of x/y coordinates for the bounding box.
        """

        # If no bounding box indicated, return blank command
        if not self.add_bounding_box:
            return BoxCoordinates(0, 0, 0, 0)

        # Text-relevant commands
        text_command = [
            f'-font "{self.font}"',
            f'-pointsize {font_size}',
            f'-gravity center',
            f'-interline-spacing {interline_spacing}',
            f'-kerning {kerning}',
            f'-interword-spacing 40',
            f'-fill "{self.title_color}"',
            f'label:"{self.title}"',
        ]

        # Get dimensions of text - since text is stacked, do max/sum operations
        dimensions = self.get_text_dimensions(text_command,
                                              width='max', height='sum')
        width, height = dimensions['width'], dimensions['height']

        # Get start coordinates of the bounding box
        x_start, x_end = 3200/2 - width/2, 3200/2 + width/2
        y_start, y_end = 1800/2 - height/2, 1800/2 + height/2
        y_end -= 35     # Additional offset necessary for things to work out

        # Adjust corodinates by spacing and manual adjustments
        x_start -= self.BOUNDING_BOX_SPACING + self.box_adjustments[3]
        x_end += self.BOUNDING_BOX_SPACING + self.box_adjustments[1]
        y_start -= self.BOUNDING_BOX_SPACING  + self.box_adjustments[0]
        y_end += self.BOUNDING_BOX_SPACING + self.box_adjustments[2]

        # Shift y coordinates by vertical shift
        y_start += self.vertical_shift
        y_end += self.vertical_shift

        return BoxCoordinates(x_start, y_start, x_end, y_end)


    def add_bounding_box_command(self, coordinates: BoxCoordinates) ->list[str]:
        """
        Subcommand to add the bounding box around the title text.

        Args:
            coordinates: Tuple of coordinates to that indicate where to darken.

        Returns:
            List of ImageMagick commands.
        """

        # No bounding box, return empty command
        if not self.add_bounding_box:
            return []

        x_start, y_start, x_end, y_end = coordinates

        return [
            # Create blank image 
            f'\( -size 3200x1800',
            f'xc:None',
            # Create bounding box
            f'-fill transparent',
            f'-strokewidth 10',
            f'-stroke "{self.title_color}"',
            f'-draw "rectangle {x_start},{y_start},{x_end},{y_end}"',
            # Create shadow of the bounding box
            f'\( +clone',
            f'-background None',
            f'-shadow 80x3+10+10 \)',
            # Underlay drop shadow 
            f'+swap',
            f'-background None',
            f'-layers merge',
            f'+repage \)',
            # Add bounding box and shadow to base image
            f'-composite',
        ]


    @staticmethod
    def modify_extras(extras: dict[str, Any], custom_font: bool,
                      custom_season_titles: bool) -> None:
        """
        Modify the given extras base on whether font or season titles are
        custom.

        Args:
            extras: Dictionary to modify.
            custom_font: Whether the font are custom.
            custom_season_titles: Whether the season titles are custom.
        """

        # Generic font, reset box adjustments
        if not custom_font:
            if 'box_adjustments' in extras:
                extras['box_adjustments'] = '0 0 0 0'


    @staticmethod
    def is_custom_font(font: 'Font') -> bool:
        """
        Determine whether the given font characteristics constitute a default
        or custom font.

        Args:
            font: The Font being evaluated.

        Returns:
            True if the given font is custom, False otherwise.
        """

        return ((font.file != LandscapeTitleCard.TITLE_FONT)
            or (font.size != 1.0)
            or (font.color != LandscapeTitleCard.TITLE_COLOR)
            or (font.interline_spacing != 0)
            or (font.kerning != 1.0))


    @staticmethod
    def is_custom_season_titles(custom_episode_map: bool, 
                                episode_text_format: str) -> bool:
        """
        Determine whether the given attributes constitute custom or generic
        season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            False, as season titles aren't used.
        """

        return False


    def create(self):
        """
        Make the necessary ImageMagick and system calls to create this object's
        defined title card.
        """

        # If title is 0-length, just stylize
        if len(self.title.strip()) == 0:
            self.__add_no_title()
            return None

        # Scale font size and interline spacing of roman text
        font_size = int(150 * self.font_size)
        interline_spacing = int(60 * self.interline_spacing)
        kerning = int(40 * self.kerning)

        # Get coordinates for bounding box
        bounding_box = self.get_bounding_box_coordinates(
            font_size, interline_spacing, kerning
        )

        # Generate command to create card
        command = ' '.join([
            f'convert "{self.source.resolve()}"',
            # Resize and apply any style modifiers
            *self.resize_and_style,
            *self.darken_command(bounding_box),
            # Add title text
            f'\( -background None',
            f'-font "{self.font}"',
            f'-pointsize {font_size}',
            f'-gravity center',
            f'-interline-spacing {interline_spacing}',
            f'-kerning {kerning}',
            f'-interword-spacing 40',
            f'-fill "{self.title_color}"',
            f'label:"{self.title}"',
            # Create drop shadow of title text
            f'\( +clone',
            f'-background None',
            f'-shadow 80x3+10+10 \)',
            # Underlay drop shadow 
            f'+swap',
            f'-background None',
            f'-layers merge',
            f'+repage \)',
            # Add title image(s) to source
            # Shift images vertically by indicated shift
            f'-geometry +0+{self.vertical_shift}',
            f'-composite',
            # Optionally add bounding box
            *self.add_bounding_box_command(bounding_box),
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)