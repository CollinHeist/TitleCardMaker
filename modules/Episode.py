from pathlib import Path

from modules.Debug import log
from modules.TitleCard import TitleCard

class Episode:
    """
    This class defines an episode of a series that has a corresponding Title
    Card. An Episode encapsulates some EpisodeInfo, as well as attributes that
    map that info to a source and destination file.
    """

    __slots__ = ('episode_info', 'card_class', '__base_source', 'source',
                 'destination', 'downloadable_source', 'extra_characteristics',
                 'watched', 'blur', 'spoil_type', )
    

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
        self.downloadable_source = True

        # Store extra characteristics
        self.extra_characteristics = extras

        # Episodes are watched, not blurred, and spoiled - until updated
        self.watched = True
        self.blur = False
        self.spoil_type = 'spoiled'


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'Episode {self.episode_info}'


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object"""

        return (f'<Episode {self.episode_info=}, {self.card_class=}, '
                f'{self.source=}, {self.destination=}, {self.watched=},'
                f'{self.blur=}, {self.extra_characteristics=}>')


    def update_statuses(self, watched: bool, watched_style: str, 
                        unwatched_style: str) -> None:
        """
        Update the statuses of this Episode. In particular the watched and
        spoil type statuses.
        
        :param      watched:          New watched status for this Episode.
        :param      watched_style:    Watched style to assign spoil type from.
        :param      unwatched_style:  Unwatched style to assign spoil tyle from.
        """

        # Update watched attribute
        self.watched = watched

        # Update spoil type based on given style and new watch status
        SPOIL_TYPE_STYLE_MAP={'unique': 'spoiled', 'art': 'art', 'blur': 'blur'}
        if self.watched:
            self.spoil_type = SPOIL_TYPE_STYLE_MAP[watched_style]
        else:
            self.spoil_type = SPOIL_TYPE_STYLE_MAP[unwatched_style]


    def update_source(self, new_source, *, downloadable: bool) -> bool:
        """
        Update the source image for this Episode, as well as the downloadable
        flag for the source.
        
        :param      new_source:     New source file.
        :type       new_source:     If Path, then source is taken as-is. If a
                                    str, the the file is looked for within this
                                    Episode's base source directory. If that
                                    file doesn't exist under the base source,
                                    then the string source is taken as a Path
                                    and converted. If None nothing happens.
        :param      downloadable:   Keyword-only argument for whether the new
                                    source is downloadable or not.

        :returns:   True if a new non-None source was provided, False otherwise.
        """

        # If no actual new source was provided, return
        if new_source is None:
            return False

        # Update source path based on input (Path/str of filename in source,etc)
        if isinstance(new_source, Path):
            self.source = new_source
        elif (self.__base_source / new_source).exists():
            self.source = self.__base_source / new_source
        else:
            self.source = Path(new_source)

        # Set the downloadable flag for the new source
        self.downloadable_source = downloadable

        return True


    def delete_card(self) -> None:
        """Delete the title card for this Episode."""

        self.destination.unlink(missing_ok=True)

        