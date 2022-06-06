from pathlib import Path
from re import findall

from modules.CardType import CardType
from modules.Debug import log

class AnimeTitleCard(CardType):
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
        'max_line_count': 3,    # Maximum number of lines a title can take up
        'top_heavy': False,     # This class uses bottom heavy titling
    }

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Anime Style'

    """Path to the font to use for the episode title"""
    TITLE_FONT = str((REF_DIRECTORY / 'Flanker Griffo.otf').resolve())
    DEFAULT_FONT_CASE = 'source'

    """Color to use for the episode title"""
    TITLE_COLOR = 'white'

    """Color of the episode/episode number text"""
    EPISODE_TEXT_COLOR = 'white'

    """Default characters to replace in the generic font"""
    FONT_REPLACEMENTS = {}

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = True

    """Source path for the gradient image overlayed over all title cards"""
    __GRADIENT_IMAGE: Path = REF_DIRECTORY / 'GRADIENT.png'

    """Path to the font to use for the kanji font"""
    KANJI_FONT = REF_DIRECTORY / 'hiragino-mincho-w3.ttc'

    """Path to the font to use for the series count text"""
    SERIES_COUNT_FONT = REF_DIRECTORY / 'Avenir.ttc'

    """Character used to join season and episode text (with spacing)"""
    SERIES_COUNT_JOIN_CHARACTER = '·'

    SERIES_COUNT_TEXT_COLOR = '#CFCFCF'

    """Paths to intermediate files that are deleted after the card is created"""
    __CONSTRAST_SOURCE = CardType.TEMP_DIR / 'adj_source.png'
    __SOURCE_WITH_GRADIENT = CardType.TEMP_DIR / 'source_with_gradient.png'
    __GRADIENT_WITH_TITLE = CardType.TEMP_DIR / 'gradient_with_title.png'

    
    def __init__(self, source: Path, output_file: Path, title: str, 
                 season_text: str, episode_text: str, hide_season: bool,
                 kanji: str=None, require_kanji: bool=False, blur: bool=False,
                 font_size: float=1.0, *args, **kwargs) -> None:
        """
        Constructs a new instance.
        
        :param      source:             Source image for this card.
        :param      output_file:        Output filepath for this card.
        :param      title:              The title for this card.
        :param      season_text:        The season text for this card.
        :param      episode_text:       The episode text for this card.
        :param      hide_season:        Whether to hide the season text on this
                                        card.
        :param      kanji:              Kanji text to place above the
                                        episode title on this card.
        :param      require_kanji:      Whether to require kanji for this card.
        :param      blur:               Whether to blur the source image.
        :param      font_size:          Scalar to apply to the title font size.
        :param      args and kwargs:    Unused arguments to permit generalized
                                        function calls for any CardType.
        """
        
        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__()

        # Store source and output file
        self.source_file = source
        self.output_file = output_file

        # Apply titlecase case function, escape characters
        self.title = self.image_magick.escape_chars(title)

        # Store kanji, set bool for whether to use it or not
        self.kanji = self.image_magick.escape_chars(kanji)
        self.use_kanji = (kanji is not None)
        self.require_kanji = require_kanji

        # Store season and episode text
        self.season_text = self.image_magick.escape_chars(season_text.upper())
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())
        self.hide_season = hide_season
        self.blur = blur

        # Font customizations
        self.font_size = font_size


    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object."""

        return (f'<AnimeTitleCard {self.source_file=}, {self.output_file=}, '
                f'{self.title=}, {self.kanji=}, {self.season_text=}, '
                f'{self.episode_text=}, {self.blur=}, {self.font_size=}>')


    def __title_text_global_effects(self) -> list:
        """
        ImageMagick commands to implement the title text's global effects.
        Specifically the the font, kerning, fontsize, and southwest gravity.
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-font "{self.TITLE_FONT}"',
            f'-kerning 2',
            f'-interline-spacing -30',
            f'-pointsize {150 * self.font_size}',
            f'-gravity southwest',
        ]


    def __title_text_black_stroke(self) -> list:
        """
        ImageMagick commands to implement the title text's black stroke.
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 5',
        ]


    def __title_text_effects(self) -> list:
        """
        ImageMagick commands to implement the title text's standard effects.
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-fill white',
            f'-stroke white',
            f'-strokewidth 0.5',
        ]


    def __series_count_text_global_effects(self) -> list:
        """
        ImageMagick commands for global text effects applied to all series count
        text (season/episode count and dot).
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-font "{self.SERIES_COUNT_FONT.resolve()}"',
            f'-kerning 2',
            f'-pointsize 67',
            f'-interword-spacing 25',
            f'-gravity southwest',
        ]


    def __series_count_text_black_stroke(self) -> list:
        """
        ImageMagick commands for adding the necessary black stroke effects to
        series count text.
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 6',
        ]


    def __series_count_text_effects(self) -> list:
        """
        ImageMagick commands for adding the necessary text effects to the series
        count text.
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-fill "{self.SERIES_COUNT_TEXT_COLOR}"',
            f'-stroke "{self.SERIES_COUNT_TEXT_COLOR}"',
        ]


    def __increase_contrast(self) -> Path:
        """
        Increases the contrast of this card's source image.
        
        :returns:   Path to the created image.
        """

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            f'+profile "*"',    # To avoid profile conversion warnings
            f'-modulate 100,125',
            f'"{self.__CONSTRAST_SOURCE.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__CONSTRAST_SOURCE


    def __add_gradient(self, image: Path) -> Path:
        """
        Add the static gradient to the given image, and resizes to the standard
        title card size.
        
        :returns:   Path to the created image.
        """

        command = ' '.join([
            f'convert "{image.resolve()}"',
            f'-profile "*"',
            f'-gravity center',
            f'-resize "{self.TITLE_CARD_SIZE}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            f'"{self.__GRADIENT_IMAGE.resolve()}"',
            f'-background None',
            f'-layers Flatten',
            f'"{self.__SOURCE_WITH_GRADIENT.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__SOURCE_WITH_GRADIENT


    def __add_title_text(self, gradient_image: Path) -> Path:
        """
        Adds episode title text to the provide image.

        :param      gradient_image: The image with gradient added.
        
        :returns:   Path to the created image that has a gradient and the title
                    text added.
        """

        command = ' '.join([
            f'convert "{gradient_image.resolve()}"',
            *self.__title_text_global_effects(),
            *self.__title_text_black_stroke(),
            f'-annotate +75+175 "{self.title}"',
            *self.__title_text_effects(),
            f'-annotate +75+175 "{self.title}"',
            f'"{self.__GRADIENT_WITH_TITLE.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__GRADIENT_WITH_TITLE


    def __add_title_and_kanji_text(self, gradient_image: Path) -> Path:
        """
        Adds episode title text and kanji to the provide image.

        :param      gradient_image: The image with gradient added.
        
        :returns:   Path to the created image that has a gradient, the title
                    text, and kanji added.
        """

        # Shift kanji text up based on the number of lines in the title
        base_offset = 175
        variable_offset = 200 + (165 * (len(self.title.split('\n'))-1))
        kanji_offset = base_offset + variable_offset * self.font_size

        command = ' '.join([
            f'convert "{gradient_image.resolve()}"',
            *self.__title_text_global_effects(),
            *self.__title_text_black_stroke(),
            f'-annotate +75+175 "{self.title}"',
            *self.__title_text_effects(),
            f'-annotate +75+175 "{self.title}"',
            f'-font "{self.KANJI_FONT.resolve()}"',
            *self.__title_text_black_stroke(),
            f'-pointsize {85 * self.font_size}',
            f'-annotate +75+{kanji_offset} "{self.kanji}"',
            *self.__title_text_effects(),
            f'-annotate +75+{kanji_offset} "{self.kanji}"',
            f'"{self.__GRADIENT_WITH_TITLE.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__GRADIENT_WITH_TITLE


    def __add_series_count_text(self, titled_image: Path) -> Path:
        """
        Adds the series count text; including season and episode number.
        
        :param      titled_image:  The titled image to add text to.

        :returns:   Path to the created image (the output file).
        """

        # Construct season text
        season_text = f'{self.season_text} {self.SERIES_COUNT_JOIN_CHARACTER} '

        # Command list used by both the metric and season text command
        season_text_command_list = [
            *self.__series_count_text_global_effects(),
            f'-gravity southwest',
            *self.__series_count_text_black_stroke(),
            f'-annotate +75+90 "{season_text}"',
            *self.__series_count_text_effects(),
            f'-strokewidth 2',
            f'-annotate +75+90 "{season_text}"',
        ]

        # Construct command for getting the width of the season text
        width_command = ' '.join([
            f'convert -debug annotate "{titled_image.resolve()}"',
            *season_text_command_list,
            ' null: 2>&1',
        ])

        # Get the width of the season text (reported twice, get first width)
        metrics = self.image_magick.run_get_output(width_command)
        width = list(map(int, findall(r'Metrics:.*width:\s+(\d+)', metrics)))[0]

        # Construct command to add season and episode text
        command = ' '.join([
            f'convert "{titled_image.resolve()}"',
            *season_text_command_list,
            *self.__series_count_text_black_stroke(),
            f'-annotate +{75+width}+90 "{self.episode_text}"',
            *self.__series_count_text_effects(),
            f'-strokewidth 0',
            f'-annotate +{75+width}+90 "{self.episode_text}"',
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output_file


    def __add_series_count_text_no_season(self, titled_image: Path) -> Path:
        """
        Adds the series count text without the season text.
        
        :param      titled_image:  The titled image to add text to.

        :returns:   Path to the created image (the output file).
        """

        command = ' '.join([
            f'convert "{titled_image.resolve()}"',
            *self.__series_count_text_global_effects(),
            *self.__series_count_text_black_stroke(),
            f'-annotate +75+90 "{self.episode_text}"',
            *self.__series_count_text_effects(),
            f'-strokewidth 0',
            f'-annotate +75+90 "{self.episode_text}"',
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output_file


    @staticmethod
    def is_custom_font(font: 'Font') -> bool:
        """
        Determines whether the given arguments represent a custom font for this
        card. This CardType only uses custom font cases.
        
        :param      font:   The Font being evaluated.
        
        :returns:   True if the given font uses a case function other than
                    'title', False otherwise.
        """

        return ((font.case_name != AnimeTitleCard.DEFAULT_FONT_CASE)
            or (font.size != 1.0))


    @staticmethod
    def is_custom_season_titles(custom_episode_map: bool, 
                                episode_text_format: str) -> bool:
        """
        Determines whether the given attributes constitute custom or generic
        season titles.
        
        :param      custom_episode_map:     Whether the EpisodeMap was
                                            customized.
        :param      episode_text_format:    The episode text format in use.
        
        :returns:   True if custom season titles are indicated, False otherwise.
        """

        standard_etf = AnimeTitleCard.EPISODE_TEXT_FORMAT.upper()
        
        return (custom_episode_map or
                episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this object's
        defined title card.
        """

        # If kanji is required (and not given), error!
        if self.require_kanji and not self.use_kanji:
            log.error(f'Kanji is required and not provided - skipping card')
            return None
        
        # Create the output directory and any necessary parents 
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Increase contrast of source image
        adjusted_image = self.__increase_contrast()
        
        # Add the gradient and resize the source image
        gradient_image = self.__add_gradient(adjusted_image)

        # Add title text and optional kanji
        if self.use_kanji:
            titled_image = self.__add_title_and_kanji_text(gradient_image)
        else:
            titled_image = self.__add_title_text(gradient_image)

        # If season text is hidden, just add episode text 
        if self.hide_season:
            self.__add_series_count_text_no_season(titled_image)
        else:
            self.__add_series_count_text(titled_image)

        # Delete all intermediate images
        self.image_magick.delete_intermediate_images(
            adjusted_image, gradient_image, titled_image
        )

