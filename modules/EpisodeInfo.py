class EpisodeInfo:
    """
    This class describes static information about an Episode, such as the
    season, episode, and absolute number, as well as the various ID's associated
    with it - such as Sonarr, TVDb, and TMDb.
    """

    __slots__ = ('title', 'season_number', 'season', 'episode_number','episode',
                 'abs_number', 'abs', 'key', 'sonarr_id', 'tvdb_id', 'tmdb_id')
    

    def __init__(self, title: 'Title', season_number: int, episode_number: int,
                 abs_number: int=None) -> None:
        """
        Constructs a new instance of an EpisdeInfo object.
        
        :param      title:          The Title object of this Episode.
        :param      season_number:  The season number of this Episode.
        :param      episode_number: The episode number of this Episode.
        :param      abs_number:     The absolute episode number of this Episode.
        """

        # Store title
        self.title = title

        # Store indices
        self.season_number = int(season_number)
        self.season = self.season_number

        self.episode_number = int(episode_number)
        self.episode = self.episode_number

        self.abs_number = None if abs_number is None else int(abs_number)
        self.abs = self.abs_number

        # Create key for unique indexing associated with this Episode
        self.key = f'{self.season_number}-{self.episode_number}'

        # Optional attributes
        self.sonarr_id = None
        self.tvdb_id = None
        self.tmdb_id = None


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'S{self.season_number:02}E{self.episode_number:02}'


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        # Static information
        ret = (f'<EpisodeInfo {self.title=}, {self.season_number=}, '
               f'{self.episode_number=}')

        ret += '' if self.sonarr_id is None else f', {self.sonarr_id=}'
        ret += '' if self.tvdb_id is None else f', {self.tvdb_id=}'
        ret += '' if self.tmdb_id is None else f', {self.tmdb_id=}'
        ret += '' if self.abs_number is None else f', {self.abs_number=}'

        return f'{ret}>'


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


    @property
    def episode_characteristics(self) -> dict:
        """This object's season/episode indices (as a dictionary)"""

        return {
            'season_number': self.season_number,
            'episode_number': self.episode_number,
            'abs_number': self.abs_number,
        }


    def set_abs_number(self, abs_number: int) -> None:
        """
        Set the absolute number for this object.
        
        :param      abs_number: The absolute number to set.
        """

        self.abs_number = int(abs_number)
        self.abs = self.abs_number


    def set_sonarr_id(self, sonarr_id: int) -> None:
        """
        Sets the Sonarr ID for this object.
        
        :param      tmdb_id:    The Sonarr ID to set.
        """

        self.sonarr_id = int(sonarr_id)


    def set_tvdb_id(self, tvdb_id: int) -> None:
        """
        Sets the TVDb ID for this object.
        
        :param      tmdb_id:    The TVDb ID to set.
        """

        self.tvdb_id = int(tvdb_id)


    def set_tmdb_id(self, tmdb_id: int) -> None:
        """
        Sets the TMDb ID for this object.
        
        :param      tmdb_id:    The TMDb ID to set.
        """

        self.tmdb_id = int(tmdb_id)


    def copy_ids(self, other: 'EpisodeInfo') -> None:
        """
        Copy all ID's from the given EpisodeInfo object. This copies the Sonarr,
        TVDb, and TMDb ID's.
        
        :param      other:  The EpisodeInfo object to copy ID's from.
        """

        if not isinstance(other, EpisodeInfo):
            raise TypeError(f"Can only copy ID's into an EpisodeInfo object")

        self.sonarr_id = other.sonarr_id
        self.tvdb_id = other.tvdb_id
        self.tmdb_id = other.tmdb_id
        