from pathlib import Path

from modules.Debug import info, warn, error
from modules.Title import Title
from modules.TitleCard import TitleCard

class Episode:
    """
    This class defines an episode of a series that has a corresponding Title
    Card. An Episode is defined (and identified) by its season and episode
    number.
    """

    def __init__(self, season_number: int, episode_number: int,
                 card_class: 'CardType', base_source: Path, destination: Path,
                 title: Title, abs_number: int=None,
                 **extra_characteristics: dict) -> None:
        """
        Constructs a new instance of an Episode.

        :param      season_number:  The season number of this episode.
        :param      episode_number: The episode number of this episode.
        :param      base_source:    The base source directory to look for
                                    source images within.
        :param      destination:    The destination for the title card
                                    associated with this episode.
        :param      title:          The title (full text) of this episode.
        :param      abs_number:     The absolute episode number of this episode.
        :param      extra_characteristics:  Additional characteristics to pass
                                            to the creation of the TitleCard
                                            from this Episode.
        """

        # Set object attributes
        self.season_number = int(season_number)
        self.episode_number = int(episode_number)
        self.card_class = card_class
        self.abs_number = int(abs_number) if abs_number != None else None

        # Set source/destination paths
        source_name = (f's{season_number}e{episode_number}'
                       f'{TitleCard.INPUT_CARD_EXTENSION}')
        self.source = base_source / source_name
        self.destination = destination

        # Store Title object
        self.title = title

        # Store extra characteristics
        self.extra_characteristics = extra_characteristics


    def __str__(self) -> str:
        """
        Returns a string representation of the object.
        
        :returns:   String representation of the object.
        """

        return f'Episode S{self.season_number:02}E{self.episode_number:02}'


    def __repr__(self) -> str:
        """
        Returns an unambiguous string representation of the object.
        
        :returns:   String representation of the object.
        """

        return (f'<Episode season_number={self.season_number}, episode_number='
                f'{self.episode_number}, abs_number={self.abs_number}, '
                f'card_class={self.card_class}, source={self.source}, '
                f'destination={self.destination}, title={self.title}>')


    def matches(self, episode_info: dict) -> bool:
        """
        Check if the provided episode info matches this object.

        Matching is done by season and episode number.
        
        :param      episode_info:   Episode info dictionary. Must have keys for
                                    'season_number' and 'episode_number'.
        
        :returns:   True if the info matches this object.
        """

        season_match = episode_info['season_number'] == self.season_number
        episode_match = episode_info['episode_number'] == self.episode_number

        return (season_match and episode_match)

        