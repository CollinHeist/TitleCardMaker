from pathlib import Path
from random import random
from typing import Optional

from modules.BaseCardType import (
    BaseCardType, CardDescription, Extra, ImageMagickCommands,
)


class CalligraphyTitleCard(BaseCardType):
    """
    CardType that produces title cards featuring a prominet logo, with
    all text using a handwritten calligraphy font. A matte paper texture
    is applied to the image.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Calligraphy',
        identifier='calligraphy',
        example='/internal_assets/cards/calligraphy.jpg',
        creators=['CollinHeist', '/u/Recker_Man'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Texture Toggle',
                identifier='add_texture',
                description='Whether to add the "grain" texture',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is <v>True</v>.'
                ),
            ), Extra(
                name='Texture Randomization Toggle',
                identifier='randomize_texture',
                description='Whether to randomly reposition the texture overlay',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is <v>True</v>.'
                ),
            ), Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Defaults to match the Font color.'
            ), Extra(
                name='Offset Title Toggle',
                identifier='offset_titles',
                description='Whether to offset multi-line titles',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If enabled, then '
                    'multi-line titles will be adjusted so the second line '
                    'hangs below the first. Default is <v>True</v>.'
                ),
            ), Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
            ), Extra(
                name='Logo Size',
                identifier='logo_size',
                description=(
                    'Scalar for how much to scale the size of the logo element'
                ), tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>'
            ), Extra(
                name='Deep Blur Unwatched Toggle',
                identifier='deep_blur_if_unwatched',
                description=(
                    'Whether to apply a stronger blur to unwatched Episodes'
                ), tooltip=(
                    'Either <v>True</v> or <v>False</v>. Applies a more '
                    'spoiler-free blurring if a Blur style is used and the '
                    'Episode is unwatched. Default is <v>True</v>.'
                ),
            ),
        ], description=[
            'Stylized Card featuring a prominent logo and all text in a '
            'hand-written calligraphy font. A subtle matte paper texture is '
            'applied to the image.', 'Looks best when a blurred/grayscale '
            'style is utilized as the text and texture are more pronounced.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'calligraphy'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 20,
        'max_line_count': 2,
        'top_heavy': 'even',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'SlashSignature.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'source'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'Episode {episode_number_cardinal_title}'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
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
        'font_size', 'font_color', 'font_interline_spacing',
        'font_interword_spacing', 'font_kerning', 'font_vertical_shift',
        'logo_file', 'add_texture', 'episode_text_color', 'logo_size',
        'randomize_texture', 'separator', 'deep_blur',
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
            logo_file: Optional[Path] = None,
            watched: bool = True,
            blur: bool = False,
            grayscale: bool = False,
            add_texture: bool = True,
            deep_blur_if_unwatched: bool = True,
            episode_text_color: str = TITLE_COLOR,
            logo_size: float = 1.0,
            offset_titles: bool = True,
            randomize_texture: bool = True,
            separator: str = '-',
            preferences: Optional['Preferences'] = None, # type: ignore
            **unused,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file
        self.logo_file = logo_file

        # Ensure characters that need to be escaped are
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text
        self.hide_episode_text = hide_episode_text

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
        self.episode_text_color = episode_text_color
        self.logo_size = logo_size
        self.randomize_texture = randomize_texture
        self.separator = separator


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
        if len(lines[1]) > len(lines[0]) * 2:
            return title_text

        def limit(lower: int, value: int, upper: int) -> int:
            return max(lower, min(value, upper))

        offset_count = limit(3, len(lines[1]), 10)
        offset_count2 = 7 # limit(6, (len(lines[0]) // 2) + offset_count, 8)
        lines[0] = lines[0] + (' ' * offset_count)
        lines[1] = (' ' * offset_count2) + lines[1]
        title_text = '\n'.join(lines)

        return title_text


    def __add_drop_shadow(self,
            commands: ImageMagickCommands,
            shadow: str,
            x: int = 0,
            y: int = 0,
        ) -> ImageMagickCommands:
        """
        Amend the given commands to apply a drop shadow effect.

        Args:
            commands: List of commands being modified. Must contain some
                image definition that can be cloned.
            shadow: IM Shadow string - i.e. `85x10+10+10`.
            x: X-position of the offset to apply when compositing.
            y: Y-position of the offset to apply when compositing.

        Returns:
            List of ImageMagick commands.
        """

        return [
            f'\(',
            *commands,
            f'\( +clone',
            f'-background None',
            f'-shadow {shadow} \)',
            f'+swap',
            f'-background None',
            f'-layers merge',
            f'+repage \)',
            f'-geometry {x:+}{y:+}',
            f'-composite',
        ]


    @property
    def texture_commands(self) -> ImageMagickCommands:
        """
        Subcommand to apply the texture image (if enabled).

        Returns:
            List of ImageMagick commands.
        """

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
        """
        Subcommand to add the logo (and drop shadow) to the image.

        Returns:
            List of ImageMagick commands.
        """

        # Logo not specified or does not exist, return empty commands
        if not self.logo_file or not self.logo_file.exists():
            return []

        logo_height = 750 * self.logo_size

        base_command = [
            f'"{self.logo_file.resolve()}"',
            f'-resize 2800x',
            f'-resize x{logo_height}\>',
        ]

        return self.__add_drop_shadow(base_command, '95x10+0+35', 0, 0)


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """
        Subcommand for adding title text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # No title text, or not being shown
        if len(self.title_text) == 0:
            return []

        # Font characteristics
        size = 160 * self.font_size
        interline_spacing = -50 + self.font_interline_spacing
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

        return self.__add_drop_shadow(
            base_commands, '95x2+0+17', 0, vertical_shift,
        )


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """
        Subcommands for adding index text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # Return if not showing text
        if self.hide_season_text and self.hide_episode_text:
            return []

        index_text = f'{self.season_text} {self.separator} {self.episode_text}'
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_season_text:
            index_text = self.season_text

        interline_spacing = -50 + self.font_interline_spacing
        kerning = 1.0 * self.font_kerning
        size = 75 * self.font_size

        base_commands = [
            f'-background None',
            f'-font "{self.font_file}"',
            f'-pointsize {size}',
            f'-interline-spacing {interline_spacing}',
            f'-kerning {kerning}',
            f'-fill "{self.episode_text_color}"',
            f'label:"{index_text}"',
        ]

        return self.__add_drop_shadow(base_commands, '95x2+0+12', 0, -500)


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


    @staticmethod
    def is_custom_font(font: 'Font') -> bool: # type: ignore
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.color != CalligraphyTitleCard.TITLE_COLOR)
            or (font.file != CalligraphyTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
            or (font.vertical_shift != 0)
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
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

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
            f'magick "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *style_commands,
            # Add each layer
            *self.texture_commands,
            *self.logo_commands,
            *self.title_text_commands,
            *self.index_text_commands,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
