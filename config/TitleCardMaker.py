from pathlib import Path
from re import findall
from subprocess import run

class TitleCardMaker:
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
        5. If season text is required, query ImageMagick's metrics to get the end
           width of the season and episode text.
        6. Create a transparent image of only the provided season and episode text
           of the dimensions computed above.
        7. Place the intermediate transparent text image on top of the image with
           title text.
        8. The resulting title card file is placed at the provided output path. 
        9. Delete all intermediate files used in the creation of the title card.
    """

    """Source path for the gradient image overlayed over all title cards"""
    GRADIENT_IMAGE_PATH = Path(__file__).parent / 'GRADIENT.png'

    """Default font and text color for episode title text"""
    TITLE_DEFAULT_FONT = 'Sequel-Neue'
    TITLE_DEFAULT_COLOR = '#EBEBEB'

    """Default fonts and color for series count text"""
    SEASON_COUNT_DEFAULT_FONT = 'ProximaNova-Semibold'
    EPISODE_COUNT_DEFAULT_FONT = 'Proxima-Nova-Regular'
    SERIES_COUNT_DEFAULT_COLOR = '#CFCFCF'

    """Character used to join season and episode text (with spacing)"""
    SERIES_COUNT_JOIN_CHARACTER = '•'

    """Paths to intermediate files that are deleted after the card is created"""
    __SOURCE_WITH_GRADIENT_PATH = Path(__file__).parent / 'source_gradient.png'
    __GRADIENT_WITH_TITLE_PATH = Path(__file__).parent / 'gradient_title.png'
    __SERIES_COUNT_TEXT_PATH = Path(__file__).parent / 'series_count_text.png'

    def __init__(self, source: Path, output_file: Path,
                 title_line1: str, title_line2: str, 
                 season_text: str, episode_text: str, font: str,
                 title_color: str, hide_season: bool) -> None:

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

        self.source_file = source
        self.output_file = output_file
        self.title_line1 = title_line1.upper()
        self.title_line2 = title_line2.upper() if title_line2 else None
        self.font = font
        self.season_text = season_text.upper()
        self.episode_text = episode_text.upper()
        self.title_color = title_color
        self.hide_season = hide_season

        self.has_two_lines = title_line2 is not None


    def __episode_text_global_effects(self) -> list:
        """
        ImageMagick commands to implement the episode text's global
        effects. Specifically the the font, kerning, fontsize, and
        center gravity.
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-font "{self.font}"',
            f'-kerning -1.75',
            f'-pointsize 157.41',
            f'-gravity center'
        ]   


    def __episode_text_black_stroke(self) -> list:
        """
        ImageMagick commands to implement the episode text's
        black stroke. Specifically a black fill and stroke, and
        a strokewidth of 3.
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 3',
        ]


    def __series_count_text_global_effects(self) -> list:
        """
        { function_description }
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-kerning 5.42',
            f'-pointsize 67.75',
        ]


    def __series_count_text_black_stroke(self) -> list:
        """
        { function_description }
        
        :returns:   { description_of_the_return_value }
        :rtype:     list
        """

        return [
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 6',
        ]


    def __series_count_text_effects(self) -> list:
        """
        { function_description }
        
        :returns:   { description_of_the_return_value }
        :rtype:     list
        """

        return [
            f'-fill "{self.SERIES_COUNT_DEFAULT_COLOR}"',
            f'-stroke "{self.SERIES_COUNT_DEFAULT_COLOR}"',
            f'-strokewidth 0.75',
        ]


    def _add_gradient(self) -> Path:
        """
        Adds a gradient to this object's source image.
        
        :returns:   { description_of_the_return_value }
        :rtype:     Path
        """

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            f'-resize "3200x1800^"',
            f'-extent "3200x1800"',
            f'"{self.GRADIENT_IMAGE_PATH.resolve()}"',
            f'-background None',
            f'-layers Flatten',
            f'"{self.__SOURCE_WITH_GRADIENT_PATH.resolve()}"',
        ])

        run(command, shell=True)

        return self.__SOURCE_WITH_GRADIENT_PATH


    def _add_one_line_episode_text(self, gradient_image: Path) -> Path:
        """
        Adds one line of episode text to the provide image.
        
        :returns:   { description_of_the_return_value }
        :rtype:     Path
        """

        command = ' '.join([
            f'convert "{gradient_image.resolve()}"',
            *self.__episode_text_global_effects(),
            *self.__episode_text_black_stroke(),
            f'-annotate +0+560 "{self.title_line1}"',
            f'-fill "{self.title_color}"',               # Actual text
            f'-annotate +0+560 "{self.title_line1}"',
            f'"{self.__GRADIENT_WITH_TITLE_PATH.resolve()}"',
        ])

        run(command, shell=True)

        return self.__GRADIENT_WITH_TITLE_PATH


    def _add_two_line_episode_text(self, gradient_image: Path) -> Path:
        """
        Adds one lines of episode text to the provide image.
        
        :param      gradient_image:  The gradient image
        
        :returns:   { description_of_the_return_value }
        :rtype:     Path
        """

        command =  ' '.join([
            f'convert "{gradient_image.resolve()}"',
            *self.__episode_text_global_effects(),
            *self.__episode_text_black_stroke(),    # Black stroke behind text (top)
            f'-annotate +0+385 "{self.title_line2}"',
            f'-fill "{self.title_color}"',    
            f'-annotate +0+385 "{self.title_line2}"',    # Top line text
            *self.__episode_text_black_stroke(),    # Black stroke behind text (bottom)
            f'-annotate +0+560 "{self.title_line1}"',
            f'-fill "{self.title_color}"',    
            f'-annotate +0+560 "{self.title_line1}"',    # Bottom line text
            f'"{self.__GRADIENT_WITH_TITLE_PATH.resolve()}"',
        ])

        run(command, shell=True)

        return self.__GRADIENT_WITH_TITLE_PATH


    def _add_series_count_text_no_season(self, titled_image: Path) -> None:
        """
        Adds a series count text no season.
        
        :param      titled_image:  The titled image
        :type       titled_image:  Path
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

        run(command, shell=True)


    def _get_series_count_text_dimensions(self) -> dict:
        """
        Gets the series count text dimensions.
        
        :returns:   The series count text dimensions.
        :rtype:     dict
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

        metrics = run(command, shell=True, capture_output=True).stdout.decode()
        
        widths = list(map(int, findall('width: (\d+)', metrics)))
        heights = list(map(int, findall('height: (\d+)', metrics)))

        return {
            'width': sum(widths),
            'width text 1': widths[0],
            'width text 2': widths[1],
            'height': max(heights)+25,
        }


    def _create_series_count_text_image(self, dimensions: dict) -> Path:
        """
        Creates a series count text image.
        
        :returns:   { description_of_the_return_value }
        :rtype:     Path
        """

        # Get total widths
        height, width = dimensions['height'], dimensions['width']
        width1, width2 = dimensions['width text 1'], dimensions['width text 2']

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

        run(command, shell=True)

        return self.__SERIES_COUNT_TEXT_PATH


    def _combine_titled_image_series_count_text(self, titled_image: Path,
                                                series_count_image: Path,
                                                dimensions: dict) -> None:


        """
        { item_description }
        """

        command = ' '.join([
            f'composite',
            f'-gravity center',
            f'-geometry +0+690.2',
            f'"{series_count_image.resolve()}"',
            f'"{titled_image.resolve()}"',
            f'"{self.output_file.resolve()}"',
        ])

        run(command, shell=True)


    def _delete_intermediate_images(self, *paths: tuple) -> None:
        """
        Delete all the provided files using `rm`.
        
        :param      paths:  Any number of files to delete.
        :type       paths:  tuple of Path objects.
        """

        for image in paths:
            run(f'rm {image.resolve()}', shell=True)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card file.
        """

        # Add the gradient to the source image (always)
        gradient_image = self._add_gradient()

        # Add either one/two lines of episode text 
        if self.has_two_lines:
            titled_image = self._add_two_line_episode_text(gradient_image)
        else:
            titled_image = self._add_one_line_episode_text(gradient_image)

        # Create the output directory parents necessary ...
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # If season text is hidden, just add episode text 
        if self.hide_season:
            self._add_series_count_text_no_season(titled_image)
        else:
            dimensions = self._get_series_count_text_dimensions()
            series_count_image = self._create_series_count_text_image(dimensions)
            self._combine_titled_image_series_count_text(
                titled_image,
                series_count_image,
                dimensions
            )

        # Delete all intermediate images
        intermediate_images = [
            gradient_image, titled_image
        ] + ([] if self.hide_season else [series_count_image])
        self._delete_intermediate_images(*intermediate_images)

