from pathlib import Path
from typing import Literal, Optional, TYPE_CHECKING

from modules.BaseCardType import (
    BaseCardType, Coordinate, ImageMagickCommands, Rectangle, Shadow,
)
from modules.Debug import log

if TYPE_CHECKING:
    from modules.PreferenceParser import PreferenceParser
    from modules.Font import Font

Element = Literal['index', 'logo', 'omit', 'title']
MiddleElement = Literal['logo', 'omit']


class TintedFrameTitleCard(BaseCardType):
    """
    CardType that produces title cards featuring a rectangular frame
    with blurred content on the edges of the frame, and unblurred
    content within. The frame itself can be intersected by title text,
    index text, or a logo at the top and bottom.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'tinted_frame'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 42,
        'max_line_count': 2,
        'top_heavy': 'even',
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
    ARCHIVE_NAME = 'Tinted Frame Style'

    """Implementation details"""
    BOX_OFFSET = 185
    BOX_WIDTH = 5
    SHADOW_COLOR = 'black'


    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_file',
        'font_size', 'font_color', 'font_interline_spacing',
        'font_interword_spacing', 'font_kerning', 'font_vertical_shift',
        'blur_edges', 'bottom_element', 'episode_text_color',
        'episode_text_font', 'episode_text_font_size',
        'episode_text_vertical_shift', 'frame_color', 'frame_width', 'logo',
        'logo_size', 'logo_vertical_shift', 'middle_element', 'separator',
        'shadow_color', 'top_element',
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
            season_number: int = 1,
            episode_number: int = 1,
            blur: bool = False,
            grayscale: bool = False,
            separator: str = '-',
            episode_text_color: str = None,
            episode_text_font: Path = EPISODE_TEXT_FONT,
            episode_text_font_size: float = 1.0,
            episode_text_vertical_shift: int = 0,
            frame_color: str = None,
            frame_width: int = BOX_WIDTH,
            top_element: Element = 'title',
            middle_element: MiddleElement = 'omit',
            bottom_element: Element = 'index',
            logo: str = None,
            logo_size: float = 1.0,
            logo_vertical_shift: int = 0,
            shadow_color: str = SHADOW_COLOR,
            blur_edges: bool = True,
            preferences: Optional['PreferenceParser'] = None,
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

        self.blur_edges = blur_edges
        if episode_text_color is None:
            self.episode_text_color = font_color
        else:
            self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.episode_text_vertical_shift = episode_text_vertical_shift
        self.frame_color = font_color if frame_color is None else frame_color
        self.frame_width = frame_width
        self.logo_size = logo_size
        self.separator = separator
        self.shadow_color = shadow_color

        # If a logo was provided, convert to Path object
        if logo is None:
            self.logo = None
        else:
            try:
                self.logo = Path(
                    str(logo).format(
                        season_number=season_number,
                        episode_number=episode_number
                    )
                )
            except Exception as e:
                log.exception(f'Logo path is invalid', e)
                self.valid = False

        # Validate top, middle, and bottom elements
        def _validate_element(element: str, middle: bool = False) -> str:
            element = str(element).strip().lower()
            if middle and element not in ('omit', 'logo'):
                log.warning(f'Invalid element - must be "omit" or "logo')
                self.valid = False
            elif (not middle
                and element not in ('omit', 'title', 'index', 'logo')):
                log.warning(f'Invalid element - must be "omit", "title", '
                            f'"index", or "logo"')
                self.valid = False
            return element
        self.top_element = _validate_element(top_element)
        self.middle_element = _validate_element(middle_element, middle=True)
        self.bottom_element = _validate_element(bottom_element)

        # Validate no duplicate elements were indicated
        if ((self.top_element != 'omit'
            and (self.top_element == self.middle_element
                 or self.top_element == self.bottom_element))
            or (self.middle_element != 'omit'
                and self.middle_element == self.bottom_element)):
            log.warning(f'Top/middle/bottom elements cannot be the same')
            self.valid = False

        # If logo was indicated, verify logo was provided
        if (self.logo is None
            and ('logo' in (self.top_element, self.middle_element,
                            self.bottom_element))):
            log.warning(f'Logo file not provided')
            self.valid = False

        try:
            self.episode_text_font = Path(episode_text_font)
        except Exception as exc:
            log.exception(f'Invalid episode text font', exc)
            self.valid = False
        self.logo_vertical_shift = logo_vertical_shift


    @property
    def blur_commands(self) -> ImageMagickCommands:
        """
        Subcommand to blur the outer frame of the source image (if
        indicated).
        """

        # Blurring is disabled (or being applied globally), return empty command
        if not self.blur_edges or self.blur:
            return []

        crop_width = self.WIDTH - (2 * self.BOX_OFFSET) - 6 # 6px margin
        crop_height = self.HEIGHT - (2 * self.BOX_OFFSET) - 4 # 4px margin

        return [
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
        ]


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommand for adding title text to the source image."""

        # No title text, or not being shown
        if (len(self.title_text) == 0
            or (self.top_element != 'title' and self.bottom_element !='title')):
            return []

        # Determine vertical position based on which element the title is
        if self.top_element == 'title':
            vertical_shift = -700 + self.font_vertical_shift
        else:
            vertical_shift = 722 + self.font_vertical_shift

        return self.add_drop_shadow(
            [
                f'-background transparent',
                f'-font "{self.font_file}"',
                f'-pointsize {100 * self.font_size}',
                f'-kerning {1 * self.font_kerning}',
                f'-interline-spacing {self.font_interline_spacing}',
                f'-interword-spacing {self.font_interword_spacing}',
                f'-fill "{self.font_color}"',
                f'label:"{self.title_text}"',
            ],
            Shadow(opacity=85, sigma=3, x=8, y=8),
            x=0, y=vertical_shift,
            shadow_color=self.shadow_color,
        )


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommand for adding index text to the source image."""

        # If not showing index text, or all text is hidden, return
        if ((self.top_element != 'index' and self.bottom_element != 'index')
            or (self.hide_season_text and self.hide_episode_text)):
            return []

        # Set index text based on which text is hidden/not
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text} {self.separator} {self.episode_text}'

        # Determine vertical position based on which element this text is
        if self.top_element == 'index':
            vertical_shift = -705
        else:
            vertical_shift = 722
        vertical_shift += self.episode_text_vertical_shift

        return self.add_drop_shadow(
            [
                f'-background transparent',
                f'-font "{self.episode_text_font.resolve()}"',
                f'+kerning +interline-spacing +interword-spacing',
                f'-pointsize {60 * self.episode_text_font_size}',
                f'-fill "{self.episode_text_color}"',
                f'label:"{index_text}"',
            ],
            Shadow(opacity=85, sigma=3, x=6, y=6),
            x=0, y=vertical_shift, shadow_color=self.shadow_color,
        )


    @property
    def logo_commands(self) -> ImageMagickCommands:
        """
        Subcommand for adding the logo to the image if indicated by
        either extra (and the logo file exists).
        """

        # Logo not indicated or not available, return empty commands
        if ((self.top_element != 'logo'
             and self.middle_element != 'logo'
             and self.bottom_element != 'logo')
            or self.logo is None or not self.logo.exists()):
            return []

        # Determine vertical position based on which element the logo is
        if self.top_element == 'logo':
            vertical_shift = -720
        elif self.middle_element == 'logo':
            vertical_shift = 0
        elif self.bottom_element == 'logo':
            vertical_shift = 700
        else:
            vertical_shift = 0
        vertical_shift += self.logo_vertical_shift

        # Determine logo height
        if self.middle_element == 'logo':
            logo_height = 350 * self.logo_size
        else:
            logo_height = 150 * self.logo_size

        # Determine resizing for the logo
        if self.middle_element == 'logo':
            # Constrain by width and height
            resize_command = [
                f'-resize x{logo_height}',
                f'-resize {2500 * self.logo_size}x{logo_height}\>',
            ]
        else:
            resize_command = [f'-resize x{logo_height}']

        return self.add_drop_shadow(
            [
                f'\( "{self.logo.resolve()}"',
                *resize_command,
                f'\) -gravity center',
            ],
            shadow=Shadow(opacity=85, sigma=4),
            x=0, y=vertical_shift,
        )


    @property
    def _frame_top_commands(self) -> ImageMagickCommands:
        """
        Subcommand to add the top of the frame, intersected by the
        selected element.
        """

        # Coordinates used by multiple rectangles
        INSET = self.BOX_OFFSET
        BOX_WIDTH = self.frame_width
        TopLeft = Coordinate(INSET, INSET)
        TopRight = Coordinate(self.WIDTH - INSET, INSET + BOX_WIDTH)

        # This frame is uninterrupted, draw single rectangle
        if (self.top_element == 'omit'
            or (self.top_element == 'index'
                and self.hide_season_text and self.hide_episode_text)
            or (self.top_element == 'logo'
                and (self.logo is None or not self.logo.exists()))
            or (self.top_element == 'title' and len(self.title_text) == 0)):

            return [Rectangle(TopLeft, TopRight).draw()]

        # Element is index text
        if self.top_element == 'index':
            element_width, _ = self.image_magick.get_text_dimensions(
                self.index_text_commands, width='max',
            )
            margin = 25
        # Element is logo
        elif self.top_element == 'logo':
            element_width, logo_height = self.image_magick.get_image_dimensions(
                self.logo
            )
            element_width /= (logo_height / 150)
            element_width *= self.logo_size
            margin = 25
        # Element is title text
        elif self.top_element == 'title':
            element_width, _ = self.image_magick.get_text_dimensions(
                self.title_text_commands, width='max',
            )
            margin = 10

        # Determine bounds based on element width
        left_box_x = (self.WIDTH / 2) - (element_width / 2) - margin
        right_box_x = (self.WIDTH / 2) + (element_width / 2) + margin

        # If the boundaries are wider than the start of the frame, draw nothing
        if left_box_x < INSET or right_box_x > (self.WIDTH - INSET):
            return []

        # Create Rectangles for these two frame sections
        top_left_rectangle = Rectangle(
            TopLeft,
            Coordinate(left_box_x, INSET + BOX_WIDTH)
        )
        top_right_rectangle = Rectangle(
            Coordinate(right_box_x, INSET),
            TopRight,
        )

        return [
            top_left_rectangle.draw(),
            top_right_rectangle.draw()
        ]


    @property
    def _frame_bottom_commands(self) -> ImageMagickCommands:
        """
        Subcommand to add the bottom of the frame, intersected by the
        selected element.
        """

        # Coordinates used by multiple rectangles
        INSET = self.BOX_OFFSET
        BOX_WIDTH = self.frame_width
        # BottomLeft = Coordinate(INSET + BOX_WIDTH, self.HEIGHT - INSET)
        BottomRight = Coordinate(self.WIDTH - INSET, self.HEIGHT - INSET)

        # This frame is uninterrupted, draw single rectangle
        if (self.bottom_element == 'omit'
            or (self.bottom_element == 'index'
                and self.hide_season_text and self.hide_episode_text)
            or (self.bottom_element == 'logo'
                and (self.logo is None or not self.logo.exists()))
            or (self.bottom_element == 'title' and len(self.title_text) == 0)):

            return [
                Rectangle(
                    Coordinate(INSET, self.HEIGHT - INSET - BOX_WIDTH),
                    BottomRight
                ).draw()
            ]

        # Element is index text
        if self.bottom_element == 'index':
            element_width, _ = self.image_magick.get_text_dimensions(
                self.index_text_commands, width='max',
            )
            margin = 25
        # Element is logo
        elif self.bottom_element == 'logo':
            element_width, logo_height = self.image_magick.get_image_dimensions(
                self.logo
            )
            element_width /= (logo_height / 150)
            element_width *= self.logo_size
            margin = 25
        # Element is title
        elif self.bottom_element == 'title':
            element_width, _ = self.image_magick.get_text_dimensions(
                self.title_text_commands, width='max',
            )
            margin = 10

        # Determine bounds based on element width
        left_box_x = (self.WIDTH / 2) - (element_width / 2) - margin
        right_box_x = (self.WIDTH / 2) + (element_width / 2) + margin

        # If the boundaries are wider than the start of the frame, draw nothing
        if left_box_x < INSET or right_box_x > (self.WIDTH - INSET):
            return []

        # Create Rectangles for these two frame sections
        bottom_left_rectangle = Rectangle(
            Coordinate(INSET, self.HEIGHT - INSET - BOX_WIDTH),
            Coordinate(left_box_x, self.HEIGHT - INSET)
        )
        bottom_right_rectangle = Rectangle(
            Coordinate(right_box_x, self.HEIGHT - INSET - BOX_WIDTH),
            BottomRight,
        )

        return [
            bottom_left_rectangle.draw(),
            bottom_right_rectangle.draw(),
        ]


    @property
    def frame_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add the box that separates the outer (blurred)
        image and the interior (unblurred) image. This box features a
        drop shadow. The top and bottom parts of the frame are
        optionally intersected by a index text, title text, or a logo.
        """

        # Coordinates used by multiple rectangles
        INSET = self.BOX_OFFSET
        BOX_WIDTH = self.frame_width
        TopLeft = Coordinate(INSET, INSET)
        # TopRight = Coordinate(self.WIDTH - INSET, INSET + BOX_WIDTH)
        BottomLeft = Coordinate(INSET + BOX_WIDTH, self.HEIGHT - INSET)
        BottomRight = Coordinate(self.WIDTH - INSET, self.HEIGHT - INSET)

        # Determine frame draw commands
        top = self._frame_top_commands
        left = [Rectangle(TopLeft, BottomLeft).draw()]
        right = [
            Rectangle(
                Coordinate(self.WIDTH - INSET - BOX_WIDTH, INSET),
                BottomRight,
            ).draw()
        ]
        bottom = self._frame_bottom_commands

        return self.add_drop_shadow(
            [
                f'-size {self.TITLE_CARD_SIZE}',
                f'xc:transparent',
                # Draw all sets of rectangles
                f'-fill "{self.frame_color}"',
                *top, *left, *right, *bottom,
            ],
            Shadow(opacity=85, sigma=3, x=4, y=4),
            x=0, y=0,
            shadow_color=self.shadow_color,
        )


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
                extras['episode_text_color'] =\
                    TintedFrameTitleCard.EPISODE_TEXT_COLOR
            if 'episode_text_font' in extras:
                extras['episode_text_font'] =\
                    TintedFrameTitleCard.EPISODE_TEXT_FONT
            if 'episode_text_font_size' in extras:
                extras['episode_text_font_size'] = 1.0
            if 'episode_text_vertical_shift' in extras:
                extras['episode_text_vertical_shift'] = 0
            if 'frame_color' in extras:
                extras['frame_color'] = TintedFrameTitleCard.TITLE_COLOR
            if 'shadow_color' in extras:
                extras['shadow_color'] = TintedFrameTitleCard.SHADOW_COLOR


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
            ('episode_text_color' in extras
                and extras['episode_text_color'] != TintedFrameTitleCard.EPISODE_TEXT_COLOR)
            or ('episode_text_font' in extras
                and extras['episode_text_font'] != TintedFrameTitleCard.EPISODE_TEXT_FONT)
            or ('episode_text_font_size' in extras
                and extras['episode_text_font_size'] != 1.0)
            or ('episode_text_vertical_shift' in extras
                and extras['episode_text_vertical_shift'] != 0)
            or ('frame_color' in extras
                and extras['frame_color'] != TintedFrameTitleCard.TITLE_COLOR)
            or ('shadow_color' in extras
                and extras['shadow_color'] != TintedFrameTitleCard.SHADOW_COLOR)
        )

        return (custom_extras
            or ((font.color != TintedFrameTitleCard.TITLE_COLOR)
            or (font.file != TintedFrameTitleCard.TITLE_FONT)
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

        standard_etf = TintedFrameTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """Create this object's defined Title Card."""
        
        # Error and exit if logo is specified and DNE
        if ('logo' in (self.top_element, self.middle_element, self.bottom_element)
            and (self.logo is None or not self.logo.exists())):
            log.error(f'Logo file "{self.logo}" does not exist')
            return None

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Add blurred edges (if indicated)
            *self.blur_commands,
            # Add remaining sub-components
            *self.logo_commands,
            *self.title_text_commands,
            *self.index_text_commands,
            *self.frame_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
