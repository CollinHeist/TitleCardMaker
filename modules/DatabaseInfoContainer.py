from abc import ABC
from typing import Any, Optional

from modules.Debug import log

class DatabaseInfoContainer(ABC):
    """
    This class describes an abstract base class for all Info objects containing
    database ID's. This provides common methods for checking whether an object
    has a specific ID, as well as updating an ID within an objct.
    """

    def _update_attribute(self, attribute: str, value: Any, 
                          type_: Optional[callable]=None) -> None:
        """
        Set the given attribute to the given value with the given type.

        Args:
            attribute: Attribute (string) being set.
            value: Value to set the attribute to.
            type_: Optional callable to call on value before assignment.
        """

        # Set attribute if current value is None and new value isn't
        if getattr(self, attribute) is None and value is not None:
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
            True if the given ID is defined (i.e. not None) for this object.
            False otherwise.
        """

        return getattr(self, id_) is not None


    def has_ids(self, *ids: tuple[str]) -> bool:
        """
        Determine whether this object has defined all the given ID's.

        Args:
            ids: Any ID's being checked for.

        Returns:
            True if all the given ID's are defined (i.e. not None) for this
            object. False otherwise.
        """

        return all(getattr(self, id_) is not None for id_ in ids)