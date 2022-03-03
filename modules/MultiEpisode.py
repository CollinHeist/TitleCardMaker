from copy import deepcopy

from modules.TitleCard import TitleCard

class MultiEpisode:
    """
    This class describes a MultiEpisode, which is a 'type' (essentially a 
    subclass) of Episode but describes a range of sequential episodes within a
    single season for a given series. The MultiEpisode uses the first episode's
    (sequentially) episode info and source.
    """

    def __init__(self, episodes: ['Episode'], title: 'Title') -> None:
        """
        Constructs a new instance.
        
        :param      episodes:       Episodes this object describes.
        :param      title:          The modified title that describes these
                                    multiple episodes.
        """
        
        # Verify at least two episodes have been provided
        if len(episodes) < 2:
            raise ValueError(f'MultiEpisode requires at least 2 Episodes')
        
        # Verify all episodes are from the same season
        episode_infos = tuple(map(lambda e: e.episode_info, episodes))
        if not all(episode_info.season_number == episode_infos[0].season_number
                   for episode_info in episode_infos):
            raise ValueError(f'Given set of EpisodeInfo objects must be from '
                             f'the same season.')

        # Get the season for this episode set
        self.season_number = episode_infos[0].season_number
        
        # Get the episode range for the given episode set
        episode_numbers = tuple(map(lambda e: e.episode_number, episode_infos))
        self.episode_start = min(episode_numbers)
        self.episode_end = max(episode_numbers)
        
        # If all episode have absolute numbers, get their range
        self.abs_start, self.abs_end = None, None
        if all(e.abs_number != None for e in episode_infos):
            abs_numbers = tuple(map(lambda e: e.abs_number, episode_infos))
            self.abs_start = min(abs_numbers)
            self.abs_end = max(abs_numbers)
        
        # Get the first episde in the set
        for episode in episodes:
            if episode.episode_info.episode_number == self.episode_start:
                first_episode = episode
                break
                   
        # Set object attributes from first episode
        self.episode_info = deepcopy(first_episode.episode_info)
        self.card_class = first_episode.card_class
        self.source = first_episode.source
        self.extra_characteristics = first_episode.extra_characteristics

        # Override title, set blank destination
        self.episode_info.title = title
        self.destination = None


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'E{self.episode_start}-E{self.episode_end}'


    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object"""

        ret = (f'<MultiEpisode episode_start={self.episode_start}, episode_end='
               f'{self.episode_end}, title={self.episode_info.title}, '
               f'destination={self.destination}')
        ret += f', abs_start={self.abs_start}' if self.abs_start != None else ''
        ret += f', abs_end={self.abs_end}' if self.abs_end != None else ''

        return f'{ret}>'
        
        
    @staticmethod
    def modify_format_string(episode_format_string: str) -> str:
        """
        Modify the given episode text format string to be suitable for a
        MultiEpisode. This replaces {abs_number} or {episode_number} with
        {abs_start}-{abs_end} and {episode_start}-{episode_end}, and adds an S
        to the preceding text. For example:

        >>> modify_format_string('EPISODE {abs_number}')
        'EPISODES {abs_start}-{abs_end}'
        
        :param      episode_format_string:  The episode format string to modify.
        
        :returns:   The modified multiple'd format string.
        """
        
        if ' {abs_number}' in episode_format_string:
            # Split for absolute numbers
            pre, post = episode_format_string.split(' {abs_number}')

            return pre + 'S {abs_start}-{abs_end}' + post

        # Split for episode numbers
        pre, post = episode_format_string.split(' {episode_number}')

        return pre + 'S {episode_start}-{episode_end}' + post


    def set_destination(self, destination: 'Path') -> None:
        """
        Sets the destination.
        
        :param      destination:    The destination for the card that is created
                                    for these episodes.
        """

        self.destination = destination
        