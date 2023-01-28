from re import match, compile as re_compile
from typing import ClassVar

from modules.CleanPath import CleanPath
from modules.Debug import log

class SeriesInfo:
    """
    This class encapsulates static information that is tied to a single Series.
    """

    """Regex to match name + year from given full name"""
    __FULL_NAME_REGEX: ClassVar['Pattern'] =re_compile(r'^(.*?)\s+\((\d{4})\)$')


    __slots__ = (
        'name', 'year', 'imdb_id', 'sonarr_id', 'tmdb_id', 'tvdb_id',
        'match_titles', 'full_name', 'match_name', 'full_match_name',
        'clean_name', 'full_clean_name',
    )


    def __init__(self, name: str, year: int=None, *, imdb_id: str=None,
                 sonarr_id: int=None, tmdb_id: int=None, tvdb_id: int=None, 
                 match_titles: bool=True) -> None:
        """
        Create a SeriesInfo object that defines a series described by all of 
        these attributes.

        Args:
            name: Name of the series. Can be just the name, or a full name of
                the series and year like "name (year)".
            year: Year of the series. Can be omitted if a year is provided from
                the name. Defaults to None.
            imdb_id: IMDb ID of the series. Defaults to None.
            sonarr_id: Sonarr ID of the series. Defaults to None.
            tmdb_id: TMDb ID of the series. Defaults to None.
            tvdb_id: TVDb ID of the series. Defaults to None.
            match_titles: Whether to match titles when comparing episodes for
                this series. Defaults to True.

        Raises:
            ValueError: If no year is provided.
        """

        # Parse arguments into attributes
        self.name = name
        self.year = year
        self.imdb_id = imdb_id
        self.sonarr_id = sonarr_id
        self.tmdb_id = tmdb_id
        self.tvdb_id = tvdb_id
        self.match_titles = match_titles

        # If no year was specified, parse from name as "name (year)"
        if (self.year is None
            and (group := match(self.__FULL_NAME_REGEX,self.name)) is not None):
            self.name = group.group(1)
            self.year = int(group.group(2))

        # If year still isn't specified, error
        if self.year is None:
            raise ValueError(f'Year not provided')

        self.year = int(self.year)
        self.update_name(self.name)


    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object."""

        return (f'<SeriesInfo name={self.name}, year={self.year}, imdb_id='
                f'{self.imdb_id}, sonarr_id={self.sonarr_id}, tmdb_id='
                f'{self.tmdb_id}, tvdb_id={self.tvdb_id}>')


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return self.full_name


    @property
    def characteristics(self) -> dict[str, str]:
        
        return {
            'series_name': self.name,
            'series_year': self.year,
        }


    def update_name(self, name: str) -> None:
        """
        Update all names for this series.

        Args:
            name: The new name of the series info.
        """

        # If the given name already has the year, remove it
        name = str(name)
        if (group := match(rf'^(.*?)\s+\({self.year}\)$', name)) is not None:
            self.name = group.group(1)
        else:
            self.name = name

        # Set full name
        self.full_name = f'{self.name} ({self.year})'

        # Set match names
        self.match_name = self.get_matching_title(self.name)
        self.full_match_name = self.get_matching_title(self.full_name)

        # Set folder-safe name
        self.clean_name = CleanPath.sanitize_name(self.name)
        self.full_clean_name =  CleanPath.sanitize_name(self.full_name)


    def has_id(self, id_: str) -> bool:
        """
        Determine whether this object has defined the given ID.

        Args:
            id_: ID being checked

        Returns:
            True if the given ID is defined (i.e. not None) for this object.
            False otherwise.
        """

        return getattr(self, id_) is not None


    def has_ids(self, *ids: tuple[str]) -> bool:
        """
        Determine whether this object has defined all the given ID's.

        Args:
            ids: Any ID's being checked for.

        Returns:
            True if all the given ID's are defined (i.e. not None) for this
            object. False otherwise.
        """

        return all(getattr(self, id_) is not None for id_ in ids)


    def set_imdb_id(self, imdb_id: 'str | None') -> None:
        """
        Set the IMDb ID for this series.

        Args:
            imdb_id: The IMDb ID for this series.
        """

        if self.imdb_id is None and imdb_id is not None:
            self.imdb_id = str(imdb_id)


    def set_sonarr_id(self, sonarr_id: 'int | None') -> None:
        """
        Set the Sonarr ID for this series.

        Args:
            sonarr_id: The Sonarr ID used for this series.
        """

        if self.sonarr_id is None and sonarr_id is not None:
            self.sonarr_id = int(sonarr_id)


    def set_tmdb_id(self, tmdb_id: 'int | None') -> None:
        """
        Set the TMDb ID for this series.

        Args:
            tmdb_id: The TMDb ID for this series.
        """

        if self.tmdb_id is None and tmdb_id is not None:
            self.tmdb_id = int(tmdb_id)


    def set_tvdb_id(self, tvdb_id: 'int | None') -> None:
        """
        Set the TVDb ID for this series.

        Args:
            tvdb_id: The TVDb ID for this series.
        """

        if self.tvdb_id is None and tvdb_id is not None:
            self.tvdb_id = int(tvdb_id)


    @staticmethod
    def get_matching_title(text: str) -> str:
        """
        Remove all non A-Z characters from the given title.

        Args:
            text: The title to strip of special characters.

        Returns:
            The input `text` with all non A-Z characters removed.
        """

        return ''.join(filter(str.isalnum, text)).lower()


    def matches(self, *names: tuple[str]) -> bool:
        """
        Get whether any of the given names match this Series.

        Args:
            names: The names to check

        Returns:
            True if any of the given names match this series, False otherwise.
        """

        matching_names = map(self.get_matching_title, names)

        return any(name == self.match_name for name in matching_names)