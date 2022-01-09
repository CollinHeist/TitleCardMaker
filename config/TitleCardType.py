from abc import ABC, abstractmethod

from ImageMagickInterface import ImageMagickInterface
import preferences

class TitleCardType(ABC):
    """
    Abstract class that outlines the creation of a title card maker profile.

    A title card profile is responsible for taking title card information, such
    as season and episode numbers, fonts, etc., and then producing a title card
    according to that class's own functions. 

    All instances of this class must implement `create()` as the main callable
    function to produce a title card. The specifics of how that card looks are
    completely customizable.
    """

    @abstractmethod
    def __init__(self) -> None:
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