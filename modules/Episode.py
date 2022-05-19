from pathlib import Path

from modules.Title import Title
from modules.TitleCard import TitleCard

class Episode:
    """
    This class defines an episode of a series that has a corresponding Title
    Card. An Episode encapsulates some EpisodeInfo, as well as attributes that
    map that info to a source and destination file.
    """

    __slots__ = ('episode_info', 'card_class', '__base_source', 'source',
                 'destination', 'blur', 'extra_characteristics', 'spoiler',
                 '_spoil_type')
    

    def __init__(self, episode_info: 'EpisodeInfo', card_class: 'CardType',
                 base_source: Path, destination: Path, **extras: dict) -> None:
        """
        Constructs a new instance of an Episode.

        :param      episode_info:   Episode info for this episode.
        :param      base_source:    The base source directory to look for source
                                    images within.
        :param      destination:    The destination for the title card
                                    associated with this Episode.
        :param      extras:         Additional characteristics to pass to the
                                    creation of the TitleCard from this Episode.
        """

        # Set object attributes
        self.episode_info = episode_info
        self.card_class = card_class

        # Set source/destination paths
        self.__base_source = base_source
        source_name = (f's{episode_info.season_number}'
                       f'e{episode_info.episode_number}'
                       f'{TitleCard.INPUT_CARD_EXTENSION}')
        self.source = base_source / source_name
        self.destination = destination

        # Store extra characteristics
        self.extra_characteristics = extras

        # Episodes are spoilers and not blurred until updated
        self.spoiler = True
        self.blur = False
        self._spoil_type = 'spoiled'


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'Episode {self.episode_info}'


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object"""

        return (f'<Episode {self.episode_info=}, {self.card_class=}, '
                f'{self.source=}, {self.destination=}, {self.spoiler=},'
                f'{self.blur=}, {self.extra_characteristics=}>')


    def update_source(self, new_source: str=None) -> None:
        """
        { function_description }
        
        :param      source:  The source
        """

        if new_source != None:
            if isinstance(new_source, Path):
                self.source = new_source
            else:
                self.source = self.__base_source / new_source


    def delete_card(self) -> None:
        """Delete the title card for this Episode."""

        self.destination.unlink(missing_ok=True)


    def make_spoiler_free(self, action: str) -> None:
        """
        Modify this Episode to be spoiler-free according to the given spoil
        action. This updates the spoiler and blur attribute flags, and changes
        the source Path for the Episode if art is the specified action.
        
        :param      action: Spoiler action to update according to.
        """

        # Return if action isn't blur or art
        if action == 'ignore':
            return None

        # Update spoiler and blur attributes
        self.spoiler = False
        self.blur = action in ('blur', 'blur_all')
        self._spoil_type = 'art' if 'art' in action else 'blur'

        # Blurring, set source to blurred source in 
        if action in ('art', 'art_all'):
            self.source = self.source.parent / 'backdrop.jpg'

        