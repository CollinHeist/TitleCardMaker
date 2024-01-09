from logging import Logger
from typing import Generic, Iterable, Iterator, Mapping, Optional, TypeVar

from modules.Debug import log
from modules.Interface import Interface

_InterfaceID = TypeVar('_InterfaceID', bound=int)
_Interface = TypeVar('_Interface', bound=Interface)


# class InterfaceGroup(Mapping[int, type[Interface]]):
class InterfaceGroup(Generic[_InterfaceID, _Interface],
                     Mapping[_InterfaceID, _Interface]):
    """
    Class that defines a group of like-classed Interfaces. This class
    creates a mapping of interface IDs to Interface instances, and also
    provides convenience methods for adding and modifying interfaces.

    >>> ig = InterfaceGroup.from_argument_list(
        MyInterface,
        [{'interface_id': 0, 'url': '...', 'api_key': '...'},
         {'interface_id': 2, 'url': '...', 'api_key': '...'}],
    ) # This is practically equivalent to:
    >>> ig = {
        0: MyInterface(url='...', api_key='...'),
        2: MyInterface(url='...', api_key='...'),
    }
    """


    __slots__ = ('cls', 'interfaces', '_uninitialized')


    def __init__(self, cls: type[_Interface]) -> None:
        """
        Initialize this object as a group containing interfaces of
        the given class.

        Args:
            cls: Class to initialize and construct whenever interfaces
                are added.
        """

        self.cls = cls
        self.interfaces: dict[_InterfaceID, _Interface] = {}
        self._uninitialized: dict[_InterfaceID, dict] = {}


    def __repr__(self) -> str:
        """Get an unambigious string representation of this object."""

        return f'<InterfaceGroup[{self.cls.__name__}]{self.interfaces}>'


    def __bool__(self) -> bool:
        """
        Get the truthy-ness of this group of interfaces.

        Returns:
            True if all mapped interfaces are also truthy (activated).
            False otherwise.
        """

        return any(bool(interface) for interface in self.interfaces.values())


    def __len__(self) -> int:
        """
        The number of interfaces defined in this group.
        """

        return len(self.interfaces)


    def __getitem__(self, interface_id: _InterfaceID) -> Optional[_Interface]:
        """
        Get the Interface with the given ID. If the Interface with the
        given ID is defined but not initialized / active, then an
        attempt is made to re-initialize and return it.

        Args:
            interface_id: ID of the Interface to get.

        Returns:
            Interface with the given ID. None if there is no Interface
            with the given ID.
        """

        if interface_id in self.interfaces:
            return self.interfaces[interface_id]

        if interface_id in self._uninitialized:
            try:
                return self.initialize_interface(
                    interface_id, self._uninitialized[interface_id]
                )
            except Exception:
                pass

        return None


    def __setitem__(self,
            interface_id: _InterfaceID,
            interface: _Interface,
        ) -> None:
        """
        Store the given Interface at the given ID.

        Args:
            interface_id: ID to store the given Interface at.
            interface: Interface being stored.
        """

        self.interfaces[interface_id] = interface


    def __contains__(self, interface_id: _InterfaceID) -> bool:
        """
        Whether the given interface ID has an associated Interface.
        """

        return (
            interface_id in self.interfaces
            or interface_id in self._uninitialized
        )


    def __iter__(self) -> Iterator[tuple[_InterfaceID, _Interface]]:
        """
        Iterate through this object. Practically identical to calling
        `dict.items()`.

        Returns:
            Tuple of the interface ID and Interface object.
        """

        for interface_id, interface in self.interfaces.items():
            yield interface_id, interface


    @property
    def first_interface_id(self) -> Optional[_InterfaceID]:
        """The first interface ID with a defined, active Interface."""

        for interface_id, interface in self.interfaces.items():
            if interface:
                return interface_id

        return None


    @classmethod
    def from_argument_list(
            cls: type['InterfaceGroup'],
            interface_cls: type[_Interface],
            interface_kwargs: Iterable[dict],
            *,
            log: Logger = log,
        ) -> 'InterfaceGroup':
        """
        Construct a new `InterfaceGroup` object of the given
        `interface_cls`, each initialized with the given arguments.

        >>> # Construct two MyInterface objects with the given URL's
        >>> ig = InterfaceGroup.from_argument_list(
            MyInterface,
            [{'interface_id': 0, 'url': '...'},
             {'interface_id': 1, 'url': '...'}],
        )

        Args:
            interface_cls: Interface class the created `InterfaceGroup`
                will map and initialize.
            interface_kwargs: Iterable of kwargs for initializing each
                Interface object with.
            log: Logger for all log messages.

        Returns:
            Initialized `InterfaceGroup` object containing initalized
            `interface_cls` objects.
        """

        interface_group = cls(interface_cls)
        for kwargs in interface_kwargs:
            interface_id = kwargs['interface_id']
            interface_group.interfaces[interface_id] = interface_cls(
                **kwargs, log=log,
            )

        return interface_group


    def initialize_interface(self,
            interface_id: _InterfaceID,
            interface_kwargs: dict,
            *,
            log: Logger = log,
        ) -> _Interface:
        """
        Construct and initialize the Interface with the given ID.

        Args:
            interface_id: ID of the Interface to initialize.
            interface_kwargs: Kwargs to pass to the Interface
                initialization.
            log: Logger for all log messages.

        Returns:
            Initialized Interface.
        """

        log.debug(f'Initializing {self.cls.__name__}[{interface_id}]..')
        try:
            self.interfaces[interface_id] = self.cls(
                **interface_kwargs, log=log
            )
            self._uninitialized.pop(interface_id, None)
        except Exception as exc:
            self._uninitialized[interface_id] = interface_kwargs
            raise exc
        log.debug(f'Finished initializing {self.cls.__name__}[{interface_id}]')

        return self.interfaces[interface_id]


    def refresh(self,
            interface_id: _InterfaceID,
            interface_kwargs: dict,
            *,
            log: Logger = log,
        ) -> _Interface:
        """
        Refresh the given interface.

        Args:
            interface_id: ID of the interface being refreshed.
            interface_kwargs: Keyword arguments to initialize the
                Interface with.
            log: Logger for all log messages.

        Returns:
            Interface initialized with the given arguments.
        """

        self.interfaces[interface_id] = self.cls(**interface_kwargs, log=log)

        return self.interfaces[interface_id]


    def disable(self, interface_id: _InterfaceID, /) -> None:
        """
        Disable (and delete) the Interface with the given ID.

        Args:
            interface_id: ID of the Interface to disable.
        """

        if interface_id in self.interfaces:
            del self.interfaces[interface_id]
