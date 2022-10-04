from pathlib import Path

from modules.Debug import log
from modules.ImageMaker import ImageMaker

class AspectRatioFixer(ImageMaker):
    """
    This class describes a type of ImageMaker that corrects the aspect ratio of
    source images (usually 4x3) to the TitleCard aspect ratio of 16x9.
    """

    """Valid styles for the fixer"""
    DEFAULT_STYLE = 'copy'
    VALID_STYLES = ('copy', 'stretch')

    """Temporary intermediate files"""
    __RESIZED_TEMP = ImageMaker.TEMP_DIR / 'ar_temp.png'

    __slots__ = ('source', 'destination', 'style')


    def __init__(self, source: Path, destination: Path,
                 style: str=DEFAULT_STYLE) -> None:
        """
        Initialize this object. This stores attributes, and initialzies the 
        parent ImageMaker object.

        Args:
            source: Path to the source image to use.
            destination: Path to the desination file to write the image at.
            style: Aspect ratio correction style. Must be one of VALID_STYLES.

        Raises:
            AssertionError: If 'style' is invalid.
        """

        # Initialize parent object for the ImageMagickInterface
        super().__init__()

        # Store attributes
        self.source = source
        self.destination = destination
        self.style = style.lower()

        assert self.style in self.VALID_STYLES, 'Invalid style'


    def create(self) -> None:
        """
        Create the aspect-ratio-corrected image for this object's source file.
        """

        # If source DNE, exit
        if not self.source.exists():
            log.error(f'Input file "{self.source.resolve()}" does not exist')
            return None

        # Copy style command
        if self.style == 'copy':
            command = ' '.join([
                f'convert "{self.source.resolve()}"',
                # Force resize source to correct size
                f'-resize "3200x1800!"',
                # Blur source
                f'-blur 0x16',
                f'-gravity center',
                f'-append',
                # Add source image over blurred source
                f'"{self.source.resolve()}"',
                f'-resize "3200x1800"',
                f'-composite',
                f'"{self.destination.resolve()}"',
            ])
        # Stretch style command
        elif self.style == 'stretch':
            # Resize source image to correct height
            resize_command = ' '.join([
                f'convert',
                f'+profile "*"',
                f'"{self.source.resolve()}"',
                f'-resize x1800',
                f'"{self.__RESIZED_TEMP.resolve()}"',
            ])
            self.image_magick.run(resize_command)

            # Get dimensions of resized image, exit if too narrow for stretching
            dimensions = self.get_image_dimensions(self.__RESIZED_TEMP)
            if dimensions['width'] < 400 or dimensions['height'] < 1800:
                log.error(f'Image too narrow for correcting with "stretch" style')
                return None

            # Stretch sides to fit into 3200px wide
            side_width = (3200 - dimensions['width'] + 100) // 2

            command = ' '.join([
                f'convert',
                # Crop left 50px and stretch
                f'\( "{self.__RESIZED_TEMP.resolve()}"',
                f'-crop "50x1800+0+0"',
                f'-resize "{side_width}!" \)',
                # Crop middle section
                f'\(  "{self.__RESIZED_TEMP.resolve()}"',
                f'-crop "{dimensions["width"]-100}x1800+50+0" \)',
                # Crop right 50px and stretch
                f'\(  "{self.__RESIZED_TEMP.resolve()}"',
                f'-crop "50x1800+{dimensions["width"]-50}+0"',
                f'-resize "{side_width}!" \)',
                # Append like [LEFT 50][MIDDLE][RIGHT 50] left-to-right
                f'+append',
                f'"{self.destination.resolve()}"',
            ])

        self.image_magick.run(command)

        # Delete temporary images
        if self.style == 'stretch':
            self.image_magick.delete_intermediate_images(self.__RESIZED_TEMP)

        log.debug(f'Created "{self.destination.resolve()}"')