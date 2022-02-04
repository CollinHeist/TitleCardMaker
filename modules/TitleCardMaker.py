from pathlib import Path
from re import findall

from modules.Debug import *
import modules.preferences as preferences
from modules.ImageMaker import ImageMaker

class TitleCardMaker(ImageMaker):
    """
    This class describes the object that actually makes the title card using
    programmed ImageMagick commands. 

    Once initialized with the required title card information, the maker should
    only be used to call `create()`. This will use those arguments to construct
    the desired title card, and delete all intermediate files from that process.

    The process for this creation is:
        1. Take the source image and add the preset gradient overlay.
        2. Add the title text (either one or two lines) to the image. Using the
           provided text line(s), font, and color.
        3. Create the output file's necessary parent folders.
        4. If no season text is required, add just the episode count and skip to 8.
        5. If season text is required, query ImageMagick's to get the end width of
           the season and episode text.
        6. Create a transparent image of only the provided season and episode text
           of the dimensions computed in 5.
        7. Place the intermediate transparent text image on top of the image with
           title text.
        8. The resulting title card file is placed at the provided output path. 
        9. Delete all intermediate files created above.
    """

    """Map of 'case' values to their relevant functions"""
    DEFAULT_CASE_VALUE = 'upper'
    CASE_FUNCTION_MAP = {
        'upper': str.upper,
        'lower': str.lower,
        'title': str.title,
    }

    """Default characters to replace in the generic font"""
    DEFAULT_FONT_REPLACEMENTS = {
        '[': '(', ']': ')', '(': '[', ')': ']'
    }

    """Source path for the gradient image overlayed over all title cards"""
    GRADIENT_IMAGE_PATH: Path = Path(__file__).parent / 'ref' / 'GRADIENT.png'

    """Default font and text color for episode title text"""
    TITLE_DEFAULT_FONT = Path(__file__).parent / 'ref' / 'Sequel-Neue.otf'
    TITLE_DEFAULT_COLOR = '#EBEBEB'

    """Default fonts and color for series count text"""
    SEASON_COUNT_DEFAULT_FONT = Path(__file__).parent / 'ref' / 'Proxima Nova Semibold.otf'
    EPISODE_COUNT_DEFAULT_FONT = Path(__file__).parent / 'ref' / 'Proxima Nova Regular.otf'
    SERIES_COUNT_DEFAULT_COLOR = '#CFCFCF'

    """Character used to join season and episode text (with spacing)"""
    SERIES_COUNT_JOIN_CHARACTER = '•'

    """Paths to intermediate files that are deleted after the card is created"""
    __SOURCE_WITH_GRADIENT_PATH = Path(__file__).parent / '.objects' / 'source_gradient.png'
    __GRADIENT_WITH_TITLE_PATH = Path(__file__).parent / '.objects' / 'gradient_title.png'
    __SERIES_COUNT_TEXT_PATH = Path(__file__).parent / '.objects' / 'series_count_text.png'

    def __init__(self, source: Path, output_file: Path, title_top_line: str,
                 title_bottom_line: str, season_text: str, episode_text: str,
                 font: str, font_size: float, title_color: str, hide_season: bool) -> None:

        """
        Initialize the TitleCardMaker object. This primarily just stores
        instance variables for later use in `create()`. If the provided font
        does not have a character in the title text, a space is used instead.

        :param      source:         Path to the image source for this card.

        :param      output_file:    Path to the output destination for this card.

        :param      title_line1:    First line of episode title text. This is
                                    the BOTTOM line of text.

        :param      title_line2:    Second line of episode title text. This is
                                    the TOP line of text.

        :param      season_text:    Text to use as season count text. Ignored
                                    if hide_season is True.

        :param      episode_text:   Text to use as episode count text.

        :param      font:           Font to use for the episode title. MUST be
                                    a valid ImageMagick font. See
                                    `convert -list font` for full list.

        :param      title_color:    Color to use for the episode title.

        :param      hide_season:    Whether to omit the season text (and
                                    joining character) from the title card
                                    completely.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__()

        self.source_file = source
        self.output_file = output_file

        # Since all text is sent to ImageMagick wrapped in quotes, escape actual quotes
        # found within the episode text
        self.title_top_line = title_top_line.replace('"', r'\"')
        self.title_bottom_line = title_bottom_line.replace('"', r'\"') if title_bottom_line else None

        self.season_text = season_text.upper()
        self.episode_text = episode_text.upper()

        self.font = font
        self.font_size = font_size
        self.title_color = title_color

        self.hide_season = hide_season
        self.has_two_lines = title_top_line not in (None, '')


    def __episode_text_global_effects(self) -> list:
        """
        ImageMagick commands to implement the episode text's global effects.
        Specifically the the font, kerning, fontsize, and center gravity.
        
        :returns:   List of ImageMagick commands.
        """

        font_size = 157.41 * self.font_size

        return [
            f'-font "{self.font}"',
            f'-kerning -1.25',
            f'-interword-spacing 50',
            f'-pointsize {font_size}',
            f'-gravity center',
        ]   


    def __episode_text_black_stroke(self) -> list:
        """
        ImageMagick commands to implement the episode text's black stroke.
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 3', #3, euphoria is 0.5, the wire is 1, punisher 1.5
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
            f'-fill "{self.SERIES_COUNT_DEFAULT_COLOR}"',
            f'-stroke "{self.SERIES_COUNT_DEFAULT_COLOR}"',
            f'-strokewidth 0.75',
        ]


    def _add_gradient(self) -> Path:
        """
        Adds a gradient to this object's source image.
        
        :returns:   Path to the created image that has a gradient added.
        """

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            f'+profile "*"',    # To avoid profile conversion warnings
            f'-gravity center', # For images that aren't in 4x3, center crop
            f'-resize "{self.TITLE_CARD_SIZE}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            f'"{self.GRADIENT_IMAGE_PATH.resolve()}"',
            f'-background None',
            f'-layers Flatten',
            f'"{self.__SOURCE_WITH_GRADIENT_PATH.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__SOURCE_WITH_GRADIENT_PATH


    def _add_one_line_episode_text(self, gradient_image: Path) -> Path:
        """
        Adds one line of episode text to the provide image.

        :param      gradient_image: The image with gradient added.
        
        :returns:   Path to the created image that has a gradient and
                    a single line of title text.
        """

        command = ' '.join([
            f'convert "{gradient_image.resolve()}"',
            *self.__episode_text_global_effects(),
            *self.__episode_text_black_stroke(),
            f'-annotate +0+560 "{self.title_bottom_line}"',
            f'-fill "{self.title_color}"',               # Actual text
            f'-annotate +0+560 "{self.title_bottom_line}"',
            f'"{self.__GRADIENT_WITH_TITLE_PATH.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__GRADIENT_WITH_TITLE_PATH


    def _add_two_line_episode_text(self, gradient_image: Path) -> Path:
        """
        Adds one lines of episode text to the provide image.
        
        :param      gradient_image: The image with gradient added.
        
        :returns:   Path to the created image that has a gradient and
                    two lines of title text.
        """

        command =  ' '.join([
            f'convert "{gradient_image.resolve()}"',
            *self.__episode_text_global_effects(),
            *self.__episode_text_black_stroke(),    # Black stroke behind text (top)
            f'-annotate +0+385 "{self.title_top_line}"',
            f'-fill "{self.title_color}"',    
            f'-annotate +0+385 "{self.title_top_line}"',    # Top line text
            *self.__episode_text_black_stroke(),    # Black stroke behind text (bottom)
            f'-annotate +0+560 "{self.title_bottom_line}"',
            f'-fill "{self.title_color}"',    
            f'-annotate +0+560 "{self.title_bottom_line}"',    # Bottom line text
            f'"{self.__GRADIENT_WITH_TITLE_PATH.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__GRADIENT_WITH_TITLE_PATH


    def _add_series_count_text_no_season(self, titled_image: Path) -> None:
        """
        Adds a series count text no season.
        
        :param      titled_image:  The titled image
        """

        command = ' '.join([
            f'convert "{titled_image.resolve()}"',
            *self.__series_count_text_global_effects(),
            f'-font "{self.EPISODE_COUNT_DEFAULT_FONT}"',
            f'-gravity center',
            *self.__series_count_text_black_stroke(),
            f'-annotate +0+697.2 "{self.episode_text}"',
            *self.__series_count_text_effects(),
            f'-annotate +0+697.2 "{self.episode_text}"',
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)


    def _get_series_count_text_dimensions(self) -> dict:
        """
        Gets the series count text dimensions.
        
        :returns:   The series count text dimensions.
        """

        command = ' '.join([
            f'convert -debug annotate xc: ',
            *self.__series_count_text_global_effects(),
            f'-font "{self.SEASON_COUNT_DEFAULT_FONT}"',    # Season text
            f'-gravity east',
            *self.__series_count_text_effects(),
            f'-annotate +1600+697.2 "{self.season_text} "',
            f'-font "{self.EPISODE_COUNT_DEFAULT_FONT}"',   # Separator dot
            f'-gravity center',
            *self.__series_count_text_effects(),
            f'-annotate +0+689.5 "{self.SERIES_COUNT_JOIN_CHARACTER} "',
            f'-gravity west',                               # Episode text
            *self.__series_count_text_effects(),
            f'-annotate +1640+697.2 "{self.episode_text}"',
            f'null: 2>&1 | grep Metrics'
        ])

        metrics = self.image_magick.run(command, capture_output=True).stdout.decode()
        
        widths = list(map(int, findall('width: (\d+)', metrics)))
        heights = list(map(int, findall('height: (\d+)', metrics)))

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
            f'-font "{self.SEASON_COUNT_DEFAULT_FONT}"',
            *self.__series_count_text_black_stroke(),
            f'-annotate +0+{height-25} "{self.season_text} "',
            *self.__series_count_text_effects(),
            f'-annotate +0+{height-25} "{self.season_text} "',
            f'-font "{self.EPISODE_COUNT_DEFAULT_FONT}"',
            *self.__series_count_text_black_stroke(),
            f'-annotate +{width1}+{height-25-6.5} "{self.SERIES_COUNT_JOIN_CHARACTER}"',
            *self.__series_count_text_effects(),
            f'-annotate +{width1}+{height-25-6.5} "{self.SERIES_COUNT_JOIN_CHARACTER}"',
            *self.__series_count_text_black_stroke(),
            f'-annotate +{width1+width2}+{height-25} "{self.episode_text}"',
            *self.__series_count_text_effects(),
            f'-annotate +{width1+width2}+{height-25} "{self.episode_text}"',
            f'"PNG32:{self.__SERIES_COUNT_TEXT_PATH.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__SERIES_COUNT_TEXT_PATH


    def _combine_titled_image_series_count_text(self, titled_image: Path,
                                                series_count_image: Path) -> None:

        """
        Combine the titled image (image+gradient+episode title) and the 
        series count image (optional season number+optional dot+episode number)
        into a single image.

        This image is written into the output image for this object.
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


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """
        
        # Add the gradient to the source image (always)
        gradient_image = self._add_gradient()

        # Add either one or two lines of episode text 
        if self.has_two_lines:
            titled_image = self._add_two_line_episode_text(gradient_image)
        else:
            titled_image = self._add_one_line_episode_text(gradient_image)

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
            self._combine_titled_image_series_count_text(titled_image, series_count_image)

        # Delete all intermediate images
        self.image_magick.delete_intermediate_images(
            *([gradient_image, titled_image] + ([] if self.hide_season else [series_count_image]))
        )
