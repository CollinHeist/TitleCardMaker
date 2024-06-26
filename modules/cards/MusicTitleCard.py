from pathlib import Path
from random import random
from typing import TYPE_CHECKING, Literal, NamedTuple, Optional, Union

from modules.BaseCardType import (
    BaseCardType, Coordinate, Dimensions, ImageMagickCommands, Rectangle, Shadow
)
from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


class ControlColors(NamedTuple): # pylint: disable=missing-class-docstring
    shuffle: str
    previous: str
    action: str
    next: str
    repeat: str
PlayerAction = Literal['pause', 'play', 'watched']
PlayerPosition = Literal['left', 'middle', 'right']
PlayerStyle = Literal['basic', 'artwork', 'logo', 'poster']


class MusicTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards which are
    styled after a music player. These cards feature a repositionable
    "player" which can display info like the series name, title, as well
    as a timeline, and artwork or a logo.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'music'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 17,
        'max_line_count': 4,
        'top_heavy': False,
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
    DEFAULT_CONTROL_COLORS = ('white', 'white', 'white', 'white', 'white')
    DEFAULT_TIMELINE_COLOR = 'rgb(29,185,84)' # Spotify Green
    DEFAULT_LINE_WIDTH = 9
    DEFAULT_PLAYER_COLOR = 'rgba(0,0,0,0.50)' # Black @ 50% opacity
    DEFAULT_PLAYER_WIDTH = 900
    GLASS_BLUR_PROFILE = '0x12'
    DEFAULT_INSET = 50
    DEFAULT_PLAYER_ACTION: PlayerAction = 'play'
    DEFAULT_PLAYER_POSITION: PlayerPosition = 'left'
    DEFAULT_PLAYER_STYLE: PlayerStyle = 'logo'

    """How far from the bottom of the glass the line is drawn"""
    _LINE_Y_INSET = 71 # 85px originally

    """
    SVG commands for each control element. SVGs made relative with this fiddle
    https://codepen.io/MausWorks/pen/eLrmmY.
    """
    _HEART_SVG = """m0,0c-3.6,-3.6,-9.5,-3.6,-13.2,0l-2.1,2.1l-2.1,-2.1c-3.6,
    -3.6,-9.5,-3.6,-13.2,0c-3.6,3.6,-3.6,9.5,0,13.2l2.1,2.1l13.2,13.2l13.2,
    -13.2l2.1,-2.1c3.7,-3.6,3.7,-9.5,0,-13.2z"""
    _SHUFFLE_SVG = """m0,0c-0.3,-0.2,-0.7,0,-0.7,0.3v3h-5.5c-2.8,0,-4.2,-2,-5.6,
    -4.3c1.3,-2.4,2.8,-4.3,5.6,-4.3h5.5v3.1c0,0.3,0.4,0.5,0.6,0.3l5.8,-4.4c0.2,
    -0.2,0.2,-0.5,0,-0.6l-5.8,-4.4c-0.3,-0.2,-0.6,0,-0.6,0.3v3.6h-5.5c-3.3,0,
    -5.3,2,-6.7,4.3c-1.4,-2.5,-3,-4.9,-6.1,-4.7c-3.7,0.2,-6.8,0,-6.8,0l-0.1,2
    c0.1,0,3.2,0.2,7,0c2.1,-0.1,3.2,1.7,4.7,4.5c0,0.1,0.1,0.1,0.1,0.2c0,0.1,
    -0.1,0.1,-0.1,0.2c-1.6,2.9,-2.6,4.7,-4.7,4.5c-3.8,-0.2,-6.9,0,-7,0l0.1,2c0,
    0,3.1,-0.2,6.8,0c0.1,0,0.2,0,0.3,0c2.9,0,4.5,-2.3,5.8,-4.7c1.4,2.3,3.4,4.3,
    6.7,4.3h5.5v3.6c0,0.4,0.4,0.6,0.7,0.3l5.7,-4.3c0.2,-0.2,0.2,-0.5,0,-0.7
    l-5.7,-4.1z"""
    _PREVIOUS_SVG = """m0,0l-17.1,12.2v-11.3c0,-0.6,-0.4,-1,-1,-1h-4.4c-0.6,0,
    -1,0.4,-1,1v28.5c0,0.6,0.4,1,1,1h4.4c0.6,0,1,-0.4,1,-1v-12.4l17.1,12.2c0.7,
    0.5,1.6,0,1.6,-0.8v-27.7c0,-0.7,-0.9,-1.1,-1.6,-0.7z"""
    _PAUSE_SVG = """m0,0.6c-16.8,0,-30.4,13.6,-30.4,30.4s13.6,30.4,30.4,30.4
    s30.4,-13.6,30.4,-30.4s-13.6,-30.4,-30.4,-30.4zm-4,48.2h-9.2v-34.9h9.2
    v34.9zm16,0h-9.2v-34.9h9.2v34.9z"""
    _PLAY_SVG = """m0,0c-16.8,0,-30.4,13.6,-30.4,30.4s13.6,30.4,30.4,30.4s30.4,
    -13.6,30.4,-30.4s-13.6,-30.4,-30.4,-30.4zm15.5,29.8l-27.1,14.4c-0.5,0.3,
    -1.2,-0.1,-1.2,-0.7v-28.8c0,-0.6,0.7,-1,1.2,-0.7l27.1,14.4c0.6,0.2,0.6,1.1,
    0,1.4z"""
    _NEXT_SVG = """m0,0h-4.7c-0.5,0,-0.8,0.4,-0.8,0.8v11.4l-17.4,-12.3c-0.6,
    -0.4,-1.3,0,-1.3,0.7v28.3c0,0.7,0.8,1.1,1.3,0.7l17.4,-12.4v12.5c0,0.5,0.4,
    0.8,0.8,0.8h4.7c0.5,0,0.8,-0.4,0.8,-0.8v-28.8c0,-0.5,-0.3,-0.9,-0.8,-0.9z"""
    _REPEAT_SVG_1 = """m0,0h11.9v3c0,0.3,0.3,0.4,0.5,0.3l5.2,-3.8c0.2,-0.1,0.2,
    -0.4,0,-0.5l-5.2,-3.8c-0.2,-0.2,-0.5,0,-0.5,0.3v2.8l-11.9,-0.2c-3.9,0,-7.9,
    2.7,-7.9,8.8h2c0,-5.1,3.2,-6.9,5.9,-6.9z"""
    _REPEAT_SVG_2 = """m16.1,7.6c0,5,-3.2,6.8,-5.9,6.8h-11.9v-3c0,-0.3,-0.3,
    -0.4,-0.5,-0.3l-5.2,3.8c-0.2,0.1,-0.2,0.4,0,0.5l5.2,3.8c0.2,0.2,0.5,0,0.5,
    -0.3v-2.9l11.9,0.2c3.9,0,7.9,-2.7,7.9,-8.8h-2z"""


    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_interline_spacing', 'font_interword_spacing', 'font_file',
        'font_kerning', 'font_size', 'font_vertical_shift', 'add_controls',
        'album_cover', 'album_size', 'control_colors', 'draw_heart',
        'episode_text_color', 'heart_color', 'heart_stroke_color',
        'pause_or_play', 'percentage', 'player_color', 'player_inset',
        'player_position', 'player_style', 'player_width', 'round_corners',
        'subtitle', 'timeline_color', '__album_dimensions',
        '__title_dimensions', '__season_x', '__episode_x', '__cleanup',
    )


    @staticmethod
    def SEASON_TEXT_FORMATTER(episode_info: EpisodeInfo) -> str:
        """
        Fallback season title formatter.

        Args:
            episode_info: Info of the Episode whose season text is being
                determined.

        Returns:
            `S{x}` for the given season number.
        """

        return f'S{episode_info.season_number}'


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
            watched: Optional[bool] = None,
            add_controls: bool = False,
            album_cover: Optional[Path] = None,
            album_size: float = 1.0,
            control_colors: str = 'white white white white white',
            draw_heart: bool = False,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            heart_color: str = 'transparent',
            heart_stroke_color: str = 'white',
            pause_or_play: PlayerAction = DEFAULT_PLAYER_ACTION,
            percentage: Union[float, Literal['random']] = 'random',
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
        self.season_text = self.image_magick.escape_chars(season_text.upper())
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())
        self.hide_season_text = hide_season_text or not season_text
        self.hide_episode_text = hide_episode_text or not episode_text

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = -10 + font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        # Default font is +15px from bottom; add 10px margin
        self.font_vertical_shift = -15 + 10 + font_vertical_shift

        # Extras
        self.add_controls = add_controls
        if self.add_controls and player_width < 600:
            log.error(f'Controls can only be added if player_width is at least'
                      f'600')
            self.valid = False

        self.album_cover = None
        if album_cover and isinstance(album_cover, str):
            if Path(album_cover).exists():
                self.album_cover = Path(album_cover)
            elif (cover := (self.source_file.parent / str(album_cover))).exists():
                self.album_cover = album_cover
        elif isinstance(album_cover, Path):
            self.album_cover = album_cover

        self.album_size = album_size
        if len((control_colors := control_colors.split(' '))) == 5:
            self.control_colors = ControlColors(*control_colors)
        else:
            log.error(f'control_colors must be specified as five space-'
                      f'separated colors - e.g. "red white white white red"')
            self.valid = False
        self.draw_heart = draw_heart
        self.episode_text_color = episode_text_color
        self.heart_color = heart_color
        self.heart_stroke_color = heart_stroke_color
        if (pause_or_play := pause_or_play.lower()) == 'watched':
            if watched is None:
                self.pause_or_play = self.DEFAULT_PLAYER_ACTION
            else:
                self.pause_or_play = 'pause' if watched else 'play'
        else:
            self.pause_or_play = pause_or_play
        self.percentage = random() if percentage == 'random' else percentage
        self.player_color = player_color
        self.player_inset = player_inset
        if not (0 <= self.player_inset <= 1200):
            log.error(f'player_inset must be between 0 and 1200')
            self.valid = False
        self.player_position: PlayerPosition = player_position.lower()
        if self.player_position not in ('left', 'middle', 'right'):
            log.error(f'player_position must be "left", "middle", or "right"')
            self.valid = False
        self.player_style: PlayerStyle = player_style.lower()
        if self.player_style not in ('basic', 'artwork', 'logo', 'poster'):
            log.error(f'player_style must be "basic", "artwork", "logo", or '
                      f'"poster"')
            self.valid = False
        self.player_width = player_width
        if not (400 <= self.player_width <= 3000):
            log.error(f'player_width must be between 400 and 3000')
            self.valid = False
        self.round_corners = round_corners
        self.subtitle = subtitle
        self.timeline_color = timeline_color

        if (self.player_style != 'basic'
            and (not isinstance(self.album_cover, Path)
                 or not self.album_cover.exists())):
            log.error(f'album_cover file must be specified and exist if '
                      f'player_style is not "basic"')
            self.valid = False

        # Implementation details
        self.__album_dimensions: Optional[Dimensions] = None
        self.__title_dimensions: Optional[Dimensions] = None
        self.__season_x: Optional[float] = None
        self.__episode_x: Optional[float] = None
        self.__cleanup: list[Path] = []


    @property
    def _control_height(self) -> int:
        return 108 if self.add_controls else 0

    @property
    def _subtitle_height(self) -> int:
        return 60 if self.subtitle else 9

    @property
    def _timeline_height(self) -> int:
        return 106

    @property
    def _title_margin_height(self) -> int:
        return 15

    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # If no title text, return empty commands
        if not self.title_text:
            return []

        # Determine x position of text based on player positon
        MARGIN = 50 # - | + orientation
        if self.player_position == 'left':
            x = self.player_inset + MARGIN
        elif self.player_position == 'middle':
            x = (self.WIDTH - self.player_width) / 2 + MARGIN
        elif self.player_position == 'right':
            x = self.WIDTH - self.player_width - self.player_inset + MARGIN

        y = self.player_inset \
            + self._control_height \
            + self._timeline_height \
            + self._subtitle_height \
            + self.font_vertical_shift

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
            self.title_text_commands,
            density=100,
            interline_spacing=self.font_interline_spacing,
            line_count=len(self.title_text.splitlines()),
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

        y = self.player_inset + self._control_height + self._timeline_height

        return [
            f'-font "{self.SUBTITLE_FONT.resolve()}"',
            f'-fill {self.episode_text_color}',
            f'-pointsize 32',
            f'-interline-spacing 0',
            f'-interword-spacing 0',
            f'-gravity southwest',
            f'-annotate {x:+}{y:+} "{self.subtitle}"',
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
        max_width = self.player_width - (50 * 2) # 50px margin on both sides

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
        """
        Subcommands to add the album cover. This adds the album based on
        the specified player style.
        """

        if (self.player_style == 'basic' or not self.album_cover
            or not self.album_cover.exists()):
            return []

        # Dimensions of the album cover
        dimensions = self._album_dimensions

        # Coordinates for composing the cover
        if self.player_position == 'left':
            x = -(self.WIDTH / 2) + self.player_inset + (self.player_width / 2)
        elif self.player_position == 'middle':
            x = 0
        else: # right
            x = (self.WIDTH - self.player_width) / 2 - self.player_inset

        y = self.player_inset \
            + self._control_height \
            + self._timeline_height \
            + self._subtitle_height \
            + self.font_vertical_shift \
            + self._title_dimensions.height \
            + self._title_margin_height
        # Dist / controls / timeline / subtitle / text diff / title / margin

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
        height = self._control_height \
            + self._timeline_height \
            + self._subtitle_height \
            + self.font_vertical_shift \
            + self._title_dimensions.height \
            + self._title_margin_height \
            + self._album_dimensions.height \
            + (25 if self.player_style == 'basic' else 60)
        # Controls / timeline / subtitle / text diff / title / margin / album / margin

        start = Coordinate(start_x, self.HEIGHT - self.player_inset - height)
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

        # Center y coordinate for all lines
        y = self.HEIGHT - self.player_inset - self._LINE_Y_INSET - 3 # offset
        if self.add_controls:
            y -= self._control_height

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


    @property
    def draw_controls(self) -> ImageMagickCommands:
        """
        Subcommands to draw the media controls on the image. This
        separately draws and colors each control.
        """

        # Controls are not displayed, return empty commands
        if not self.add_controls:
            return []

        # Scale for all SVGs
        scale = 1.75

        # Player center for all controls
        x_mid: float = {
            'left': self.player_inset + (self.player_width / 2),
            'middle': (self.WIDTH / 2),
            'right': self.WIDTH - self.player_inset - (self.player_width / 2),
        }[self.player_position]

        # Center y-coordinate for all lines
        y_mid = self.HEIGHT - self.player_inset - self._LINE_Y_INSET - 14 - 3

        # Start with the left-most controls, work right
        control_commands = [
            f'-stroke none',
            f'-strokewidth 0',
        ]
        if self.control_colors.shuffle.lower() not in ('transparent', 'none'):
            x, y = x_mid - 197, y_mid + 5
            control_commands += [
                f'-fill "{self.control_colors.shuffle}"',
                f'-draw "translate {x:+.0f},{y:+.0f} scale {scale},{scale}',
                f'path \'{self._SHUFFLE_SVG}\'"',
            ]
        if self.control_colors.previous.lower() not in ('transparent', 'none'):
            x, y = x_mid - 100, y_mid - 22
            control_commands += [
                f'-fill "{self.control_colors.previous}"',
                f'-draw "translate {x:+.0f},{y:+.0f} scale {scale},{scale}',
                f'path \'{self._PREVIOUS_SVG}\'"',
            ]
        if self.control_colors.action.lower() not in ('transparent', 'none'):
            if self.pause_or_play == 'pause':
                x, y = x_mid, y_mid - 52
                control_commands += [
                    f'-fill "{self.control_colors.action}"',
                    f'-draw "translate {x:+.0f},{y:+.0f} scale {scale},{scale}',
                    f'path \'{self._PAUSE_SVG}\'"',
                ]
            else:
                x, y = x_mid, y_mid - 51
                control_commands += [
                    f'-fill "{self.control_colors.action}"',
                    f'-draw "translate {x:+.0f},{y:+.0f} scale {scale},{scale}',
                    f'path \'{self._PLAY_SVG}\'"',
                ]
        if self.control_colors.next.lower() not in ('transparent', 'none'):
            x, y = x_mid + 139, y_mid - 23
            control_commands += [
                f'-fill "{self.control_colors.next}"',
                f'-draw "translate {x:+.0f},{y:+.0f} scale {scale},{scale}',
                f'path \'{self._NEXT_SVG}\'"',
            ]
        if self.control_colors.repeat.lower() not in ('transparent', 'none'):
            x, y = x_mid + 210, y_mid - 8
            control_commands += [
                f'-fill "{self.control_colors.repeat}"',
                f'-draw "translate {x:+.0f},{y:+.0f} scale {scale},{scale}',
                f'path \'{self._REPEAT_SVG_1}\'"',
                f'-draw "translate {x:+.0f},{y:+.0f} scale {scale},{scale}',
                f'path \'{self._REPEAT_SVG_2}\'"',
            ]

        return control_commands


    @property
    def draw_heart_commands(self) -> ImageMagickCommands:
        """Subcommands to draw the heart SVG icon on the image."""

        # No heart, return empty commands
        if not self.draw_heart:
            return []

        x: float = {
            'left': self.player_inset + self.player_width,
            'middle': (self.WIDTH + self.player_width) / 2,
            'right': self.WIDTH - self.player_inset,
        }[self.player_position] - 30

        y = self.HEIGHT - self.player_inset \
            - self._control_height \
            - self._timeline_height \
            - self._subtitle_height \
            - self.font_vertical_shift \
            - self._title_dimensions.height \
            - self._title_margin_height \
            - self._album_dimensions.height \
            - (25 if self.player_style == 'basic' else 60) \
            + 28

        return [
            f'-fill "{self.heart_color}"',
            f'-stroke "{self.heart_stroke_color}"',
            f'-strokewidth 2',
            f'-draw "translate {x-7:+.0f},{y+8:+.0f} scale 1.75,1.75',
            f'path \'{self._HEART_SVG}\'"',
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
            if 'control_colors' in extras:
                extras['control_colors'] = MusicTitleCard.DEFAULT_CONTROL_COLORS
            if 'episode_text_color' in extras:
                extras['episode_text_color'] = MusicTitleCard.EPISODE_TEXT_COLOR
            if 'timeline_color' in extras:
                extras['timeline_color'] = MusicTitleCard.DEFAULT_TIMELINE_COLOR


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
            ('control_colors' in extras
                and extras['control_colors'] != MusicTitleCard.DEFAULT_CONTROL_COLORS)
            or ('episode_text_color' in extras
                and extras['episode_text_color'] != MusicTitleCard.EPISODE_TEXT_COLOR)
            or ('timeline_color' in extras
                and extras['timeline_color'] != MusicTitleCard.DEFAULT_TIMELINE_COLOR)
        )

        return custom_extras or MusicTitleCard._is_custom_font(font)


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
                    MusicTitleCard.EPISODE_TEXT_FORMAT.upper())


    def create(self) -> None:
        """Create this object's defined Title Card."""

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            f'-density 100',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Add background player glass
            *self.glass_command,
            # Add the indicated album cover art/logo
            *self.add_album_cover,
            # Add all text
            *self.title_text_commands,
            *self.subtitle_commands,
            *self.index_text_commands,
            # Draw the timeline
            *self.draw_timeline,
            # Draw the media player controls and heart
            *self.draw_controls,
            *self.draw_heart_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
        self.image_magick.delete_intermediate_images(*self.__cleanup)
