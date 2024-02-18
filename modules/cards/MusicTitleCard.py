from pathlib import Path
from random import random
from typing import TYPE_CHECKING, Literal, Optional, Union

from modules.BaseCardType import (
    BaseCardType, CardDescription, Coordinate, Dimensions, ImageMagickCommands,
    Extra, Rectangle, Shadow,
)
from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font

PlayerPosition = Literal['left', 'middle', 'right']
PlayerStyle = Literal['basic', 'artwork', 'logo', 'poster']


class MusicTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards ...
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Music',
        identifier='music',
        example='/internal_assets/cards/music.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Album Size',
                identifier='album_size',
                description=(
                    'Scalar for how much to scale the size of the album image'
                ),
                tooltip='Number ><v>0.0</v>. Default is <v>1.0</v>.'
            ),
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is to match the Font color.'
            ),
            Extra(
                name='Player Inset',
                identifier='player_inset',
                description='How far to inset the player from the edges',
                tooltip=(
                    'Number between <v>0</v> and <v>1800</v>. Default is '
                    '<v>75</v>. Unit is pixels.'
                ),
            ),
            Extra(
                name='Player Background Color',
                identifier='player_color',
                description='Background color of the player',
                tooltip='Default is <c>rgba(0,0,0,0.50)</c>.',
            ),
            Extra(
                name='Player Width',
                identifier='player_width',
                description='Width of the player',
                tooltip=(
                    'Number between <v>400</v> and <v>3200</v>. Default is '
                    '<v>900</v>. Unit is pixels.'
                ),
            ),
            Extra(
                name='Percentage',
                identifier='percentage',
                description='Filled percentage of the timeline',
                tooltip=(
                    'Can be a number (e.g. <v>0.3</v> for 30% filled), '
                    '<v>random</v> to randomize the filled percentage, or a '
                    'format string for how to calculate the percentage (e.g. '
                    '<v>{episode_number / season_episode_max}</v> to calculate '
                    'as a percentage of the season). Default is <v>random</v>.'
                ),
            ),
            Extra(
                name='Player Position',
                identifier='player_position',
                description='Where to position the player on the image',
                tooltip=(
                    'Either <v>left</v>, <v>middle</v>, or <v>right</v>. '
                    'Default is <v>left</v>.'
                ),
            ),
            Extra(
                name='Player Style',
                identifier='player_style',
                description='Which style of the player to display',
                tooltip=(
                    'Either <v>basic</v> for no image at all, <v>artwork</v> '
                    'to use the Series backdrop, <v>logo</v> to use the Series '
                    'logo, or <v>poster</v> to use the Series poster. The '
                    'default is <v>logo</v>.'
                ),
            ),
            Extra(
                name='Album Subtitle',
                identifier='subtitle',
                description='Text to display below the title',
                tooltip=(
                    'Can be literal text (e.g. <v>My Series</v>), or a format '
                    'string (e.g. <v>{series_name}</v>) to dynamically adjust '
                    'the text. Default is <v>{series_name}</v>.'
                ),
            ),
            Extra(
                name='Round Album Corners',
                identifier='round_corners',
                description='Whether to round the corners of the album image',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is '
                    '<v>True</v>.'
                ),
            ),
            Extra(
                name='Timeline Color',
                identifier='timeline_color',
                description='Color of the filled timeline',
                tooltip='Default is <c>rgb(29,185,84)</c>.',
            ),
            Extra(
                name='Long Line Truncation',
                identifier='truncate_long_titles',
                description='Whether and how to truncate very long titles',
                tooltip=(
                    'Either a number ><v>0</v>, or <v>False</v>. If a number, '
                    'then titles are cut off after that many lines; if '
                    '<v>False</v>, then titles are not cut off. Default is '
                    '<v>2</v>.'
                ),
            ),
        ],
        description=[
            '',
        ],
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'music'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 15,   # Character count to begin splitting titles
        'max_line_count': 4,    # Maximum number of lines a title can take up
        'top_heavy': False,      # This class uses top heavy titling
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
    SUBTITLE_FONT = REF_DIRECTORY / 'Gotham-Light.otf'
    BACKGROUND_LINE_COLOR = 'rgb(120,120,120)'
    DEFAULT_TIMELINE_COLOR = 'rgb(29,185,84)' # Spotify Green
    DEFAULT_LINE_WIDTH = 9 # pixels
    DEFAULT_PLAYER_COLOR = 'rgba(0,0,0,0.50)' # Black @ 50% opacity
    DEFAULT_PLAYER_WIDTH = 900
    GLASS_BLUR_PROFILE = '0x12'
    DEFAULT_INSET = 50
    DEFAULT_PLAYER_POSITION: PlayerPosition = 'left'
    DEFAULT_PLAYER_STYLE: PlayerStyle = 'logo'

    """How far from the bottom of the glass the line is drawn"""
    _LINE_Y_INSET = 85

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_interline_spacing', 'font_interword_spacing', 'font_file',
        'font_kerning', 'font_size', 'font_vertical_shift', 'album_cover',
        'album_size', 'episode_text_color', 'percentage', 'player_color',
        'player_inset', 'player_position', 'player_style', 'player_width',
        'round_corners', 'subtitle', 'timeline_color', '__album_dimensions',
        '__title_dimensions', '__season_x', '__episode_x', '__cleanup',
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
            album_cover: Optional[Path] = None,
            album_size: float = 1.0,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            percentage: Union[float, str, Literal['random']] = 'random',
            player_position: PlayerPosition = DEFAULT_PLAYER_POSITION,
            player_color: str = DEFAULT_PLAYER_COLOR,
            player_inset: int = DEFAULT_INSET,
            player_style: PlayerStyle = DEFAULT_PLAYER_STYLE,
            player_width: int = DEFAULT_PLAYER_WIDTH,
            round_corners: bool = True,
            subtitle: str = '',
            timeline_color: str = DEFAULT_TIMELINE_COLOR,
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
        self.album_cover = Path(album_cover) if album_cover else album_cover
        self.album_size = album_size
        self.episode_text_color = episode_text_color
        self.percentage = random() if percentage == 'random' else percentage
        self.player_color = player_color
        self.player_inset = player_inset
        self.player_position: PlayerPosition = player_position
        self.player_style: PlayerStyle = player_style
        self.player_width = player_width
        self.round_corners = round_corners
        self.subtitle = subtitle
        self.timeline_color = timeline_color

        # Implementation details
        self.__album_dimensions: Optional[Dimensions] = None
        self.__title_dimensions: Optional[Dimensions] = None
        self.__season_x: Optional[float] = None
        self.__episode_x: Optional[float] = None
        self.__cleanup: list[Path] = []


    @staticmethod
    def SEASON_TEXT_FORMATTER(episode_info: EpisodeInfo) -> str:
        """
        Fallback season title formatter.

        Args:
            episode_info: Info of the Episode whose season text is being
                determined.

        Returns:
            'S{x}' for the given season number.
        """

        return f'S{episode_info.season_number}'


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # If no title text, return empty commands
        if len(self.title_text) == 0:
            return []

        # Determine x position of text based on player positon
        MARGIN = 50 # - | + orientation
        if self.player_position == 'left':
            x = self.player_inset + MARGIN
        elif self.player_position == 'middle':
            x = (self.WIDTH - self.player_width) / 2 + MARGIN
        elif self.player_position == 'right':
            x = self.WIDTH - self.player_width - self.player_inset + MARGIN

        # Determine y position based on whether a subtitle is present
        y = (240 if self.subtitle else 195) + self.font_vertical_shift

        return [
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {60 * self.font_size}',
            f'-interline-spacing {-10 + self.font_interline_spacing:+}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-kerning {1 * self.font_kerning}',
            f'-gravity southwest',
            f'-annotate +{x}+{y} "{self.title_text}"',
        ]


    @property
    def _title_dimensions(self) -> Dimensions:
        """
        Dimensions of the title text. This value is only calculated
        once.
        """

        # Already calculated, return
        if self.__title_dimensions is not None:
            return self.__title_dimensions

        # No title text, return 0
        if len(self.title_text) == 0:
            return Dimensions(0, 0)

        self.__title_dimensions = self.image_magick.get_text_dimensions(
            self.title_text_commands
        )

        return self.__title_dimensions


    @property
    def subtitle_commands(self) -> ImageMagickCommands:
        """Subcommands to add the subtitle to the image."""

        # No subtitle, return empty command
        if not self.subtitle:
            return []

        # Determine x position of text based on player positon
        MARGIN = 53 # - | + orientation
        if self.player_position == 'left':
            x = self.player_inset + MARGIN
        elif self.player_position == 'middle':
            x = (self.WIDTH - self.player_width) / 2 + MARGIN
        elif self.player_position == 'right':
            x = self.WIDTH - self.player_width - self.player_inset + MARGIN

        return [
            f'-font "{self.SUBTITLE_FONT.resolve()}"',
            f'-fill {self.episode_text_color}',
            f'-pointsize 32',
            f'-interline-spacing 0',
            f'-interword-spacing 0',
            f'-gravity southwest',
            f'-annotate +{x}+185 "{self.subtitle}"',
        ]


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
        y = (self.HEIGHT / 2) - self.player_inset - self._LINE_Y_INSET

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


    @property
    def _album_dimensions(self) -> Dimensions:
        """
        Post-resize dimensions of the album cover. This accounts for all
        constrains and manual scaling. If the cover is not specified or
        does not exist, then `Dimensions(0, 0)` are returned.
        """

        if self.__album_dimensions is not None:
            return self.__album_dimensions

        if (self.player_style == 'basic'
            or not self.album_cover
            or not self.album_cover.exists()):
            return Dimensions(0, 0)

        # Max dimensions for the file post-resize
        max_height = {
            'artwork': 300, 'logo': 250, 'poster': 400,
        }[self.player_style] * self.album_size
        max_width = self.player_width - (35 * 2) # 35px margin on both sides

        # Get starting dimensions
        album_w, album_h = self.image_magick.get_image_dimensions(
            self.album_cover
        )

        # -resize {max_width}x
        scaled_w = max_width
        scaled_h = album_h * (scaled_w / album_w)

        # -resize x{max_height}>
        downsize = max_height / scaled_h if scaled_h > max_height else 1.0

        # Effective dimensions post any scaling
        self.__album_dimensions = Dimensions(
            scaled_w * downsize, scaled_h * downsize
        )

        return self.__album_dimensions


    @property
    def add_album_cover(self) -> ImageMagickCommands:
        """"""

        if (self.player_style == 'basic' 
            or not self.album_cover or not self.album_cover.exists()):
            return []

        # Dimensions of the album cover
        dimensions = self._album_dimensions

        # y-coorindate is adjusted by whether a subtitle is present and text height
        y = (35 if self.subtitle else 0) + self._title_dimensions.height \
            + self.font_vertical_shift + 250

        # Coordinates for composing the cover
        if self.player_position == 'left':
            x = -(self.WIDTH / 2) + self.player_inset + (self.player_width / 2)
        elif self.player_position == 'middle':
            x = 0
        else: # right
            x = (self.WIDTH - self.player_width) / 2 - self.player_inset

        # Base commands to add and resize the image
        base_commands = [
            f'-gravity south',
            f'\( "{self.album_cover.resolve()}"',
            f'-resize {dimensions.width}x',
            f'-resize x{dimensions.height}\>',
            f'\)',
        ]

        # ABoth artwork and poster can have rounded corners, and use drop shadow
        if self.player_style in ('artwork', 'poster'):
            # If rounding corners, create temp file with rounded asset
            if self.round_corners:
                rounded_file = self.image_magick.round_image_corners(
                    self.album_cover, base_commands, dimensions, radius=25,
                )
                self.__cleanup.append(rounded_file)
                base_commands[1] = f'\( "{rounded_file.resolve()}"'

            return self.add_drop_shadow(
                base_commands,
                Shadow(opacity=80, sigma=5, x=10, y=10),
                x=x, y=y
            )

        if self.player_style == 'logo':
            return [
                *base_commands,
                f'-geometry {x:+}{y:+}',
                f'-composite',
            ]

        return []


    @property
    def glass_command(self) -> ImageMagickCommands:
        """
        Subcommands to add the "glass" effect to the image. This is
        positioned dynamically based on the indicated player position,
        and is scaled to accomodate the height of all content.
        """

        # Start in the top left corner; determine x coordinate
        if self.player_position == 'left':
            start_x = self.player_inset
        elif self.player_position == 'middle':
            start_x = (self.WIDTH - self.player_width) / 2
        elif self.player_position == 'right':
            start_x = self.WIDTH - self.player_inset - self.player_width

        # Determine height
        MARGIN = 35 if self.player_style == 'basic' else 50
        height = self._album_dimensions.height + self._title_dimensions.height \
            + (35 if self.subtitle else 0) + 150 + (2 * MARGIN)
        start = Coordinate(
            start_x,
            self.HEIGHT - self.player_inset - height
        )
        end = start + (self.player_width, height)

        return [
            # Blur rectangle in the given bounds
            f'\( -clone 0',
            f'-fill white',
            f'-colorize 100',
            f'-fill black',
            f'-draw "roundrectangle {start.x},{start.y} {end.x},{end.y} 25,25"',
            f'-alpha off',
            f'-write mpr:mask',
            f'+delete \)',
            f'-mask mpr:mask',
            f'-blur {self.GLASS_BLUR_PROFILE}',
            f'+mask',
            # Draw glass shape
            f'-fill "{self.player_color}"',
            f'-draw "roundrectangle {start.x},{start.y} {end.x},{end.y} 25,25"',
        ]


    @property
    def draw_timeline(self) -> ImageMagickCommands:
        """
        Subcommands to draw the timeline onto the image. This includes
        the background and foreground lines, as well as the player
        circle. The width of the timeline is dynamic with the glass
        width and is filled according to the indicated percentage.
        """

        # Margin between text and the line boundaries
        SPACING_MARGIN = 15

        # Determine coordinates for the background timeline
        background_start_x, background_end_x = self.__season_x, self.__episode_x

        # Center y-coordinate for all lines
        y = self.HEIGHT - self.player_inset - self._LINE_Y_INSET - 3 # 3px offset

        # No season text, draw from standard offset
        if background_start_x is None:
            background_start_x: float = {
                'left': self.player_inset + 105,
                'middle': (self.WIDTH - self.player_width) / 2 + 105,
                'right': self.WIDTH - self.player_inset - self.player_width + 105,
            }[self.player_position]
        # There is season text, remove previous gravity offset
        else:
            background_start_x = self.WIDTH - background_start_x +SPACING_MARGIN

        # No episode text, draw from standard offset
        if background_end_x is None:
            background_end_x: float = {
                'left': self.player_inset + self.player_width - 105,
                'middle': (self.WIDTH + self.player_width) / 2 - 105,
                'right': self.WIDTH - self.player_inset - 105,
            }[self.player_position]
        # There is episode text, add margin
        else:
            background_end_x = background_end_x - SPACING_MARGIN

        background_start = Coordinate(background_start_x, y - (6 / 2))
        background_end = Coordinate(background_end_x, y + (6 / 2))

        # Determine coordinates of the filled in timeline
        foreground_end_x = ((background_end_x - background_start_x) \
            * self.percentage) + background_start_x
        foreground_start = Coordinate(background_start_x, y - (7 / 2))
        foreground_end = Coordinate(foreground_end_x, y + (7 /2))

        # Circle at the end of the filled timeline
        circle_center = Coordinate(foreground_end_x, y)

        return [
            # Draw background timeline
            f'-fill "{self.BACKGROUND_LINE_COLOR}"',
            f'-stroke none',
            f'-strokewidth 0',
            Rectangle(background_start, background_end).draw(),
            f'-fill "{self.timeline_color}"',
            Rectangle(foreground_start, foreground_end).draw(),
            # Circle at the end of the filled timeline
            f'-draw "translate {circle_center} circle 0,0 15,0"',
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
            or ((font.color != MusicTitleCard.TITLE_COLOR)
            or (font.file != MusicTitleCard.TITLE_FONT)
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

        standard_etf = MusicTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """Create this object's defined Title Card."""

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            f'-density 100',
            # Resize and apply styles to source image
            *self.resize_and_style,

            *self.glass_command,
            *self.add_album_cover,
            *self.title_text_commands,
            *self.subtitle_commands,
            *self.index_text_commands,
            *self.draw_timeline,

            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
        self.image_magick.delete_intermediate_images(*self.__cleanup)
