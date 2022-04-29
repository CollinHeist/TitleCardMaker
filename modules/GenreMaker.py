from pathlib import Path

from modules.Debug import log
from modules.ImageMaker import ImageMaker

class GenreMaker(ImageMaker):
    """
    This class defines a type of maker that creates genre cards. These are
    posters that have text (the genre) at the bottom of their image, and are
    outlined by a white border (in this implementation).
    """

    """Directory where all reference files used by this maker are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'genre'

    """Base font for genre text"""
    FONT = REF_DIRECTORY / 'MyriadRegular.ttf'

    """Base gradient image to overlay over source image"""
    __GENRE_GRADIENT = REF_DIRECTORY / 'genre_gradient.png'

    """Temporary image paths used in the process of title card making"""
    __RESIZED_SOURCE = ImageMaker.TEMP_DIR / 'resized.png'
    __SOURCE_WITH_GRADIENT = ImageMaker.TEMP_DIR / 'swg.png'


    def __init__(self, source: Path, genre: str, output: Path,
                 font_size: float=1.0) -> None:
        """
        Constructs a new instance.
        
        :param      source:     The source image to use for the genre card.
        :param      genre:      The genre text to put on the genre card.
        :param      output:     The output path to write the genre card to.
        :param      font_size:  Scalar to apply to the title font size.
        """

        # Initialize parent object for the ImageMagickInterface
        super().__init__()

        # Store the arguments
        self.source = source
        self.genre = genre
        self.output = output
        self.font_size = font_size


    def __resize_source(self) -> Path:
        """
        Resize the source file for this card into the necessary dimensions
        (946x1446).
        
        :returns:   Path to the created image.
        """

        command = ' '.join([
            f'convert "{self.source.resolve()}"',
            f'-resize "946x1446^"',
            f'-gravity center',
            f'-extent "946x1446"',
            f'"{self.__RESIZED_SOURCE.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__RESIZED_SOURCE


    def __add_gradient(self, resized_source: Path) -> Path:
        """
        Add the static gradient image to the given resized image.
        
        :param      resized_source: Path to the image to add a gradient to.
        
        :returns:   Path to the created image.
        """

        command = ' '.join([
            f'convert "{resized_source.resolve()}"',
            f'"{self.__GENRE_GRADIENT.resolve()}"',
            f'-gravity south',
            f'-composite',
            f'"{self.__SOURCE_WITH_GRADIENT.resolve()}"'
        ])

        self.image_magick.run(command)

        return self.__SOURCE_WITH_GRADIENT


    def __add_text_and_border(self, source_with_gradient: Path) -> Path:
        """
        Add the genre text and the white border to the given image.
        
        :param      source_with_gradient:   The source image with the gradient
                                            applied.
        
        :returns:   Path to the created image (the output file).
        """

        command = ' '.join([
            f'convert "{source_with_gradient.resolve()}"',
            f'-gravity center',
            f'-font "{self.FONT.resolve()}"',
            f'-bordercolor white',
            f'-border 27x27',
            f'-fill white',
            f'-pointsize {self.font_size * 159.0}',
            f'-kerning 2.25',
            f'-annotate +0+564 "{self.genre}"',
            f'"{self.output.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output

        
    def create(self) -> None:
        """
        Create the genre card. This WILL overwrite the existing file if it 
        already exists. Errors and returns if the image source does not exist.
        """

        # If the source file doesn't exist, exit
        if not self.source.exists():
            log.error(f'Cannot create genre card, "{self.source.resolve()}" '
                      f'does not exist.')
            return None
        
        # Resize source to fit in contrained space
        resized_source = self.__resize_source()

        # Add gradient overlay to the image
        source_with_gradient = self.__add_gradient(resized_source)

        # Create the output directory and any necessary parents 
        self.output.parent.mkdir(parents=True, exist_ok=True)

        # Add genre text and outer border, result is the genre card
        output = self.__add_text_and_border(source_with_gradient)
        
        # Delete intermediate files
        self.image_magick.delete_intermediate_images(
            resized_source,
            source_with_gradient
        )

