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

    """Paths to reference images to overlay"""
    __FRAME = REF_DIRECTORY / 'frame.png'
    __GRADIENT = REF_DIRECTORY / 'gradient.png'


    def __init__(self, source: Path, output: Path, title: str, subtitle: str='',
                 font: Path=FONT, font_color: str=FONT_COLOR,
                 font_size: float=1.0, omit_gradient: bool=False) -> None:
        """
        Construct a new instance of a CollectionPosterMaker.

        Args:
            source: The source image to use for the poster.
            output: The output path to write the poster to.
            title: String to use on the created poster.
            subtitle: String to use for smaller title text.
            font: Path to the font file of the poster's title.
            font_color: Font color of the poster text.
            font_size: Scalar for the font size of the poster's title.
            omit_gradient: Whether to make the poster with no gradient overlay.
        """

        # Initialize parent object for the ImageMagickInterface
        super().__init__()

        # Store the arguments
        self.source = source
        self.output = output
        self.font = font
        self.font_color = font_color
        self.font_size = font_size
        self.omit_gradient = omit_gradient

        # Uppercase title if using default font
        if font == self.FONT:
            self.title = title.upper()
            self.subtitle = subtitle.upper()
        else:
            self.title = title
            self.subtitle = subtitle


    def create(self) -> None:
        """
        Create this object's poster. This WILL overwrite the existing file if it 
        already exists. Errors and returns if the source image does not exist.
        """

        # If the source file doesn't exist, exit
        if not self.source.exists():
            log.error(f'Cannot create movie poster, "{self.source.resolve()}" '
                      f'does not exist.')
            return None

        # Gradient command to either add/omit gradient
        if self.omit_gradient:
            gradient_command = []
        else:
            gradient_command = [
                f'"{self.__GRADIENT.resolve()}"',
                f'-compose Multiply',
                f'-composite',
            ]

        # Set variables
        title_font_size = 190 * self.font_size
        subtitle_font_size = 95 * self.font_size
        
        # Command to create collection poster
        command = ' '.join([
            f'convert',
            f'"{self.__FRAME.resolve()}"',
            f'\( "{self.source.resolve()}"',
            f'-gravity center',
            f'-resize "1892x2892^"',
            f'-extent 1892x2892',
            *gradient_command,
            f'-background None',
            f'-extent 2000x3000 \)',
            f'+swap',
            f'-composite',
            f'-gravity south',
            f'-font "{self.font.resolve()}"',
            f'-pointsize {title_font_size}',
            f'-fill {self.font_color}',
            f'-interline-spacing -40',
            f'-annotate +0+265 "{self.title}"',
            f'-pointsize {subtitle_font_size}',
            f'-interword-spacing 15',
            f'-kerning 7',
            f'-annotate +0+185 "{self.subtitle}"',
            f'"{self.output.resolve()}"',
        ])

        self.image_magick.run(command)