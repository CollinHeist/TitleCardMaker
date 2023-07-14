from abc import ABC


class Interface(ABC):
    """
    This class describes an abstract interface to some service. This
    class only defines the `__bool__` method and an `active` attribute.
    """

    def __init__(self) -> None:
        """
        Initialize this Interface with an inactive state.
        """

        self.active = False


    def __bool__(self) -> bool:
        """
        Return whether this Interface is active.
        """

        return self.active


    def activate(self) -> None:
        """
        Set this Interface as active.
        """

        self.active = True
