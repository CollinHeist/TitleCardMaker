from pathlib import Path
from random import choice as random_choice
from typing import Literal, Optional, TYPE_CHECKING

from modules.BaseCardType import (
    BaseCardType, CardDescription, Coordinate, Extra, ImageMagickCommands,
    Rectangle, Shadow,
)
from modules.ImageMagickInterface import Dimensions
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


TextPosition = Literal[
    'upper left', 'upper right', 'left', 'right', 'lower left', 'lower right'
]


class SlashTitleCard(BaseCardType):
    """
    CardType that produces title cards ... TODO
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
            
        ],
        description=[
            
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'music'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 20,
        'max_line_count': 3,
        'style': 'top',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Gotham-Bold.otf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'source'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = TITLE_COLOR
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Gotham-Bold.otf'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Tinted Frame Style'

    """Implementation details"""
    DEFAULT_TEXT_POSITION: TextPosition = 'lower left'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_file',
        'font_size', 'font_color', 'font_interline_spacing',
        'font_interword_spacing', 'font_kerning', 'font_vertical_shift',

        'text_position',
        '__title_dimensions'
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
            
            text_position: TextPosition = DEFAULT_TEXT_POSITION,

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
        self.font_interline_spacing = 0 + font_interline_spacing
        self.font_interword_spacing = 0 + font_interword_spacing
        self.font_kerning = 1.0 * font_kerning
        self.font_size = font_size
        self.font_vertical_shift = 0 + font_vertical_shift

        # Extras
        self.text_position: TextPosition = text_position

        # Implementation
        self.__title_dimensions = Dimensions(0, 0)


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommand for adding title text to the source image."""

        # No title text
        if not self.title_text:
            return []

        x, y = 100, self.font_vertical_shift
        if self.text_position == 'upper left':
            y += 100
            gravity = 'northwest'
        elif self.text_position == 'upper right':
            y += 100
            gravity = 'northeast'
        elif self.text_position == 'left':
            y += 0
            gravity = 'west'
        elif self.text_position == 'right':
            y += 0
            gravity = 'east'
        elif self.text_position == 'lower left':
            y += 100
            gravity = 'southwest'
        elif self.text_position == 'lower right':
            y += 100
            gravity = 'southeast'

        return [
            f'-font "{self.font_file}"',
            f'-pointsize {125 * self.font_size}',
            f'-kerning {self.font_kerning}',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-fill "{self.font_color}"',
            f'-gravity {gravity}',
            f'-annotate {x:+}{y:+} "{self.title_text}"',
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommand for adding index text to the source image."""

        # If not showing index text, or all text is hidden, return
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Set index text based on which text is hidden/not
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text} {self.episode_text}'

        x = 100 + (self.__title_dimensions.width / 2)
        y = self.font_vertical_shift + self.__title_dimensions.height + 25
        if self.text_position == 'upper left':
            y += 100
        elif self.text_position == 'upper right':
            y += 100
        elif self.text_position == 'left':
            y += 0
        elif self.text_position == 'right':
            y += 0
        elif self.text_position == 'lower left':
            y += 100
        elif self.text_position == 'lower right':
            y += 100

        return [
            f'-font "{self.font_file}"',
            f'-pointsize {65 * self.font_size}',
            f'-kerning {self.font_kerning}',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-fill "{self.font_color}"',
            # f'-gravity {gravity}',
            f'-gravity south',
            f'-annotate {x:+}{y:+} "{index_text}"',
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

        # Generic font, reset episode text and box colors
        if not custom_font:
            ...


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

        standard_etf = SlashTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """Create this object's defined Title Card."""

        # Index: Gotham Bold @ 75px
        # Title: Gotham Bold @ 150px
        """
        convert \( in.jpg -resize 3200x1800 -gravity center -pointsize 250
        -fill white -annotate +0+0 "Example Title" -pointsize 125
        -annotate +0+200 "Season One" \) \( -size 3200x1800 xc:none
        -gravity center -pointsize 250 -fill crimson
        -annotate +0+0 "Example Title" -pointsize 125
        -annotate +0+201 "Season One" \) mask.png -composite _.jpg
        """

        # Store dimensions of all text
        self.__title_dimensions = self.image_magick.get_text_dimensions(
            self.title_text_commands,
            density=100,
            interline_spacing=self.font_interline_spacing,
            line_count=len(self.title_text.splitlines()),
        )

        """
        convert -size 3200x1800 xc:black -fill white -draw "polygon 0,1000 3200,800 3200,1800 0,1800" mask.png
        """

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            f'-density 100',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Add remaining sub-components
            # *self.title_text_commands,
            # *self.index_text_commands,
            f'-background transparent',
            f'\( '
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
