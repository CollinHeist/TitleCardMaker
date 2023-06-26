from abc import ABC, abstractproperty
from typing import Any, Callable, Optional

from modules.Debug import log

class DatabaseInfoContainer(ABC):
    """
    This class describes an abstract base class for all Info objects
    containing database ID's. This provides common methods for checking
    whether an object has a specific ID, as well as updating an ID
    within an objct.
    """

    __slots__ = ()


    @abstractproperty
    def __repr__(self) -> str:
        raise NotImplementedError(f'All DatabaseInfoContainers must define this')
    

    def __eq__(self, other: 'DatabaseInfoContainer') -> bool:
        """
        Compare the equality of two like objects. This compares all
        `_id` attributes of the objects.

        Args:
            other: Reference object to compare equality of.

        Returns:
            True if any of the `_id` attributes of these objects are
            equal (and not None). False otherwise.

        Raises:
            TypeError if `other` is not of the same class as `self`.
        """

        # Verify class comparison
        if not isinstance(other, self.__class__):
            raise TypeError(f'Can only compare like DatabaseInfoContainer objects')

        # Compare each ID attribute in slots
        for attr in self.__slots__:
            if attr.endswith('_id'):
                # ID is defined, non-None, and matches
                if (getattr(self, attr, None) is not None
                    and getattr(self, attr, None) == getattr(other, attr, None)):
                    return True

        # No matches, inequality
        return False


    def _update_attribute(self,
            attribute: str,
            value: Any, 
            type_: Optional[Callable] = None
        ) -> None:
        """
        Set the given attribute to the given value with the given type.

        Args:
            attribute: Attribute (string) being set.
            value: Value to set the attribute to.
            type_: Optional callable to call on value before assignment.
        """

        # Set attribute if current value is None and new value isn't
        if (value is not None
            and value != 0
            and getattr(self, attribute) is None
            and len(str(value)) > 0):
            # If a type is defined, use that
            if type_ is None:
                setattr(self, attribute, value)
            else:
                setattr(self, attribute, type_(value))


    def has_id(self, id_: str) -> bool:
        """
        Determine whether this object has defined the given ID.

        Args:
            id_: ID being checked

        Returns:
            True if the given ID is defined (i.e. not None) for this
            object. False otherwise.
        """

        return getattr(self, id_) is not None


    def has_ids(self, *ids: tuple[str]) -> bool:
        """
        Determine whether this object has defined all the given ID's.

        Args:
            ids: Any ID's being checked for.

        Returns:
            True if all the given ID's are defined (i.e. not None) for
            this object. False otherwise.
        """

        return all(getattr(self, id_) is not None for id_ in ids)
    

    def copy_ids(self, other: 'DatabaseInfoContainer') -> None:
        """
        Copy the database ID's from another DatabaseInfoContainer into
        this object. Only updating the more precise ID's (e.g. this
        object's ID must be None and the other ID must be non-None).

        Args:
            other: Container whose ID's are being copied over.
        """

        # Go through all attributes of this object
        for attr in self.__slots__:
            # Attribute is ID, this container doesn't have, other does
            if (attr.endswith('_id')
                and not getattr(self, attr)
                and getattr(other, attr)):
                # Transfer ID 
                log.debug(f'Copied {attr}[{getattr(other, attr)}] into {self!r}')
                setattr(self, attr, getattr(other, attr))

        return None