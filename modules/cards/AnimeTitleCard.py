from pathlib import Path
from typing import Optional

from modules.BaseCardType import BaseCardType, ImageMagickCommands


class AnimeTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards in
    the anime-styled cards designed by reddit user /u/Recker_Man. These
    cards support custom fonts, and optional kanji text.
    """


    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'anime'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 25,   # Character count to begin splitting titles
        'max_line_count': 4,    # Maximum number of lines a title can take up
        'top_heavy': False,     # This class uses bottom heavy titling
    }

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Anime Style'

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Flanker Griffo.otf').resolve())
    DEFAULT_FONT_CASE = 'source'
    TITLE_COLOR = 'white'
    FONT_REPLACEMENTS = {'♡': '', '☆': '', '✕': 'x'}

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = True

    """Source path for the gradient image overlayed over all title cards"""
    __GRADIENT_IMAGE: Path = REF_DIRECTORY / 'GRADIENT.png'

    """Path to the font to use for the kanji font"""
    KANJI_FONT = REF_DIRECTORY / 'hiragino-mincho-w3.ttc'

    """Font characteristics for the series count text"""
    SERIES_COUNT_FONT = REF_DIRECTORY / 'Avenir.ttc'
    SERIES_COUNT_TEXT_COLOR = '#CFCFCF'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_file', 'font_kerning', 'font_size', 'font_stroke_width',
        'font_interline_spacing', 'font_interword_spacing',
        'font_vertical_shift', 'omit_gradient', 'stroke_color', 'separator',
        'kanji', 'use_kanji', 'require_kanji', 'kanji_vertical_shift',
        'episode_text_color',
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
            kanji: Optional[str] = None,
            episode_text_color: str = SERIES_COUNT_TEXT_COLOR,
            separator: str = '·',
            omit_gradient: bool = False,
            require_kanji: bool = False,
            kanji_vertical_shift: float = 0.0,
            stroke_color: str = 'black',
            preferences: Optional['Preferences'] = None, # type: ignore
            **unused,
        ) -> None:

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store source and output file
        self.source_file = source_file
        self.output_file = card_file

        # Escape title, season, and episode text
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text.upper())
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())
        self.hide_season_text = hide_season_text or len(season_text) == 0
        self.hide_episode_text = hide_episode_text or len(episode_text) == 0

        # Store kanji, set bool for whether to use it or not
        self.kanji = self.image_magick.escape_chars(kanji)
        self.use_kanji = kanji is not None
        self.require_kanji = require_kanji
        self.kanji_vertical_shift = float(kanji_vertical_shift)

        # Font customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.episode_text_color = episode_text_color
        self.separator = separator
        self.omit_gradient = omit_gradient
        self.stroke_color = stroke_color


    @property
    def __title_text_global_effects(self) -> ImageMagickCommands:
        """
        ImageMagick commands to implement the title text's global
        effects. Specifically the the font, kerning, fontsize, and
        southwest gravity.

        Returns:
            List of ImageMagick commands.
        """

        kerning = 2.0 * self.font_kerning
        interline_spacing = -30 + self.font_interline_spacing
        font_size = 150 * self.font_size

        return [
            f'-font "{self.font_file}"',
            f'-kerning {kerning}',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-pointsize {font_size}',
            f'-gravity southwest',
        ]


    @property
    def __title_text_black_stroke(self) -> ImageMagickCommands:
        """
        ImageMagick commands to implement the title text's black stroke.

        Returns:
            List of ImageMagick commands.
        """

        # No stroke, return empty command
        if self.font_stroke_width == 0:
            return []

        stroke_width = 5 * self.font_stroke_width

        return [
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width}',
        ]


    @property
    def __title_text_effects(self) -> ImageMagickCommands:
        """
        ImageMagick commands to implement the title text's standard
        effects.

        Returns:
            List of ImageMagick commands.
        """

        return [
            f'-fill "{self.font_color}"',
            f'-stroke "{self.font_color}"',
            f'-strokewidth 0.5',
        ]


    @property
    def __series_count_text_global_effects(self) -> ImageMagickCommands:
        """
        ImageMagick commands for global text effects applied to all
        series count text (season/episode count and dot).

        Returns:
            List of ImageMagick commands.
        """

        return [
            f'-font "{self.SERIES_COUNT_FONT.resolve()}"',
            f'-kerning 2',
            f'-pointsize 67',
            f'-interword-spacing 25',
            f'-gravity southwest',
        ]


    @property
    def __series_count_text_black_stroke(self) -> ImageMagickCommands:
        """
        ImageMagick commands for adding the necessary black stroke
        effects to series count text.

        Returns:
            List of ImageMagick commands.
        """

        return [
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 6',
        ]


    @property
    def title_text_command(self) -> ImageMagickCommands:
        """
        Subcommand for adding title text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # Base offset for the title text
        base_offset = 175 + self.font_vertical_shift

        # If adding kanji, add additional annotate commands for kanji
        if self.use_kanji:
            linecount = len(self.title_text.split('\n')) - 1
            variable_offset = 200 + ((165 + self.font_interline_spacing) * linecount)
            kanji_offset = base_offset + variable_offset * self.font_size
            kanji_offset += self.font_vertical_shift + self.kanji_vertical_shift

            return [
                *self.__title_text_global_effects,
                *self.__title_text_black_stroke,
                f'-annotate +75+{base_offset} "{self.title_text}"',
                *self.__title_text_effects,
                f'-annotate +75+{base_offset} "{self.title_text}"',
                f'-font "{self.KANJI_FONT.resolve()}"',
                *self.__title_text_black_stroke,
                f'-pointsize {85 * self.font_size}',
                f'-annotate +75+{kanji_offset} "{self.kanji}"',
                *self.__title_text_effects,
                f'-annotate +75+{kanji_offset} "{self.kanji}"',
            ]

        # No kanji, just add title
        return [
            *self.__title_text_global_effects,
            *self.__title_text_black_stroke,
            f'-annotate +75+{base_offset} "{self.title_text}"',
            *self.__title_text_effects,
            f'-annotate +75+{base_offset} "{self.title_text}"',
        ]


    @property
    def index_text_command(self) -> ImageMagickCommands:
        """
        Subcommand for adding the index text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # Hiding all index text, return blank commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Add only season or episode text
        if self.hide_season_text or self.hide_episode_text:
            text = self.episode_text if self.hide_season_text else self.season_text
            return [
                *self.__series_count_text_global_effects,
                *self.__series_count_text_black_stroke,
                f'-annotate +75+90 "{text}"',
                f'-fill "{self.episode_text_color}"',
                f'-stroke "{self.episode_text_color}"',
                f'-strokewidth 0',
                f'-annotate +75+90 "{text}"',
            ]

        # Add season and episode text
        return [
            f'-background transparent',
            *self.__series_count_text_global_effects,
            *self.__series_count_text_black_stroke,
            # Black stroke behind season and episode text
            f'\( -gravity center',
            # Black stroke uses same font for season/episode text
            f'label:"{self.season_text} {self.separator}"',
            f'label:"{self.episode_text}"',
            # Combine season+episode text into one "image"
            f'+smush 30 \)',        # Smush less for black stroke
            f'-gravity southwest',
            # Overlay black stroke "image"
            f'-geometry +73+88',    # Different offset for black stroke
            f'-composite',
            # Primary season+episode text
            *self.__series_count_text_global_effects,
            f'-fill "{self.episode_text_color}"',
            f'-stroke "{self.episode_text_color}"',
            f'\( -gravity center',
            # Season text and separator uses larger stroke
            f'-strokewidth 2',
            f'label:"{self.season_text} {self.separator}"',
            # Zero-width stroke for episode text
            f'-strokewidth 0',
            f'label:"{self.episode_text}"',
            # Combine season+episode text "images"
            f'+smush 35 \)',
            # Add text to source image
            f'-gravity southwest',
            f'-geometry +75+90',
            f'-composite',
        ]


    @staticmethod
    def modify_extras(
            extras: dict,
            custom_font: bool,
            custom_season_titles: bool,
        ) -> None:
        """
        Modify the given extras base on whether font or season titles
        are custom.

        Args:
            extras: Dictionary to modify.
            custom_font: Whether the font are custom.
            custom_season_titles: Whether the season titles are custom.
        """

        # Generic font, reset kanji vertical shift key
        if not custom_font:
            if 'kanji_vertical_shift' in extras:
                extras['kanji_vertical_shift'] = 0


    @staticmethod
    def is_custom_font(font: 'Font') -> bool: # type: ignore
        """
        Determines whether the given arguments represent a custom font
        for this card.

        Args:
            font: The Font being evaluated.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.color != AnimeTitleCard.TITLE_COLOR)
            or (font.file != AnimeTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
            or (font.stroke_width != 1.0)
            or (font.vertical_shift != 0)
        )


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> bool:
        """
        Determines whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        standard_etf = AnimeTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # Sub-command to optionally add gradient
        gradient_command = []
        if not self.omit_gradient:
            gradient_command = [
                f'"{self.__GRADIENT_IMAGE.resolve()}"',
                f'-composite',
            ]

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and optionally blur source image
            *self.resize_and_style,
            # Increase contrast of source image
            f'-modulate 100,125',
            # Overlay gradient
            *gradient_command,
            # Add title or title+kanji
            *self.title_text_command,
            # Add season or season+episode text
            *self.index_text_command,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
