from abc import ABC, abstractmethod
from typing import Any

class SyncInterface(ABC):
    """
    This class describes an abstract SyncInterface. This is some Interface which
    can be synced (e.g. series can be grabbed) from.
    """

    def get_library_paths(self, filter_libraries: list[str]=[]
                          ) -> dict[str, list[str]]:
        """
        Get all libraries and their associated base directories.

        Args:
            filer_libraries: List of library names to filter the return by.

        Returns:
            Dictionary whose keys are the library names, and whose values are
            the list of paths to that library's base directories.
        """

        return {}


    @abstractmethod
    def get_all_series(self) -> Any: 
        """Abstract method to get all series within this Interface."""
        raise NotImplementedError('All SyncInterfaces must implement this')