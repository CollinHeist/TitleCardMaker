from datetime import datetime
from typing import Any, Optional, Union

from num2words import num2words
from titlecase import titlecase

from modules import global_objects
from modules.DatabaseInfoContainer import DatabaseInfoContainer
from modules.Title import Title


class WordSet(dict):
    """
    Dictionary subclass that contains keys for translated word-versions
    of numbers.
    """


    def add_numeral(self,
            label: str,
            number: int,
            lang: Optional[str] = None
        ) -> None:
        """
        Add the cardinal and ordinal versions of the given number under
        the given label. For example:

        >>> word_set = WordSet()
        >>> word_set.add_numeral('season_number', 4)
        >>> print(word_set)
        {'season_number_cardinal': 'four',
         'season_number_ordinal': 'fourth'}
        >>> word_set.add_numeral('abs_number', 2, 'es')
        {'season_number_cardinal': 'four',
         'season_number_ordinal': 'fourth',
         'abs_number_cardinal_es': 'dos',
         'abs_number_ordinal_es': 'segundo'}

        Args:
            label: Label key to add the converted number under.
            number: Number to wordify and add into this object.
            lang: Optional language to wordify the object into. Appended
                to any added keys.
        """

        # If value is None, do nothing
        if number is None:
            return None

        # If a specific language was indicated, use in conversion
        if lang is not None and lang != 'en':
            # Catch exceptions caused by an unsupported language
            try:
                cardinal = num2words(number, to='cardinal', lang=lang)
                self.update({
                    f'{label}_cardinal_{lang}': cardinal,
                    f'{label}_cardinal_{lang}_title': titlecase(cardinal),
                })
            except NotImplementedError:
                pass
            try:
                ordinal = num2words(number, to='ordinal', lang=lang)
                self.update({
                    f'{label}_ordinal_{lang}': ordinal,
                    f'{label}_ordinal_{lang}_title': titlecase(ordinal),
                })
            except NotImplementedError:
                pass
        # No language indicated, convert using base language
        else:
            cardinal = num2words(number, to='cardinal')
            ordinal = num2words(number, to='ordinal')
            self.update({
                f'{label}_cardinal': cardinal,
                f'{label}_cardinal_title': f'{titlecase(cardinal)}',
                f'{label}_ordinal': ordinal,
                f'{label}_ordinal_title': titlecase(ordinal),
            })

        return None


    def has_number(self, label: str, lang: Optional[str] = None) -> bool:
        """
        Whether this object has defined translations for the given label
        and language combination.

        Args:
            label: Label key of the converted numbers.
            lang: Language of the converted numbers.

        Returns:
            True if the cardinal and ordinal translations are defined
            for this label and language; False otherwise.
        """

        if lang is not None and lang != 'en':
            return (
                f'{label}_cardinal_{lang}' in self
                and f'{label}_ordinal_{lang}' in self
            )

        return f'{label}_cardinal' in self and f'{label}_ordinal' in self


