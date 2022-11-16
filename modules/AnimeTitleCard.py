from pathlib import Path
from typing import Any

from modules.BaseCardType import BaseCardType
from modules.Debug import log

class AnimeTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards in the
    anime-styled cards designed by reddit user /u/Recker_Man. These cards don't
    support custom fonts, but does support optional kanji text.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'anime'

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
        'vertical_shift', 'interline_spacing', 'kerning'
    )
    
    def __init__(self, source: Path, output_file: Path, title: str, 
                 season_text: str, episode_text: str, font: str,font_size:float,
                 title_color: str, hide_season: bool, vertical_shift: int=0,
                 interline_spacing: int=0, kerning: float=1.0, kanji: str=None,
                 require_kanji: bool=False, kanji_vertical_shift: float=0,
                 separator: str='·', blur: bool=False, grayscale: bool=False,
                 **kwargs)->None:
        """
        Construct a new instance.
        
        Args:
            source: Source image for this card.
            output_file: Output filepath for this card.
            title: The title for this card.
            season_text: The season text for this card.
            episode_text: The episode text for this card.
            font: Font name or path (as string) to use for episode title.
            font_size: Scalar to apply to the title font size.
            title_color: Color to use for title text.
            hide_season: Whether to hide the season text on this card
            vertical_shift: Vertical shift to apply to the title and kanji
                text.
            interline_spacing: Offset to interline spacing of the title text
            kanji: Kanji text to place above the episode title on this card.
            require_kanji: Whether to require kanji for this card.
            kanji_vertical_shift: Vertical shift to apply to just kanji text.
            separator: Character to use to separate season and episode text.
            blur: Whether to blur the source image.
            grayscale: Whether to make the source image grayscale.
            kwargs: Unused arguments.
        """
        
        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        # Store source and output file
        self.source_file = source
        self.output_file = output_file

        # Escape title, season, and episode text
        self.title = self.image_magick.escape_chars(title)
        self.season_text = self.image_magick.escape_chars(season_text.upper())
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())

        # Store kanji, set bool for whether to use it or not
        self.kanji = self.image_magick.escape_chars(kanji)
        self.use_kanji = (kanji is not None)
        self.require_kanji = require_kanji
        self.kanji_vertical_shift = float(kanji_vertical_shift)

        # Font customizations
        self.font = font
        self.font_size = font_size
        self.font_color = title_color
        self.vertical_shift = vertical_shift
        self.interline_spacing = interline_spacing
        self.kerning = kerning

        # Miscellaneous attributes
        self.hide_season = hide_season
        self.separator = separator


    @property
    def __title_text_global_effects(self) -> list:
        """
        ImageMagick commands to implement the title text's global effects.
        Specifically the the font, kerning, fontsize, and southwest gravity.
        
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

        return [
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 5',
        ]


    @property
    def __title_text_effects(self) -> list[str]:
        """
        ImageMagick commands to implement the title text's standard effects.
        
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
        ImageMagick commands for global text effects applied to all series count
        text (season/episode count and dot).
        
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
        ImageMagick commands for adding the necessary black stroke effects to
        series count text.
        
        Returns:
            List of ImageMagick commands.
        """

        return [
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 6',
        ]


    @property
    def title_command(self) -> list[str]:
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
    def index_command(self) -> list[str]:
        """
        Subcommand for adding the index text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # Add only episode text using annotate
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
            
        # Add season+episode text
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
    def modify_extras(extras: dict[str, Any], custom_font: bool,
                      custom_season_titles: bool) -> None:
        """
        Modify the given extras base on whether font or season titles are
        custom.

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
        Determines whether the given arguments represent a custom font for this
        card. This CardType only uses custom font cases.
        
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
    def is_custom_season_titles(custom_episode_map: bool, 
                                episode_text_format: str) -> bool:
        """
        Determines whether the given attributes constitute custom or generic
        season titles.
        
        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.
        
        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        standard_etf = AnimeTitleCard.EPISODE_TEXT_FORMAT.upper()
        
        return (custom_episode_map or
                episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this object's
        defined title card.
        """

        # If kanji is required, and not given, error
        if self.require_kanji and not self.use_kanji:
            log.error(f'Kanji is required and not provided - skipping card '
                      f'"{self.output_file.name}"')
            return None

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and optionally blur source image
            *self.resize_and_style,
            # Increase contrast of source image
            f'-modulate 100,125',
            # Overlay gradient
            f'"{self.__GRADIENT_IMAGE.resolve()}"',
            f'-composite',
            # Add title or title+kanji
            *self.title_command,
            # Add season or season+episode text
            *self.index_command,
            f'"{self.output_file.resolve()}"',
        ])
        
        self.image_magick.run(command)