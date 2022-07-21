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

    """Temporary image paths used in the process of title card making"""
    __RESIZED_SOURCE = ImageMaker.TEMP_DIR / 'resized.png'
    __SOURCE_WITH_GRADIENT = ImageMaker.TEMP_DIR / 'swg.png'


    def __init__(self, source: Path, output: Path, title: str, font: Path=FONT,
                 font_color: str=FONT_COLOR, font_size: float=1.0,
                 omit_collection: str=False, borderless: bool=False) -> None:
        """
        Constructs a new instance of a CollectionPosterMaker.
        
        :param      source:             The source image to use for the poster.
        :param      output:             The output path to write the poster to.
        :param      title:              Title to use on the created poster.
        :param      font:               Font of the poster's title.
        :param      font_color:         Font color of the poster text.
        :param      omit_collection:    Whether to omit "COLLECTION" from the
                                        created poster.
        :param      borderless:         Whether to make the poster borderless.
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

        # Uppercase title if using default font
        if font == self.FONT:
            self.collection = title.upper()
        else:
            self.collection = title


    def create(self) -> None:
        """
        Create this object's poster. This WILL overwrite the existing file if it 
        already exists. Errors and returns if the image source does not exist.
        """

        # If the source file doesn't exist, exit
        if not self.source.exists():
            log.error(f'Cannot create genre card, "{self.source.resolve()}" '
                      f'does not exist.')
            return None

        command = ' '.join([
            f'convert',
            f'"{self.source.resolve()}"',               # Resize source
            f'-background transparent',                 
            f'-resize "946x1446^"',
            f'-gravity center',
            f'-extent "946x1446"',
            f'"{self.__GRADIENT.resolve()}"',           # Add gradient overlay
            f'-gravity south',
            f'-composite',
            f'-gravity center',                         # Add border
            f'-bordercolor white',
            f'-border 27x27' if not self.borderless else f'',
            f'-font "{self.font.resolve()}"',           # Add collection title
            f'-interline-spacing -40',
            f'-fill "{self.font_color}"',
            f'-gravity south',
            f'-pointsize {125.0 * self.font_size}',
            f'-kerning 2.25',
            f'-annotate +0+200 "{self.collection}"',
            f'-pointsize 35',                           # Add "COLLECTION" text
            f'-kerning 15',
            f'-font "{self.__COLLECTION_FONT.resolve()}"',
            f'' if self.omit_collection else f'-annotate +0+150 "COLLECTION"',
            f'"{self.output.resolve()}"'
        ])

        self.image_magick.run(command)

