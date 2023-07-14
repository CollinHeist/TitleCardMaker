from pathlib import Path

from modules.Debug import log
from modules.ImageMaker import ImageMaker

class CollectionPosterMaker(ImageMaker):
    """
    This class defines a type of maker that creates collection posters.
    """

    """Directory where all reference files used by this maker are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'collection'

    """Base font for collection text"""
    FONT = REF_DIRECTORY / 'NimbusSansNovusT_Bold.ttf'
    FONT_COLOR = 'white'
    __COLLECTION_FONT = REF_DIRECTORY / 'HelveticaNeue-Thin-13.ttf'

    """Base gradient image to overlay over source image"""
    __GRADIENT = REF_DIRECTORY.parent / 'genre' / 'genre_gradient.png'


    def __init__(self,
            source: Path,
            output: Path,
            title: str,
            font: Path = FONT,
            font_color: str = FONT_COLOR,
            font_size: float = 1.0,
            omit_collection: bool = False,
            borderless: bool = False,
            omit_gradient: bool = False) -> None:
        """
        Construct a new instance of a CollectionPosterMaker.

        Args:
            source: The source image to use for the poster.
            output: The output path to write the poster to.
            title: String to use on the created poster.
            font: Path to the font file of the poster's title.
            font_color: Font color of the poster text.
            font_size: Scalar for the font size of the poster's title.
            omit_collection: Whether to omit "COLLECTION" from the
                poster.
            borderless:  Whether to make the poster borderless.
            omit_gradient: Whether to make the poster with no gradient
                overlay.
        """

        # Initialize parent object for the ImageMagickInterface
        super().__init__()

        # Store the arguments
        self.source = source
        self.output = output
        self.font = font
        self.font_color = font_color
        self.font_size = font_size
        self.omit_collection = omit_collection
        self.borderless = borderless
        self.omit_gradient = omit_gradient

        # Uppercase title if using default font
        if font == self.FONT:
            self.collection = title.upper()
        else:
            self.collection = title


    def create(self) -> None:
        """
        Create this object's poster. This WILL overwrite the existing
        file if it  already exists. Errors and returns if the source
        image does not exist.
        """

        # If the source file doesn't exist, exit
        if not self.source.exists():
            log.error(f'Cannot create genre card, "{self.source.resolve()}" '
                      f'does not exist.')
            return None

        # Gradient command to either add/omit gradient
        if self.omit_gradient:
            gradient_command = []
        else:
            gradient_command = [
                f'"{self.__GRADIENT.resolve()}"',
                f'-gravity south',
                f'-composite',
            ]

        # Command to create collection poster
        command = ' '.join([
            f'convert',
            # Resize source
            f'"{self.source.resolve()}"',
            f'-background transparent',
            f'-resize "946x1446^"',
            f'-gravity center',
            f'-extent "946x1446"',
            # Optionally add gradient
            *gradient_command,
            # Add border
            f'-gravity center',
            f'-bordercolor white',
            f'-border 27x27' if not self.borderless else f'',
            # Add collection title
            f'-font "{self.font.resolve()}"',
            f'-interline-spacing -40',
            f'-fill "{self.font_color}"',
            f'-gravity south',
            f'-pointsize {125.0 * self.font_size}',
            f'-kerning 2.25',
            f'-annotate +0+200 "{self.collection}"',
             # Add "COLLECTION" text
            f'-pointsize 35',
            f'-kerning 15',
            f'-font "{self.__COLLECTION_FONT.resolve()}"',
            f'' if self.omit_collection else f'-annotate +0+150 "COLLECTION"',
            # Write output file
            f'"{self.output.resolve()}"'
        ])

        self.image_magick.run(command)

        return None
