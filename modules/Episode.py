from pathlib import Path

from modules.Debug import *
from modules.TitleCard import TitleCard

class Episode:
    """
    This class defines an episode of a series that has a corresponding Title
    Card. An Episode is defined (and identified) by its season and episode
    number. Upon initialization, this class splits episode titles into up to two
    lines (if necessary, as determined by length of the title and the card
    class).

    An example usage is shown below:

    ```
    >>> e = Episode(
    >>>     1, 1, 
    >>>     '/sources/Show (Year)/', 
    >>>     '/media/Show (Year)/Season 1/Show (Year) - S01E01.jpg',
    >>>     'Long Pilot Title: Episode 1 of Season 1'
    >>> )
    >>> e.title_top_line, e.title_bottom_line
    ('Long Pilot Title:', 'Episode 1 of Season 1')
    ```
    """

    def __init__(self, season_number: int, episode_number: int,
                 card_class: 'CardType', base_source: Path, destination: Path,
                 title: str, abs_number: int=None) -> None:
        """
        Constructs a new instance.

        :param      season_number:  The season number of this episode.

        :param      episode_number: The episode number of this episode.

        :param      base_source:    The base source directory to look for
                                    source images within.

        :param      destination:    The destination for the title card
                                    associated with this episode.

        :param      title:          The title (full text) of this episode.

        :param      abs_number:     The absolute episode number of this episode.
        """

        # Set object attributes
        self.season_number = int(season_number)
        self.episode_number = int(episode_number)
        self.card_class = card_class
        self.abs_number = int(abs_number) if abs_number != None else None

        # Set in/out paths
        source_name = (f's{season_number}e{episode_number}'
                       f'{TitleCard.INPUT_CARD_EXTENSION}')
        self.source = base_source / source_name
        self.destination = destination

        # If title is a list, parse into top/botton text
        self.title = title
        if isinstance(title, (list, tuple)):
            self.title_top_line = title[0]
            self.title_bottom_line = title[1]
        else:
            top, bottom = card_class.split_title(title)
            self.title_top_line, self.title_bottom_line = top, bottom


    def __repr__(self) -> str:
        """
        Returns a unambiguous string representation of the object (for debug...).
        
        :returns:   String representation of the object.
        """

        return (
            f'<Episode(season_number={self.season_number}, episode_number='
            f'{self.episode_number}, title_top_line="{self.title_top_line}",'
            f' title_bottom_line="{self.title_bottom_line}">'
        )


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

        return season_match and episode_match

        