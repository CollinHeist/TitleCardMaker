from collections import namedtuple
from pathlib import Path
from typing import Any, Literal, Optional, Union

from modules.BaseCardType import BaseCardType, ImageMagickCommands
from modules.Debug import log


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

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'landscape'

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
        'source_file', 'output_file', 'title_text', 'font_color', 'font_file',
        'font_interline_spacing', 'font_kerning', 'font_size', 'box_color',
        'font_vertical_shift', 'darken', 'add_bounding_box', 'box_adjustments'
    )

    def __init__(self,
            source_file: Path,
            card_file: Path,
            title_text: str,
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            font_interline_spacing: int = 0,
            font_size: float = 1.0,
            font_kerning: float = 1.0,
            font_vertical_shift: float = 0,
            blur: bool = False,
            grayscale: bool = False,
            add_bounding_box: bool = False,
            box_adjustments: tuple[int, int, int, int] = None,
            box_color: str = TITLE_COLOR,
            darken: DarkenOption = False,
            preferences: Optional['Preferences'] = None, # type: ignore
            **unused,
        ) ->None:
        """
        Construct a new instance of this Card.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store object attributes
        self.source_file = source_file
        self.output_file = card_file
        self.title_text = self.image_magick.escape_chars(title_text)
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_size = font_size
        self.font_kerning = font_kerning
        self.font_vertical_shift = font_vertical_shift

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


    def darken_command(self, coordinates: BoxCoordinates) ->ImageMagickCommands:
        self.box_color = box_color
    def darken_commands(self, coordinates: BoxCoordinates) ->ImageMagickCommands:
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


    def get_bounding_box_coordinates(self,
            font_size: float,
            interline_spacing: float,
            kerning: float,
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
            f'-font "{self.font_file}"',
            f'-pointsize {font_size}',
            f'-gravity center',
            f'-interline-spacing {interline_spacing}',
            f'-kerning {kerning}',
            f'-interword-spacing 40',
            f'-fill "{self.font_color}"',
            f'label:"{self.title_text}"',
        ]

        # Get dimensions of text - since text is stacked, do max/sum operations
        width, height = self.get_text_dimensions(
            text_command, width='max', height='sum'
        )

        # Get start coordinates of the bounding box
        x_start, x_end = 3200/2 - width/2, 3200/2 + width/2
        y_start, y_end = 1800/2 - height/2, 1800/2 + height/2
        y_end -= 35     # Additional offset necessary for things to work out

        # Shift y coordinates by vertical shift
        y_start += self.font_vertical_shift
        y_end += self.font_vertical_shift

        # Adjust corodinates by spacing and manual adjustments
        x_start -= self.BOUNDING_BOX_SPACING + self.box_adjustments[3]
        x_end += self.BOUNDING_BOX_SPACING + self.box_adjustments[1]
        y_start -= self.BOUNDING_BOX_SPACING  + self.box_adjustments[0]
        y_end += self.BOUNDING_BOX_SPACING + self.box_adjustments[2]

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

        return [
            # Create blank image
            f'\( -size 3200x1800',
            f'xc:None',
            # Create bounding box
            f'-fill transparent',
            f'-strokewidth 10',
            f'-stroke "{self.box_color}"',
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
    def modify_extras(
            extras: dict[str, Any],
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
    def is_custom_font(font: 'Font') -> bool: # type: ignore
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.

        Returns:
            True if the given font is custom, False otherwise.
        """

        return ((font.color != LandscapeTitleCard.TITLE_COLOR)
            or (font.file != LandscapeTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
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
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # If title is 0-length, just stylize
        if len(self.title_text) == 0:
            self.__add_no_title()
            return None

        # Scale font size and interline spacing of roman text
        font_size = int(150 * self.font_size)
        interline_spacing = int(60 * self.font_interline_spacing)
        kerning = int(40 * self.font_kerning)

        # Get coordinates for bounding box
        bounding_box = self.get_bounding_box_coordinates(
            font_size, interline_spacing, kerning
        )

        # Generate command to create card
        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply any style modifiers
            *self.resize_and_style,
            *self.darken_commands(bounding_box),
            # Add title text
            f'\( -background None',
            f'-font "{self.font_file}"',
            f'-pointsize {font_size}',
            f'-gravity center',
            f'-interline-spacing {interline_spacing}',
            f'-kerning {kerning}',
            f'-interword-spacing 40',
            f'-fill "{self.font_color}"',
            f'label:"{self.title_text}"',
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
            f'-geometry +0+{self.font_vertical_shift}',
            f'-composite',
            # Optionally add bounding box
            *self.add_bounding_box_commands(bounding_box),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
        return None
