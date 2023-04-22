from pathlib import Path
from typing import Any, Literal, Optional, Union

from modules.BaseCardType import BaseCardType, ImageMagickCommands
from modules.Debug import log

SeriesExtra = Optional

class Coordinate:
    __slots__ = ('x', 'y')

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __str__(self) -> str:
        return f'{self.x:.0f},{self.y:.0f}'

class Rectangle:
    __slots__ = ('start', 'end')

    def __init__(self, start: Coordinate, end: Coordinate) -> None:
        self.start = start
        self.end = end

    def __str__(self) -> str:
        return f'rectangle {str(self.start)},{str(self.end)}'

    def draw(self) -> str:
        return f'-draw "{str(self)}"'


class TintedFrameTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards featuring
    a rectangular frame with blurred content on the edges of the box,
    and unblurred content within. The box itself is intersected by the
    title text on top of the image; and on the bottom with a logo or
    season/episode text.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'tinted_frame'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 35,   # Character count to begin splitting titles
        'max_line_count': 2,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses top heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Galey Semi Bold.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = TITLE_COLOR
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Galey Semi Bold.ttf'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Blurred Box Style'

    """How many pixels from the image edge the box is placed; and box width"""
    BOX_OFFSET = 185
    BOX_WIDTH = 3

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_file',
        'font_size', 'font_color', 'font_interline_spacing', 'font_kerning',
        'font_vertical_shift', 'episode_text_color', 'separator', 'box_color',
        'logo', 'bottom_element',
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
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            episode_text_color: SeriesExtra[str] = EPISODE_TEXT_COLOR,
            separator: SeriesExtra[str] = '-',
            box_color: SeriesExtra[str] = None,
            bottom_element: SeriesExtra[Literal['logo', 'omit', 'text']] = 'text',
            logo: SeriesExtra[str] = None,
            preferences: 'Preferences' = None,
            **unused) -> None:
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
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.episode_text_color = episode_text_color
        self.separator = separator
        self.box_color = font_color if box_color is None else box_color

        # If a logo was provided, convert to Path object
        if logo is None:
            self.logo = None
        else:
            try:
                self.logo = Path(logo)
            except:
                log.exception(f'Logo path is invalid', e)
                self.valid = False

        # Validate bottom element extra
        if bottom_element not in (None, 'omit', 'text', 'logo'):
            log.warning(f'Invalid "bottom_element" - must be "omit", "text", or'
                        f'"logo"')
            self.valid = False

        # If logo was indicated, verify logo was provided
        self.bottom_element = bottom_element
        if bottom_element == 'logo':
            if self.logo is None:
                log.warning(f'Logo not provided')
                self.valid = False
            else:
                self.bottom_element = 'logo'


    @property
    def title_text_command(self) -> ImageMagickCommands:
        """
        Subcommand for adding title text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        if len(self.title_text) == 0:
            return []

        return [
            f'-background transparent',
            f'\( -font "{self.font_file}"',
            f'-pointsize {100 * self.font_size}',
            f'-kerning {1 * self.font_kerning}',
            f'-interline-spacing {0 + self.font_interline_spacing}',
            f'-fill "{self.font_color}"',
            f'label:"{self.title_text}"',
            # Create drop shadow
            f'\( +clone',
            f'-shadow 80x3+10+10 \)',
            # Position shadow below text
            f'+swap',
            f'-layers merge',
            f'+repage \)',
            # Overlay text and shadow onto source image
            f'-geometry +0-{700 + self.font_vertical_shift}',
            f'-composite',
        ]


    @property
    def index_text_command(self) -> ImageMagickCommands:
        """
        Subcommand for adding index text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # If the bottom element is not text, or all text is hidden, return
        if (self.bottom_element != 'text'
            or (self.hide_season_text and self.hide_episode_text)):
            return []

        # Set index text based on which text is hidden/not
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text} {self.separator} {self.episode_text}'

        return [
            f'-background transparent',
            f'\( -font "{self.EPISODE_TEXT_FONT}"',
            f'-pointsize {60}',
            f'-fill "{self.episode_text_color}"',
            f'label:"{index_text}"',
            # Create drop shadow
            f'\( +clone',
            f'-shadow 80x3+6+6 \)',
            # Position shadow below text
            f'+swap',
            f'-layers merge',
            f'+repage \)',
            # Overlay text and shadow onto source image
            f'-gravity center',
            f'-geometry +0+722',
            f'-composite',
        ]

    
    @property
    def logo_command(self) -> ImageMagickCommands:
        """
        Subcommand for adding the logo to the image if indicated by the
        bottom element extra (and the logo file exists).

        Returns:
            List of ImageMagick commands.
        """

        # Logo not indicated or not available, return empty commands
        if (self.bottom_element != 'logo'
            or self.logo is None or not self.logo.exists()):
            return []

        return [
            f'\( "{self.logo.resolve()}"',
            f'-resize x150 \)',
            f'-gravity center',
            f'-geometry +0+700',
            f'-composite',
        ]


    @property
    def box_command(self) -> ImageMagickCommands:
        """
        Subcommand to add the box that separates the outer (blurred)
        image and the interior (unblurred) image. This box features a
        drop shadow. The top part of the box is intersected by the title
        text (if present), and the bottom part can be intersected by the
        index text, logo, or not at all.

        Returns:
            List of ImageMagick commands.
        """

        INSET = self.BOX_OFFSET
        BOX_WIDTH = self.BOX_WIDTH

        # Coordinates used by multiple rectangles
        TopLeft = Coordinate(INSET, INSET)
        TopRight = Coordinate(self.WIDTH - INSET, INSET + BOX_WIDTH)
        BottomLeft = Coordinate(INSET + BOX_WIDTH, self.HEIGHT - INSET)
        BottomRight = Coordinate(self.WIDTH - INSET, self.HEIGHT - INSET)

        # Determine top box draw commands
        if len(self.title_text) == 0:
            top_rectangle = Rectangle(TopLeft, TopRight)
            top = [top_rectangle.draw()]
        else:
            title_width, _ = self.get_text_dimensions(
                self.title_text_command, width='max', height='max',
            )
            left_box_x = (self.WIDTH / 2) - (title_width / 2) - 10
            right_box_x = (self.WIDTH / 2) + (title_width / 2) + 10

            top_left_rectangle = Rectangle(
                TopLeft,
                Coordinate(left_box_x, INSET + BOX_WIDTH)
            )
            top_right_rectangle = Rectangle(
                Coordinate(right_box_x, INSET),
                TopRight,
            )

            top = [top_left_rectangle.draw(), top_right_rectangle.draw()]

        # Left and right rectangles are never intersected by content
        left_rectangle = Rectangle(TopLeft, BottomLeft)
        left = [left_rectangle.draw()]
        right_rectangle = Rectangle(
            Coordinate(self.WIDTH - INSET - BOX_WIDTH, INSET),
            BottomRight,
        )
        right = [right_rectangle.draw()]

        # Determine bottom box draw commands
        # No bottom element, use singular full-width rectangle
        if self.bottom_element == 'omit':
            bottom_rectangle = Rectangle(
                Coordinate(INSET, self.HEIGHT - INSET - BOX_WIDTH),
                BottomRight
            )
            bottom = [bottom_rectangle.draw()]
        # Bottom element is logo, use boxes based on resized logo width
        elif (self.bottom_element == 'logo'
            and self.logo is not None
            and self.logo.exists()):
            logo_width, logo_height = self.get_image_dimensions(self.logo)
            logo_width /= logo_height / 150

            left_box_x = (self.WIDTH / 2) - (logo_width / 2) - 25
            right_box_x = (self.WIDTH / 2) + (logo_width / 2) + 25

            bottom_left_rectangle = Rectangle(
                Coordinate(INSET, self.HEIGHT - INSET - BOX_WIDTH),
                Coordinate(left_box_x, self.HEIGHT - INSET),
            )
            bottom_right_rectangle = Rectangle(
                Coordinate(right_box_x, self.HEIGHT - INSET - BOX_WIDTH),
                BottomRight,
            )

            bottom = [
                bottom_left_rectangle.draw(), bottom_right_rectangle.draw()
            ]
        # Bottom element is index text, use boxes based on text width
        elif self.bottom_element == 'text':
            index_text_width, _ = self.get_text_dimensions(
                self.index_text_command, width='max', height='max',
            )
            left_box_x = (self.WIDTH / 2) - (index_text_width / 2) - 25
            right_box_x = (self.WIDTH / 2) + (index_text_width / 2) + 25

            bottom_left_rectangle = Rectangle(
                Coordinate(INSET, self.HEIGHT - INSET - BOX_WIDTH),
                Coordinate(left_box_x, self.HEIGHT - INSET)
            )
            bottom_right_rectangle = Rectangle(
                Coordinate(right_box_x, self.HEIGHT - INSET - BOX_WIDTH),
                BottomRight,
            )
            
            bottom = [
                bottom_left_rectangle.draw(), bottom_right_rectangle.draw()
            ]

        return [
            # Create blank canvas
            f'\( -size {self.TITLE_CARD_SIZE}',
            f'xc:transparent',
            # Draw all sets of rectangles
            f'-fill "{self.box_color}"',
            *top, *left, *right, *bottom,
            f'\( +clone',
            f'-shadow 80x3+4+4 \)',
            # Position drop shadow below rectangles
            f'+swap',
            f'-layers merge',
            f'+repage \)',
            # Overlay box and shadow onto source image
            f'-geometry +0+0',
            f'-composite',
        ]


    @staticmethod
    def modify_extras(
            extras: dict[str, Any],
            custom_font: bool,
            custom_season_titles: bool) -> None:
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
                extras['episode_text_color'] =\
                    TintedFrameTitleCard.EPISODE_TEXT_COLOR
            if 'box_color' in extras:
                extras['box_color'] = TintedFrameTitleCard.TITLE_COLOR


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

        return ((font.color != DividerTitleCard.TITLE_COLOR)
            or (font.file != DividerTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
            or (font.vertical_shift != 0)
        )


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool, episode_text_format: str) -> bool:
        """
        Determine whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        standard_etf = TintedFrameTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        crop_width = self.WIDTH - (2 * self.BOX_OFFSET) - 6 # 6px margin
        crop_height = self.HEIGHT - (2 * self.BOX_OFFSET) - 4 # 4px margin

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Blur entire image
            f'-blur 0x20',
            # Crop out center area of the source image
            f'-gravity center',
            f'\( "{self.source_file.resolve()}"',
            *self.resize_and_style,
            f'-crop {crop_width}x{crop_height}+0+0',
            f'+repage \)',
            # Overlay unblurred center area 
            f'-composite',
            # Add remaining sub-components
            *self.title_text_command,
            *self.index_text_command,
            *self.logo_command,
            *self.box_command,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)