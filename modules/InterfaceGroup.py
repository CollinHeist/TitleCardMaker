from logging import Logger
from typing import Iterable, Iterator, Mapping, Type

from modules.Debug import log
from modules.Interface import Interface


class InterfaceGroup(Mapping[int, Interface]):
    """
    
    """


    def __init__(self, cls: Type[Interface]) -> None:
        """
        Initialize this object as a group containing interfaces of
        the given class.

        Args:
            cls: Class to initialize and construct whenever interfaces
                are added.
        """

        self.cls = cls
        self.interfaces: dict[int, Interface] = {}


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

        return all(bool(interface) for interface in self.interfaces.values())


    def __len__(self) -> int:
        """
        
        """

        return len(self.interfaces)


    def __getitem__(self, interface_id: int) -> Interface:
        """
        
        """

        return self.interfaces[interface_id]


    def __setitem__(self, interface_id: int, interface: Interface) -> None:
        """
        
        """

        self.interfaces[interface_id] = interface


    def __contains__(self, __key: int) -> bool:
        """
        """

        return __key in self.interfaces


    def __iter__(self) -> Iterator[tuple[int, Interface]]:
        """
        Iterate through this object. Practically identical to calling
        `dict.items()`.

        Returns:
            Tuple of the interface ID and Interface object.
        """

        for interface_id, interface in self.interfaces.items():
            yield interface_id, interface


    @classmethod
    def from_argument_list(
            cls: Type['InterfaceGroup'],
            interface_cls: Type[Interface],
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

        Args:
            interface_cls: Interface class the created `InterfaceGroup`
                will map and initialize.
            interface_kwargs: Iterable of kwargs for initializing each
                Interface object with.
            log: (Keyword) Logger for all log messages.

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


    def append_interface(self,
            *args,
            log: Logger = log,
            **kwargs,
        ) -> tuple[int, Interface]:
        """
        Construct and add a new Interface object to this group. This
        assigns a sequential interface ID.

        Args:
            args, kwargs: Any arguments to pass to the Interface
                initialization.

        Returns:
            Tuple of the assigned interface ID and the Interface object
            itself.
        """

        # Assign ID
        if self.interfaces:
            interface_id = max(self.interfaces) + 1
        else:
            interface_id = 0

        # Construct Interface, store at ID
        interface = self.cls(*args, **kwargs, log=log)
        self.interfaces[interface_id] = interface

        return interface_id, interface


    def refresh_all(self,
            interface_kwargs: list[dict],
            *,
            log: Logger = log,
        ) -> None:
        """
        
        """

        self.interfaces = {}
        for kwargs in interface_kwargs:
            interface_id = kwargs['interface_id']
            self.interfaces[interface_id] = self.cls(**kwargs, log=log)


    def refresh(self,
            interface_id: int,
            interface_kwargs: dict,
            *,
            log: Logger = log,
        ) -> None:
        """
        
        """

        self.interfaces[interface_id] = self.cls(interface_kwargs, log=log)
