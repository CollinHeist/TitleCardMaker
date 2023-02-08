from abc import ABC, abstractmethod
from typing import Any

class SyncInterface(ABC):
    """
    This class describes an abstract SyncInterface. This is some Interface which
    can be synced (e.g. series can be grabbed) from.
    """

    @abstractmethod
    def get_all_series(self) -> Any: 
        """Abstract method to get all series within this Interface."""
        raise NotImplementedError('All SyncInterfaces must implement this')