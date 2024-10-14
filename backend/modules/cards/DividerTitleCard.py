from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional, Union

from modules.BaseCardType import (
    BaseCardType,
    CardTypeDescription,
    Extra,
    ImageMagickCommands,
    TextCase,
)
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


SeriesExtra = Optional
TextGravity = Literal['center', 'east', 'west']
TitleTextPosition = Literal['left', 'right']
TextPosition = Literal[
    'upper left', 'upper right', 'right', 'lower right', 'lower left', 'left',
]


class DividerTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards
    similar to the AnimeTitleCard (same font), but featuring a vertical
    divider between the season and episode text. This card allows the
    positioning of text on the image to be adjusted. The general design
    was inspired by the title card interstitials in Overlord (season 3).
    """

    """API Parameters"""
    API_DETAILS: CardTypeDescription = CardTypeDescription(
        name='Divider',
        identifier='divider',
        example='/internal_assets/cards/divider.jpg',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Text Gravity',
                identifier='text_gravity',
                description='Alignment of the index text (relative to itself)',
                tooltip=(
                    'Either <v>center</v>, <v>east</v>, or <v>west</v>. '
                    'Default is based on the specified Title Text Position '
                    '(i.e. <v>left</v> is <v>west</v>; <v>right</v> is '
                    '<v>east</v>).'
                ),
            ),
            Extra(
                name='Text Stroke Color',
                identifier='stroke_color',
                description='Color to use for the text stroke',
                tooltip='Default is <c>black</c>.',
                default='black',
            ),
            Extra(
                name='Title Text Position',
                identifier='title_text_position',
                description=(
                    'Which side the title text should be positioned relative '
                    'to the index text'
                ),
                tooltip=(
                    'Either <v>left</v>, or <v>right</v>. Default is '
                    '<v>left</v>.'
                ),
                default='left',
            ),
            Extra(
                name='Text Position',
                identifier='text_position',
                description='Where on the image to position the text',
                tooltip=(
                    'Either <v>upper left</v>, <v>upper right</v>, '
                    '<v>right</v>, <v>lower right</v>, <v>lower left</v>, or '
                    '<v>left</v>. Default is <v>lower right</v>.'
                ),
                default='lower right',
            ),
            Extra(
                name='Divider Color',
                identifier='divider_color',
                description='Color of the divider bar between text',
                tooltip='Default is to match the Font color.',
            )
        ],
        description=[
            'A simple title card featuring the title and index text separated '
            'by a vertical divider.', 'This card allows the text to be '
            'positioned at various points around the image.', 'Text on this '
            'image is unobtrusive, and is intended for shorter titles.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'anime'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 18,
        'max_line_count': 4,
        'style': 'bottom',
    }

    """Characteristics of the default title font"""
    TITLE_FONT: str = str((REF_DIRECTORY / 'Flanker Griffo.otf').resolve())
    TITLE_COLOR: str = 'white'
    DEFAULT_FONT_CASE: TextCase = 'source'
    FONT_REPLACEMENTS: dict[str, str] = {'♡': '', '☆': '', '✕': 'x'}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT: str = 'Episode {episode_number}'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE: bool = True

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME: str = 'Divider Style'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_file', 'font_interline_spacing', 'font_interword_spacing',
        'font_kerning', 'font_size', 'font_stroke_width', 'stroke_color',
        'title_text_position', 'text_position', 'font_vertical_shift',
        'divider_color', 'text_gravity',
    )

    def __init__(self,
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
            font_stroke_width: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            stroke_color: str = 'black',
            divider_color: str = TITLE_COLOR,
            text_gravity: Optional[TextGravity] = None,
            title_text_position: TitleTextPosition = 'left',
            text_position: TextPosition = 'lower right',
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
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.divider_color = divider_color
        self.stroke_color = stroke_color
        self.text_gravity = text_gravity
        self.title_text_position = title_text_position
        self.text_position = text_position


    @property
    def index_text_command(self) -> ImageMagickCommands:
        """Subcommand for adding the index text to the source image."""

        if self.text_gravity:
            gravity = self.text_gravity
        else:
            gravity = 'west' if self.title_text_position == 'left' else 'east'

        # Hiding all index text, return empty command
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Hiding season or episode text, only add that and divider bar
        if self.hide_season_text or self.hide_episode_text:
            text = self.episode_text if self.hide_season_text else self.season_text
            return [
                f'-gravity {gravity}',
                f'-pointsize {100 * self.font_size}',
                f'label:"{text}"',
            ]

        # Showing all text, add all text and divider
        return [
            f'-gravity {gravity}',
            f'-pointsize {100 * self.font_size}',
            f'label:"{self.season_text}\n{self.episode_text}"',
        ]


    @property
    def title_text_command(self) -> ImageMagickCommands:
        """Subcommand for adding the title text to the source image."""

        # No title text, return blank commands
        if len(self.title_text) == 0:
            return []

        gravity = 'east' if self.title_text_position == 'left' else 'west'

        return [
            f'-gravity {gravity}',
            f'-pointsize {100 * self.font_size}',
            f'label:"{self.title_text}"',
        ]


    @property
    def divider_height(self) -> Union[int, float]:
        """
        The height of the divider between the index and title text. This
        is calculated based on the maximum of the height of the index
        and title text. 0 is returned if a divider is not needed.
        """

        # No need for divider if either text is hidden, return 0
        if (len(self.title_text) == 0
            or (self.hide_season_text and self.hide_episode_text)):
            return 0

        index_text_line_count = (
            1 if self.hide_episode_text or self.hide_season_text else 2
        )

        return max(
            # Height of the index text
            self.image_magick.get_text_dimensions(
                [
                    f'-font "{self.font_file}"',
                    f'-interline-spacing {self.font_interline_spacing}',
                    *self.index_text_command,
                ],
                interline_spacing=self.font_interline_spacing,
                line_count=index_text_line_count,
                width='max', height='sum',
            )[1],
            # Height of the title text
            self.image_magick.get_text_dimensions(
                [
                    f'-font "{self.font_file}"',
                    f'-interline-spacing {self.font_interline_spacing}',
                    *self.title_text_command,
                ],
                interline_spacing=self.font_interline_spacing,
                line_count=len(self.title_text.splitlines()),
                width='max', height='sum'
            )[1]
        )


    def divider_command(self,
            divider_height: Union[int, float],
            color: str,
        ) -> ImageMagickCommands:
        """
        Subcommand to add the dividing rectangle to the image.

        Args:
            divider_height: Height of the divider to create.
            color: Color to create the divider in.

        Returns:
            List of ImageMagick commands.
        """

        # No need for divider, use blank command
        if (len(self.title_text) == 0
            or (self.hide_season_text and self.hide_episode_text)):
            return []

        return [
            f'\( -size 7x{divider_height-25}',
            f'xc:"{color}" \)',
            f'+size',
            f'-gravity center',
            f'+smush 25',
        ]


    def text_command(self,
            divider_height: Union[int, float],
            is_stroke_text: bool,
        ) -> ImageMagickCommands:
        """
        Subcommand to add all text - index, title, and the divider - to
        the image.

        Args:
            divider_height: Height of the divider to create.
            is_stroke_text: Whether this text command is for the stroke
                text. This informs which color is used for the divider.

        Returns:
            List of ImageMagick commands.
        """

        divider_color = (
            self.stroke_color if is_stroke_text else self.divider_color
        )

        # Title on left, add text as: title divider index
        if self.title_text_position == 'left':
            return [
                *self.title_text_command,
                *self.divider_command(divider_height, divider_color),
                *self.index_text_command,
            ]

        # Title on right, add text as index divider title
        return [
            *self.index_text_command,
            *self.divider_command(divider_height, divider_color),
            *self.title_text_command,
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

        # Generic font, reset stroke color
        if not custom_font:
            if 'divider_color' in extras:
                extras['divider_color'] = DividerTitleCard.TITLE_COLOR
            if 'stroke_color' in extras:
                extras['stroke_color'] = 'black'


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
            ('divider_color' in extras
                and extras['divider_color'] != DividerTitleCard.TITLE_COLOR)
            or ('stroke_color' in extras
                and extras['stroke_color'] != 'black')
        )

        return (custom_extras
            or ((font.color != DividerTitleCard.TITLE_COLOR)
            or (font.file != DividerTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
            or (font.stroke_width != 1.0))
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

        standard_etf = DividerTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """Create this object's defined Title Card."""

        interline_spacing = -20 + self.font_interline_spacing
        kerning = -0.5 * self.font_kerning
        stroke_width = 8 * self.font_stroke_width

        # The gravity of the text composition is based on the text position
        gravity = {
            'upper left':  'northwest',
            'upper right': 'northeast',
            'right':       'east',
            'lower right': 'southeast',
            'lower left':  'southwest',
            'left':        'west',
        }[self.text_position]

        # Get the height for the divider character based on the max text height
        divider_height = self.divider_height

        self.image_magick.run([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Add blurred stroke behind the title text
            f'-background transparent',
            f'-bordercolor transparent',
            f'-font "{self.font_file}"',
            f'-kerning {kerning}',
            f'-strokewidth {stroke_width}',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'\( -stroke "{self.stroke_color}"',
            *self.text_command(divider_height, is_stroke_text=True),
            # Combine text images
            f'+smush 25',
            # Add border so the blurred text doesn't get sharply cut off
            f'-border 50x{50+self.font_vertical_shift}',
            f'-blur 0x5 \)',
            # Overlay blurred text in correct position
            f'-gravity {gravity}',
            f'-composite',
            # Add title text
            f'\( -fill "{self.font_color}"',
            # Use basically transparent color so text spacing matches
            f'-stroke "rgba(1, 1, 1, 0.01)"',
            *self.text_command(divider_height, is_stroke_text=False),
            f'+smush 25',
            f'-border 50x{50+self.font_vertical_shift} \)',
            # Overlay title text in correct position
            f'-gravity {gravity}',
            f'-composite',
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])
