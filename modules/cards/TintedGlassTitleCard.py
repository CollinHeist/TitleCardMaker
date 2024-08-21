from collections import namedtuple
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from modules.BaseCardType import (
    BaseCardType,
    CardDescription,
    Extra,
    ImageMagickCommands,
)
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


BoxCoordinates = namedtuple('BoxCoordinates', ('x0', 'y0', 'x1', 'y1'))
Position = Literal['left', 'center', 'right']


class TintedGlassTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards
    featuring a darkened and blurred rounded rectangle surrounding the
    title and index text. This card is inspired by Reddit user
    /u/RaceDebriefF1's Lucky! (2022) title cards.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Tinted Glass',
        identifier='tinted glass',
        example='/internal_assets/cards/tinted glass.jpg',
        creators=['/u/RaceDebriefF1', 'CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is <c>rgb(198, 226, 255)</c>.',
                default='rgb(198, 226, 255)',
            ),
            Extra(
                name='Episode Text Position',
                identifier='episode_text_position',
                description=(
                    'Position of the episode text relative to the title text'
                ),
                tooltip=(
                    'Either <v>left</v>, <v>center</v>, or <v>right</v>. '
                    'Default is <v>center</v>.'
                ),
                default='center',
            ),
            Extra(
                name='Glass Adjustments',
                identifier='box_adjustments',
                description='Manual adjustments to the bounds of the glass',
                tooltip=(
                    'Specified like <v>{top} {right} {bottom} {left}</v>. For '
                    'example: <v>-20 10 0 5</v>. Positive values move that '
                    'face out, negative values move the face in. Unit is '
                    'pixels. Default is <v>0 0 0 0</v>.'
                ),
                default='0 0 0 0',
            ),
            Extra(
                name='Glass Corner Radius',
                identifier='rounding_radius',
                description='How round to make the title text glass rectangle',
                tooltip=(
                    'Number between <v>1</v> and <v>150</v>. Larger values '
                    'will result in more round edges. Default is <v>40</v>. '
                    'Unit is pixels.'
                ),
                default=40,
            ),
            Extra(
                name='Glass Color',
                identifier='glass_color',
                description='Color of the "glass" beneath the text',
                tooltip='Default is <c>rgba(25, 25, 25, 0.7)</c>.',
                default='rgba(25, 25, 25, 0.7)',
            ),
            Extra(
                name='Vertical Adjustment',
                identifier='vertical_adjustment',
                description='Vertical adjustment for the glass and text',
                tooltip=(
                    'Positive values to move up, negative values to move down. '
                    'Default value is <v>0</v>. Unit is pixels.'
                ),
                default=0,
            )
        ],
        description=[
            'Card type featuring a darkened and blurred rounded rectangle '
            'surrounding the title and episode text.', 'By default, these '
            'cards also feature the name of the series in the episode text.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'darkened'
    SW_REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'star_wars'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 24,
        'max_line_count': 3,
        'style': 'bottom',
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

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Tinted Glass Style'

    """Darkened area behind title/episode text is nearly black and 70% opaque"""
    DARKEN_COLOR = 'rgba(25, 25, 25, 0.7)'

    """Blur profile for darkened area behind title/episode text"""
    TEXT_BLUR_PROFILE = '0x6'
    DEFAULT_ROUNDING_RADIUS = 40

    __slots__ = (
        'source', 'output_file', 'title_text', '__line_count', 'episode_text',
        'hide_episode_text', 'font_file', 'font_size', 'font_color',
        'font_interline_spacing', 'font_interword_spacing', 'font_kerning',
        'font_vertical_shift', 'episode_text_color', 'episode_text_position',
        'box_adjustments', 'glass_color', 'rounding_radius',
        'vertical_adjustment',
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
            box_adjustments: tuple[int, int, int, int] = (0, 0, 0, 0),
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_position: Position = 'center',
            glass_color: str = DARKEN_COLOR,
            rounding_radius: int = DEFAULT_ROUNDING_RADIUS,
            vertical_adjustment: int = 0,
            preferences: Optional['Preferences'] = None,
            **unused,
        ) -> None:

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store object attributes
        self.source = source_file
        self.output_file = card_file

        self.title_text = self.image_magick.escape_chars(title_text)
        self.__line_count = len(title_text.splitlines())
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_episode_text = hide_episode_text

        self.font_file = font_file
        self.font_size = font_size
        self.font_color = font_color
        self.font_interline_spacing = -50 + font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_vertical_shift = font_vertical_shift

        # Store and validate extras
        self.box_adjustments = box_adjustments
        self.episode_text_color = episode_text_color
        self.episode_text_position = episode_text_position
        self.glass_color = glass_color
        self.rounding_radius = rounding_radius
        self.vertical_adjustment = vertical_adjustment - 50


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
            f'-blur {self.TEXT_BLUR_PROFILE}' if not self.blur else '',
            f'+mask',
            # Darken area behind title text
            f'-fill "{self.glass_color}"',
            f'-draw "roundrectangle {draw_coords}"',
        ]


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """
        Get the ImageMagick commands necessary to add the title text
        described by this card.
        """

        font_size = 200 * self.font_size
        kerning = -5 * self.font_kerning
        interword_spacing = 40 + self.font_interword_spacing
        vertical_shift = 300 + self.font_vertical_shift \
            + self.vertical_adjustment

        return [
            f'-gravity south',
            f'-font "{self.font_file}"',
            f'-pointsize {font_size}',
            f'-interline-spacing {self.font_interline_spacing}',
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

        # Get dimensions of title text
        width, height = self.image_magick.get_text_dimensions(
            self.title_text_commands,
            interline_spacing=self.font_interline_spacing,
            line_count=self.__line_count,
        )

        # Get start coordinates of the bounding box
        x_start, x_end = (self.WIDTH - width) / 2, (self.WIDTH + width) / 2
        y_start, y_end = self.HEIGHT - 300 - height, self.HEIGHT - 300

        # Additional offsets necessary for equal padding
        x_start -= 40
        x_end += 28
        y_start += 12

        # Shift y coordinates by vertical shift
        y_start -= self.font_vertical_shift + self.vertical_adjustment
        y_end -= self.font_vertical_shift + self.vertical_adjustment

        # Adjust bounds by any manual box adjustments
        x_start -= self.box_adjustments[3]
        x_end += self.box_adjustments[1]
        y_start -= self.box_adjustments[0]
        y_end += self.box_adjustments[2]

        return BoxCoordinates(x_start, y_start, x_end, y_end)


    def episode_text_commands(self,
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
            x, y = 0, 150
        elif self.episode_text_position == 'left':
            gravity = 'southwest'
            x, y = title_coordinates.x0 + 30, 150
        elif self.episode_text_position == 'right':
            gravity = 'southeast'
            x, y = self.WIDTH - title_coordinates.x1 - 20, 150
        y += self.vertical_adjustment
        position = f'{x:+.1f}{y:+.1f}'

        command = [
            f'-gravity {gravity}',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize 75',
            f'+kerning',
            f'-interword-spacing 0',
            f'-annotate {position} "{self.episode_text}"',
        ]

        width, height = self.image_magick.get_text_dimensions(
            command, width='max', height='sum'
        )

        # Center positioning requires padding adjustment
        if self.episode_text_position == 'center':
            x_start, x_end = (self.WIDTH - width) / 2, (self.WIDTH + width) / 2
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

        y_start -= self.vertical_adjustment
        y_end -= self.vertical_adjustment

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

        if not custom_font:
            if 'box_adjustments' in extras:
                del extras['box_adjustments']
            if 'episode_text_color' in extras:
                del extras['episode_text_color']
            if 'glass_color' in extras:
                extras['glass_color'] = TintedGlassTitleCard.DARKEN_COLOR


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
            or ('episode_text_color' in extras
                and extras['episode_text_color'] != \
                    TintedGlassTitleCard.EPISODE_TEXT_COLOR)
            or ('glass_color' in extras
                and extras['glass_color'] != TintedGlassTitleCard.DARKEN_COLOR)
        )

        return (custom_extras
            or ((font.color != TintedGlassTitleCard.TITLE_COLOR)
            or  (font.file != TintedGlassTitleCard.TITLE_FONT)
            or  (font.interline_spacing != 0)
            or  (font.interword_spacing != 0)
            or  (font.kerning != 1.0)
            or  (font.size != 1.0)
            or  (font.vertical_shift != 0))
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
            *self.blur_rectangle_command(
                title_box_coordinates,
                self.rounding_radius
            ),
            # Add title text
            *self.title_text_commands,
            # Add episode text
            *self.episode_text_commands(title_box_coordinates),
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
