from copy import deepcopy
from pathlib import Path
from re import compile as re_compile
from typing import Any, Iterable, Optional, Union

from modules import global_objects
from modules.BaseCardType import BaseCardType
from modules.CleanPath import CleanPath
from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo, WordSet
from modules.StyleSet import StyleSet
from modules.Title import Title
from modules.TitleCard import TitleCard


class Episode:
    """
    This class defines an episode of a series that has a corresponding
    Title Card. An Episode encapsulates some EpisodeInfo, as well as
    attributes that map that info to a source and destination file.
    """

    __slots__ = (
        'episode_info', 'card_class', '_base_source', 'source', 'destination',
        'downloadable_source', 'extra_characteristics', 'given_keys', 'watched',
        'blur', 'grayscale', 'spoil_type',
    )


    def __init__(self,
            episode_info: EpisodeInfo,
            card_class: BaseCardType,
            base_source: Path,
            destination: Path,
            given_keys: set[str],
            **extras: Any
        ) -> None:
        """
        Construct a new instance of an Episode.

        Args:
            episode_info: Episode info for this episode.
            base_source: The base source directory to look for source
                images within.
            destination: The destination for the title card associated
                with this Episode.
            given_keys: Set of keys present in the initialization of
                this Episode.
            extras: Additional characteristics to pass to the creation
                of the TitleCard from this Episode.
        """

        # Set object attributes
        self.episode_info = episode_info
        self.card_class = card_class

        # Set source/destination paths
        self._base_source = base_source
        source_name = (f's{episode_info.season_number}'
                       f'e{episode_info.episode_number}'
                       f'{TitleCard.INPUT_CARD_EXTENSION}')
        self.source = base_source / source_name
        self.destination = destination
        self.downloadable_source = True

        # Store given keys and extra characteristics
        self.given_keys = given_keys
        self.extra_characteristics = extras

        # Episodes are watched, not blurred, and spoiled - until updated
        self.watched = False
        self.blur = False
        self.grayscale = False
        self.spoil_type = StyleSet.DEFAULT_SPOIL_TYPE


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'Episode {self.episode_info}'


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object"""

        attrs = ', '.join(f'{attr}={getattr(self, attr)}'
                          for attr in self.__slots__)

        return f'<Episode {attrs}>'


    def add_maxima(self,
            season_episode_count: int,
            season_episode_max: int,
            season_absolute_max: int,
            series_episode_count: int,
            series_episode_max: int,
            series_absolute_max: int
        ) -> None:
        """
        Add the given episode maxima characteristics to this Episode.
        """

        self.extra_characteristics.update(
            season_episode_count=season_episode_count,
            season_episode_max=season_episode_max,
            season_absolute_max=season_absolute_max,
            series_episode_count=series_episode_count,
            series_episode_max=series_episode_max,
            series_absolute_max=series_absolute_max,
        )


    @property
    def characteristics(self) -> dict:
        """
        Get the characteristics of this object for formatting.

        Returns:
            Dictionary of characteristics that define this object. Keys
            are the start/end indices of the range, and the extra
            characteristics of the first episode.
        """

        return self.episode_info.characteristics | self.extra_characteristics


    def key_is_specified(self, key: str) -> bool:
        """
        Return whether the given key was present in the initialization
        for this Episode, i.e. whether the key can be added to the
        datafile.

        Args:
            key: The key being checked.

        Returns:
            Whether the given key was specified in the initialization of
            this Episode.
        """

        return key in self.given_keys


    def update_statuses(self, watched: bool, style_set: StyleSet) -> None:
        """
        Update the statuses of this Episode. In particular the watched
        status and un/watched styles.

        Args:
            watched: New watched status for this Episode.
            style_set: StyleSet object to assign spoil type with.
        """

        self.watched = watched
        self.spoil_type = style_set.effective_spoil_type(watched)


    def update_source(self,
            new_source: Union[Path, str, None],
            *,
            downloadable: bool,
        ) -> bool:
        """
        Update the source image for this Episode, as well as the
        downloadable flag for the source.

        Args:
            new_source: New source file. If source the path is taken
                as-is; if string, then the file is looked for within
                this Episode's base source directory - if that file DNE
                then it's taken as a Path and converted; if None,
                nothing happens.
            downloadable: Whether the new source is downloadable.

        Returns:
            True if a new non-None source was provided, False otherwise.
        """

        # If no actual new source was provided, return
        if new_source is None:
            return False

        # Update source path based on input (Path/str of filename in source,etc)
        if isinstance(new_source, Path):
            self.source = new_source
        elif (self._base_source / new_source).exists():
            self.source = self._base_source / new_source
        else:
            self.source = CleanPath(new_source).sanitize()

        # Set the downloadable flag for the new source
        self.downloadable_source = downloadable

        return True


    def delete_card(self, *, reason: Optional[str] = None) -> bool:
        """
        Delete the title card for this Episode.

        Args:
            reason: String to log why the card is being deleted.

        Returns:
            True if card was deleted, False otherwise.
        """

        # No destination, nothing to delete
        if self.destination is None or not self.destination.exists():
            return False

        # Destination exists, delete and return True
        self.destination.unlink(missing_ok=True)

        # Log deletion
        message = f'Deleted "{self.destination.resolve()}"'
        if reason:
            message += f' [{reason}]'
        log.debug(message)

        return True


class MultiEpisode:
    """
    This class describes a MultiEpisode, which is a 'type' (practically
    a  subclass) of Episode but describes a range of sequential episodes
    within a single season for a given series. The MultiEpisode uses the
    first episode's (sequentially) episode info and source.
    """

    """Regex to match ETF strings for multi episodes"""
    ETF_REGEX = re_compile(r'^(.*?)(\s*){(episode|abs)_number(.*?)}(.*)')

    __slots__ = (
        'season_number', 'episode_start', 'episode_end', 'abs_start', 'abs_end',
        '_first_episode', 'episode_info', 'destination', 'episode_range',
        'word_set',
    )


    def __init__(self,
            episodes: Iterable[Episode],
            title: Title,
        ) -> None:
        """
        Constructs a new instance of a MultiEpisode that represents the
        given list of Episode objects, and has the given (modified)
        Title.

        Args:
            episodes: List of Episode objects this MultiEpisode
                encompasses.
            title: The modified title that describes these multiple
                episodes.
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

        # Create modified WordSet with words for the start/ends of this range
        self.word_set = WordSet()
        for label, number in (
            ('episode_start', self.episode_start),
            ('episode_end', self.episode_end),
            ('abs_start', self.abs_start),
            ('abs_end', self.abs_end)):
            self.word_set.add_numeral(label, number)

        # Add translated word variations for each globally enabled language
        for lang in global_objects.pp.supported_language_codes:
            for label, number in (
                ('episode_start', self.episode_start),
                ('episode_end', self.episode_end),
                ('abs_start', self.abs_start),
                ('abs_end', self.abs_end)):
                self.word_set.add_numeral(label, number, lang)

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


    def __getattr__(self, attribute: str) -> Any:
        """
        Get an attribute from the first episode of this object.

        Args:
            attribute:  The attribute to get from the first Episode.
        """

        return getattr(self._first_episode, attribute)


    def __setattr__(self, attribute: str, value: Any) -> None:
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


    @property
    def characteristics(self) -> dict:
        """
        Get the characteristics of this object for formatting.

        Returns:
            Dictionary of characteristics that define this object. Keys
            are the start/end indices of the range (in numeric and
            written forms), and the extra characteristics of the first
            episode.
        """

        return self._first_episode.characteristics | {
            'season_number': self.season_number,
            'episode_start': self.episode_start,
            'episode_end': self.episode_end,
            'abs_start': self.abs_start,
            'abs_end': self.abs_end,
            **self.word_set,
        }


    @staticmethod
    def modify_format_string(episode_format_string: str) -> str:
        """
        Modify the given episode text format string to be suitable for a
        MultiEpisode. This replaces {abs_number} or {episode_number}
        with {abs_start}-{abs_end} and {episode_start}-{episode_end},
        and adds an "S" to the preceding text (if a space preceeds the
        identifier) For example:

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


    def set_destination(self, destination: Path) -> None:
        """
        Set the destination for the card associated with these Episdoes.

        Args:
            destination: The destination for the card that is created
                for these episodes.
        """

        self.destination = destination
