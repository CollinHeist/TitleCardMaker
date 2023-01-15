from dataclasses import dataclass, field

from num2words import num2words

from modules.Debug import log
import modules.global_objects as global_objects
from modules.Title import Title

class WordSet(dict):
    """
    Dictionary subclass that contains keys for translated word-versions of
    numbers.
    """

    def add_numeral(self, label: str, number: int, lang: str=None) -> None:
        """
        Add the cardinal and ordinal versions of the given number under the
        given label. For example:

        >>> word_set = WordSet()
        >>> word_set.add_numeral('season_number', 4)
        >>> print(word_set)
        {'season_number_cardinal': 'four', 'season_number_ordinal': 'fourth'}
        >>> word_set.add_numeral('abs_number', 2, 'es')
        {'season_number_cardinal': 'four', 'season_number_ordinal': 'fourth',
         'abs_number_cardinal_es': 'dos', 'abs_number_ordinal_es': 'segundo'}

        Args:
            label: Label key to add the converted number under.
            number: Number to wordify and add into this object.
            lang: Optional language to wordify the object into. Appended to any
                added keys.
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


@dataclass(eq=False, order=False)
class EpisodeInfo:
    """
    This class describes static information about an Episode, such as the
    season, episode, and absolute number, as well as the various ID's associated
    with it.
    """

    # Dataclass initialization attributes
    title: str
    season_number: int
    episode_number: int
    abs_number: int=None
    imdb_id: str=None
    tmdb_id: int=None
    tvdb_id: int=None
    queried_plex: bool=False
    queried_sonarr: bool=False
    queried_tmdb: bool=False
    airdate: 'datetime'=None
    key: str = field(init=False, repr=False)
    word_set: WordSet = field(init=False, repr=False)
    

    def __post_init__(self):
        """Called after __init__, sets types of indices, assigns key field"""

        # Convert title to Title object if given as string
        if isinstance(self.title, str):
            self.title = Title(self.title)

        # Convert indices to integers
        self.season_number = int(self.season_number)
        self.episode_number = int(self.episode_number)
        if self.abs_number is not None:
            self.abs_number = int(self.abs_number)

        # Create key
        self.key = f'{self.season_number}-{self.episode_number}'

        # Add word variations for each of this episode's indices
        self.word_set = WordSet()
        for label, number in (
            ('season_number', self.season_number),
            ('episode_number', self.episode_number),
            ('abs_number', self.abs_number)):
            self.word_set.add_numeral(label, number)

        # Add translated word variations for each globally enabled language
        for lang in global_objects.pp.supported_language_codes:
            for label, number in (
                ('season_number', self.season_number),
                ('episode_number', self.episode_number),
                ('abs_number', self.abs_number)):
                self.word_set.add_numeral(label, number, lang)


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'S{self.season_number:02}E{self.episode_number:02}'


    def __add__(self, count: int) -> str:
        """
        Get the key for the episode corresponding to given number of episodes
        after this one. For example. if this object is S01E05, adding 5 would 
        return '1-10'.
        
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
        Returns whether the given EpisodeInfo object corresponds to the same
        entry (has the same season and episode index).

        Args:
            other_info: EpisodeInfo object to compare.

        Returns:
            True if the season and episode number of the two objects match, 
            False otherwise.
        """

        # Verify the comparison is another EpisodeInfo object
        if not isinstance(other_info, EpisodeInfo):
            raise TypeError(f'Can only compare equality between EpisodeInfo'
                            f' objects')

        # Equality is determined by season and episode number only
        season_match = (self.season_number == other_info.season_number)
        episode_match = (self.episode_number == other_info.episode_number)

        return season_match and episode_match


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


    @property
    def has_all_ids(self) -> bool:
        """Whether this object has all ID's defined"""

        return ((self.tvdb_id is not None)
                and (self.imdb_id is not None)
                and (self.tmdb_id is not None))


    @property
    def ids(self) -> dict:
        """This object's ID's (as a dictionary)"""

        return {
            'tvdb_id': self.tvdb_id,
            'imdb_id': self.imdb_id,
            'tmdb_id': self.tmdb_id
        }


    @property
    def characteristics(self) -> dict[str, 'int | str']:
        """
        Get the characteristics of this object for formatting.

        Returns:
            Dictionary of characteristics that define this object. Keys are the
            indices of the episode in numeric, cardinal, and ordinal form.
        """

        return {
            'season_number': self.season_number,
            'episode_number': self.episode_number,
            'abs_number': self.abs_number,
            'airdate': self.airdate,
            **self.word_set,
        }


    @property
    def indices(self) -> dict:
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


    def set_tvdb_id(self, tvdb_id: int) -> None:
        """
        Sets the TVDb ID for this object.
        
        Args:
            tmdb_id: The TVDb ID to set.
        """

        if self.tvdb_id is None and tvdb_id is not None:
            self.tvdb_id = int(tvdb_id)


    def set_imdb_id(self, imdb_id: str) -> None:
        """
        Sets the IMDb ID for this object.
        
        Args:
            imdb_id: The IMDb ID to set.
        """

        if self.imdb_id is None and imdb_id is not None:
            self.imdb_id = imdb_id

    
    def set_tmdb_id(self, tmdb_id: int) -> None:
        """
        Sets the TMDb ID for this object.
        
        Args:
            tmdb_id: The TMDb ID to set.
        """

        if self.tmdb_id is None and tmdb_id is not None:
            self.tmdb_id = tmdb_id


    def update_queried_statuses(self, queried_plex: bool=False,
                                queried_sonarr: bool=False,
                                queried_tmdb: bool=False) -> None:
        """
        Update the queried attributes of this object to reflect the given
        arguments. Only updates from False -> True.
        
        Args:
            queried_plex: Whether this EpisodeInfo has been queried on Plex.
            queried_sonarr: Whether this EpisodeInfo has been queried on Sonarr.
            queried_tmdb: Whether this EpisodeInfo has been queried on TMDb.
        """

        if not self.queried_plex and queried_plex:
            self.queried_plex = queried_plex
        if not self.queried_sonarr and queried_sonarr:
            self.queried_sonarr = queried_sonarr
        if not self.queried_tmdb and queried_tmdb:
            self.queried_tmdb = queried_tmdb