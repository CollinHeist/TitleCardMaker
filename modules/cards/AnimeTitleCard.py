from pathlib import Path
from typing import Any, Optional

from modules.BaseCardType import BaseCardType
from modules.Debug import log

SeriesExtra = Optional

class AnimeTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards in
    the anime-styled cards designed by reddit user /u/Recker_Man. These
    cards support custom fonts, and optional kanji text.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Anime',
        example='/assets/cards/anime.jpg',
        creators=['/u/Recker_Man', 'CollinHeist'],
        source='local',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Kanji Text',
                identifier='kanji',
                description='Japanese text to place above title text',
            ), Extra(
                name='Require Kanji Text',
                identifier='require_kanji',
                description='Whether to require kanji text for card creation',
            ), Extra(
                name='Kanji Vertical Shift',
                identifier='kanji_vertical_shift',
                description='Additional vertical offset to apply only to kanji text',
            ), Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
            ), Extra(
                name='Stroke Text Color',
                identifier='stroke_color',
                description='Color to use for the text stroke',
            ), Extra(
                name='Gradient Omission',
                identifier='omit_gradient',
                description='Whether to omit the gradient overlay from the card',
            ), Extra(
                name='Gradient Omission',
                identifier='omit_gradient',
                description='Whether to omit the gradient overlay from the card',
            ),
        ], description=[
            'Title card with all text aligned in the lower left of the image.',
            'Although it is referred to as the "anime" card style, the only '
            'Anime specific feature is the ability to add Kani (Japanese) text'
            'above the title text.',
        ]
    )

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
        'source_file', 'output_file', 'title', 'kanji', 'use_kanji',
        'require_kanji', 'kanji_vertical_shift', 'season_text', 'episode_text',
        'hide_season', 'separator', 'font', 'font_size', 'font_color',
        'vertical_shift', 'interline_spacing', 'kerning', 'stroke_width',
        'omit_gradient', 'stroke_color', 'hide_episode_text',
    )

    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title: str,
            season_text: str,
            episode_text: str,
            hide_season_text: bool = False,
            hide_episode_text: bool = False,
            font_file: str = TITLE_FONT,
            font_color: str = TITLE_COLOR,
            font_size: float = 1.0,
            font_interline_spacing: int = 0,
            font_kerning: float = 1.0,
            font_stroke_width: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            kanji: SeriesExtra[str] = None,
            separator: SeriesExtra[str] = '·',
            omit_gradient: SeriesExtra[bool] = False,
            require_kanji: SeriesExtra[bool] = False,
            kanji_vertical_shift: SeriesExtra[float] = 0,
            stroke_color: SeriesExtra[str] = 'black',
            preferences: 'Preferences' = None,
            **unused) -> None:
        """
        Construct a new instance of this card.

        Args:
            source: Source image for this card.
            output_file: Output filepath for this card.
            title: The title for this card.
            season_text: The season text for this card.
            episode_text: The episode text for this card.
            font: Font name or path (as string) to use for episode title.
            font_size: Scalar to apply to the title font size.
            title_color: Color to use for title text.
            hide_season: Whether to hide the season text.
            vertical_shift: Vertical shift to apply to the title and
                kanji text.
            interline_spacing: Offset to interline spacing of title text
            kerning: Scalar to apply to kerning of the title text.
            stroke_width: Scalar to apply to stroke.
            blur: Whether to blur the source image.
            grayscale: Whether to make the source image grayscale.
            kanji: Kanji text to place above the episode title.
            separator: Character to use to separate season/episode text.
            omit_gradient: Whether to omit the gradient overlay.
            require_kanji: Whether to require kanji for this card.
            kanji_vertical_shift: Vertical shift to apply to kanji text.
            stroke_color: Color to use for the back-stroke color.
            unused: Unused arguments.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store source and output file
        self.source_file = source_file
        self.output_file = card_file

        # Escape title, season, and episode text
        self.hide_season = hide_season_text
        self.hide_episode_text = hide_episode_text
        self.title = self.image_magick.escape_chars(title)
        self.season_text = self.image_magick.escape_chars(season_text.upper())
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())

        # Store kanji, set bool for whether to use it or not
        self.kanji = self.image_magick.escape_chars(kanji)
        self.use_kanji = (kanji is not None)
        self.require_kanji = require_kanji
        self.kanji_vertical_shift = float(kanji_vertical_shift)

        # Font customizations
        self.font = font_file
        self.font_size = font_size
        self.font_color = font_color
        self.vertical_shift = font_vertical_shift
        self.interline_spacing = font_interline_spacing
        self.kerning = font_kerning
        self.stroke_width = font_stroke_width

        # Optional extras
        self.separator = separator
        self.omit_gradient = omit_gradient
        self.stroke_color = stroke_color


    @property
    def __title_text_global_effects(self) -> list:
        """
        ImageMagick commands to implement the title text's global
        effects. Specifically the the font, kerning, fontsize, and
        southwest gravity.

        Returns:
            List of ImageMagick commands.
        """

        kerning = 2.0 * self.kerning
        interline_spacing = -30 + self.interline_spacing
        font_size = 150 * self.font_size

        return [
            f'-font "{self.font}"',
            f'-kerning {kerning}',
            f'-interline-spacing {interline_spacing}',
            f'-pointsize {font_size}',
            f'-gravity southwest',
        ]


    @property
    def __title_text_black_stroke(self) -> list[str]:
        """
        ImageMagick commands to implement the title text's black stroke.

        Returns:
            List of ImageMagick commands.
        """

        # No stroke, return empty command
        if self.stroke_width == 0:
            return []

        stroke_width = 5 * self.stroke_width

        return [
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width}',
        ]


    @property
    def __title_text_effects(self) -> list[str]:
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
    def __series_count_text_global_effects(self) -> list[str]:
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
    def __series_count_text_black_stroke(self) -> list:
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
    def title_text_command(self) -> list[str]:
        """
        Subcommand for adding title text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # Base offset for the title text
        base_offset = 175 + self.vertical_shift

        # If adding kanji, add additional annotate commands for kanji
        if self.use_kanji:
            linecount = len(self.title.split('\n')) - 1
            variable_offset = 200 + ((165 + self.interline_spacing) * linecount)
            kanji_offset = base_offset + variable_offset * self.font_size
            kanji_offset += self.vertical_shift + self.kanji_vertical_shift

            return [
                *self.__title_text_global_effects,
                *self.__title_text_black_stroke,
                f'-annotate +75+{base_offset} "{self.title}"',
                *self.__title_text_effects,
                f'-annotate +75+{base_offset} "{self.title}"',
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
            f'-annotate +75+{base_offset} "{self.title}"',
            *self.__title_text_effects,
            f'-annotate +75+{base_offset} "{self.title}"',
        ]


    @property
    def index_text_command(self) -> list[str]:
        """
        Subcommand for adding the index text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # Hiding all index text, return blank commands
        if self.hide_season and self.hide_episode_text:
            return []

        # Add only episode text
        if self.hide_season:
            return [
                *self.__series_count_text_global_effects,
                *self.__series_count_text_black_stroke,
                f'-annotate +75+90 "{self.episode_text}"',
                f'-fill "{self.SERIES_COUNT_TEXT_COLOR}"',
                f'-stroke "{self.SERIES_COUNT_TEXT_COLOR}"',
                f'-strokewidth 0',
                f'-annotate +75+90 "{self.episode_text}"',
            ]
        
        # Add only season text
        if self.hide_episode_text:
            return [
                *self.__series_count_text_global_effects,
                *self.__series_count_text_black_stroke,
                f'-annotate +75+90 "{self.season_text}"',
                f'-fill "{self.SERIES_COUNT_TEXT_COLOR}"',
                f'-stroke "{self.SERIES_COUNT_TEXT_COLOR}"',
                f'-strokewidth 0',
                f'-annotate +75+90 "{self.season_text}"',
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
            f'-fill "{self.SERIES_COUNT_TEXT_COLOR}"',
            f'-stroke "{self.SERIES_COUNT_TEXT_COLOR}"',
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
            extras: dict[str, Any],
            custom_font: bool,
            custom_season_titles: bool) -> None:
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
    def is_custom_font(font: 'Font') -> bool:
        """
        Determines whether the given arguments represent a custom font
        for this card.

        Args:
            font: The Font being evaluated.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.file != AnimeTitleCard.TITLE_FONT)
            or (font.size != 1.0)
            or (font.color != AnimeTitleCard.TITLE_COLOR)
            or (font.vertical_shift != 0)
            or (font.interline_spacing != 0)
            or (font.kerning != 1.0)
            or (font.stroke_width != 1.0))


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool, episode_text_format: str) -> bool:
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

        # If kanji is required, and not given, error
        if self.require_kanji and not self.use_kanji:
            log.error(f'Kanji is required and not provided - skipping card '
                      f'"{self.output_file.name}"')
            return None

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