from collections import namedtuple
from pathlib import Path
from typing import Literal, Optional

from modules.BaseCardType import BaseCardType, ImageMagickCommands
from modules.Debug import log


SeriesExtra = Optional
BoxCoordinates = namedtuple('BoxCoordinates', ('x0', 'y0', 'x1', 'y1'))
Position = Literal['left', 'center', 'right']

class TintedGlassTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards
    featuring a darkened and blurred rounded rectangle surrounding the
    title and index text. This card is inspired by Reddit user
    /u/RaceDebriefF1's Lucky! (2022) title cards.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'darkened'
    SW_REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'star_wars'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 24,   # Character count to begin splitting titles
        'max_line_count': 3,    # Maximum number of lines a title can take up
        'top_heavy': False,     # This class uses bottom heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((SW_REF_DIRECTORY / 'HelveticaNeue-Bold.ttf').resolve())
    TITLE_COLOR = 'white'
    FONT_REPLACEMENTS = {}

    """Default episode text format for this class"""
    EPISODE_TEXT_FORMAT = '{series_name} | S{season_number} E{episode_number}'
    EPISODE_TEXT_COLOR = 'SlateGray1'
    EPISODE_TEXT_FONT = SW_REF_DIRECTORY / 'HelveticaNeue-Bold.ttf'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = False

    """Whether this CardType uses unique source images"""
    USES_UNIQUE_SOURCES = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Tinted Glass Style'

    """Darkened area behind title/episode text is nearly black and 70% opaque"""
    DARKEN_COLOR = 'rgba(25, 25, 25, 0.7)'

    """Blur profile for darkened area behind title/episod text"""
    TEXT_BLUR_PROFILE = '0x6'

    __slots__ = (
        'source', 'output_file', 'title_text', '__line_count', 'episode_text',
        'hide_episode_text', 'font_file', 'font_size', 'font_color',
        'font_interline_spacing', 'font_interword_spacing', 'font_kerning',
        'font_vertical_shift', 'episode_text_color', 'episode_text_position',
        'box_adjustments', 'glass_color',
    )

    def __init__(self,
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
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_position: Position = 'center',
            box_adjustments: Optional[str] = None,
            glass_color: str = DARKEN_COLOR,
            preferences: Optional['Preferences'] = None, # type: ignore
            **unused,
        ) -> None:

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store object attributes
        self.source = source_file
        self.output_file = card_file

        self.title_text = self.image_magick.escape_chars(title_text)
        self.__line_count = len(title_text.split('\n'))
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())
        self.hide_episode_text = hide_episode_text or len(episode_text) == 0

        self.font_file = font_file
        self.font_size = font_size
        self.font_color = font_color
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_vertical_shift = font_vertical_shift

        # Store and validate extras
        self.episode_text_color = episode_text_color

        # Validate episode text position
        position = episode_text_position.lower().strip()
        if position not in ('left', 'center', 'right'):
            log.warning(f'episode_text_position "{position}" is invalid - must '
                        f'be "left", "center", or "right"')
            self.valid = False
        else:
            self.episode_text_position = position

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
        self.glass_color = glass_color


    def blur_rectangle_command(self,
            coordinates: BoxCoordinates,
            rounding_radius: int
        ) -> ImageMagickCommands:
        """
        Get the commands necessary to blur and darken a rectangle
        encompassing the given coordinates.

        Args:
            coordinates: BoxCoordinates that defines the bounds of the
                rectangle to blur/darken.
            rounding_radius: Pixel radius to use for the round edges of
                the rectangle.

        Returns:
            List of ImageMagick commands necessary to blur/darken the
            rectangle.
        """

        x0, y0, x1, y1 = coordinates
        draw_coords = f'{x0},{y0} {x1},{y1} {rounding_radius},{rounding_radius}'

        return [
            # Blur rectangle in the given bounds
            f'\( -clone 0',
            f'-fill white',
            f'-colorize 100',
            f'-fill black',
            f'-draw "roundrectangle {draw_coords}"',
            f'-alpha off',
            f'-write mpr:mask',
            f'+delete \)',
            f'-mask mpr:mask',
            f'-blur {self.TEXT_BLUR_PROFILE}',
            f'+mask',
            # Darken area behind title text
            f'-fill "{self.glass_color}"',
            f'-draw "roundrectangle {draw_coords}"',
        ]


    @property
    def add_title_text_command(self) -> ImageMagickCommands:
        """
        Get the ImageMagick commands necessary to add the title text
        described by this card.
        """

        font_size = 200 * self.font_size
        kerning = -5 * self.font_kerning
        interline_spacing = -50 + self.font_interline_spacing
        interword_spacing = 40 + self.font_interword_spacing
        vertical_shift = 300 + self.font_vertical_shift

        return [
            f'-gravity south',
            f'-font "{self.font_file}"',
            f'-pointsize {font_size}',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {interword_spacing}',
            f'-kerning {kerning}',
            f'-fill "{self.font_color}"',
            f'-annotate +0+{vertical_shift} "{self.title_text}"',
        ]


    def get_title_box_coordinates(self) -> BoxCoordinates:
        """
        Get the coordinates of the bounding box around the title.

        Returns:
            BoxCoordinates of the bounding box.
        """

        # Get dimensions of text - since text is stacked, do max/sum operations
        width, height = self.get_text_dimensions(
            self.add_title_text_command, width='max', height='sum'
        )

        # Get start coordinates of the bounding box
        x_start, x_end = self.WIDTH/2 - width/2, self.WIDTH/2 + width/2
        y_start, y_end = self.HEIGHT - 300 - height, self.HEIGHT - 300

        # Additional offsets necessary for equal padding
        x_start -= 50
        x_end += 50
        y_start += 12

        # Shift y coordinates by vertical shift
        y_start -= self.font_vertical_shift
        y_end -= self.font_vertical_shift

        # Adjust upper bounds of box if title is multi-line
        y_start += (65 * (self.__line_count-1)) if self.__line_count > 1 else 0

        # Adjust bounds by any manual box adjustments
        x_start -= self.box_adjustments[3]
        x_end += self.box_adjustments[1]
        y_start -= self.box_adjustments[0]
        y_end += self.box_adjustments[2]

        return BoxCoordinates(x_start, y_start, x_end, y_end)


    def add_episode_text_command(self,
            title_coordinates: BoxCoordinates,
        ) -> ImageMagickCommands:
        """
        Get the list of ImageMagick commands to add episode text.

        Args:
            title_coordinates: Coordinates of the title text for left/right
                alignment.

        Returns:
            List of ImageMagik commands.
        """

        # If hidden, return blank command
        if self.hide_episode_text:
            return []

        # Determine text position
        if self.episode_text_position == 'center':
            gravity = 'south'
            position = '+0+150'
        elif self.episode_text_position == 'left':
            gravity = 'southwest'
            position = f'+{title_coordinates.x0+30}+150'
        elif self.episode_text_position == 'right':
            gravity = 'southeast'
            position = f'+{self.WIDTH-(title_coordinates.x1-20)}+150'

        command = [
            f'-gravity {gravity}',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize 75',
            f'+kerning',
            f'-interword-spacing 0',
            f'-annotate {position} "{self.episode_text}"',
        ]

        width, height = self.get_text_dimensions(
            command, width='max', height='max'
        )

        # Center positioning requires padding adjustment
        if self.episode_text_position == 'center':
            x_start, x_end = self.WIDTH/2 - width/2, self.WIDTH/2 + width/2
            x_start, x_end = x_start - 30, x_end + 20
        # Left positioning requires padding right bounds
        elif self.episode_text_position == 'left':
            x_start, x_end = title_coordinates.x0, title_coordinates.x0 + width
            x_end += 30 + 20
        # Right positioning requires padding left bounds
        elif self.episode_text_position == 'right':
            x_start, x_end = title_coordinates.x1 - width, title_coordinates.x1
            x_start -= 30 + 20

        y_start, y_end = self.HEIGHT - 150 - height, self.HEIGHT - 150

        # Additional y offset necessary for equal padding
        y_start, y_end = y_start - 7, y_end + 10

        coordinates = BoxCoordinates(x_start, y_start, x_end, y_end)

        return [
            *self.blur_rectangle_command(coordinates, rounding_radius=20),
            *command,
        ]


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

        # Generic font, reset box adjustments and episode text color
        if not custom_font:
            if 'box_adjustments' in extras:
                del extras['box_adjustments']
            if 'episode_text_color' in extras:
                del extras['episode_text_color']


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

        return ((font.color != TintedGlassTitleCard.TITLE_COLOR)
            or  (font.file != TintedGlassTitleCard.TITLE_FONT)
            or  (font.interline_spacing != 0)
            or  (font.interword_spacing != 0)
            or  (font.kerning != 1.0)
            or  (font.size != 1.0)
            or  (font.vertical_shift != 0)
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

        standard_etfs = (
            '{series_name} | S{season_number} E{episode_number}',
            'S{season_number} E{episode_number}'
        )

        return (custom_episode_map
                or episode_text_format not in standard_etfs)


    def create(self):
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # Get coordinates for bounding box
        title_box_coordinates = self.get_title_box_coordinates()

        # Generate command to create card
        command = ' '.join([
            f'convert "{self.source.resolve()}"',
            # Resize and apply any style modifiers
            *self.resize_and_style,
            # Blur area behind title text
            *self.blur_rectangle_command(title_box_coordinates, 40),
            # Add title text
            *self.add_title_text_command,
            # Add episode text
            *self.add_episode_text_command(title_box_coordinates),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
