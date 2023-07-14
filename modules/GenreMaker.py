from pathlib import Path

from modules.Debug import log
from modules.ImageMaker import ImageMaker

class GenreMaker(ImageMaker):
    """
    This class defines a type of maker that creates genre cards. These
    are posters that have text (the genre) at the bottom of their image,
    and are outlined by a white border (in this implementation).
    """

    """Directory where all reference files used by this maker are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'genre'

    """Base font for genre text"""
    FONT = REF_DIRECTORY / 'MyriadRegular.ttf'

    """Base gradient image to overlay over source image"""
    __GENRE_GRADIENT = REF_DIRECTORY / 'genre_gradient.png'


    def __init__(self,
            source: Path,
            genre: str,
            output: Path,
            font_size: float = 1.0,
            borderless: bool = False,
            omit_gradient: bool = False) -> None:
        """
        Construct a new instance of this object.

        Args:
            source: The source image to use for the genre card.
            genre: The genre text to put on the genre card.
            output: The output path to write the genre card to.
            font_size: Scalar to apply to the title font size.
            borderless: Whether to make the card as borderless or not.
            omit_gradient: Whether to omit the gradient overlay or not.
        """

        # Initialize parent object for the ImageMagickInterface
        super().__init__()

        # Store the arguments
        self.source = source
        self.genre = genre
        self.output = output
        self.font_size = font_size
        self.borderless = borderless
        self.omit_gradient = omit_gradient


    def create(self) -> None:
        """
        Create the genre card. This WILL overwrite the existing file if
        it  already exists. Errors and returns if the source image does
        not exist.
        """

        # If the source file doesn't exist, exit
        if not self.source.exists():
            log.error(f'Cannot create genre card, "{self.source.resolve()}" '
                      f'does not exist.')
            return None

        # Create the output directory and any necessary parents
        self.output.parent.mkdir(parents=True, exist_ok=True)

        # Gradient command to either add/omit gradient
        if self.omit_gradient:
            gradient_command = []
        else:
            gradient_command = [
                f'"{self.__GENRE_GRADIENT.resolve()}"',
                f'-gravity south',
                f'-composite',
            ]

        # Command to create genre poster
        command = ' '.join([
            # Resize source image
            f'convert "{self.source.resolve()}"',
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
            # Add genre text
            f'-font "{self.FONT.resolve()}"',
            f'-fill white',
            f'-pointsize {self.font_size * 159.0}',
            f'-kerning 2.25',
            f'-annotate +0+564 "{self.genre}"',
            f'"{self.output.resolve()}"',
        ])

        self.image_magick.run(command)
        return None
