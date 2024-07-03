from pathlib import Path
from random import random
from typing import TYPE_CHECKING, Optional

from modules.BaseCardType import (
    BaseCardType, Dimensions, ImageMagickCommands, Shadow,
)
from modules.EpisodeInfo import EpisodeInfo

if TYPE_CHECKING:
    from modules.PreferenceParser import PreferenceParser
    from modules.Font import Font


class CalligraphyTitleCard(BaseCardType):
    """
    CardType that produces title cards featuring a prominet logo, with
    all text using a handwritten calligraphy font. A matte paper texture
    is applied to the image.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'calligraphy'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 20,
        'max_line_count': 2,
        'top_heavy': 'forced even',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'SlashSignature.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'source'
    FONT_REPLACEMENTS = {}

    """How to format episode text"""
    EPISODE_TEXT_FORMAT = 'Episode {episode_number_cardinal_title}'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Calligraphy Style'

    """Texture image to compose with"""
    TEXTURE_IMAGE = REF_DIRECTORY / 'texture.jpg'

    """Custom blur profile"""
    BLUR_PROFILE = '0x10'

    """Blur profile to use if deep blurring is enabled"""
    DEEP_BLUR_PROFILE = BaseCardType.BLUR_PROFILE

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_file',
        'font_size', 'font_color', 'font_interline_spacing', 'shadow_color',
        'font_interword_spacing', 'font_kerning', 'font_vertical_shift',
        'logo_file', 'add_texture', 'episode_text_color', 'logo_size',
        'randomize_texture', 'separator', 'deep_blur', 'episode_text_font_size',
    )

    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title_text: str,
            season_text: str,
            episode_text: str,
            hide_season_text: bool = True,
            hide_episode_text: bool = False,
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_vertical_shift: int = 0,
            logo: Optional[Path] = None,
            watched: bool = True,
            blur: bool = False,
            grayscale: bool = False,
            add_texture: bool = True,
            deep_blur_if_unwatched: bool = True,
            episode_text_color: str = TITLE_COLOR,
            episode_text_font_size: float = 1.0,
            logo_size: float = 1.0,
            offset_titles: bool = True,
            randomize_texture: bool = True,
            separator: str = '-',
            shadow_color: str = 'black',
            preferences: Optional['PreferenceParser'] = None,
            **unused,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file
        self.logo_file = None if logo is None else Path(logo)

        # Ensure characters that need to be escaped are
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text or len(season_text) == 0
        self.hide_episode_text = hide_episode_text or len(episode_text) == 0

        # Offset multi-line titles if indicated
        if offset_titles:
            title_text = self.__offset_title(title_text)
        self.title_text = self.image_magick.escape_chars(title_text)

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.add_texture = add_texture
        self.deep_blur = blur and deep_blur_if_unwatched and not watched
        self.episode_text_color = (
            font_color if episode_text_color is None else episode_text_color
        )
        self.episode_text_font_size = episode_text_font_size
        self.logo_size = logo_size
        self.randomize_texture = randomize_texture
        self.separator = separator
        self.shadow_color = shadow_color


    @staticmethod
    def SEASON_TEXT_FORMATTER(episode_info: EpisodeInfo) -> str:
        """
        Fallback season title formatter.

        Args:
            episode_info: Info of the Episode whose season text is being
                determined.

        Returns:
            'Specials' if the season number is 0; otherwise the cardinal
            version of the season number. If that's not possible, then
            just 'Season {x}'.
        """

        if episode_info.season_number == 0:
            return 'Specials'

        try:
            number = episode_info.word_set['season_number_cardinal_title']
            return f'Season {number}'
        except KeyError:
            return f'Season {episode_info.season_number}'


    def __offset_title(self, title_text: str) -> str:
        """
        Apply indention / offset to the given title text.

        Args:
            title_text: Title to apply the offset to.

        Returns:
            Modified title text.
        """

        # Cannot offset single-line titles
        if '\n' not in title_text:
            return title_text

        # Split into separate lines
        lines = title_text.splitlines()

        # Don't offset if the bottom line is much longer than the first
        if (len(lines[1]) > len(lines[0]) * 2
            or len(lines[1]) > len(lines[0]) + 12):
            return title_text

        def limit(lower: int, value: int, upper: int) -> int:
            return max(lower, min(value, upper))

        offset_count = limit(3, len(lines[1]), 10)
        offset_count2 = 7 # limit(6, (len(lines[0]) // 2) + offset_count, 8)
        lines[0] = lines[0] + (' ' * offset_count)
        lines[1] = (' ' * offset_count2) + lines[1]
        title_text = '\n'.join(lines)

        return title_text


    def __get_logo_size(self) -> Dimensions:
        """
        Get the effective size of the logo as it is overlaid onto the
        image.

        Returns:
            Effective dimensions of the logo after having been scaled.
        """

        # Get base dimensions of the logo (before resizing)
        width, height = self.image_magick.get_image_dimensions(self.logo_file)

        # -resize 2800x
        scaled_w = 2800
        scaled_h = height * (scaled_w / width)

        # -resize x{750 * self.logo_size}>
        if scaled_h > (max_height := 750 * self.logo_size):
            downsize = max_height / scaled_h
            return Dimensions(scaled_w * downsize, scaled_h * downsize)

        return Dimensions(scaled_w, scaled_h)


    @property
    def texture_commands(self) -> ImageMagickCommands:
        """Subcommand to apply the texture image (if enabled)."""

        # Not adding texture, return
        if not self.add_texture:
            return []

        texture_command = [
            f'"{self.TEXTURE_IMAGE.resolve()}"',
        ]

        # If randomizing the texture, scale by random value
        if self.randomize_texture:
            random_height = (random() + 1.0) * self.HEIGHT
            texture_command = [
                f'\( "{self.TEXTURE_IMAGE.resolve()}"',
                f'-resize x{random_height} \)',
            ]

        return [
            *texture_command,
            f'-gravity center',
            f'-compose multiply',
            f'-composite',
            f'-compose over',
        ]


    @property
    def logo_commands(self) -> ImageMagickCommands:
        """Subcommand to add the logo (and drop shadow) to the image."""

        # Logo not specified or does not exist, return empty commands
        if not self.logo_file or not self.logo_file.exists():
            return []

        logo_height = 725 * self.logo_size

        base_command = [
            f'"{self.logo_file.resolve()}"',
            f'-resize 2800x',
            f'-resize x{logo_height}\>',
        ]

        return self.add_drop_shadow(base_command, '95x10+0+35', 0, 0)


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommand for adding title text to the source image."""

        # No title text, or not being shown
        if len(self.title_text) == 0:
            return []

        # Font characteristics
        size = 160 * self.font_size
        interline_spacing = -70 + self.font_interline_spacing
        kerning = 1.0 * self.font_kerning
        vertical_shift = 600 + self.font_vertical_shift

        base_commands = [
            f'-background None',
            f'-font "{self.font_file}"',
            f'-pointsize {size}',
            f'-interline-spacing {interline_spacing}',
            f'-kerning {kerning}',
            f'-fill "{self.font_color}"',
            f'label:"{self.title_text}"',
        ]

        return self.add_drop_shadow(
            base_commands,
            Shadow(opacity=95, sigma=2, x=0, y=17),
            x=0, y=vertical_shift,
            shadow_color=self.shadow_color,
        )


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommands for adding index text to the source image."""

        # Return if not showing text
        if self.hide_season_text and self.hide_episode_text:
            return []

        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_season_text:
            index_text = self.season_text
        else:
            index_text = (
                f'{self.season_text} {self.separator} {self.episode_text}'
            )

        interline_spacing = -50 + self.font_interline_spacing
        kerning = 1.0 * self.font_kerning
        size = 75 * self.episode_text_font_size

        # Determine vertical offset - if no logo, place on top of image
        if not self.logo_file or not self.logo_file.exists():
            y = -750
        # Logo is provided, position just above logo
        else:
            _, logo_height = self.__get_logo_size()
            y = (-logo_height / 2) - 125 # 125px margin

        base_commands = [
            f'-background None',
            f'-font "{self.font_file}"',
            f'-pointsize {size}',
            f'-interline-spacing {interline_spacing}',
            f'-kerning {kerning}',
            f'-fill "{self.episode_text_color}"',
            f'label:"{index_text}"',
        ]

        return self.add_drop_shadow(
            base_commands, '95x2+0+12', x=0, y=y,
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

        # Generic font, reset episode color
        if not custom_font:
            if 'episode_text_color' in extras:
                extras['episode_text_color'] = CalligraphyTitleCard.TITLE_COLOR
            if 'episode_text_font_size' in extras:
                extras['episode_text_font_size'] = 1.0
            if 'shadow_color' in extras:
                extras['shadow_color'] = 'black'


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
                and extras['episode_text_color'] != CalligraphyTitleCard.TITLE_COLOR)
            or ('episode_text_font_size' in extras
                and extras['episode_text_font_size'] != 1.0)
            or ('shadow_color' in extras
                and extras['shadow_color'] != 'black')
        )

        return (custom_extras
            or ((font.color != CalligraphyTitleCard.TITLE_COLOR)
            or (font.file != CalligraphyTitleCard.TITLE_FONT)
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

        standard_etf = CalligraphyTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """Create this object's defined Title Card."""

        style_commands = self.resize_and_style
        if self.deep_blur:
            style_commands = [
                *self.resize,
                # Optionally blur
                f'-blur {self.DEEP_BLUR_PROFILE}',
                # Optionally set gray colorspace
                f'-colorspace gray' if self.grayscale else '',
                # Reset to full colorspace
                f'-set colorspace sRGB',
            ]

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *style_commands,
            # Add each layer
            *self.texture_commands,
            *self.logo_commands,
            *self.title_text_commands,
            *self.index_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
