from copy import deepcopy
from re import compile as re_compile

from modules.TitleCard import TitleCard

class MultiEpisode:
    """
    This class describes a MultiEpisode, which is a 'type' (practically a 
    subclass) of Episode but describes a range of sequential episodes within a
    single season for a given series. The MultiEpisode uses the first episode's
    (sequentially) episode info and source.
    """

    """Regex to match/modify ETF strings for multi episodes"""
    ETF_REGEX = re_compile(r'^(.*?)(\s*){(episode|abs)_number(.*?)}(.*)')

    __slots__ = ('season_number', 'episode_start', 'episode_end', 'abs_start',
                 'abs_end', '_first_episode', 'episode_info', 'destination',
                 'episode_range')


    def __init__(self, episodes: list['Episode'], title: 'Title') -> None:
        """
        Constructs a new instance of a MultiEpisode that represents the given
        list of Episode objects, and has the given (modified) Title.
        
        Args:
            episodes: List of Episode objects this MultiEpisode describes.
            title: The modified title that describes these multiple episodes.
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
        self.episode_range = f'{self.episode_start}-{self.episode_end}'
        
        # If all episode have absolute numbers, get their range
        self.abs_start, self.abs_end = None, None
        if all(e.abs_number is not None for e in episode_infos):
            abs_numbers = tuple(map(lambda e: e.abs_number, episode_infos))
            self.abs_start = min(abs_numbers)
            self.abs_end = max(abs_numbers)
        
        # Get the first episde in the set
        for episode in episodes:
            if episode.episode_info.episode_number == self.episode_start:
                self._first_episode = episode
                break
                   
        # Set object attributes from first episode
        self.episode_info = deepcopy(self._first_episode.episode_info)

        # Override title, set blank destination
        self.episode_info.title = title
        self.destination = None


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return (f'S{self.season_number:02}'
                f'E{self.episode_start:02}-E{self.episode_end:02}')


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object"""

        ret = (f'<MultiEpisode episode_start={self.episode_start}, episode_end='
               f'{self.episode_end}, title={self.episode_info.title}, '
               f'destination={self.destination}')
        ret += '' if self.abs_start is None else f', abs_start={self.abs_start}'
        ret += '' if self.abs_end is None else f', abs_end={self.abs_end}'

        return f'{ret}>'


    def __getattr__(self, attribute):
        """
        Get an attribute from the first episode of this object.
        
        Args:
            attribute:  The attribute to get from the first Episode.
        """

        return getattr(self._first_episode, attribute)


    def __setattr__(self, attribute, value) -> None:
        """
        Set an attribute of the first episode of this object.
        
        Args:
            attribute: The attribute to set on the first Episode.
            value: The value to set on the attribute.
        """

        # If an attribute of this object, set, otherwise set on first Episode
        if attribute in self.__slots__:
            object.__setattr__(self, attribute, value)
        else:
            setattr(self._first_episode, attribute, value)
        
        
    @staticmethod
    def modify_format_string(episode_format_string: str) -> str:
        """
        Modify the given episode text format string to be suitable for a
        MultiEpisode. This replaces {abs_number} or {episode_number} with
        {abs_start}-{abs_end} and {episode_start}-{episode_end}, and adds an S
        to the preceding text (if a space preceeds the identifier) For example:

        >>> modify_format_string('EPISODE {abs_number}')
        'EPISODES {abs_start}-{abs_end}'
        >>> modify_format_string('E{episode_number}')
        'E{episode_start}-{episode_end}'
        
        Args:
            episode_format_string: The episode format string to modify.
        
        Returns:
            The modified format string.
        """

        # Attempt to match with regex
        if (groups := MultiEpisode.ETF_REGEX.match(episode_format_string)):
            pre, spacing, key, modifier, post = groups.groups()

            # Pluralize prefix text if there is spacing
            plural = 's' if spacing != '' else ''

            # Create key range
            key_range = ('{' + key + '_start' + modifier + '}-{'
                             + key + '_end' + modifier + '}')

            return f'{pre}{plural}{spacing}{key_range}{post}'

        # Cannot identify episode keys to modify, return as-is
        return episode_format_string


    def set_destination(self, destination: 'Path') -> None:
        """
        Set the destination for the card associated with these Episdoes.
        
        Args:
            destination: The destination for the card that is created for these
                episodes.
        """

        self.destination = destination


    def make_spoiler_free(self, action: str) -> None:
        """
        Modify this Episode to be spoiler-free according to the given spoil
        action. This updates the spoiler and blur attribute flags, and changes
        the source Path for the Episode if art is the specified action.
        
        Args:
            action: Spoiler action to update according to.
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