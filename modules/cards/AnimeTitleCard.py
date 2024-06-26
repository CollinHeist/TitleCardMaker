from pathlib import Path
from typing import TYPE_CHECKING, Optional

from modules.BaseCardType import BaseCardType, ImageMagickCommands
from modules.Debug import log

if TYPE_CHECKING:
    from modules.PreferenceParser import PreferenceParser
    from modules.Font import Font


class AnimeTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards in
    the anime-styled cards designed by Reddit user /u/Recker_Man. These
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
    EPISODE_STROKE_COLOR = 'black'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_file', 'font_kerning', 'font_size', 'font_stroke_width',
        'font_interline_spacing', 'font_interword_spacing',
        'font_vertical_shift', 'omit_gradient', 'stroke_color', 'separator',
        'kanji', 'use_kanji', 'require_kanji', 'kanji_vertical_shift',
        'episode_text_color', 'kanji_color', 'episode_stroke_color',
        'kanji_stroke_color', 'kanji_stroke_width', 'kanji_font_size',
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
            episode_stroke_color: str = EPISODE_STROKE_COLOR,
            episode_text_color: str = SERIES_COUNT_TEXT_COLOR,
            separator: str = '·',
            omit_gradient: bool = False,
            require_kanji: bool = False,
            kanji_color: str = TITLE_COLOR,
            kanji_font_size: float = 1.0,
            kanji_stroke_color: str = 'black',
            kanji_stroke_width: float = 1.0,
            kanji_vertical_shift: float = 0.0,
            stroke_color: str = 'black',
            preferences: Optional['PreferenceParser'] = None,
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
        self.kanji_vertical_shift = kanji_vertical_shift

        # Font customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = -30 + font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = 2.0 * font_kerning
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.episode_stroke_color = episode_stroke_color
        self.episode_text_color = episode_text_color
        self.omit_gradient = omit_gradient
        self.kanji_color = kanji_color
        self.kanji_font_size = kanji_font_size
        self.kanji_stroke_color = kanji_stroke_color
        self.kanji_stroke_width = kanji_stroke_width
        self.separator = separator
        self.stroke_color = stroke_color


    @property
    def __title_text_global_effects(self) -> ImageMagickCommands:
        """
        ImageMagick commands to implement the title text's global
        effects. Specifically the the font, kerning, fontsize, and
        southwest gravity.
        """

        font_size = 150 * self.font_size

        return [
            f'-font "{self.font_file}"',
            f'-kerning {self.font_kerning}',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-pointsize {font_size}',
            f'-gravity southwest',
        ]


    @property
    def __title_text_black_stroke(self) -> ImageMagickCommands:
        """
        ImageMagick commands to implement the title text's black stroke.
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
        """Subcommands to implement the title text's standard effects."""

        return [
            f'-fill "{self.font_color}"',
            f'-stroke "{self.font_color}"',
            f'-strokewidth 0.5',
        ]


    @property
    def __series_count_text_global_effects(self) -> ImageMagickCommands:
        """
        Subcommands for global text effects applied to all series count
        text (season/episode count and dot).
        """

        return [
            f'-font "{self.SERIES_COUNT_FONT.resolve()}"',
            f'-kerning 2',
            f'-pointsize 67',
            f'-interword-spacing 25',
            f'-gravity southwest',
        ]


    @property
    def title_text_command(self) -> ImageMagickCommands:
        """
        Subcommands for adding title and kanji text to the source image.
        """

        # Base offset for the title text
        base_offset = 175 + self.font_vertical_shift

        title_commands = [
            *self.__title_text_global_effects,
            *self.__title_text_black_stroke,
            f'-annotate +75+{base_offset} "{self.title_text}"',
            *self.__title_text_effects,
            f'-annotate +75+{base_offset} "{self.title_text}"',
        ]

        if not self.use_kanji:
            return title_commands

        # Determine kanji positioning based on height of title text
        _, title_height = self.image_magick.get_text_dimensions(
            [
                *self.__title_text_global_effects,
                *self.__title_text_effects,
                f'-annotate +75+{base_offset} "{self.title_text}"',
            ],
            interline_spacing=self.font_interline_spacing,
            line_count=len(self.title_text.splitlines()),
            width='max', height='sum'
        )
        kanji_offset = base_offset + title_height + self.kanji_vertical_shift

        return [
            *title_commands,
            f'-font "{self.KANJI_FONT.resolve()}"',
            f'-kerning -3.0',
            f'-pointsize {85 * self.kanji_font_size}',
            f'-strokewidth {5 * self.kanji_stroke_width:.2f}',
            f'-fill "{self.kanji_stroke_color}"',
            f'-stroke "{self.kanji_stroke_color}"',
            f'-annotate +75+{kanji_offset} "{self.kanji}"',
            f'-fill "{self.kanji_color}"',
            f'-stroke "{self.kanji_stroke_color}"',
            f'-strokewidth 0.5',
            f'-annotate +75+{kanji_offset} "{self.kanji}"',
        ]


    @property
    def index_text_command(self) -> ImageMagickCommands:
        """Subcommand for adding the index text to the source image."""

        # Hiding all index text, return blank commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Add only season or episode text
        if self.hide_season_text or self.hide_episode_text:
            text = self.episode_text if self.hide_season_text else self.season_text
            return [
                *self.__series_count_text_global_effects,
                f'-fill "{self.episode_stroke_color}"',
                f'-stroke "{self.episode_stroke_color}"',
                f'-strokewidth 6',
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
            f'-fill "{self.episode_stroke_color}"',
            f'-stroke "{self.episode_stroke_color}"',
            f'-strokewidth 6',
            # Stroke behind season and episode text
            f'\( -gravity center',
            # Stroke uses same font for season/episode text
            f'label:"{self.season_text} {self.separator}"',
            f'label:"{self.episode_text}"',
            # Combine season and episode text into one "image"
            f'+smush 30 \)',        # Smush less for stroke
            f'-gravity southwest',
            # Overlay stroke "image"
            f'-geometry +73+88',    # Different offset for stroke
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
            if 'episode_stroke_color' in extras:
                extras['episode_stroke_color'] =\
                    AnimeTitleCard.EPISODE_STROKE_COLOR
            if 'episode_text_color' in extras:
                extras['episode_text_color'] =\
                    AnimeTitleCard.SERIES_COUNT_TEXT_COLOR
            if 'kanji_font_size' in extras:
                extras['kanji_font_size'] = 1.0
            if 'kanji_stroke_width' in extras:
                extras['kanji_stroke_width'] = 1.0
            if 'kanji_stroke_color' in extras:
                extras['episode_stroke_color'] = 'black'
            if 'kanji_vertical_shift' in extras:
                extras['kanji_vertical_shift'] = 0
            if 'stroke_color' in extras:
                extras['stroke_color'] = 'black'


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determines whether the given arguments represent a custom font
        for this card.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        custom_extras = (
            ('episode_stroke_color' in extras
                and extras['episode_stroke_color'] != AnimeTitleCard.EPISODE_STROKE_COLOR)
            or ('episode_text_color' in extras
                and extras['episode_text_color'] != AnimeTitleCard.SERIES_COUNT_TEXT_COLOR)
            or ('kanji_color' in extras
                and extras['kanji_color'] != AnimeTitleCard.TITLE_COLOR)
            or ('kanji_font_size' in extras and extras['kanji_font_size'] !=1.0)
            or ('kanji_stroke_color' in extras
                and extras['kanji_stroke_color'] != 'black')
            or ('kanji_stroke_width' in extras
                and extras['kanji_stroke_width'] != 1.0)
            or ('kanji_vertical_shift' in extras
                and extras['kanji_vertical_shift'] != 0)
            or ('stroke_color' in extras
                and extras['stroke_color'] != 'black')
        )

        return custom_extras or AnimeTitleCard._is_custom_font(font)


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
        """Create this object's defined Title Card."""

        # Sub-command to optionally add gradient
        gradient_command = []
        if not self.omit_gradient:
            gradient_command = [
                f'"{self.__GRADIENT_IMAGE.resolve()}"',
                f'-composite',
            ]

        contrast = [f'-modulate 100,125']
        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and optionally blur source image
            *self.resize_and_style,
            # Increase contrast of source image
            *contrast,
            # Overlay gradient
            *gradient_command,
            # Add title and/or kanji
            *self.title_text_command,
            # Add index text
            *self.index_text_command,
            # Attempt to overlay mask
            *self.add_overlay_mask(
                self.source_file,
                pre_processing=self.resize_and_style + contrast,
            ),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
