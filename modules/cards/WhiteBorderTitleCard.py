from pathlib import Path
from typing import TYPE_CHECKING, Optional

from modules.BaseCardType import (
    BaseCardType, ImageMagickCommands, Extra, CardDescription
)
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


class WhiteBorderTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards based on
    the Standard card type, but including a white border to match the
    style of Musikmann2000's Posters.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='White Border',
        identifier='white border',
        example='/internal_assets/cards/white border.webp',
        creators=['Musikmann2000', 'CollinHeist', 'mvanbaak', 'supermariobruh'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Border Color',
                identifier='border_color',
                description='Color of the border',
                tooltip='Default is <c>white</c>.',
                default='white',
            ),
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color of the season and episode text',
                tooltip='Default is <c>white</c>.',
                default='white',
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description=(
                    'Character that separates the season and episode text'
                ),
                tooltip='Default is <v>•</v>.',
                default='•',
            ),
        ],
        description=[
            'Card type based on the Standard card, but modified to include a '
            "white border frame and a changed Font to match Musikmann2000's "
            "posters.",
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'white_border'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 30,
        'max_line_count': 3,
        'style': 'top',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Arial_Bold.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = TITLE_COLOR
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Arial.ttf'

    """Default stroke color"""
    STROKE_COLOR = 'black'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'White Border Style'

    """White border frame image to overlay"""
    FRAME_IMAGE = REF_DIRECTORY / 'border.png'

    """Gradient image to overlay"""
    __GRADIENT_IMAGE = REF_DIRECTORY.parent / 'GRADIENT.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_file', 'font_interline_spacing', 'font_kerning', 'font_size',
        'font_stroke_width', 'font_vertical_shift', 'border_color',
        'stroke_color', 'episode_text_color', 'episode_text_font_size',
        'font_interword_spacing', 'separator', 'omit_gradient',
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
            font_stroke_width: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            border_color: str = 'white',
            episode_text_color: str = TITLE_COLOR,
            episode_text_font_size: float = 1.0,
            omit_gradient: bool = False,
            separator: str = '•',
            stroke_color: str = STROKE_COLOR,
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
        self.border_color = border_color
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.omit_gradient = omit_gradient
        self.separator = separator
        self.stroke_color = stroke_color


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommand for adding title text to the image."""

        # No title text
        if len(self.title_text) == 0:
            return []

        vertical_shift = 250 + self.font_vertical_shift

        return [
            # Global text effects
            f'-gravity south',
            f'-font "{self.font_file}"',
            f'-pointsize {160 * self.font_size}',
            f'-kerning {-1 * self.font_kerning}',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            # Black stroke behind primary text
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {4 * self.font_stroke_width}',
            f'-annotate +0+{vertical_shift} "{self.title_text}"',
            # Primary text
            f'-fill "{self.font_color}"',
            f'-annotate +0+{vertical_shift} "{self.title_text}"',
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommand for adding index text to the source image."""

        if self.hide_season_text and self.hide_episode_text:
            return []
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = (
                f'{self.season_text} {self.separator} {self.episode_text}'
            )

        size = 62.5 * self.episode_text_font_size

        return [
            # Global text effects
            f'-background transparent',
            f'-gravity south',
            f'-kerning 4',
            f'-pointsize {size:.2f}',
            f'-interword-spacing 14.5',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            # Black stroke behind primary text
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 6',
            f'-annotate +0+162 "{index_text}"',
            # Primary text
            f'-fill "{self.episode_text_color}"',
            f'-stroke "{self.episode_text_color}"',
            f'-strokewidth 0.75',
            f'-annotate +0+162 "{index_text}"',
        ]


    @property
    def border_color_commands(self) -> ImageMagickCommands:
        """Subcommand to recolor the border by overlaying rectangles."""

        # Do not recolor if border is white
        if self.border_color.lower() in ('white', 'rgb(255,255,255)','#ffffff'):
            return []

        return [
            f'-stroke none',
            f'-fill "{self.border_color}"',
            # Top
            f'-draw "rectangle 0,0,{self.WIDTH},25"',
            # Right
            f'-draw "rectangle {self.WIDTH-25},0,{self.WIDTH},{self.HEIGHT}"',
            # Bottom
            f'-draw "rectangle 0,{self.HEIGHT-25},{self.WIDTH},{self.HEIGHT}"',
            # Left
            f'-draw "rectangle 0,0,25,{self.HEIGHT}"',
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
            if 'border_color' in extras:
                extras['border_color'] = 'white'
            if 'episode_text_color' in extras:
                extras['episode_text_color'] =\
                    WhiteBorderTitleCard.EPISODE_TEXT_COLOR
            if 'episode_text_font_size' in extras:
                extras['episode_text_font_size'] = 1.0
            if 'stroke_color' in extras:
                extras['stroke_color'] = WhiteBorderTitleCard.STROKE_COLOR


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
            ('border_color' in extras
                and extras['border_color'] != 'white')
            or ('episode_text_color' in extras
                and extras['episode_text_color'] != \
                    WhiteBorderTitleCard.EPISODE_TEXT_COLOR)
            or ('episode_text_font_size' in extras
                and extras['episode_text_font_size'] != 1.0)
            or ('stroke_color' in extras
                and extras['stroke_color'] != WhiteBorderTitleCard.STROKE_COLOR)
        )

        return custom_extras or WhiteBorderTitleCard._is_custom_font(font)

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

        standard_etf = WhiteBorderTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        processing = [
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Fit within frame
            f'-gravity center',
            f'-resize "{self.WIDTH-(25 * 2)}x{self.HEIGHT - (25 * 2)}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
        ]

        # Command to add the gradient overlay if indicated
        gradient_command = []
        if not self.omit_gradient:
            gradient_command = [
                f'"{self.__GRADIENT_IMAGE.resolve()}"',
                f'-composite',
            ]

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            *processing,
            # Overlay gradient
            *gradient_command,
            # Add remaining sub-components
            *self.title_text_commands,
            *self.index_text_commands,
            # Overlay frame
            f'"{self.FRAME_IMAGE.resolve()}"',
            f'-composite',
            # Recolor frame
            *self.border_color_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file, pre_processing=processing),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
