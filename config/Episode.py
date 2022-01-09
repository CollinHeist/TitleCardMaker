from pathlib import Path

from Debug import *
from TitleCard import TitleCard

class Episode:
    """
    This class defines an episode of a series that has a corresponding Title Card.
    An Episode is defined (and identified) by its season and episode number.
    Upon initialization, this class splits episode titles into up to two lines (if
    necessary, as determined by length of the title itself).

    This class is not intended to execute any methods, and is instead intended
    to contain data for use by other classes.

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

    """Character count to begin splitting episode text into 2 lines"""
    MAX_LINE_LENGTH: int = 32

    def __init__(self, season_number: int, episode_number: int,
                 base_source: Path, destination: Path, title: str) -> None:
        """
        Constructs a new instance.

        :param      season_number:  The season number

        :param      episode_number: The episode number

        :param      base_source:    The source

        :param      title:          The title
        """

        # Set object attributes
        self.season_number = int(season_number)
        self.episode_number = int(episode_number)

        # Set in/out paths
        name = f's{season_number}e{episode_number}{TitleCard.INPUT_CARD_EXTENSION}'
        self.source = base_source / name
        self.destination = destination

        # If title is a list, parse into top/botton text
        self.title = title
        if isinstance(title, (list, tuple)):
            self.title_top_line = title[0]
            self.title_bottom_line = title[1]
        else:
            self.title_top_line, self.title_bottom_line = self._split_title(title)

        # Set attribute for whether this episode exists in the Database, for checking later
        self.in_database = True


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


    def __str__(self) -> str:
        """
        Returns a string representation of the object.
        
        :returns:   String representation of the object.
        """

        return f'Season {self.season_number}, Episode {self.episode_number}'


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


    @staticmethod
    def split_episode_title(title: str) -> (str, str):
        """
        Split a given title into top and bottom title text.
        
        :param      title:  The title to be split.
        
        :returns:   Tuple of titles. First entry is the top title, second
                    is the bottom.
        """

        return Episode._split_title(title)


    @staticmethod
    def _split_title(title: str) -> (str, str):
        """
        Inner function to split a given title into top and bottom title text.
        Splitting takes priority on some special characters, such as colons,
        and commas. Final splitting is then done on spaces
        
        :param      title:  The title to be split.
        
        :returns:   Tuple of titles. First entry is the top title, second
                    is the bottom.
        """

        top, bottom = '', title
        if len(title) >= Episode.MAX_LINE_LENGTH:
            # Only look for colon/comma in the first half of the text to avoid long top lines
            # for titles with these in the last part of the title like [.......]: [..]
            if ': ' in bottom[:len(bottom)//2]:
                top, bottom = title.split(': ', 1)
                top += ':'
            elif ', ' in bottom[:len(bottom)//2]:
                top, bottom = title.split(', ', 1)
                top += ','
            else:
                top, bottom = title.split(' ', 1)

            while len(bottom) >= Episode.MAX_LINE_LENGTH:
                top2, bottom = bottom.split(' ', 1)
                top += f' {top2}'

        return top, bottom

        