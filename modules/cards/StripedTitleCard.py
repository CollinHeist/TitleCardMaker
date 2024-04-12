from math import tan, pi as PI
from pathlib import Path
from random import choice as random_choice, randint
from typing import TYPE_CHECKING, Literal, NamedTuple, Optional, Union

from modules.BaseCardType import (
    BaseCardType, CardDescription, Coordinate, Dimensions, ImageMagickCommands,
    Extra, Rectangle, Shadow,
)
from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


from dataclasses import dataclass
@dataclass(repr=False)
class Polygon:
    c0: Coordinate
    c1: Coordinate
    c2: Coordinate
    c3: Coordinate

    def __str__(self) -> str:
        # return f'M {self.c0} L {self.c1} {self.c2} {self.c3} {self.c0}'
        return f'polygon {self.c0} {self.c1} {self.c2} {self.c3}'

    def draw(self) -> str:
        return str(self)

    @property
    def in_bounds(self) -> bool:
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


class StripedTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards which are
    
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Striped',
        identifier='striped',
        example='/internal_assets/cards/striped.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=False,
        supported_extras=[
            
        ],
        description=[
            
        ],
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'music'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 17,
        'max_line_count': 4,
        'style': 'bottom',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Gotham-Bold.otf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'source'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'E{episode_number}'
    EPISODE_TEXT_COLOR = 'white'
    INDEX_TEXT_FONT = REF_DIRECTORY / 'Gotham-Medium.ttf'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Music Style'

    """Implementation details"""
    DEFAULT_ANGLE = 79.5
    DEFAULT_INSET = 50
    DEFAULT_MASK_COLOR = 'white'
    _MIN_SHAPE_HEIGHT = BaseCardType.HEIGHT // 2
    _INTER_SHAPE_MARGIN = 15
    _SHAPE_SIZES = {
        's': [15, 40],
        'm': [50, 200],
        'l': [250, 500],
    }


    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_interline_spacing', 'font_interword_spacing', 'font_file',
        'font_kerning', 'font_size', 'font_vertical_shift',

        'angle',
        'inset',
        'mask_color',
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
            inset: int = DEFAULT_INSET,
            mask_color: str = DEFAULT_MASK_COLOR,

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
        self.inset = inset
        self.mask_color = mask_color

        # Implementation details
        

    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # If no title text, return empty commands
        if not self.title_text:
            return []

        return [
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {60 * self.font_size}',
            f'-interline-spacing {self.font_interline_spacing:+}',
            f'-interword-spacing {self.font_interword_spacing:+}',
            f'-kerning {self.font_kerning}',
            f'-gravity southwest',
            f'-annotate {x:+}{y:+} "{self.title_text}"',
        ]


    def _generate_coordinates(self) -> list[int]:
        """
        
        """

        # Start from left-hand side
        x = self.inset

        coordinates = [x]
        while x < self.WIDTH - self.inset:
            # Generate random size for the polygon
            size = random_choice('ssmmmlll')

            # Try and increment x by random width
            x += randint(
                self._SHAPE_SIZES[size][0],
                min(
                    self._SHAPE_SIZES[size][1],
                    self.WIDTH - self.inset,
                )
            )

            # Add polygon end to list of coordinates
            coordinates.append(x)

            # Increment x by inter-shape spacing, add space to coordinate list
            x += self._INTER_SHAPE_MARGIN
            coordinates.append(x)

        return coordinates


    def _create_polygons(self) -> list[Polygon]:
        """
        """

        coordinates = self._generate_coordinates()
        slope = tan(self.angle * PI / 180)

        # Generate list of polygons
        polygons: list[Polygon] = []
        for b0, b1 in zip(coordinates[::2], coordinates[1::2]):
            # Pick random y-coordinates for the top and bottom of the polygon
            top_y = randint(
                self.inset,
                (self.HEIGHT - self._MIN_SHAPE_HEIGHT) // 2,
            )
            bottom_y = randint(
                (self.HEIGHT // 2) + self._MIN_SHAPE_HEIGHT // 3,
                self.HEIGHT - self.inset - 300
            )

            # x = y / m + b; where m is the slope, b is the x-intercept
            polygon = Polygon(
                Coordinate((self.HEIGHT - bottom_y) / slope + b0, bottom_y),
                Coordinate((self.HEIGHT - bottom_y) / slope + b1, bottom_y),
                Coordinate((self.HEIGHT - top_y) / slope + b1, top_y),
                Coordinate((self.HEIGHT - top_y) / slope + b0, top_y),
            )
            if polygon.in_bounds:
                polygons.append(polygon)

        return polygons


    def _create_polygon_mask(self) -> Path:
        """
        
        """

        mask = self.image_magick.get_random_filename(self.source_file)

        command = ' '.join([
            f'convert',
            f'-size {self.WIDTH}x{self.HEIGHT}',
            # Alpha mask composition, non-polygons must be white
            f'xc:white',
            # Polgons (cutout) must be black
            f'-fill black',
            f'-draw "',
            *[polygon.draw() for polygon in self._create_polygons()],
            f'"',
            f'"{mask.resolve()}"',
        ])
        self.image_magick.run(command)

        return mask


    @property
    def season_text_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add the season text to the image. This uses
        placeholder annotation coordinates (+0+0) which should be
        modified when the finalized coordinates of the text is
        determined.
        """

        # No season text, return empty commands
        if self.hide_season_text:
            return []

        return [
            f'-gravity east',
            f'-font "{self.INDEX_TEXT_FONT.resolve()}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize 37',
            f'-kerning 1',
            f'-annotate +0+0', # Replaced later
            f'"{self.season_text}"',
        ]


    @property
    def episode_text_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add the episode text to the image. This uses
        placeholder annotation coordinates (+0+0) which should be
        modified when the finalized coordinates of the text is
        determined.
        """

        # No episode text, return empty commands
        if self.hide_episode_text:
            return []

        return [
            f'-gravity west',
            f'-font "{self.INDEX_TEXT_FONT.resolve()}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize 37',
            f'-kerning 1',
            f'-annotate +0+0', # Replaced later
            f'"{self.episode_text}"',
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add both the season and episode text to the image
        (as indicated).
        """

        # y-coordinate for all text
        y = (self.HEIGHT / 2) - self.player_inset - self._LINE_Y_INSET \
            + (-108 if self.add_controls else 0)

        # Determine position of season text
        season_commands = []
        if not self.hide_season_text:
            # Determine how far in from the right side to place text
            season_commands = self.season_text_commands
            width, _ = self.image_magick.get_text_dimensions(season_commands)
            dx = 105 + width # + | - directionality
            if self.player_position == 'left':
                x = self.WIDTH - self.player_inset - dx
            elif self.player_position == 'middle':
                x = (self.WIDTH + self.player_width) / 2 - dx
            elif self.player_position == 'right':
                x = self.player_inset + self.player_width - dx
            self.__season_x = x

            # Adjust placement of text based on new calculated offset
            season_commands[-2] = f'-annotate {x:+}{y:+}'

        # Determine position of episode text
        episode_commands = []
        if not self.hide_episode_text:
            # Determine how far in from left side to place text
            episode_commands = self.episode_text_commands
            width, _ = self.image_magick.get_text_dimensions(episode_commands)
            dx = 105 + width # - | + directionality
            if self.player_position == 'left':
                x = self.player_inset + self.player_width - dx
            elif self.player_position == 'middle':
                x = (self.WIDTH + self.player_width) / 2 - dx
            elif self.player_position == 'right':
                x = self.WIDTH - self.player_inset - dx
            self.__episode_x = x

            # Adjust placement of text based on new calculated offset
            episode_commands[-2] = f'-annotate {x:+}{y:+}'

        return [
            *season_commands,
            *episode_commands,
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
            ...


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
            ...
        )

        return (custom_extras
            or ((font.color != StripedTitleCard.TITLE_COLOR)
            or (font.file != StripedTitleCard.TITLE_FONT)
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

        standard_etf = StripedTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


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
            f'xc:"{self.mask_color}" \)',

            # Use mask composition
            f'"{mask.resolve()}"',
            f'-composite',
            
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
