from abc import ABC, abstractmethod
from typing import Literal


InterfaceType = Literal[
    'Emby', 'Jellyfin', 'Plex', 'Sonarr', 'Tautulli', 'TMDb', 'TVDb'
]


class Interface(ABC):
    """
    This class describes an abstract interface to some service. This
    class only defines the `__bool__` method and an `active` attribute.
    """

    @property
    @abstractmethod
    def INTERFACE_TYPE(self) -> InterfaceType:
        """The name/type of interface which the subclass defines."""
        raise NotImplementedError


    def __init__(self) -> None:
        """Initialize this Interface with an inactive state."""

        self.active = False


    def __bool__(self) -> bool:
        """Whether this Interface is active."""

        return self.active


    def activate(self) -> None:
        """Set this Interface as active."""

        self.active = True
