from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from modules import global_objects
from modules.Debug import log
from modules.ImageMagickInterface import ImageMagickInterface, Dimensions

if TYPE_CHECKING:
    from app.models.preferences import Preferences


ImageMagickCommands = list[str]


__all__ = [
    'ImageMagickInterface', 'Dimensions', 'ImageMaker', 'ImageMagickCommands'
]


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

    __slots__ = ('card_dimensions', 'quality', 'image_magick')


    @abstractmethod
    def __init__(self,
            *,
            preferences: Optional['Preferences'] = None,
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
            self.card_dimensions = getattr(
                global_objects.pp, 'card_dimensions', '3200x1800'
            )
            self.quality = getattr(global_objects.pp, 'card_quality', 92)
            self.image_magick = ImageMagickInterface(
                getattr(global_objects.pp, 'imagemagick_container', 'ImageMagick'),
                getattr(global_objects.pp, 'use_magick_prefix', True),
                getattr(global_objects.pp, 'executable', None),
                getattr(global_objects.pp, 'imagemagick_timeout', 30),
            )
        # Preferences object provided, use directly
        else:
            self.card_dimensions = preferences.card_dimensions
            self.quality = preferences.card_quality
            self.image_magick = ImageMagickInterface(
                use_magick_prefix=preferences.use_magick_prefix,
                executable=preferences.imagemagick_executable,
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
