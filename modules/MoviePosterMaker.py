from pathlib import Path

from modules.Debug import log
from modules.ImageMaker import ImageMaker

class MoviePosterMaker(ImageMaker):
    """This class defines a type of maker that creates movie posters."""

    """Directory where all reference files used by this maker are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'movie'

    """Base font for title text"""
    FONT = REF_DIRECTORY / 'Arial Bold.ttf'
    FONT_COLOR = 'white'
    INDEX_FONT_COLOR = 'rgb(154,154,154)'

    """Paths to reference images to overlay"""
    __FRAME = REF_DIRECTORY / 'frame.png'
    __GRADIENT = REF_DIRECTORY / 'gradient.png'


    def __init__(self, source: Path, output: Path, title: str, subtitle: str='',
                 top_subtitle: str='', movie_index: str='', logo: Path=None,
                 font: Path=FONT, font_color: str=FONT_COLOR,
                 font_size: float=1.0, omit_gradient: bool=False) -> None:
        """
        Construct a new instance of a CollectionPosterMaker.

        Args:
            source: The source image to use for the poster.
            output: The output path to write the poster to.
            title: String to use on the created poster.
            subtitle: String to use for smaller title text.
            top_subtitle: String to use for smaller subtitle text that appears
                above the title text.
            movie_index: Optional (series) index to place behind the movie
                title.
            logo: Optional path to a logo file to place on top of the poster.
            font: Path to the font file of the poster's title.
            font_color: Font color of the poster text.
            font_size: Scalar for the font size of the poster's title.
            omit_gradient: Whether to make the poster with no gradient overlay.
        """

        # Initialize parent object for the ImageMagickInterface
        super().__init__()

        # Store arguments as attributes
        self.source = source
        self.output = output
        self.movie_index = movie_index
        self.logo = logo
        self.font = font
        self.font_color = font_color
        self.font_size = font_size
        self.omit_gradient = omit_gradient

        # Uppercase title(s) if using default font
        if font == self.FONT:
            self.top_subtitle = top_subtitle.upper()
            self.title = title.upper()
            self.subtitle = subtitle.upper()
        else:
            self.top_subtitle = top_subtitle
            self.title = title
            self.subtitle = subtitle


    @property
    def gradient_command(self) -> list[str]:
        """
        ImageMagick commands to add the gradient to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # If gradient is omitted, return empty command
        if self.omit_gradient:
            return []
        
        return [
            f'"{self.__GRADIENT.resolve()}"',
            f'-compose Multiply',
            f'-composite',
        ]


    @property
    def index_command(self) -> list[str]:
        """
        ImageMagick command(s) to add the underlying index text behind the
        title text.

        Returns:
            List of ImageMagick commands.
        """

        # No index, return empty command
        if len(self.movie_index) == 0:
            return []

        return [
            f'-font "{self.FONT.resolve()}"',
            f'-pointsize 598',
            f'-fill "{self.INDEX_FONT_COLOR}"',
            f'-annotate +0+1150 "{self.movie_index}"',
        ]


    @property
    def title_font_attributes(self) -> list[str]:
        """
        Imagemagick commands to define the font attributes of the title text.

        Returns:
            List of ImageMagick commands.
        """

        title_font_size = 190 * self.font_size
        
        return [
            f'-pointsize {title_font_size}',
            f'-interline-spacing -44.5',
            f'-interword-spacing 55',
            f'-kerning 0.70',
        ]


    @property
    def subtitle_font_attributes(self) -> list[str]:
        """
        Imagemagick commands to define the font attributes of the subtitle text.

        Returns:
            List of ImageMagick commands.
        """

        subtitle_font_size = 95 * self.font_size

        return [
            f'-pointsize {subtitle_font_size}',
            f'-interword-spacing 18',
            f'-kerning 0.5',
        ]

    
    @property
    def logo_command(self) -> list[str]:
        """
        ImageMagick subcommands to add the logo file to the poster.

        Returns:
            List of Imagemagick commands.
        """

        # Logo not indicated, return empty command
        if self.logo is None:
            return []

        return [
            # Bring in logo image
            f'\( "{self.logo.resolve()}"',
            # Resize to 400px wide, limit to 200px tall
            f'-resize 400x',
            f'-resize x200\> \)',
            # Overlay 100px from top of image
            f'-gravity north',
            f'-geometry +0+100',
            f'-compose Atop',
            f'-composite',
        ]


    @property
    def title_command(self) -> list[str]:
        """
        ImageGagick subcommands to add the title text to the poster.

        Returns:
            List of ImageMagick commands
        """

        # No titles, return empty command
        if (len(self.top_subtitle.strip()) == 0
            and len(self.title.strip()) == 0
            and len(self.subtitle.strip()) == 0):
            return []

        # At least one title being added, return entire command
        return [
            ## Global font attributes
            f'-font "{self.font.resolve()}"',
            f'-fill "{self.font_color}"',
            # Create an image for each title
            f'\( -background transparent',
            *self.subtitle_font_attributes,
            f'label:"{self.top_subtitle}"',
            *self.title_font_attributes,
            f'label:"{self.title}"',
            *self.subtitle_font_attributes,
            f'label:"{self.subtitle}"',
            # Combine in order [TOP SUBTITLE] / [TITLE] / [SUBTITLE]
            f'-smush 30 \)',
            # Add titles to image
            f'-gravity south',
            f'-geometry +0+{182.5 if len(self.subtitle) > 0 else 262.5}',
            f'-compose atop',
            f'-composite',
        ]


    def create(self) -> None:
        """
        Create this object's poster. This WILL overwrite the existing file if it 
        already exists. Errors and returns if the source image does not exist.
        """

        # If the source file doesn't exist, exit
        if not self.source.exists():
            log.error(f'Cannot create movie poster - "{self.source.resolve()}" '
                      f'does not exist.')
            return None
        elif isinstance(self.logo, Path) and not self.logo.exists():
            log.error(f'Cannot create movie poster - "{self.logo.resolve()}" '
                      f'does not exist.')
            return None
        
        # Command to create collection poster
        command = ' '.join([
            f'convert',
            # Start with frame
            f'"{self.__FRAME.resolve()}"',
            # Add source image
            f'\( "{self.source.resolve()}"',
            # Resize image
            f'-gravity center',
            f'-resize "1892x2892^"',
            f'-extent 1892x2892',
            # Add gradient to source image
            *self.gradient_command,
            f'-background None',
            f'-extent 2000x3000 \)',
            # Swap, putting frame on top of source+gradient
            f'+swap',
            f'-composite',
            # Optionally overlay logo
            *self.logo_command,
            # Add index text
            *self.index_command,
            # Add title text
            *self.title_command,
            f'"{self.output.resolve()}"',
        ])

        self.image_magick.run(command)