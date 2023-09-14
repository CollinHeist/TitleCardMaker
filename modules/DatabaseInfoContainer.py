from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from modules.Debug import log


class InterfaceID:
    """
    This class describes a "singular" ID for a given interface - i.e.
    all of "Sonarr" - but whose actual ID is varied by the interface
    number/ID itself. The idea being a singular Show/Episode may exist
    on multiple interfaces under multiple IDs, but all those IDs
    correspond to the same content.
    
    This can be viewed as a dictionary that maps interface IDs (keys) to
    actual IDs (values). For example:

    >>> iid = InterfaceID('0:123,1:234', type_=int)
    >>> print(repr(iid))
    '<InterfaceID {0: 123, 1: 234}>'

    These IDs can then be set/got via the interface IDs:

    >>> print(iid[0])
    123
    >>> iid[2] = 999
    >>> print(iid[2])
    999

    The intention is to be able to represent a collection of interface
    ID's with a single string that can be stored in a DB, while also
    providing ID-related functionality.
    """

    INTER_ID_KEY = ':'
    INTER_INTERFACE_KEY = ','


    def __init__(self,
            id_: Optional[str] = None,
            /,
            *,
            type_: Optional[Callable] = None,
        ) -> None:
        """
        Construct a new InterfaceID object from the given ID string.

        Args:
            id_: ID string to parse for interface ID pairs.
            type_: Callable for converting the type of each ID.
        """

        self._type = type_

        # No ID provided
        if id_ is None:
            self._ids = {}
        # No type provided, parse directly
        elif type_ is None:
            if '-' in id_:
                self._ids = {
                    int(substr.split('-')[0]): substr.split('-')[1]
                    for substr in id_.split(self.INTER_INTERFACE_KEY)
                }
            else:
                self._ids = {
                    int(substr.split(self.INTER_ID_KEY)[0]):
                        substr.split(self.INTER_ID_KEY)[1]
                    for substr in id_.split(self.INTER_INTERFACE_KEY)
                }
        else:
            if '-' in id_:
                self._ids = {
                    int(substr.split('-')[0]): type_(substr.split('-')[1])
                    for substr in id_.split(self.INTER_INTERFACE_KEY)
                }
            else:
                self._ids = {
                    int(substr.split(self.INTER_ID_KEY)[0]):
                        type_(substr.split(self.INTER_ID_KEY)[1])
                    for substr in id_.split(self.INTER_INTERFACE_KEY)
                }


    def __setitem__(self, interface_id: int, id_: Any, /) -> None:
        """
        Set the ID for the given interface to the given value. This
        performs any assigned type conversions if this object was
        initialized with a type.

        Args:
            interface_id: ID of the interface whose ID this is.
            id_: ID to set.
        """

        self._ids[interface_id] = id_ if self._type is None else self._type(id_)


    def __getitem__(self, interface_id: int, /) -> Optional[Any]:
        """
        Get the ID for the given interface.

        Args:
            interface_id: ID of the interface whose ID to get.

        Returns:
            ID of the given interface. None if there is no ID.
        """

        return self._ids.get(interface_id)


    def __eq__(self, other: 'InterfaceID') -> bool:
        """
        Evaluate the equality of two InterfaceID objects.

        Args:
            other: InterfaceID to compare against.

        Returns:
            True if any IDs of the two IDs (of the same Interface ID)
            match. False otherwise.

        Raises:
            TypeError if `other` is not an InterfaceID object.
        """

        # Verify class comparison
        if not isinstance(other, self.__class__):
            raise TypeError(f'Can only compare like InterfaceID objects')

        return any(
            other[interface_id] == id_
            for interface_id, id_ in self._ids.items()
        )


    def __bool__(self) -> bool:
        """
        Get the boolean value of this ID.

        Returns:
            True if there is at least one mapped ID, False otherwise.
        """

        return len(self._ids) > 0


    def __repr__(self) -> str:
        """Get an unambigious representation of this object."""

        return f'<InterfaceId {self._ids}>'


    def __str__(self) -> str:
        """
        Get a string representation of this object. This is a string
        that can be used to initialize an exact InterfaceID object.
        """

        return self.INTER_INTERFACE_KEY.join(
            f'{key}{self.INTER_ID_KEY}{value}'
            for key, value in self._ids.items()
        )


class DatabaseInfoContainer(ABC):
    """
    This class describes an abstract base class for all Info objects
    containing database ID's. This provides common methods for checking
    whether an object has a specific ID, as well as updating an ID
    within an objct.
    """

    __slots__ = ()


    @abstractmethod
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
            raise TypeError(f'Can only compare like DatabaseInfoContainers')

        return any(
            attr.endswith('_id')
            and getattr(self, attr, None) is not None
            and getattr(self, attr, None) == getattr(other, attr, None)
            for attr in self.__slots__
        )


    def _update_attribute(self,
            attribute: str,
            value: Any,
            type_: Optional[Callable] = None,
            *,
            interface_id: Optional[int] = None,
        ) -> None:
        """
        Set the given attribute to the given value with the given type.

        Args:
            attribute: Attribute (string) being set.
            value: Value to set the attribute to.
            type_: Optional callable to call on value before assignment.
                Resulting value is thus `type_(value)`.
            interface_id: ID of the interface for this ID. Required if
                the specified attribute corresponds to an `InterfaceID`
                object.
        """

        if not value:
            return None

        if isinstance(getattr(self, attribute), InterfaceID):
            if getattr(self, attribute)[interface_id] is None:
                getattr(self, attribute)[interface_id] = value
        elif getattr(self, attribute) is None:
            if type_ is None:
                setattr(self, attribute, value)
            else:
                setattr(self, attribute, type_(value))

        return None


    def has_id(self, id_: str, /, interface_id: Optional[int] = None) -> bool:
        """
        Determine whether this object has defined the given ID.

        Args:
            id_: ID being checked.
            interface_id: ID of the interface whose ID is being checked.

        Returns:
            True if the given ID is defined (i.e. not None) for this
            object. False otherwise.
        """

        id_name = id_ if id_.endswith('_id') else f'{id_}_id'

        if interface_id is None:
            if isinstance((val := getattr(self, id_name)), InterfaceID):
                raise ValueError(f'InterfaceID objects require an interface_id')

            return val is not None

        return getattr(self, id_name)[interface_id] is not None


    def has_ids(self,
            *ids: tuple[str],
            interface_id: Optional[int] = None,
        ) -> bool:
        """
        Determine whether this object has defined all the given ID's.

        Args:
            ids: Any ID's being checked for.

        Returns:
            True if all the given ID's are defined (i.e. not None) for
            this object. False otherwise.
        """

        return all(self.has_id(id_, interface_id=interface_id) for id_ in ids)


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
