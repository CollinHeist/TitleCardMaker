from pathlib import Path
from re import findall

from modules.CardType import CardType
from modules.Debug import log

class StandardTitleCard(CardType):
    """
    This class describes a type of CardType that produces the 'generic' title
    cards based on Reddit user /u/UniversalPolymath. This card supports 
    customization of every aspect of the card, but does not use any arbitrary
    data.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 32,   # Character count to begin splitting titles
        'max_line_count': 3,    # Maximum number of lines a title can take up
        'top_heavy': False,     # This class uses bottom heavy titling
    }

    """Default font and text color for episode title text"""
    TITLE_FONT = str((REF_DIRECTORY / 'Sequel-Neue.otf').resolve())
    TITLE_COLOR = '#EBEBEB'

    """Default characters to replace in the generic font"""
    FONT_REPLACEMENTS = {'[': '(', ']': ')', '(': '[', ')': ']', '―': '-',
                         '…': '...'}

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'standard'

    """Source path for the gradient image overlayed over all title cards"""
    __GRADIENT_IMAGE = REF_DIRECTORY / 'GRADIENT.png'

    """Default fonts and color for series count text"""
    SEASON_COUNT_FONT = REF_DIRECTORY / 'Proxima Nova Semibold.otf'
    EPISODE_COUNT_FONT = REF_DIRECTORY / 'Proxima Nova Regular.otf'
    SERIES_COUNT_TEXT_COLOR = '#CFCFCF'

    """Paths to intermediate files that are deleted after the card is created"""
    __SOURCE_WITH_GRADIENT = CardType.TEMP_DIR / 'source_gradient.png'
    __GRADIENT_WITH_TITLE = CardType.TEMP_DIR / 'gradient_title.png'
    __SERIES_COUNT_TEXT = CardType.TEMP_DIR / 'series_count_text.png'

    __slots__ = ('source_file', 'output_file', 'title', 'season_text',
                 'episode_text', 'font', 'font_size', 'title_color',
                 'hide_season', 'blur', 'vertical_shift', 'interline_spacing',
                 'kerning', 'stroke_width')


    def __init__(self, source: Path, output_file: Path, title: str,
                 season_text: str, episode_text: str, font: str,
                 font_size: float, title_color: str, hide_season: bool,
                 blur: bool=False, vertical_shift: int=0,
                 interline_spacing: int=0, kerning: float=1.0,
                 stroke_width: float=1.0, *args, **kwargs) -> None:
        """
        Initialize the TitleCardMaker object. This primarily just stores
        instance variables for later use in `create()`. If the provided font
        does not have a character in the title text, a space is used instead.

        :param  source:             Source image.
        :param  output_file:        Output file.
        :param  title_top_line:     Episode title.
        :param  season_text:        Text to use as season count text. Ignored if
                                    hide_season is True.
        :param  episode_text:       Text to use as episode count text.
        :param  font:               Font to use for the episode title. MUST be a
                                    a valid ImageMagick font, or filepath to a
                                    font.
        :param  font_size:          Scalar to apply to the title font size.
        :param  title_color:        Color to use for the episode title.
        :param  hide_season:        Whether to omit the season text (and joining
                                    character) from the title card completely.
        :param  blur:               Whether to blur the source image.
        :param  vertical_shift:     Pixels to adjust title vertical shift by.
        :param  interline_spacing:  Pixels to adjust title interline spacing by.
        :param  kerning:            Scalar to apply to kerning of the title text.
        :param  stroke_width:       Scalar to apply to black stroke of the title
                                    text.
        :param  args and kwargs:    Unused arguments to permit generalized calls
                                    for any CardType.
        """
        
        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__()

        self.source_file = source
        self.output_file = output_file

        # Ensure characters that need to be escaped are
        self.title = self.image_magick.escape_chars(title)
        self.season_text = self.image_magick.escape_chars(season_text.upper())
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())

        self.font = font
        self.font_size = font_size
        self.title_color = title_color
        self.hide_season = hide_season
        self.blur = blur
        self.vertical_shift = vertical_shift
        self.interline_spacing = interline_spacing
        self.kerning = kerning
        self.stroke_width = stroke_width


    def __title_text_global_effects(self) -> list:
        """
        ImageMagick commands to implement the title text's global effects.
        Specifically the the font, kerning, fontsize, and center gravity.
        
        :returns:   List of ImageMagick commands.
        """

        font_size = 157.41 * self.font_size
        interline_spacing = -22 + self.interline_spacing
        kerning = -1.25 * self.kerning

        return [
            f'-font "{self.font}"',
            f'-kerning {kerning}',
            f'-interword-spacing 50',
            f'-interline-spacing {interline_spacing}',
            f'-pointsize {font_size}',
            f'-gravity south',
        ]   


    def __title_text_black_stroke(self) -> list:
        """
        ImageMagick commands to implement the title text's black stroke.
        
        :returns:   List of ImageMagick commands.
        """

        stroke_width = 3.0 * self.stroke_width

        return [
            f'-fill black',
            f'-stroke black',
            f'-strokewidth {stroke_width}',
        ]


    def __series_count_text_global_effects(self) -> list:
        """
        ImageMagick commands for global text effects applied to all series count
        text (season/episode count and dot).
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-kerning 5.42',
            f'-pointsize 67.75',
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
            f'-strokewidth 0.75',
        ]


    def _add_gradient(self) -> Path:
        """
        Add the static gradient to this object's source image.
        
        :returns:   Path to the created image.
        """

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            f'+profile "*"',
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


    def _add_title_text(self, gradient_image: Path) -> Path:
        """
        Adds episode title text to the provide image.

        :param      gradient_image: The image with gradient added.
        
        :returns:   Path to the created image that has a gradient and the title
                    text added.
        """

        vertical_shift = 245 + self.vertical_shift

        command = ' '.join([
            f'convert "{gradient_image.resolve()}"',
            *self.__title_text_global_effects(),
            *self.__title_text_black_stroke(),
            f'-annotate +0+{vertical_shift} "{self.title}"',
            f'-fill "{self.title_color}"',
            f'-annotate +0+{vertical_shift} "{self.title}"',
            f'"{self.__GRADIENT_WITH_TITLE.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__GRADIENT_WITH_TITLE


    def _add_series_count_text_no_season(self, titled_image: Path) -> Path:
        """
        Adds the series count text without season title/number.
        
        :param      titled_image:  The titled image to add text to.

        :returns:   Path to the created image (the output file).
        """

        command = ' '.join([
            f'convert "{titled_image.resolve()}"',
            *self.__series_count_text_global_effects(),
            f'-font "{self.EPISODE_COUNT_FONT.resolve()}"',
            f'-gravity center',
            *self.__series_count_text_black_stroke(),
            f'-annotate +0+697.2 "{self.episode_text}"',
            *self.__series_count_text_effects(),
            f'-annotate +0+697.2 "{self.episode_text}"',
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output_file


    def _get_series_count_text_dimensions(self) -> dict:
        """
        Gets the series count text dimensions.
        
        :returns:   The series count text dimensions.
        """

        command = ' '.join([
            f'convert -debug annotate xc: ',
            *self.__series_count_text_global_effects(),
            f'-font "{self.SEASON_COUNT_FONT.resolve()}"',
            f'-gravity east',
            *self.__series_count_text_effects(),
            f'-annotate +1600+697.2 "{self.season_text} "',
            f'-font "{self.EPISODE_COUNT_FONT.resolve()}"',
            f'-gravity center',
            *self.__series_count_text_effects(),
            f'-annotate +0+689.5 "• "',
            f'-gravity west',
            *self.__series_count_text_effects(),
            f'-annotate +1640+697.2 "{self.episode_text}"',
            f'null: 2>&1'
        ])

        # Get text dimensions from the output
        metrics = self.image_magick.run_get_output(command)
        widths = list(map(int, findall(r'Metrics:.*width:\s+(\d+)', metrics)))
        heights = list(map(int, findall(r'Metrics:.*height:\s+(\d+)', metrics)))

        # Don't raise IndexError if no dimensions were found
        if len(widths) < 2 or len(heights) < 2:
            log.warning(f'Unable to identify font dimensions, file bug report')
            widths = [370, 47, 357]
            heights = [68, 83, 83]

        return {
            'width':    sum(widths),
            'width1':   widths[0],
            'width2':   widths[1],
            'height':   max(heights)+25,
        }


    def _create_series_count_text_image(self, width: float, width1: float,
                                        width2: float, height: float) -> Path:
        """
        Creates an image with only series count text. This image is transparent,
        and not any wider than is necessary (as indicated by `dimensions`).
        
        :returns:   Path to the created image containing only series count text.
        """

        # Create text only transparent image of season count text
        command = ' '.join([
            f'convert -size "{width}x{height}"',
            f'-alpha on',
            f'-background transparent',
            f'xc:transparent',
            *self.__series_count_text_global_effects(),
            f'-font "{self.SEASON_COUNT_FONT.resolve()}"',
            *self.__series_count_text_black_stroke(),
            f'-annotate +0+{height-25} "{self.season_text} "',
            *self.__series_count_text_effects(),
            f'-annotate +0+{height-25} "{self.season_text} "',
            f'-font "{self.EPISODE_COUNT_FONT.resolve()}"',
            *self.__series_count_text_black_stroke(),
            f'-annotate +{width1}+{height-25-6.5} "•"',
            *self.__series_count_text_effects(),
            f'-annotate +{width1}+{height-25-6.5} "•"',
            *self.__series_count_text_black_stroke(),
            f'-annotate +{width1+width2}+{height-25} "{self.episode_text}"',
            *self.__series_count_text_effects(),
            f'-annotate +{width1+width2}+{height-25} "{self.episode_text}"',
            f'"PNG32:{self.__SERIES_COUNT_TEXT.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__SERIES_COUNT_TEXT


    def _combine_titled_image_series_count_text(self, titled_image: Path,
                                                series_count_image: Path)->Path:
        """
        Combine the titled image (image+gradient+episode title) and the series
        count image (optional season number+optional dot+episode number) into a
        single image. This is written into the output image for this object.

        :param      titled_image:       Path to the titled image to add.
        :param      series_count_image: Path to the series count transparent
                                        image to add.

        :returns:   Path to the created image (the output file).
        """

        command = ' '.join([
            f'composite',
            f'-gravity center',
            f'-geometry +0+690.2',
            f'"{series_count_image.resolve()}"',
            f'"{titled_image.resolve()}"',
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output_file


    @staticmethod
    def is_custom_font(font: 'Font') -> bool:
        """
        Determines whether the given font characteristics constitute a default
        or custom font.
        
        :param      font:   The Font being evaluated.
        
        :returns:   True if a custom font is indicated, False otherwise.
        """

        return ((font.file != StandardTitleCard.TITLE_FONT)
            or (font.size != 1.0)
            or (font.color != StandardTitleCard.TITLE_COLOR)
            or (font.replacements != StandardTitleCard.FONT_REPLACEMENTS)
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
        
        :param      custom_episode_map:     Whether the EpisodeMap was
                                            customized.
        :param      episode_text_format:    The episode text format in use.
        
        :returns:   True if custom season titles are indicated, False otherwise.
        """

        return (custom_episode_map or
                episode_text_format.upper() != self.EPISODE_TEXT_FORMAT.upper())


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this object's
        defined title card.
        """
        
        # Add the gradient to the source image (always)
        gradient_image = self._add_gradient()

        # Add either one or two lines of episode text 
        titled_image = self._add_title_text(gradient_image)

        # Create the output directory and any necessary parents 
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # If season text is hidden, just add episode text 
        if self.hide_season:
            self._add_series_count_text_no_season(titled_image)
        else:
            # If adding season text, create intermediate images and combine them
            series_count_image = self._create_series_count_text_image(
                **self._get_series_count_text_dimensions()
            )
            self._combine_titled_image_series_count_text(
                titled_image,
                series_count_image
            )

        # Delete all intermediate images
        images = [gradient_image, titled_image]
        if not self.hide_season:
            images.append(series_count_image)

        self.image_magick.delete_intermediate_images(*images)
