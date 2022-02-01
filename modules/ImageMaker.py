from abc import ABC, abstractmethod

from modules.ImageMagickInterface import ImageMagickInterface
import modules.preferences as global_preferences

class ImageMaker(ABC):
    """
    Abstract class that outlines the necessary attributes for any class that
    creates images.

    All instances of this class must implement `create()` as the main callable
    function to produce an image. The specifics of how that image is created are
    completely customizable.
    """

    @abstractmethod
    def __init__(self) -> None:
        """
        Initializes a new instance. This gives all subclasses access to an
        `ImageMagickInterface` object that uses the docker ID found within
        preferences, as well as a preference object.
        """

        # Store global PreferenceParse object
        self.preferences = global_preferences.pp

        # All ImageMakers have an instance of an ImageMagickInterface
        self.image_magick = ImageMagickInterface(
            self.preferences.imagemagick_docker_id
        )


    @abstractmethod
    def create(self) -> None:
        """
        Abstract method for the creation of the image outlined by this maker.
        This method should delete any intermediate files, and should make
        ImageMagick calls through the parent class' ImageMagickInterface object.
        """

        pass