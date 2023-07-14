from abc import ABC, abstractmethod

from modules.EpisodeInfo import EpisodeInfo

class EpisodeDataSource(ABC):
    """
    This class describes an abstract episode data source. Classes of
    this type define sources of Episode data.
    """


    @property
    @abstractmethod
    def SERIES_IDS(self) -> tuple[str]:
        """Valid SeriesInfo ID's that can be set by this data source."""
        raise NotImplementedError(f'All EpisodeDataSources must implement this')


    @abstractmethod
    def set_series_ids(self) -> None:
        """Set the series ID's for the given SeriesInfo object."""
        raise NotImplementedError(f'All EpisodeDataSources must implement this')


    @abstractmethod
    def set_episode_ids(self) -> None:
        """Set the episode ID's for the given EpisodeInfo objects."""
        raise NotImplementedError(f'All EpisodeDataSources must implement this')


    @abstractmethod
    def get_all_episodes(self) -> list[EpisodeInfo]:
        """Get all the EpisodeInfo objects associated with the given series."""
        raise NotImplementedError(f'All EpisodeDataSources must implement this')
