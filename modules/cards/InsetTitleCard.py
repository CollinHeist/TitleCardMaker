from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from modules.BaseCardType import (
    BaseCardType, ImageMagickCommands, Extra, CardDescription, Shadow
)
from modules.Debug import log # noqa: F401
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


TextPosition = Literal[
    'upper left', 'upper right',
    'left', 'right',
    'lower left', 'lower right',
]
SeasonTextPosition = Literal['above', 'below']


class InsetTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards in which
    the index text is inset into the title text.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Inset',
        identifier='inset',
        example='/internal_assets/cards/inset.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is <c>crimson</c>.',
                default='crimson',
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
                description='Character to separate season and episode text',
                tooltip='Default is <v>-</v>.',
                default='-',
            ),
            Extra(
                name='Inset Text Transparency',
                identifier='transparency',
                description='How transparent to make inset text.',
                tooltip=(
                    'Number between <v>0.0</v> and <v>1.0</v>. Default is '
                    '<v>1.0</v> (not transparent).'
                ),
                default=1.0,
            ),
            Extra(
                name='Gradient Omission',
                identifier='omit_gradient',
                description='Whether to omit the gradient overlay',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v>, text '
                    'may appear less legible on brighter images. Default is '
                    '<v>False</v>.'
                ),
                default='False',
            ),
        ],
        description=[
            'A title card in which the season and episode text is inset into '
            '(and appears to "cut out") the title text.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'inset'
    SW_REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'star_wars'
    GRADIENT = REF_DIRECTORY.parent / 'overline' / 'small_gradient.png'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 20,
        'max_line_count': 3,
        'style': 'bottom',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((SW_REF_DIRECTORY / 'HelveticaNeue.ttc').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = 'crimson'
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'HelveticaNeue-BoldItalic.ttf'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Inset Style'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_file', 'font_interline_spacing', 'font_interword_spacing',
        'font_kerning', 'font_size', 'font_vertical_shift',
        'episode_text_color', 'episode_text_font_size', 'omit_gradient',
        'separator', 'transparency', '_title_height',
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
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            omit_gradient: bool = False,
            separator: str = '-',
            transparency: float = 1.0,
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
        self.font_interline_spacing = -100 + font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.omit_gradient = omit_gradient
        self.separator = separator
        self.transparency = transparency

        # Implementation variables
        self._title_height = None


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the title text to the image."""

        # No title, return empty commands
        if not self.title_text:
            return []

        size = 250 * self.font_size

        return [
            f'\( -background none',
            f'-pointsize {size}',
            f'-font "{self.font_file}"',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-kerning {self.font_kerning}',
            f'-fill "{self.font_color}"',
            f'label:"{self.title_text}" \)',
            f'-gravity south',
        ]


    @property
    def title_height(self) -> int:
        """The height of the title text."""

        # No title, zero height
        if not self.title_text:
            return 0

        # Determine the height of the text
        if self._title_height is None:
            # Utilize only the bottom line of text for the line height
            bottom_line = self.title_text.splitlines()[-1]
            modified_commands = self.title_text_commands
            modified_commands[-2] = f'label:"{bottom_line}"'

            _, self._title_height = self.image_magick.get_text_dimensions(
                modified_commands,
                interline_spacing=self.font_interline_spacing,
                line_count=1,
            )

        return self._title_height


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the index text to the image."""

        # All text is hidden
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Determine index text
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text =\
                f'{self.season_text} {self.separator} {self.episode_text}'

        size = 75 * self.episode_text_font_size # 1-3-1/4 font size base

        index_text_commands = [
            f'\( -background none',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'+interline-spacing',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize {size}',
            f'-gravity south',
            f'label:"{index_text}" \)',
        ]
        index_width, index_height = self.image_magick.get_text_dimensions(
            index_text_commands
        )
        crop_width = index_width + 40 # Increase margin
        crop_height = index_height - 20 # Reduce margin
        crop_y = self.font_vertical_shift + (self.title_height / 2) \
            - (index_height / 2) + 30

        return [
            # Copy source image
            f'\( "{self.source_file.resolve()}"',
            # Make source transparent (according to transparency)
            f'-alpha set',
            f'-channel A',
            f'-evaluate multiply {self.transparency:.2f}',
            f'+channel',
            # Stylize so it matches the background
            *self.resize_and_style,
            *self.gradient_commands,
            # Crop out the area which the index text will cover
            f'-gravity south',
            f'-crop {crop_width}x{crop_height}+0+{crop_y:.0f}',
            f'-gravity center',
            # Increase canvas size so blurring can extend beyond bounds
            f'-extent {crop_width+20}x{crop_height+20}',
            # Blur edges so cropping is not so sharp
            f'-blur 0x7',
            f'-gravity south',
            f'\) -geometry +0+{crop_y-10:.0f}',
            f'-composite',
            # Add index text with a drop shadow
            *self.add_drop_shadow(
                index_text_commands, '95x4-6+6', x=3, y=crop_y - 15 - 6,
            ),
        ]


    @property
    def gradient_commands(self) -> ImageMagickCommands:
        """Subcommand to add the gradient overlay to the image."""

        if self.omit_gradient:
            return []

        return [
            f'"{self.GRADIENT.resolve()}"',
            f'-composite',
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
            if 'episode_text_color' in extras:
                extras['episode_text_color'] = InsetTitleCard.EPISODE_TEXT_COLOR
            if 'episode_text_font_size' in extras:
                extras['episode_text_fon_size'] = 1.0


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
                and extras['episode_text_color'] != InsetTitleCard.EPISODE_TEXT_COLOR)
            or ('episode_text_font_size' in extras
                and extras['episode_text_font_size'] != 1.0)
        )

        return (custom_extras
            or ((font.color != InsetTitleCard.TITLE_COLOR)
            or (font.file != InsetTitleCard.TITLE_FONT)
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

        standard_etf = InsetTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """Create this object's defined Title Card."""

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Add gradient overlay
            *self.gradient_commands,
            # Add title text with a drop shadow
            *self.add_drop_shadow(
                self.title_text_commands,
                Shadow(opacity=95, sigma=6, x=-12, y=12),
                x=0, y=self.font_vertical_shift,
            ),
            # Add index text
            *self.index_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
