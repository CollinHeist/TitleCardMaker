from abc import ABC, abstractmethod

from modules.ImageMagickInterface import ImageMagickInterface
import modules.preferences as preferences

class ImageMaker(ABC):
    """
    Abstract class that outlines the necessary attributes for any class that
    creates images.

    All instances of this class must implement `create()` as the main callable
    function to produce a title card. The specifics of how that card looks are
    completely customizeable.
    """

    @abstractmethod
    def __init__(self) -> None:
        """
        Initializes a new instance. This gives all subclasses access to an
        `ImageMagickInterface` object that uses the docker ID found within
        preferences. 
        """

        self.image_magick = ImageMagickInterface(preferences.imagemagick_docker_id)


    @abstractmethod
    def create(self) -> None:
        """
        Abstract method for the creation of the title card outlined by this
        profile. This method should delete any intermediate files, and should
        make ImageMagick calls through this parent class' `image_magick`
        attribute.
        """
        pass