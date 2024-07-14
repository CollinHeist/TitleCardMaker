from pathlib import Path
from random import choice as random_choice
from re import compile as re_compile, IGNORECASE
from typing import Literal, Optional, TYPE_CHECKING

from modules.BaseCardType import (
    BaseCardType, CardDescription, Coordinate, Extra, ImageMagickCommands,
    Rectangle, Shadow,
)
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


RandomColorRegex = re_compile(r'random\[([^[\]]*(?:,[^[\]]*)*)\]', IGNORECASE)
Element = Literal['index', 'logo', 'omit', 'title']
MiddleElement = Literal['logo', 'omit']


class TintedFrameTitleCard(BaseCardType):
    """
    CardType that produces title cards featuring a rectangular frame
    with blurred content on the edges of the frame, and unblurred
    content within. The frame itself can be intersected by title text,
    index text, or a logo at the top and bottom.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Tinted Frame',
        identifier='tinted frame',
        example='/internal_assets/cards/tinted frame.jpg',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color of the season and episode text',
                tooltip='Default is to match the Font color.',
            ),
            Extra(
                name='Episode Text Font',
                identifier='episode_text_font',
                description='Font to use for the season and episode text',
                tooltip=(
                    'This can be just a file name if the font file is in the '
                    "Series' source directory, <v>{title_font}</v> to match "
                    'the Font used for the title text, or a full path to the '
                    'font file.'
                ),
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the season and episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Episode Text Vertical Shift',
                identifier='episode_text_vertical_shift',
                description=(
                    'Additional vertical shift to apply to the season and '
                    'episode text. Default is <v>0</v>.'
                ),
                default=0,
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description=(
                    'Character that separates the season and episode text'
                ),
                tooltip='Default is <v>-</v>.',
                default='-',
            ),
            Extra(
                name='Frame Color',
                identifier='frame_color',
                description='Color of the frame edges',
                tooltip=(
                    'Can be any color or randomized like <v>random[color0, '
                    'color1, ...]</v>  to select a randomly specified color. '
                    'If randomly selecting, colors MUST be comma-separated '
                    'with a space (, ) and any <v>rgb()</v> colors cannot have '
                    'spaces. Default is to match the Font color.'
                ),
            ),
            Extra(
                name='Frame Width',
                identifier='frame_width',
                description='Width of the frame',
                tooltip=(
                    'Number ≥<v>0</v>. Default is <v>5</v>. Unit is pixels.'
                ),
                default=5,
            ),
            Extra(
                name='Top Element',
                identifier='top_element',
                description='Which element to display on the top of the frame',
                tooltip=(
                    'Either <v>index</v> to display the season and episode '
                    'text, <v>logo</v> to display the logo, <v>omit</v> to not '
                    'display anything, or <v>title</v> to display the title '
                    'text. Default is <v>title</v>.'
                ),
                default='title',
            ),
            Extra(
                name='Middle Element',
                identifier='middle_element',
                description='Which element to display in the middle of the frame',
                tooltip=(
                    'Either <v>logo</v> to display the logo, or <v>omit</v> to '
                    'not display anything. Default is <v>omit</v>.'
                ),
                default='omit',
            ),
            Extra(
                name='Bottom Element',
                identifier='bottom_element',
                description='Which element to display on the bottom of the frame',
                tooltip=(
                    'Either <v>index</v> to display the season and episode '
                    'text, <v>logo</v> to display the logo, <v>omit</v> to not '
                    'display anything, or <v>title</v> to display the title '
                    'text. Default is <v>index</v>.'
                ),
                default='index',
            ),
            Extra(
                name='Logo Size',
                identifier='logo_size',
                description=(
                    'Scalar for how much to scale the size of the logo element'
                ),
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Logo Vertical Shift',
                identifier='logo_vertical_shift',
                description='Vertical shift to apply to the logo',
                tooltip=(
                    'Positive values to shift the logo down, negative values to'
                    'shift it up. Unit is pixels. Default is <v>0.0</v>.'
                ),
                default=0.0,
            ),
            Extra(
                name='Edge Blurring',
                identifier='blur_edges',
                description='Whether to blur the edges around the frame',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is '
                    '<v>True</v>.'
                ),
                default='True',
            ),
            Extra(
                name='Shadow Color',
                identifier='shadow_color',
                description='Color of the drop shadow.',
                tooltip='Default is <c>black</c>.',
                default='black',
            ),
        ],
        description=[
            'Title card featuring a rectangular frame with blurred content on '
            'the outside of the frame, and unblurred content within.', 'The '
            'frame and all text can be recolored via extras.', 'Which type of '
            'content is displayed in the top, middle, and bottom of the frame '
            'can also be adjusted independently.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'tinted_frame'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 42,
        'max_line_count': 2,
        'style': 'even',
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

    """How to name archive directories for this type of card"""
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
            logo_file: Optional[Path] = None,
            logo_size: float = 1.0,
            logo_vertical_shift: int = 0,
            shadow_color: str = SHADOW_COLOR,
            blur_edges: bool = True,
            preferences: Optional['Preferences'] = None,
            **unused,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file
        self.logo = logo_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text
        self.hide_episode_text = hide_episode_text

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.blur_edges = blur_edges
        self.bottom_element = bottom_element
        self.episode_text_color = episode_text_color
        self.episode_text_font = episode_text_font
        self.episode_text_font_size = episode_text_font_size
        self.episode_text_vertical_shift = episode_text_vertical_shift
        self.frame_color = self.__select_color(frame_color)
        self.frame_width = frame_width
        self.logo_size = logo_size
        self.logo_vertical_shift = logo_vertical_shift
        self.middle_element = middle_element
        self.separator = separator
        self.shadow_color = shadow_color
        self.top_element = top_element


    def __select_color(self, color_str: str, /) -> str:
        """
        Determine a color from the given string. This will parse random
        strings, as well as explicit ones. For example:

        >>> self.__select_color('random[blue, red]')
        'blue' # Has 50% chance to choose blue or red
        >>> self.__select_color('red')
        'red'

        Args:
            color_str: Color string to parse for colors.

        Returns:
            Selected color as indicated or randomly selected.
        """

        # If color is randomized, select from specification
        if (match := RandomColorRegex.match(color_str)):
            return random_choice(list(map(
                str.strip,
                match.group(1).split(', ')
            )))

        return color_str


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
