from abc import ABC, abstractmethod
from collections import namedtuple
from pathlib import Path
from re import findall, match
from typing import Literal, Optional, Union

from modules.Debug import log
from modules.ImageMagickInterface import ImageMagickInterface
import modules.global_objects as global_objects

Dimensions = namedtuple('Dimensions', ('width', 'height'))

class ImageMaker(ABC):
    """
    Abstract class that outlines the necessary attributes for any class
    that creates images.

    All instances of this class must implement `create()` as the main
    callable function to produce an image. The specifics of how that
    image is created are completely customizable.
    """

    """Base reference directory for local assets"""
    BASE_REF_DIRECTORY = Path(__file__).parent / 'ref'

    """Directory for all temporary images created during image creation"""
    TEMP_DIR = Path(__file__).parent / '.objects'

    """Temporary file location for svg -> png conversion"""
    TEMPORARY_SVG_FILE = TEMP_DIR / 'temp_logo.svg'

    """Temporary file location for image filesize reduction"""
    TEMPORARY_COMPRESS_FILE = TEMP_DIR / 'temp_compress.jpg'

    """
    Valid file extensions for input images - ImageMagick supports more
    than just these types, but these are the most common across all
    OS's.
    """
    VALID_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tiff', '.gif', '.webp')

    __slots__ = ('preferences', 'image_magick')


    @abstractmethod
    def __init__(self, *, preferences: Optional['Preferences'] = None) -> None:
        """
        Initializes a new instance. This gives all subclasses access to
        an ImageMagickInterface via the image_magick attribute.
        """

        if preferences is None:
            self.preferences = global_objects.pp
        else:
            self.preferences = preferences

        # All ImageMakers have an instance of an ImageMagickInterface
        self.image_magick = ImageMagickInterface(
            self.preferences.imagemagick_container,
            self.preferences.use_magick_prefix,
            self.preferences.imagemagick_timeout,
        )


    def get_image_dimensions(self, image: Path) -> Dimensions:
        """
        Get the dimensions of the given image.

        Args:
            image: Path to the image to get the dimensions of.

        Returns:
            Namedtuple of dimensions.
        """

        # Return dimenions of zero if image DNE
        if not image.exists():
            return Dimensions(0, 0)

        # Get the dimensions
        command = ' '.join([
            f'identify',
            f'-format "%w %h"',
            f'"{image.resolve()}"',
        ])

        output = self.image_magick.run_get_output(command)

        # Get width/height from output
        try:
            return Dimensions(
                *map(int, match(r'^(\d+)\s+(\d+)$', output).groups())
            )
        except Exception as e:
            log.debug(f'Cannot identify dimensions of {image.resolve()}')
            return Dimensions(0, 0)


    def get_text_dimensions(self, text_command: list[str], *,
            width: Literal['sum', 'max'],
            height: Literal['sum', 'max']) -> Dimensions:
        """
        Get the dimensions of the text produced by the given text
        command. For 'width' and 'height' arguments, if 'max' then the
        maximum value of the text is utilized, while 'sum' will add each
        value. For example, if the given text command produces text like:

            Top Line Text
            Bottom Text

        Specifying width='sum', will add the widths of the two lines
        (not very meaningful), width='max' will return the maximum width
        of the two lines. Specifying height='sum' will return the total
        height of the text, and height='max' will return the tallest
        single line of text.

        Args:
            text_command: ImageMagick commands that produce text(s) to
                measure.
            width: How to process the width of the produced text(s).
            height: How to process the height of the produced text(s).

        Returns:
            Dimensions namedtuple.
        """

        text_command = ' '.join([
            f'convert',
            f'-debug annotate',
            f'' if '-annotate ' in ' '.join(text_command) else f'xc: ',
            *text_command,
            f'null: 2>&1',
        ])

        # Execute dimension command, parse output
        metrics = self.image_magick.run_get_output(text_command)
        widths = map(int, findall(r'Metrics:.*width:\s+(\d+)', metrics))
        heights = map(int, findall(r'Metrics:.*height:\s+(\d+)', metrics))

        try:
            # Label text produces duplicate Metrics
            sum_ = lambda v: sum(v)//(2 if ' label:"' in text_command else 1)

            # Process according to given methods
            return Dimensions(
                sum_(widths)  if width  == 'sum' else max(widths),
                sum_(heights) if height == 'sum' else max(heights),
            )
        except ValueError as e:
            log.debug(f'Cannot identify text dimensions - {e}')
            return Dimensions(0, 0)


    @staticmethod
    def reduce_file_size(image: Path, quality: int = 90) -> Path:
        """
        Reduce the file size of the given image.

        Args:
            image: Path to the image to reduce the file size of.
            quality: Quality of the reduction. 100 being no reduction, 0
                being complete reduction. Passed to ImageMagick -quality.

        Returns:
            Path to the created image.
        """

        # Verify quality is 0-100
        if (quality := int(quality)) not in range(0, 100):
            return None

        # If image DNE, warn and return
        if not image.exists():
            log.warning(f'Cannot reduce file size of non-existent image '
                        f'"{image.resolve()}"')
            return None

        # Create ImageMagickInterface for this command
        image_magick_interface = ImageMagickInterface(
            global_objects.pp.imagemagick_container,
            global_objects.pp.use_magick_prefix,
            global_objects.pp.imagemagick_timeout,
        )

        # Downsample and reduce quality of source image
        command = ' '.join([
            f'convert',
            f'"{image.resolve()}"',
            f'-sampling-factor 4:2:0',
            f'-quality {quality}%',
            f'"{ImageMaker.TEMPORARY_COMPRESS_FILE.resolve()}"',
        ])

        image_magick_interface.run(command)

        return ImageMaker.TEMPORARY_COMPRESS_FILE


    @staticmethod
    def convert_svg_to_png(
            image: Path,
            destination: Path,
            min_dimension: int = 2500) -> Union[Path, None]:
        """
        Convert the given SVG image to PNG format.

        Args:
            image: Path to the SVG image being converted.
            destination: Path to the output image.
            min_dimension: Minimum dimension of converted image.

        Returns:
            Path to the converted file. None if the conversion failed.
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

        # Print command history if conversion failed
        if destination.exists():
            return destination
        else:
            image_magick_interface.print_command_history()
            return None


    @abstractmethod
    def create(self) -> None:
        """
        Abstract method for the creation of the image outlined by this
        maker. This method should delete any intermediate files, and
        should make ImageMagick calls through the parent class'
        ImageMagickInterface object.
        """
        raise NotImplementedError(f'All ImageMaker objects must implement this')