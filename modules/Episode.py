from pathlib import Path

from modules.Debug import info, warn, error
from modules.Title import Title
from modules.TitleCard import TitleCard

class Episode:
    """
    This class defines an episode of a series that has a corresponding Title
    Card. An Episode encapsulates some EpisodeInfo, as well as attributes that
    map that info to a source and destination file.
    """

    def __init__(self, episode_info: 'EpisodeInfo', card_class: 'CardType',
                 base_source: Path, destination: Path, **extras: dict) -> None:
        """
        Constructs a new instance of an Episode.

        :param      episode_info:   Episode info for this episode.
        :param      base_source:    The base source directory to look for source
                                    images within.
        :param      destination:    The destination for the title card
                                    associated with this episode.
        :param      extras:         Additional characteristics to pass to the
                                    creation of the TitleCard from this Episode.
        """

        # Set object attributes
        self.episode_info = episode_info
        self.card_class = card_class

        # Set source/destination paths
        source_name = (f's{episode_info.season_number}'
                       f'e{episode_info.episode_number}'
                       f'{TitleCard.INPUT_CARD_EXTENSION}')
        self.source = base_source / source_name
        self.destination = destination

        # Store extra characteristics
        self.extra_characteristics = extras


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'Episode {self.episode_info}'


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object"""

        return (f'<Episode episode_info={self.episode_info}, card_class='
                f'{self.card_class}, source={self.source}, destination='
                f'{self.destination}, extras={self.extra_characteristics}')

        