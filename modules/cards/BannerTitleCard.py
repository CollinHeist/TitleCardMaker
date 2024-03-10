from pathlib import Path
from typing import TYPE_CHECKING, Optional

from modules.BaseCardType import (
    BaseCardType, ImageMagickCommands, Extra, CardDescription
)
from modules.Debug import log
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


class BannerTitleCard(BaseCardType):
    """
    This class describes a CardType that feature a solid-color banner at
    the bottom of the image, with all text directly on top of or within
    the banner. The banner and text can be recolored and resized.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Banner',
        identifier='banner',
        example='/internal_assets/cards/banner.webp',
        creators=['CollinHeist', 'Danny Beaton'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Alternate Color',
                identifier='alternate_color',
                description='Color of the text that appears in the banner',
                tooltip='Default is <c>black</c>.',
            ),
            Extra(
                name='Banner Color',
                identifier='banner_color',
                description='Color of the banner',
                tooltip='Defaults is to match the Font color.',
            ),
            Extra(
                name='Banner Height',
                identifier='banner_height',
                description='Height of the banner',
                tooltip=(
                    'Number ><v>0</v>. Default is <v>185</v>. Unit is pixels.'
                ),
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
            ),
            Extra(
                name='Banner Toggle',
                identifier='hide_banner',
                description='Whether to hide the banner',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is '
                    '<v>False</v>.'
                ),
            ),
            Extra(
                name='Horizontal Offset',
                identifier='x_offset',
                description='How far from the edge the text should appear',
                tooltip=(
                    'Number ≥<v>0</v>. Default is <v>50</v>. Unit is pixels.'
                ),
            ),
        ],
        description=[
            'Cards of this type feature a solid-color banner at the bottom of '
            'the image, with all text directly on top of (or within) the '
            'banner.', 'The banner and text can be recolored and resized.'
        ],
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'banner'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 19,
        'max_line_count': 3,
        'style': 'forced even',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Gill Sans Nova ExtraBold.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS = {'(': '', ')': ''}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = 'black'
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Gill Sans Nova ExtraBold.ttf'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Banner Style'

    """Implementation details"""
    BANNER_HEIGHT = 185
    X_OFFSET = 50

    __slots__ = (
        'source_file', 'output_file', 'top_title_text', 'bottom_title_text',
        'season_text', 'episode_text', 'hide_season_text', 'hide_episode_text',
        'font_color', 'font_file', 'font_interline_spacing',
        'font_interword_spacing', 'font_kerning', 'font_size',
        'font_vertical_shift', 'alternate_color', 'banner_height',
        'episode_text_font_size', 'hide_banner', 'banner_color', 'x_offset',
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
            alternate_color: str = EPISODE_TEXT_COLOR,
            banner_color: str = TITLE_COLOR,
            banner_height: int = BANNER_HEIGHT,
            episode_text_font_size: float = 1.0,
            hide_banner: bool = False,
            x_offset: int = X_OFFSET,
            preferences: Optional['Preferences'] = None,
            **unused,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        if len(lines := title_text.split('\n')) > 1:
            top_title = '\n'.join(lines[:-1])
            bottom_title = lines[-1]
        else:
            top_title, bottom_title = title_text, ''
        self.top_title_text = self.image_magick.escape_chars(top_title)
        self.bottom_title_text = self.image_magick.escape_chars(bottom_title)
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
        self.alternate_color = alternate_color
        self.banner_height = banner_height
        self.episode_text_font_size = episode_text_font_size
        self.hide_banner = hide_banner
        self.banner_color = banner_color
        self.x_offset = x_offset


    @property
    def banner_commands(self) -> ImageMagickCommands:
        """Subcommands to add the solid color banner to the image."""

        if self.hide_banner:
            return []

        # Draw from bottom left to top right
        height = self.HEIGHT - self.banner_height

        return [
            f'-fill "{self.banner_color}"',
            f'-draw "rectangle 0,{self.HEIGHT} {self.WIDTH},{height}"',
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the index text to the image."""

        # All text hidden, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Determine effective index text
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text}\n{self.episode_text}'

        # Determine placement
        x = self.x_offset
        y = self.HEIGHT - self.banner_height - self.font_vertical_shift - 48

        return [
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-fill "{self.alternate_color}"',
            f'-pointsize {95 * self.episode_text_font_size:.0f}',
            f'-gravity northwest',
            f'-interline-spacing -65',
            f'-interword-spacing 20',
            f'-annotate {x:+.0f}{y:+.0f}',
            f'"{index_text}"',
        ]


    @property
    def index_text_width(self) -> int:
        """Width of the index text."""

        # All text hidden, return 0
        if self.hide_season_text and self.hide_episode_text:
            return 0

        # Determine the longest text
        if self.hide_season_text:
            text = self.episode_text
        elif self.hide_episode_text:
            text = self.season_text
        else:
            if len(self.season_text) > len(self.episode_text):
                text = self.season_text
            elif len(self.season_text) < len(self.episode_text):
                text = self.episode_text
            else:
                text = self.episode_text

        # Return width of the longest text
        modified_commands = self.index_text_commands
        modified_commands[-1] = f'"{text}"'
        return self.image_magick.get_text_dimensions(modified_commands)[0]


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the title text to the image."""

        # No title, return empty commands
        if not self.top_title_text and not self.bottom_title_text:
            return []

        # Font characteristics
        interline_spacing = -125 + self.font_interline_spacing
        interword_spacing = 40 + self.font_interword_spacing
        kerning = 1.0 * self.font_kerning
        size = 200 * self.font_size

        # Base font commands for top and bottom text
        base_commands = [
            f'-font "{self.font_file}"',
            f'-fill {self.font_color}',
            f'-interline-spacing {interline_spacing:+}',
            f'-interword-spacing {interword_spacing:+}',
            f'-kerning {kerning:.0f}',
            f'-pointsize {size:.0f}',
        ]

        # Determine the width of the title text
        top_y = self.banner_height + self.font_vertical_shift - 60
        top_text_commands = [
            f'\( -background none',
            *base_commands,
            f'-gravity southwest',
            f'label:"{self.top_title_text}" \)',
        ]
        top_width, _ = self.image_magick.get_text_dimensions(top_text_commands)

        # Determine commands for the bottom line of text
        if self.bottom_title_text:
            bottom_text_commands = [
                *base_commands,
                f'-fill "{self.alternate_color}"',
                f'-gravity northwest',
                f'-annotate +0+0',
                f'"{self.bottom_title_text}"',
            ]

            # Positioning the bottom line of text 300px within from end of top
            bottom_x = self.x_offset + top_width - 300
            bottom_y = self.HEIGHT - self.banner_height \
                - self.font_vertical_shift - 90 + self.font_interline_spacing

            # Determine the width of the text to avoid overlap
            left_boundary = self.x_offset + self.index_text_width
            bottom_width, _ = self.image_magick.get_text_dimensions(
                bottom_text_commands,
            )

            # If within 35px of edge of index text, move right
            if bottom_x < left_boundary + 35:
                bottom_x = left_boundary + 55 # 20px spacing
            # If would overlap from right edge, move left
            if bottom_x + bottom_width > self.WIDTH - self.x_offset:
                bottom_x = self.WIDTH - self.x_offset - bottom_width
            bottom_text_commands[-2] = f'-annotate +{bottom_x}+{bottom_y}'
        else:
            bottom_text_commands = []

        return [
            # Draw top line(s) of the title text
            *self.add_drop_shadow(
                top_text_commands,
                '95x4+0+0',
                x=self.x_offset-12, y=top_y-8,
            ),
            # Draw banner
            *self.banner_commands,
            # Draw bottom line of the title text
            *bottom_text_commands,
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
            if 'alternate_color' in extras:
                extras['alternate_color'] = BannerTitleCard.EPISODE_TEXT_COLOR
            if 'banner_color' in extras:
                extras['banner_color'] = BannerTitleCard.TITLE_COLOR
            if 'episode_text_font_size' in extras:
                extras['episode_text_font_size'] = 1.0
            if 'x_offset' in extras:
                extras['x_offset'] = BannerTitleCard.X_OFFSET


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
            ('alternate_color' in extras
                and extras['alternate_color'] != BannerTitleCard.EPISODE_TEXT_COLOR)
            or ('banner_color' in extras
                and extras['banner_color'] != BannerTitleCard.TITLE_COLOR)
            or ('episode_text_font_size' in extras
                and extras['episode_text_font_size'] != 1.0)
            or ('x_offset' in extras
                and extras['x_offset'] != BannerTitleCard.X_OFFSET)
        )

        return (custom_extras
            or ((font.color != BannerTitleCard.TITLE_COLOR)
            or (font.file != BannerTitleCard.TITLE_FONT)
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

        standard_etf = BannerTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """Create this object's defined Title Card."""

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Add text and banner
            *self.title_text_commands,
            *self.index_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
