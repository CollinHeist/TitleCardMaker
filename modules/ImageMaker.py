from abc import ABC, abstractmethod
from pathlib import Path
from re import match

from modules.Debug import log
from modules.ImageMagickInterface import ImageMagickInterface
import modules.global_objects as global_objects

class ImageMaker(ABC):
    """
    Abstract class that outlines the necessary attributes for any class that
    creates images.

    All instances of this class must implement `create()` as the main callable
    function to produce an image. The specifics of how that image is created are
    completely customizable.
    """

    """Directory for all temporary images created during image creation"""
    TEMP_DIR = Path(__file__).parent / '.objects'

    """Temporary file location for svg -> png conversion"""
    TEMPORARY_SVG_FILE = TEMP_DIR / 'temp_logo.svg'

    """
    Valid file extensions for input images - ImageMagick supports more than just
    these types, but these are the most common across all OS's.
    """
    VALID_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tiff', '.gif')

    __slots__ = ('preferences', 'image_magick')


    @abstractmethod
    def __init__(self) -> None:
        """
        Initializes a new instance. This gives all subclasses access to an
        `ImageMagickInterface` object that uses the docker ID found within
        preferences, as well as a preference object.
        """

        # Store global PreferenceParse object
        self.preferences = global_objects.pp

        # All ImageMakers have an instance of an ImageMagickInterface
        self.image_magick = ImageMagickInterface(
            self.preferences.imagemagick_container,
            self.preferences.use_magick_prefix,
            self.preferences.imagemagick_timeout,
        )


    def get_image_dimensions(self, image: Path) -> dict[str: int]:
        """
        Get the dimensions of the given image.

        Args:
            image: Path to the image to get the dimensions of.

        Returns:
            Dictionary of the image dimensions whose keys are 'width' and
            'height'.
        """

        # Return dimenions of zero if image DNE
        if not image.exists():
            return {'width': 0, 'height': 0}

        # Get the dimensions
        command = ' '.join([
            f'identify',
            f'-format "%w %h"',
            f'"{image.resolve()}"',
        ])

        output = self.image_magick.run_get_output(command)

        # Get width/height from output
        try:
            width, height = map(int, match(r'^(\d+)\s+(\d+)$', output).groups())
            return {'width': width, 'height': height}
        except Exception as e:
            log.debug(f'Cannot identify dimensions of {image.resolve()}')
            return {'width': 0, 'height': 0}


    @staticmethod
    def convert_svg_to_png(image: Path, destination: Path,
                           min_dimension: int=2500) -> Path:
        """
        Convert the given SVG image to PNG format.

        Args:
            image: Path to the image being converted.
            destination: Path to the destination image location.
            min_dimension: Minimum dimension of converted image.
        
        Returns:
            Path to the converted file.
        """

        # If the temp file doesn't exist, return
        if not image.exists():
            return None

        # Create ImageMagickInterface for this command
        image_magick_interface = ImageMagickInterface(
            global_objects.pp.imagemagick_container,
            global_objects.pp.use_magick_prefix,
            global_objects.pp.imagemagick_timeout,
        )

        # Command to convert file to PNG
        command = ' '.join([
            f'convert',
            f'-density 512',
            f'-resize "{min_dimension}x{min_dimension}"',
            f'-background None',
            f'"{image.resolve()}"',
            f'"{destination.resolve()}"',
        ])

        image_magick_interface.run(command)

        return destination


    @abstractmethod
    def create(self) -> None:
        """
        Abstract method for the creation of the image outlined by this maker.
        This method should delete any intermediate files, and should make
        ImageMagick calls through the parent class' ImageMagickInterface object.
        """
        raise NotImplementedError(f'All ImageMaker objects must implement this')