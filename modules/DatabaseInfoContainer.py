from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, Callable, Literal, Optional, TypeVar, Union, overload

from modules.Debug import log


ConnectionID = Union[int, tuple[int, str]]
DatabaseID = TypeVar('DatabaseID')


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

    IDs can also be compared with `<` and `>` for evaluating which
    contains more or less information. For example:

    >>> id0 = InterfaceID('0:123,1:234')
    >>> id1 = InterfaceID('0:123')
    >>> id0 > id1
    True
    >>> id0 > '0:123,1:999'
    False

    The intention is to be able to represent a collection of interface
    ID's with a single string that can be stored in a DB, while also
    providing ID-related functionality.
    """

    INTER_ID_KEY = ':'
    INTER_INTERFACE_KEY = ','

    # """Regex to match library sub ID components"""
    # LIBRARY_SUB_ID_REGEX = re_compile(r'^(\d+):(.+):(.*)$', IGNORECASE)

    __slots__ = ('_type', '_ids', '_libraries')


    def __init__(self,
            /,
            id_: Optional[str] = None,
            *,
            type_: Callable[[str], DatabaseID] = str,
            libraries: bool = False,
        ) -> None:
        """
        Construct a new InterfaceID object from the given ID string.

        Args:
            id_: ID string to parse for interface ID pairs.
            type_: Callable for converting the type of each ID.
            libraries: Whether these types of IDs allow per-library ID
                specification (in addition to per-interface).
        """

        self._type = type_
        self._libraries = libraries

        # No ID provided
        if libraries:
            self._ids: dict[int, dict[str, DatabaseID]] = {}
        else:
            self._ids: dict[int, DatabaseID] = {}
        if not id_:
            return None

        for sub_id in id_.split(self.INTER_INTERFACE_KEY):
            id_vals = sub_id.split(self.INTER_ID_KEY)
            interface_id = int(id_vals[0])
            id_value = type_(id_vals[-1])
            if libraries:
                library = id_vals[1]
                if interface_id in self._ids:
                    self._ids[interface_id][library] = id_value
                else:
                    self._ids[interface_id] = {library: id_value}
            else:
                self._ids[interface_id] = id_value

        return None


    def __setitem__(self,
            connection_id: ConnectionID,
            id_: DatabaseID,
            /,
        ) -> None:
        """
        Set the ID for the given interface to the given value. This
        performs any assigned type conversions if this object was
        initialized with a type.

        Args:
            connection_id: ID of the interface whose ID this is.
            id_: ID to set.
        """

        # Apply type conversion
        typed_id = id_ if self._type is None else self._type(id_)

        if self._libraries and isinstance(connection_id, tuple):
            connection_id, library = connection_id
            if connection_id in self._ids:
                self._ids[connection_id][library] = typed_id
            else:
                self._ids[connection_id] = {library: typed_id}
        else:
            self._ids[connection_id] = typed_id


    def __getitem__(self, connection_id: ConnectionID, /) -> Optional[DatabaseID]:
        """
        Get the ID for the given interface.

        Args:
            connection_id: ID of the interface whose ID to get.

        Returns:
            ID of the given interface. None if there is no ID.
        """

        if self._libraries:
            connection_id, library = connection_id
            return self._ids.get(connection_id, {}).get(library)

        return self._ids.get(connection_id)


    def __delitem__(self, connection_id: ConnectionID, /) -> None:
        """
        Delete the ID for the given interface location.

        >>> del iid[1, 'TV Shows'] # Delete library-accessed InterfaceID
        >>> del iid[2]             # Delete non-library-accessed IDs

        Args:
            connection_id: ID of the interface to reset.
        """

        if self._libraries and isinstance(connection_id, tuple):
            connection_id, library = connection_id
            del self._ids[connection_id][library]
        else:
            del self._ids[connection_id]


    def __eq__(self, other: Union[str, 'InterfaceID']) -> bool:
        """
        Evaluate the equality of two InterfaceID objects.

        Args:
            other: InterfaceID to compare against.

        Returns:
            True if any IDs of the two IDs (of the same Interface ID)
            match. False otherwise.
        """

        # If string, convert to InterfaceID and compare
        if isinstance(other, str):
            return self == InterfaceID(
                other, type_=self._type, libraries=self._libraries
            )

        # Verify class comparison
        if not isinstance(other, self.__class__):
            raise TypeError(f'Can only compare like InterfaceID objects')

        # Per-library IDs, compare each interface and library field
        if self._libraries:
            return any(
                other[iid, library] == id_
                for iid, sub_id in self._ids.items()
                for library, id_ in sub_id.items()
            )

        return any(other[iid] == id_ for iid, id_ in self._ids.items())


    def __gt__(self, other: Union[str, 'InterfaceID']) -> bool:
        """
        Evaluate whether this object contains more information than is
        available in the comparison ID.

        >>> id0 = InterfaceID('0:123,1:234,2:345')
        >>> id1 = InterfaceID('0:123')
        >>> id0 > id1
        True
        >>> id0 > '0:123,1:234,2:999'
        False

        Returns:
            True if this object defines an ID for an interface which is
            not defined in `other`. False otherwise.
        """

        # If a string, convert to InterfaceID and compare
        if isinstance(other, str):
            return self > InterfaceID(
                other, type_=self._type, libraries=self._libraries
            )

        # Per-library IDs, use nested comparison
        if self._libraries:
            return (
                # If this object has any interfaces not present in other
                any(key not in other._ids for key in self._ids)
                # or this object has any libraries not present in other
                or any(
                    library not in other._ids[iid]
                    for iid, libraries in self._ids.items()
                    for library in libraries
                )
            )

        return any(key not in other._ids for key in self._ids)


    def __lt__(self, other: Union[str, 'InterfaceID']) -> bool:
        """
        Evaluate whether this object contains less information than is
        available in the comparison ID.

        >>> id0 = InterfaceID('0:123,1:234,2:345')
        >>> id1 = InterfaceID('0:123')
        >>> id1 < id0
        True
        >>> id0 > '0:123,1:234,2:999'
        False

        Returns:
            True if this object is missing an ID for an interface which
            is defined in `other`. False otherwise.
        """

        # If a string, convert to InterfaceID and compare
        if isinstance(other, str):
            return self < InterfaceID(
                other, type_=self._type, libraries=self._libraries
            )

        # Per-library IDs, use nested comparison
        if self._libraries:
            return (
                # If this object has any interfaces not present in other
                any(key not in self._ids for key in other._ids)
                # or this object has any libraries not present in other
                or any(
                    library not in self._ids[iid]
                    for iid, libraries in other._ids.items()
                    for library in libraries
                )
            )

        return any(key not in self._ids for key in other._ids)


    def __bool__(self) -> bool:
        """
        Get the boolean value of this ID.

        Returns:
            True if there is at least one mapped ID, False otherwise.
        """

        return len(self._ids) > 0


    def __repr__(self) -> str:
        """Get an unambigious representation of this object."""

        return f'<InterfaceID {self._ids}>'


    def __str__(self) -> str:
        """
        Get a string representation of this object. This is a string
        that can be used to initialize an exact InterfaceID object.
        """

        if self._libraries:
            return self.INTER_INTERFACE_KEY.join(
                f'{key}{self.INTER_ID_KEY}{library}{self.INTER_ID_KEY}{id_}'
                for key, library_dict in self._ids.items()
                for library, id_ in library_dict.items()
            )

        return self.INTER_INTERFACE_KEY.join(
            f'{key}{self.INTER_ID_KEY}{value}'
            for key, value in self._ids.items()
        )


    def __add__(self, other: Union[str, 'InterfaceID']) -> 'InterfaceID':
        """
        Add this object to the given object, returning the combination
        of their IDs. This objects IDs take priority in any interface
        ID conflicts.

        >>> id0 = InterfaceID('0:123,1:234')
        >>> id1 = InterfaceID('1:999,2:987')
        >>> str(id0 + id1) # id0's 1:234 takes priority of id1's 1:999
        '0:123,1:234,2:987'
        """

        if not isinstance(other, (str, InterfaceID)):
            raise TypeError('Can only add IDs from a str or InterfaceID')

        # Convert other to an InterfaceID if provided as a string
        if isinstance(other, str):
            other = InterfaceID(
                other, type_=self._type, libraries=self._libraries
            )

        # Create new object for storing finalized attributes in 
        return_id = InterfaceID(
            str(self), type_=self._type, libraries=self._libraries
        )
        for interface_id, sub_id in other._ids.items():
            if self._libraries:
                for library, id_ in sub_id.items():
                    if return_id[interface_id, library] is None:
                        return_id[interface_id, library] = id_
            else:
                if return_id[interface_id] is None:
                    return_id[interface_id] = sub_id

        return return_id


    def delete_interface_id(self, connection_id: ConnectionID, /) -> bool:
        """
        Delete all the IDs associated with the given connection ID.

        Args:
            connection_id: ID of the Connection whose IDs are being
                deleted.

        Returns:
            Whether this object was modified.
        """

        # Connection has IDs, delete
        if connection_id in self._ids:
            del self._ids[connection_id]
            return True

        return False


    def reset(self) -> None:
        """Reset this object."""

        self._ids = {}


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
            raise TypeError(f'Can only compare like '
                            f'{self.__class__.__name__} objects')

        return any(
            getattr(self, attr, None) is not None
            and getattr(self, attr, None) == getattr(other, attr, None)
            for attr in self.__slots__
            if attr.endswith('_id')
        )


    def _update_attribute(self,
            attribute: str,
            value: Any,
            type_: Optional[Callable] = None,
            *,
            interface_id: Optional[int] = None,
            library_name: Optional[str] = None,
        ) -> None:
        """
        Set the given attribute to the given value with the given type.

        Args:
            attribute: Attribute being set.
            value: Value to set the attribute to.
            type_: Optional callable to call on `value` before
                assignment. Resulting value is thus `type_(value)`.
            interface_id: ID of the interface for this ID. Required if
                the specified attribute corresponds to an `InterfaceID`
                object.
            library_name: Name of the library associated with this
                interface. Required if the specified attribute
                corresonsd to a media-server `InterfaceID` object.
        """

        # Value not provided, don't update
        if not value:
            return None

        # Updating an InterfaceID
        if isinstance(getattr(self, attribute), InterfaceID):
            # Update via library name if not already defined
            if library_name:
                if getattr(self, attribute)[interface_id, library_name] is None:
                    getattr(self, attribute)[interface_id, library_name] = value
            # Update directly if not already defined
            elif getattr(self, attribute)[interface_id] is None:
                getattr(self, attribute)[interface_id] = value
        # Non-interface ID that is not defined, update
        elif getattr(self, attribute) is None:
            if type_ is None:
                setattr(self, attribute, value)
            else:
                try:
                    setattr(self, attribute, type_(value))
                except ValueError:
                    log.exception(f'Invalid ID {attribute} of {value} - cannot '
                                  f'be converted to type {type_}')

        return None


    @overload
    def has_id(self,
            id_: Literal['sonarr_id', 'sonarr'],
            /,
            interface_id: int,
            library_name: Literal[None] = None
        ) -> bool:
        ...

    @overload
    def has_id(self,
            id_: Literal[
                'imdb_id', 'imdb', 'tmdb_id', 'tmdb', 'tvdb_id', 'tvdb',
                'tvrage_id', 'tvrage',
            ],
            /,
            interface_id: Literal[None] = None,
            library_name: Literal[None] = None,
        ) -> bool:
        ...

    def has_id(self,
            id_: str,
            /,
            interface_id: Optional[int] = None,
            library_name: Optional[str] = None,
        ) -> bool:
        """
        Determine whether this object has defined the given ID.

        Args:
            id_: ID being checked.
            interface_id: ID of the interface whose ID is being checked.
            library_name: Name of the library containing the ID being
                checked.

        Returns:
            True if the given ID is defined (i.e. not None) for this
            object. False otherwise.

        Raises:
            ValueError if the indicated ID type is an InterfaceID object
            which requires an interface_id and/or library name, but one
            is not provided.
        """

        id_name = id_ if id_.endswith('_id') else f'{id_}_id'

        if isinstance((val := getattr(self, id_name)), InterfaceID):
            if interface_id is None:
                raise ValueError(f'InterfaceID objects require an interface_id')

            if library_name:
                return val[interface_id, library_name] is not None

            return val[interface_id] is not None

        return val is not None


    @overload
    def has_ids(self, *ids: str, interface_id: int, library_name: str) -> bool:
        ...

    @overload
    def has_ids(self,
            *ids: str,
            interface_id: Literal[None] = None,
            library_name: Literal[None] = None,
        ) -> bool:
        ...

    def has_ids(self,
            *ids: str,
            interface_id: Optional[int] = None,
            library_name: Optional[str] = None,
        ) -> bool:
        """
        Determine whether this object has defined all the given ID's.

        Args:
            ids: Any ID's being checked for.
            interface_id: ID of the interface whose IDs are being
                checked.
            library_name: Name of the library containing the ID being
                checked.

        Returns:
            True if all the given ID's are defined (i.e. not None) for
            this object. False otherwise.
        """

        return all(
            self.has_id(
                id_,
                interface_id=interface_id,
                library_name=library_name
            )
            for id_ in ids
        )


    def copy_ids(self,
            other: 'DatabaseInfoContainer',
            *,
            log: Logger = log,
        ) -> None:
        """
        Copy the database ID's from another DatabaseInfoContainer into
        this object. Only updating the more precise ID's (e.g. this
        object's ID must be None and the other ID must be non-None).

        Args:
            other: Container whose ID's are being copied over.
            log: Logger for all log messages.
        """

        # Go through all attributes of this object
        for attr in self.__slots__:
            # Skip non-ID attributes
            if not attr.endswith('_id'):
                continue

            # If this is an InterfaceID, combine
            if isinstance(getattr(self, attr), InterfaceID):
                if getattr(other, attr) > getattr(self, attr):
                    log.debug(f'Merging {attr} <-- {getattr(self, attr)!r}'
                              f' + {getattr(other, attr)!r}')
                    setattr(
                        self,
                        attr,
                        getattr(self, attr) + getattr(other, attr)
                    )
            # Regular ID, copy if this info is missing
            elif not getattr(self, attr) and getattr(other, attr):
                setattr(self, attr, getattr(other, attr))

        return None


    def reset_id(self, id_: str) -> None:
        """
        Reset the ID definition of the given type.

        Args:
            id_: ID name being reset.
        """

        id_ = id_ if id_.endswith('_id') else f'{id_}_id'
        if isinstance(getattr(self, id_), InterfaceID):
            getattr(self, id_).reset()
        else:
            setattr(self, id_, None)
