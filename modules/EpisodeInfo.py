from num2words import num2words

from modules.Debug import log
from modules.DatabaseInfoContainer import DatabaseInfoContainer
import modules.global_objects as global_objects
from modules.Title import Title

class WordSet(dict):
    """
    Dictionary subclass that contains keys for translated word-versions
    of numbers.
    """

    def add_numeral(self, label: str, number: int, lang: str=None) -> None:
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
        if lang:
            # Catch exceptions caused by an unsupported language
            try:
                cardinal = num2words(number, to='cardinal', lang=lang)
                self.update({f'{label}_cardinal_{lang}': cardinal})
            except NotImplementedError: pass
            try:
                ordinal = num2words(number, to='ordinal', lang=lang)
                self.update({f'{label}_ordinal_{lang}': ordinal})
            except NotImplementedError: pass
        # No language indicated, convert using base language
        else:
            self.update({
                f'{label}_cardinal': num2words(number, to='cardinal'),
                f'{label}_ordinal': num2words(number, to='ordinal'),
            })


class EpisodeInfo(DatabaseInfoContainer):
    """
    This class describes static information about an Episode, such as
    the season, episode, and absolute number, as well as the various
    ID's associated with it.
    """

    __slots__ = (
        'title', 'season_number', 'episode_number', 'abs_number', 'emby_id',
        'imdb_id', 'tmdb_id', 'tvdb_id', 'tvrage_id', 'queried_emby',
        'queried_plex', 'queried_sonarr', 'queried_tmdb', 'airdate', 'key',
        '__word_set',
    )


    def __init__(self, title: 'str | Title', season_number: int,
            episode_number: int, abs_number: int=None, *,
            emby_id: int=None, imdb_id: str=None, tmdb_id: int=None,
            tvdb_id: int=None, tvrage_id: int=None, airdate: 'datetime'=None,
            queried_emby: bool=False, queried_plex: bool=False,
            queried_sonarr: bool=False, queried_tmdb: bool=False) -> None:

        # Ensure title is Title object
        if isinstance(title, Title):
            self.title = title
        else:
            self.title = Title(title)

        # Store arguments as attributes
        self.season_number = int(season_number)
        self.episode_number = int(episode_number)
        self.abs_number = None if abs_number is None else int(abs_number)
        self.emby_id = None if emby_id is None else int(emby_id)
        self.imdb_id = imdb_id
        self.tmdb_id = None if tmdb_id is None else int(tmdb_id)
        self.tvdb_id = None if tvdb_id is None else int(tvdb_id)
        self.tvrage_id = None if tvrage_id is None else int(tvrage_id)
        self.queried_emby = queried_emby
        self.queried_plex = queried_plex
        self.queried_sonarr = queried_sonarr
        self.queried_tmdb = queried_tmdb
        self.airdate = airdate

        # Create key
        self.key = f'{self.season_number}-{self.episode_number}'

        # Add word variations for each of this episode's indices
        self.__word_set = WordSet()
        for label, number in (
            ('season_number', self.season_number),
            ('episode_number', self.episode_number),
            ('abs_number', self.abs_number)):
            self.__word_set.add_numeral(label, number)

        # Add translated word variations for each globally enabled language
        for lang in global_objects.pp.supported_language_codes:
            for label, number in (
                ('season_number', self.season_number),
                ('episode_number', self.episode_number),
                ('abs_number', self.abs_number)):
                self.__word_set.add_numeral(label, number, lang)


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
        """

        if not isinstance(count, int):
            raise TypeError(f'Can only add integers to EpisodeInfo objects')

        return f'{self.season_number}-{self.episode_number+count}'


    def __eq__(self, other_info: 'EpisodeInfo') -> bool:
        """
        Returns whether the given EpisodeInfo object corresponds to the
        same entry (has the same season and episode index).

        Args:
            other_info: EpisodeInfo object to compare.

        Returns:
            True if the season and episode number of the two objects
            match,  False otherwise.
        """

        # Verify the comparison is another EpisodeInfo object
        if not isinstance(other_info, EpisodeInfo):
            raise TypeError(f'Can only compare equality between EpisodeInfo'
                            f' objects')

        # Equality is determined by season and episode number only
        season_match = (self.season_number == other_info.season_number)
        episode_match = (self.episode_number == other_info.episode_number)

        return season_match and episode_match


    @property
    def has_all_ids(self) -> bool:
        """Whether this object has all ID's defined"""

        return ((self.tvdb_id is not None)
            and (self.imdb_id is not None)
            and (self.tmdb_id is not None)
        )


    @property
    def ids(self) -> dict[str, 'int | str | None']:
        """This object's ID's (as a dictionary)"""

        return {
            'emby_id': self.emby_id,
            'imdb_id': self.imdb_id,
            'tmdb_id': self.tmdb_id,
            'tvdb_id': self.tvdb_id,
            'tvrage_id': self.tvrage_id,
        }


    @property
    def characteristics(self) -> dict[str, 'int | str']:
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
            **self.__word_set,
        }


    @property
    def indices(self) -> dict[str, 'int | None']:
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


    """Functions for setting database ID's on this object"""
    def set_emby_id(self, emby_id) -> None:
        self._update_attribute('emby_id', emby_id, int)

    def set_imdb_id(self, imdb_id) -> None:
        self._update_attribute('imdb_id', imdb_id, str)

    def set_tmdb_id(self, tmdb_id) -> None:
        self._update_attribute('tmdb_id', tmdb_id, int)

    def set_tvdb_id(self, tvdb_id) -> None:
        self._update_attribute('tvdb_id', tvdb_id, int)

    def set_tvrage_id(self, tvrage_id) -> None:
        self._update_attribute('tvrage_id', tvrage_id, int)

    def set_airdate(self, airdate: 'datetime') -> None:
        self._update_attribute('airdate', airdate)


    def update_queried_statuses(self, queried_emby: bool=False,
            queried_plex: bool=False, queried_sonarr: bool=False,
            queried_tmdb: bool=False) -> None:
        """
        Update the queried attributes of this object to reflect the given
        arguments. Only updates from False -> True.

        Args:
            queried_emby: Whether this object has been queried on Emby.
            queried_plex: Whether this object has been queried on Plex.
            queried_sonarr: Whether this object has been queried on Sonarr.
            queried_tmdb: Whether this object has been queried on TMDb.
        """

        if queried_emby:   self.queried_emby = queried_emby
        if queried_plex:   self.queried_plex = queried_plex
        if queried_sonarr: self.queried_sonarr = queried_sonarr
        if queried_tmdb:   self.queried_tmdb = queried_tmdb