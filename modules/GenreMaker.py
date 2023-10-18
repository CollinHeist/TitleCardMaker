from pathlib import Path

from modules.BaseCardType import ImageMagickCommands
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
            omit_gradient: bool = False,
        ) -> None:

        # Initialize parent object for the ImageMagickInterface
        super().__init__()

        # Store the arguments
        self.source = source
        self.genre = genre
        self.output = output
        self.font_size = font_size
        self.borderless = borderless
        self.omit_gradient = omit_gradient


    @property
    def gradient_commands(self) -> ImageMagickCommand:
        """
        ImageMagick subcommands to add the gradient overlay to the image
        """

        if self.omit_gradient:
            return []

        return [
            f'"{self.__GENRE_GRADIENT.resolve()}"',
            f'-gravity south',
            f'-composite',
        ]


    @property
    def border_commands(self) -> ImageMagickCommands:
        """ImageMagick subcommands to add the border around the image"""

        if self.borderless:
            return []
        
        return [
            f'-gravity center',
            f'-bordercolor white',
            f'-border 27x27',
        ]


    def create(self) -> None:
        """
        Create the genre card. This WILL overwrite the existing file if
        it  already exists. Errors and returns if the source image does
        not exist.
        """

        # If the source file doesn't exist, exit
        if not self.source.exists():
            log.error(f'Cannot create genre card - "{self.source.resolve()}" '
                      f'does not exist.')
            return None

        # Create the output directory and any necessary parents
        self.output.parent.mkdir(parents=True, exist_ok=True)

        # Command to create genre poster
        command = ' '.join([
            # Resize source image
            f'convert "{self.source.resolve()}"',
            f'-background transparent',
            f'-resize "946x1446^"',
            f'-gravity center',
            f'-extent "946x1446"',
            # Optionally add gradient
            *self.gradient_commands,
            # Add border
            *self.border_commands,
            # Add genre text
            f'-font "{self.FONT.resolve()}"',
            f'-fill white',
            f'-pointsize {self.font_size * 159.0}',
            f'-kerning 2.25',
            f'-interline-spacing -40',
            f'-annotate +0+564 "{self.genre}"',
            f'"{self.output.resolve()}"',
        ])

        self.image_magick.run(command)
        return None
