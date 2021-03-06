from dataclasses import dataclass, field
from re import match
from typing import ClassVar

from modules.Debug import log

@dataclass(eq=False, order=False)
class SeriesInfo:
    """
    This class encapsulates static information that is tied to a single Series.
    """

    """Initialization fields"""
    name: str
    year: int
    imdb_id: str=None
    sonarr_id: int=None
    tvdb_id: int=None
    tmdb_id: int=None

    """After how many characters to truncate the short name"""
    SHORT_WIDTH: ClassVar[int] = 15

    """Mapping of illegal filename characters and their replacements"""
    __ILLEGAL_CHARACTERS: ClassVar[dict[str: str]] = {
        '?': '!',
        '<': '',
        '>': '',
        ':':' -',
        '"': '',
        '/': '+',
        '\\': '+',
        '|': '',
        '*': '-',
    }


    def __post_init__(self) -> None:
        self.update_name(self.name)

    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return self.full_name


    def update_name(self, name: str) -> None:
        """
        Update all names for this series.
        
        :param      name:  The new name of the series info.
        """

        # If the given name already has the year, remove it
        name = str(name)
        if (group := match(rf'^(.*?)\s+\({self.year}\)$', name)) is not None:
            self.name = group.group(1)
        else:
            self.name = name

        # Set full name
        self.full_name = f'{self.name} ({self.year})'
        
        # Set short name
        if len(self.name) > self.SHORT_WIDTH:
            self.short_name = f'{self.name[:self.SHORT_WIDTH]}..'
        else:
            self.short_name = self.name
            
        # Set match names
        self.match_name = self.get_matching_title(self.name)
        self.full_match_name = self.get_matching_title(self.full_name)

        # Set folder-safe name
        translation = str.maketrans(self.__ILLEGAL_CHARACTERS)
        self.legal_path = self.full_name.translate(translation)


    def has_id(self, id_: str) -> bool:
        """
        Determine whether this object has defined the given ID.
        
        :param      id_:    ID being checked
        
        :returns:   True if the given ID is defined (i.e. not None) for this
                    object. False otherwise.
        """

        return getattr(self, id_) is not None


    def has_ids(self, *ids: tuple[str]) -> bool:
        """
        Determine whether this object has defined all the given ID's.
        
        :param      ids:    Any ID's being checked for.
        
        :returns:   True if all the given ID's are defined (i.e. not None) for
                    this object. False otherwise.
        """

        return all(getattr(self, id_) is not None for id_ in ids)


    def set_sonarr_id(self, sonarr_id: int) -> None:
        """
        Set the Sonarr ID for this series.
        
        :param      sonarr_id:  The Sonarr ID used for this series.
        """
        
        if self.sonarr_id is None and sonarr_id is not None:
            self.sonarr_id = int(sonarr_id)


    def set_tvdb_id(self, tvdb_id: int) -> None:
        """
        Set the TVDb ID for this series.
        
        :param      tvdb_id:  The TVDb ID for this series.
        """

        if self.tvdb_id is None and tvdb_id is not None:
            self.tvdb_id = int(tvdb_id)


    def set_imdb_id(self, imdb_id: str) -> None:
        """
        Set the IMDb ID for this series.
        
        :param      imdb_id:    The IMDb ID for this series.
        """
        
        if self.imdb_id is None and imdb_id is not None:
            self.imdb_id = str(imdb_id)


    def set_tmdb_id(self, tmdb_id: int) -> None:
        """
        Set the TMDb ID for this series.
        
        :param      tmdb_id:    The TMDb ID for this series.
        """
        
        if self.tmdb_id is None and tmdb_id is not None:
            self.tmdb_id = int(tmdb_id)


    @staticmethod
    def get_matching_title(text: str) -> str:
        """
        Remove all non A-Z characters from the given title.
        
        :param      text:   The title to strip of special characters.
        
        :returns:   The input `text` with all non A-Z characters removed.
        """

        return ''.join(filter(str.isalnum, text)).lower()


    def matches(self, *names: tuple) -> bool:
        """
        Get whether any of the given names match this Series.
        
        :param      names:  The names to check
        
        :returns:   True if any of the given names match this series, False
                    otherwise.
        """

        matching_names = map(self.get_matching_title, names)

        return any(name == self.match_name for name in matching_names)
        