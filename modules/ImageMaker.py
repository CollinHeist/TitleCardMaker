from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from modules import global_objects
from modules.ImageMagickInterface import ImageMagickInterface


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

    """
    Valid file extensions for input images - ImageMagick supports more
    than just these types, but these are the most common across all
    OS's.
    """
    VALID_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tiff', '.gif', '.webp')

    __slots__ = ('card_dimensions', 'image_magick')


    @abstractmethod
    def __init__(self,
            *,
            preferences: Optional['Preferences'] = None, # type: ignore
        ) -> None:
        """
        Initializes a new instance. This gives all subclasses access to
        an ImageMagickInterface via the image_magick attribute.

        Args:
            preferences: Global Preferences object to initialize the
                `ImageMagickInterface` with.
        """

        # No Preferences object, use global
        if preferences is None:
            self.card_dimensions = global_objects.pp.card_dimensions
            self.image_magick = ImageMagickInterface(
                global_objects.pp.imagemagick_container,
                global_objects.pp.use_magick_prefix,
                global_objects.pp.imagemagick_timeout,
            )
        # Preferences object provided, use directly
        else:
            self.card_dimensions = preferences.card_dimensions
            self.image_magick = ImageMagickInterface(
                use_magick_prefix=preferences.use_magick_prefix,
            )


    @abstractmethod
    def create(self) -> None:
        """
        Abstract method for the creation of the image outlined by this
        maker. This method should delete any intermediate files, and
        should make ImageMagick calls through the parent class'
        ImageMagickInterface object.
        """
        raise NotImplementedError(f'All ImageMaker objects must implement this')
