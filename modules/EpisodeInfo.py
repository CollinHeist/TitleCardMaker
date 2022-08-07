from dataclasses import dataclass, field

from modules.Title import Title

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
    tvdb_id: int=None
    imdb_id: str=None
    tmdb_id: int=None
    queried_plex: bool=False
    queried_sonarr: bool=False
    queried_tmdb: bool=False
    key: str = field(init=False, repr=False)
    

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


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'S{self.season_number:02}E{self.episode_number:02}'


    def __add__(self, count: int) -> str:
        """
        Get the key for the episode corresponding to given number of episodes
        after this one. For example. if this object is S01E05, adding 5 would 
        return '1-10'.
        
        :param      count:  The number of episodes to increment the index by.
        
        :returns:   The key for count many episodes after this one.
        """

        if not isinstance(count, int):
            raise TypeError(f'Can only add integers to EpisodeInfo objects')

        return f'{self.season_number}-{self.episode_number+count}'


    def __eq__(self, other_info: 'EpisodeInfo') -> bool:
        """
        Returns whether the given EpisodeInfo object corresponds to the same
        entry (has the same season and episode index).

        :param      other_info: EpisodeInfo object to compare.

        :returns:   True if the season and episode number of the two objects
                    match, False otherwise.
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
    def episode_characteristics(self) -> dict:
        """This object's season/episode indices (as a dictionary)"""

        return {
            'season_number': self.season_number,
            'episode_number': self.episode_number,
            'abs_number': self.abs_number,
        }


    def set_tvdb_id(self, tvdb_id: int) -> None:
        """
        Sets the TVDb ID for this object.
        
        :param      tmdb_id:    The TVDb ID to set.
        """

        if self.tvdb_id is None and tvdb_id is not None:
            self.tvdb_id = int(tvdb_id)


    def set_imdb_id(self, imdb_id: str) -> None:
        """
        Sets the IMDb ID for this object.
        
        :param      imdb_id:    The IMDb ID to set.
        """

        if self.imdb_id is None and imdb_id is not None:
            self.imdb_id = imdb_id

    
    def set_tmdb_id(self, tmdb_id: int) -> None:
        """
        Sets the TMDb ID for this object.
        
        :param      tmdb_id:    The TMDb ID to set.
        """

        if self.tmdb_id is None and tmdb_id is not None:
            self.tmdb_id = tmdb_id


    def update_queried_statuses(self, queried_plex: bool=False,
                                queried_sonarr: bool=False,
                                queried_tmdb: bool=False) -> None:
        """
        Update the queried attributes of this object to reflect the given
        arguments. Only updates from False -> True.
        
        :param      queried_plex:       Whether this EpisodeInfo has been
                                        queried on Plex.
        :param      queried_sonarr:     Whether this EpisodeInfo has been
                                        queried on Sonarr.
        :param      queried_tmdb:       Whether this EpisodeInfo has been
                                        queried on TMDb.
        """

        if not self.queried_plex and queried_plex:
            self.queried_plex = queried_plex
        if not self.queried_sonarr and queried_sonarr:
            self.queried_sonarr = queried_sonarr
        if not self.queried_tmdb and queried_tmdb:
            self.queried_tmdb = queried_tmdb

        