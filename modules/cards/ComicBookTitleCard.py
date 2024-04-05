from math import cos, sin, pi as PI
from pathlib import Path
from random import uniform
from re import IGNORECASE, compile as re_compile
from typing import TYPE_CHECKING, Literal, Optional, Union

from modules.Debug import log
from modules.BaseCardType import BaseCardType, Coordinate, ImageMagickCommands

if TYPE_CHECKING:
    from modules.Font import Font


class SvgRectangle:
    """Class that defines a movable SVG rectangle."""

    def __init__(self, width: int, height: int) -> None:
        """
        Initialize this Rectangle object for a rectangle of the given
        dimensions.

        Args:
            width: Width of the rectangle.
            height: Height of the rectangle
        """

        self.width = width
        self.height = height
        self.center = Coordinate(0, 0)
        self.rotation = 0
        self.offset = Coordinate(0, 0)


    def rotate(self, angle_degrees: float = 0.0) -> 'SvgRectangle':
        """
        Set the rotation of this rectangle.

        Args:
            angle_degrees: Angle (in degrees) of the rotation to set.

        Returns:
            This object.
        """

        self.rotation = angle_degrees

        return self


    def shift_origin(self, origin: Coordinate) -> 'SvgRectangle':
        """
        Set the origin (for rotation and relative placement) of this
        Rectangle.

        Args:
            origin: Coordinates to set as this object's origin.

        Returns:
            This object.
        """

        self.center = origin

        return self


    @property
    def draw_commands(self) -> ImageMagickCommands:
        """
        Draw this rectangle with the necessary SVG ImageMagickCommands.

        Returns:
            List of ImageMagick commands to draw this rectangle.
        """

        start_position = Coordinate(
            -self.width / 2 + self.offset.x,
            -self.height / 2 + self.offset.y,
        )

        return [
            f'-draw "translate {self.center.as_svg}',
            f'rotate {self.rotation}',
            f'path \'M {start_position.as_svg}',
            f'l {self.width} 0',
            f'l 0 {self.height}',
            f'l {-self.width} 0',
            f'l 0 {-self.height}\' "',
        ]


class ComicBookTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards styled
    after a Comic Book panel. There are two banners - one for the title
    and one for the index text - on the top and bottom of the card.
    These panels can be rotated, recolored, and repositioned freely.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'comic_book'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 32,   # Character count to begin splitting titles
        'max_line_count': 2,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses top heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY /'cc-wild-words-bold-italic.ttf').resolve())
    TITLE_COLOR = 'black'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS = {'é': 'e', 'É': 'E'}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = TITLE_COLOR
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'cc-wild-words-bold-italic.ttf'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Comic Book Style'

    """Implementation details"""
    BANNER_FILL_COLOR = 'rgba(235,73,69,0.6)'
    TEXT_BOX_WIDTH_MARGIN = 50
    TEXT_BOX_HEIGHT_MARGIN = 50
    TITLE_TEXT_VERTICAL_OFFSET = 125

    RANDOM_ANGLE_REGEX = re_compile(
        r'random\[([+-]?\d+.?\d*),\s*([+-]?\d+.?\d*)\]', IGNORECASE
    )

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_interline_spacing', 'font_interword_spacing', 'font_file',
        'font_kerning', 'font_size', 'font_vertical_shift',
        'episode_text_color', 'index_text_position', 'text_box_fill_color',
        'text_box_edge_color', 'title_text_rotation_angle',
        'index_text_rotation_angle', 'banner_fill_color', 'title_banner_shift',
        'index_banner_shift', 'hide_title_banner', 'hide_index_banner',
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
            episode_text_color : str = 'black',
            index_text_position: Literal['left', 'middle', 'right'] = 'left',
            text_box_fill_color: str = 'white',
            text_box_edge_color: Optional[str] = None,
            title_text_rotation_angle: Union[float, str] = -4.0,
            index_text_rotation_angle: Union[float, str] = -4.0,
            banner_fill_color: str = 'rgba(235,73,69,0.6)',
            title_banner_shift: int = 0,
            index_banner_shift: int = 0,
            hide_title_banner: bool = False,
            hide_index_banner: bool = False,
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
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.episode_text_color = episode_text_color
        self.index_text_position = index_text_position
        self.text_box_fill_color = text_box_fill_color
        self.banner_fill_color = banner_fill_color
        self.title_banner_shift = title_banner_shift
        self.index_banner_shift = index_banner_shift
        self.hide_title_banner = hide_title_banner
        self.hide_index_banner = hide_index_banner

        # If edge color was omitted, use the font color
        if text_box_edge_color is None:
            self.text_box_edge_color = font_color
        else:
            self.text_box_edge_color = text_box_edge_color

        # Randomize rotation angles if indicated
        def get_angle(angle: Union[float, str]) -> Optional[float]:
            if isinstance(angle, (int, float)):
                return angle
            try:
                # Get bounds from the random range string
                bounds = self.RANDOM_ANGLE_REGEX.match(angle).groups()
                lower, upper = map(float, bounds)

                # Lower bound cannot be above upper bound
                if lower > upper:
                    raise ValueError(f'')

                return uniform(lower, upper)
            except ValueError:
                log.error(f'Lower bound must be below upper bound')
                self.valid = False
            except AttributeError:
                log.error(f'Invalid angle randomization - must be like '
                          f'random[lower, upper] - i.e. random[-2, 2]')
                self.valid = False
            return None
        self.title_text_rotation_angle = get_angle(title_text_rotation_angle)
        self.index_text_rotation_angle = get_angle(index_text_rotation_angle)


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # If no title text, return empty commands
        if len(self.title_text) == 0:
            return []

        # Font characteristics
        font_size = 100 * self.font_size
        y_coordinate = self.TITLE_TEXT_VERTICAL_OFFSET +self.font_vertical_shift

        # String for the rotation of the title text
        rotation = (
            f'{self.title_text_rotation_angle}x{self.title_text_rotation_angle}'
        )

        return [
            f'-gravity south',
            f'-pointsize {font_size}',
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-kerning {1 * self.font_kerning}',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-strokewidth 0',
            f'+stroke',
            f'-annotate {rotation}+0+{y_coordinate} "{self.title_text}"',
        ]


    @property
    def title_text_box_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text box."""

        # No index text, return empty commands
        if len(self.title_text) == 0:
            return []

        # Get dimensions of the title text
        title_width, title_height = self.image_magick.get_text_dimensions(
            self.title_text_commands,
            interline_spacing=self.font_interline_spacing,
            line_count=len(self.title_text.splitlines()),
            width='max',
        )

        # Create the rectangle that will border the title text
        title_text_rectangle = SvgRectangle(
            title_width + self.TEXT_BOX_WIDTH_MARGIN,
            title_height + self.TEXT_BOX_HEIGHT_MARGIN,
        )

        # Rotate by given angle
        title_text_rectangle.rotate(self.title_text_rotation_angle)

        # Shift rectangle to placement of title text
        title_text_rectangle.shift_origin(
            Coordinate(
                self.WIDTH / 2,
                self.HEIGHT
                - self.TITLE_TEXT_VERTICAL_OFFSET
                - (title_height / 2)
            )
        )

        # Only drawing the text box, return that command
        if self.hide_title_banner:
            return [
                f'-gravity center',
                f'-fill "{self.text_box_fill_color}"',
                f'-stroke "{self.text_box_edge_color}"',
                f'-strokewidth 5',
                *title_text_rectangle.draw_commands,
            ]

        # Create bottom fill rectangle
        bottom_fill_rectangle = SvgRectangle(
            self.WIDTH * 2, # x/y Margin to account for rotation
            self.TITLE_TEXT_VERTICAL_OFFSET + 500
        )
        bottom_fill_rectangle.rotate(self.title_text_rotation_angle)
        bottom_fill_rectangle.shift_origin(
            Coordinate(
                self.WIDTH / 2,
                self.HEIGHT
                - self.TITLE_TEXT_VERTICAL_OFFSET
                - (title_height / 2)
                + (self.TITLE_TEXT_VERTICAL_OFFSET+500)/2
            )
        )
        bottom_fill_rectangle.offset = Coordinate(0, self.title_banner_shift)

        return [
            # Draw bottom fill rectangle
            f'-gravity center',
            f'-fill "{self.banner_fill_color}"',
            f'-stroke "{self.text_box_edge_color}"',
            f'-strokewidth 5',
            *bottom_fill_rectangle.draw_commands,
            # Add title text rectangle
            f'-gravity center',
            f'-fill "{self.text_box_fill_color}"',
            *title_text_rectangle.draw_commands,
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the index text."""

        # No index text, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Determine index text
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text} {self.episode_text}'

        # Font characteristics
        font_size = 50 * self.font_size

        # Determine placement gravity and offset of the text
        y_coordinate = 75
        if self.index_text_position == 'left':
            gravity = 'northwest'
            x_coordinate = 35
        elif self.index_text_position == 'middle':
            gravity = 'north'
            x_coordinate = 0
        else:
            gravity = 'northeast'
            x_coordinate = 35

        # String for the rotation of the index text
        rotation = (
            f'{self.index_text_rotation_angle}x{self.index_text_rotation_angle}'
        )

        return [
            f'-gravity {gravity}',
            f'-pointsize {font_size}',
            f'-font "{self.font_file}"',
            f'-fill "{self.episode_text_color}"',
            f'+kerning',
            f'-strokewidth 0',
            f'+stroke',
            f'+interword-spacing',
            f'-annotate {rotation}+{x_coordinate}+{y_coordinate} "{index_text}"',
        ]


    @property
    def index_text_box_commands(self) -> ImageMagickCommands:
        """
        Subcommands required to add the index text box and the bottom
        fill rectangle.
        """

        # No index text, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Get dimensions of the index text
        index_width, index_height = self.image_magick.get_text_dimensions(
            self.index_text_commands,
            width='max',
        )

        # Create the rectangle that will border the index text
        index_text_rectangle = SvgRectangle(
            index_width + (self.TEXT_BOX_WIDTH_MARGIN / 2),
            index_height + (self.TEXT_BOX_HEIGHT_MARGIN / 2),
        )

        # Apply indicated rotation
        index_text_rectangle.rotate(self.index_text_rotation_angle)

        # Determine new origin of the index text based on placement location
        y_coordinate = 75 + (index_height / 2)
        if self.index_text_position == 'left':
            # The index text origin is 35px from the left of the image
            index_text_origin = Coordinate(35, y_coordinate)

            # Determine the offset to the center of the rotated index text
            angle = self.index_text_rotation_angle * PI / 180
            x = index_width / 2
            y = 0
            index_text_rectangle.offset = Coordinate(
                x * cos(angle) - y * sin(angle),
                (x * sin(angle) + y * cos(angle))/abs(self.index_text_rotation_angle),
            )
        elif self.index_text_position == 'middle':
            index_text_origin = Coordinate(self.WIDTH / 2 - 10, y_coordinate)
        else:
            index_text_origin = Coordinate(self.WIDTH - 35, y_coordinate)

            # Determine the offset to the center of the rotated index text
            angle = self.index_text_rotation_angle * PI / 180
            x = -index_width / 2
            y = 0
            index_text_rectangle.offset = Coordinate(
                x * cos(angle) - y * sin(angle),
                (x * sin(angle) + y * cos(angle))/abs(self.index_text_rotation_angle),
            )

        # Shift rectangle to placement of index text
        index_text_rectangle.shift_origin(index_text_origin)

        # If not drawing the banner, return only text rectangle
        if self.hide_index_banner:
            return [
                f'-gravity center',
                f'-fill "{self.text_box_fill_color}"',
                f'-stroke "{self.text_box_edge_color}"',
                f'-strokewidth 5',
                *index_text_rectangle.draw_commands,
            ]

        index_fill_rectangle = SvgRectangle(
            self.WIDTH * 2, # x/y Margin to account for rotation
            75 + 500
        )
        index_fill_rectangle.rotate(self.index_text_rotation_angle)

        y_coordinate = 75 + (index_height / 2) - (75 + 500) / 2 \
            + self.index_banner_shift
        if self.index_text_position == 'left':
            index_fill_rectangle.shift_origin(Coordinate(
                35,
                y_coordinate
            ))
        elif self.index_text_position == 'middle':
            index_fill_rectangle.shift_origin(Coordinate(
                self.WIDTH / 2,
                y_coordinate,
            ))
        else:
            index_fill_rectangle.shift_origin(Coordinate(
                self.WIDTH - 35,
                y_coordinate,
            ))

        return [
            # Draw banner
            f'-fill "{self.banner_fill_color}"',
            f'-stroke "{self.text_box_edge_color}"',
            f'-strokewidth 5',
            *index_fill_rectangle.draw_commands,
            # Draw text
            f'-fill "{self.text_box_fill_color}"',
            *index_text_rectangle.draw_commands,
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
                extras['episode_text_color'] = 'black'
            if 'text_box_fill_color' in extras:
                extras['text_box_fill_color'] = 'white'
            if 'text_box_edge_color' in extras:
                extras['text_box_edge_color'] = 'white'
            if 'border_fill_color' in extras:
                extras['border_fill_color'] = \
                    ComicBookTitleCard.BANNER_FILL_COLOR


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
            ('text_box_fill_color' in extras
                and extras['text_box_fill_color'] != 'black')
            or ('text_box_fill_color' in extras
                and extras['text_box_fill_color'] != 'white')
            or ('banner_fill_color' in extras
                and extras['banner_fill_color'] != ComicBookTitleCard.BANNER_FILL_COLOR)
        )

        return (custom_extras
            or ((font.color != ComicBookTitleCard.TITLE_COLOR)
            or (font.file != ComicBookTitleCard.TITLE_FONT)
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

        standard_etf = ComicBookTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """Create this object's defined Title Card."""

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # # Draw title text rectangles
            *self.title_text_box_commands,
            # Draw index text rectangles
            *self.index_text_box_commands,
            # Draw text last because the -annotate position affects -draw commands
            # Add title text
            *self.title_text_commands,
            # Add index text
            *self.index_text_commands,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