class EpisodeInfo(DatabaseInfoContainer):
    """
    This class describes static information about an Episode, such as
    the season, episode, and absolute number, as well as the various
    ID's associated with it.
    """

    __slots__ = (
        'title', 'season_number', 'episode_number', 'abs_number', 'emby_id',
        'imdb_id', 'jellyfin_id', 'tmdb_id', 'tvdb_id', 'tvrage_id',
        'queried_emby', 'queried_jellyfin', 'queried_plex', 'queried_sonarr',
        'queried_tmdb', 'airdate', 'key', '__word_set',
    )


    def __init__(self,
            title: Union[str, Title],
            season_number: int,
            episode_number: int,
            abs_number: Optional[int] = None,
            *,
            emby_id: Optional[int] = None,
            imdb_id: Optional[str] = None,
            jellyfin_id: Optional[str] = None,
            tmdb_id: Optional[int] = None,
            tvdb_id: Optional[int] = None,
            tvrage_id: Optional[int] = None,
            airdate: Optional[datetime] = None,
            queried_emby: bool = False,
            queried_jellyfin: bool = False,
            queried_plex: bool = False,
            queried_sonarr: bool = False,
            queried_tmdb: bool = False
        ) -> None:
        """
        Initialize this object with the given title, indices, database
        ID's, airdate, and queried statuses.
        """

        # Ensure title is Title object
        if isinstance(title, Title):
            self.title = title
        else:
            self.title = Title(title)

        # Store arguments as attributes
        self.season_number = int(season_number)
        self.episode_number = int(episode_number)
        self.abs_number = None if abs_number is None else int(abs_number)
        self.airdate = airdate

        # Store default database ID's
        self.emby_id = None
        self.imdb_id = None
        self.jellyfin_id = None
        self.tmdb_id = None
        self.tvdb_id = None
        self.tvrage_id = None

        # Update each ID
        self.set_emby_id(emby_id)
        self.set_imdb_id(imdb_id)
        self.set_jellyfin_id(jellyfin_id)
        self.set_tmdb_id(tmdb_id)
        self.set_tvdb_id(tvdb_id)
        self.set_tvrage_id(tvrage_id)

        self.queried_emby = queried_emby
        self.queried_jellyfin = queried_jellyfin
        self.queried_plex = queried_plex
        self.queried_sonarr = queried_sonarr
        self.queried_tmdb = queried_tmdb

        # Create key
        self.key = f'{self.season_number}-{self.episode_number}'

        # Initialize this object's WordSet
        self.__word_set = WordSet()


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        attributes = ', '.join(f'{attr}={getattr(self, attr)}'
            for attr in self.__slots__
            if not attr.startswith('__')
                and getattr(self, attr) is not None
                and getattr(self, attr) is not False)

        return f'<EpisodeInfo {attributes}>'


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'S{self.season_number:02}E{self.episode_number:02}'


    def __add__(self, count: int) -> str:
        """
        Get the key for the episode corresponding to given number of
        episodes after this one. For example. if this object is S01E05,
        adding 5 would  return '1-10'.

        Args:
            count: The number of episodes to increment the index by.

        Returns:
            The key for count many episodes after this one.

        Raises:
            TypeError if `count` is not an integer.
        """

        if not isinstance(count, int):
            raise TypeError(f'Can only add integers to EpisodeInfo objects')

        return f'{self.season_number}-{self.episode_number+count}'


    def __eq__(self, other_info: Union['EpisodeInfo', tuple[int, int]]) -> bool:
        """
        Returns whether the given EpisodeInfo object corresponds to the
        same entry (has the same season and episode index).

        Args:
            other_info: EpisodeInfo object to compare.

        Returns:
            True if the season and episode number of the two objects
            match,  False otherwise.

        Raises:
            TypeError if other_info is not an EpisodeInfo or two-length
            tuple of integers.
        """

        # If another EpisodeInfo, compare by indices
        if isinstance(other_info, EpisodeInfo):
            return (
                self.season_number == other_info.season_number
                and self.episode_number == other_info.episode_number
            )
        # If a tuple of indices, compare
        if (isinstance(other_info, tuple) and len(other_info) == 2
            and all(isinstance(entry, int) for entry in other_info)):
            return (
                self.season_number == other_info[0]
                and self.episode_number == other_info[1]
            )

        # Unsupported comparison type
        raise TypeError(
            f'Can only compare equality between EpisodeInfo objects and two-'
            f'length tuples'
        )


    @property
    def word_set(self) -> WordSet[str, str]:
        """
        The WordSet for this object. This constructs the translations of
        the season, episode, and absolute numbers if not already
        present.
        """

        number_sets = (
            ('season_number', self.season_number),
            ('episode_number', self.episode_number),
            ('absolute_number', self.abs_number)
        )

        for lang in global_objects.pp.supported_language_codes:
            for label, number in number_sets:
                if not self.__word_set.has_number(label, lang):
                    self.__word_set.add_numeral(label, number, lang=lang)

        return self.__word_set


    @property
    def has_all_ids(self) -> bool:
        """Whether this object has all ID's defined"""

        return ((self.tvdb_id is not None)
            and (self.imdb_id is not None)
            and (self.tmdb_id is not None)
        )


    @property
    def ids(self) -> dict[str, Any]:
        """This object's ID's (as a dictionary)"""

        return {
            'emby_id': self.emby_id,
            'imdb_id': self.imdb_id,
            'jellyfin_id': self.jellyfin_id,
            'tmdb_id': self.tmdb_id,
            'tvdb_id': self.tvdb_id,
            'tvrage_id': self.tvrage_id,
        }


    @property
    def characteristics(self) -> dict[str, Any]:
        """
        Get the characteristics of this object for formatting.

        Returns:
            Dictionary of characteristics that define this object. Keys
            are the indices of the episode in numeric, cardinal, and
            ordinal form.
        """

        return {
            'season_number': self.season_number,
            'episode_number': self.episode_number,
            'abs_number': self.abs_number,
            'airdate': self.airdate,
            **self.word_set,
        }


    @property
    def indices(self) -> dict[str, Optional[int]]:
        """This object's season/episode indices (as a dictionary)"""

        return {
            'season_number': self.season_number,
            'episode_number': self.episode_number,
            'abs_number': self.abs_number,
        }


    @property
    def index(self) -> str:
        """This object's index - i.e. s{season}e{episode}"""

        return f's{self.season_number}e{self.episode_number}'


    def set_emby_id(self, emby_id) -> None:
        """Set the Emby ID of this object. See `_update_attribute()`."""
        self._update_attribute('emby_id', emby_id, int)

    def set_imdb_id(self, imdb_id) -> None:
        """Set the IMDb ID of this object. See `_update_attribute()`."""
        self._update_attribute('imdb_id', imdb_id, str)

    def set_jellyfin_id(self, jellyfin_id) -> None:
        """Set the Jellyfin ID of this object. See `_update_attribute()`."""
        self._update_attribute('jellyfin_id', jellyfin_id, str)

    def set_tmdb_id(self, tmdb_id) -> None:
        """Set the TMDb ID of this object. See `_update_attribute()`."""
        self._update_attribute('tmdb_id', tmdb_id, int)

    def set_tvdb_id(self, tvdb_id) -> None:
        """Set the TVDb ID of this object. See `_update_attribute()`."""
        self._update_attribute('tvdb_id', tvdb_id, int)

    def set_tvrage_id(self, tvrage_id) -> None:
        """Set the TVRage ID of this object. See `_update_attribute()`."""
        self._update_attribute('tvrage_id', tvrage_id, int)

    def set_airdate(self, airdate: datetime) -> None:
        """Set the airdate of this object. See `_update_attribute()`."""
        self._update_attribute('airdate', airdate)


    def update_queried_statuses(self,
            queried_emby: bool = False,
            queried_jellyfin: bool = False,
            queried_plex: bool = False,
            queried_sonarr: bool = False,
            queried_tmdb: bool = False
        ) -> None:
        """
        Update the queried attributes of this object to reflect the
        given arguments. Only updates an attribute from False to True.

        Args:
            queried_emby: Whether this object has been queried on Emby.
            queried_emby: Whether this object has been queried on
                Jellyfin.
            queried_plex: Whether this object has been queried on Plex.
            queried_sonarr: Whether this object has been queried on
                Sonarr.
            queried_tmdb: Whether this object has been queried on TMDb.
        """

        if queried_emby:
            self.queried_emby = True
        if queried_jellyfin:
            self.queried_jellyfin = True
        if queried_plex:
            self.queried_plex = True
        if queried_sonarr:
            self.queried_sonarr = True
        if queried_tmdb:
            self.queried_tmdb = True
