from collections import namedtuple
from typing import Any

from re import IGNORECASE, compile as re_compile

from modules.Debug import log

AbsoluteRange = namedtuple('AbsoluteRange', ('start', 'end'))
EpisodeRange = namedtuple(
    'EpisodeRange',
    ('season_start', 'episode_start', 'season_end', 'episode_end')
)
Season = namedtuple('Season', ('season_number'))

class SeasonTitleRanges:

    ABSOLUTE_RANGE_REGEX = re_compile(r'^(\d+)-(\d+)$', IGNORECASE)
    EPISODE_RANGE_REGEX = re_compile(r'^s(\d+)e(\d+)-s(\d+)e(\d+)$', IGNORECASE)
    SEASON_REGEX = re_compile(r'^(\d+)$', IGNORECASE)

    __slots__ = ('titles')

    def __init__(self, ranges: dict[str, str]) -> None:
        """
        Create a SeasonTitleRanges object with the given ranges.

        Args:
            ranges: Dictionary of season titles. Keys must be either
                absolute, episode, or season ranges. Values are
                format strings for the season titles.
        """

        # Parse ranges into objects
        self.titles = {}
        for key, title in list(ranges.items())[::-1]:
            if (match := self.ABSOLUTE_RANGE_REGEX.match(key)) is not None:
                self.titles[AbsoluteRange(*map(int, match.groups()))] = title
            elif (match := self.EPISODE_RANGE_REGEX.match(key)) is not None:
                self.titles[EpisodeRange(*map(int, match.groups()))] = title
            elif (match := self.SEASON_REGEX.match(key)) is not None:
                self.titles[Season(*map(int, match.groups()))] = title
            else:
                log.warning(f'Unrecognized season title "{key}": "{title}"')


    def get_season_text(self,
            episode_info: 'EpisodeInfo',
            card_settings: dict[str, Any]) -> str:
        """
        Get the season text for the given Episode.

        Args:
            episode_info: EpisodeInfo of the Episode to get the text of.
            card_settings: Arbitrary dictionary of card settings to use
                in the indicated season text format string.

        Returns:
            Season text for the given Episode.
        """

        # Try and match on each season title
        for range_, title in self.titles.items():
            if isinstance(range_, AbsoluteRange):
                # Episode has no absolute number, warn and skip
                if episode_info.absolute_number is None:
                    log.warning(f'Episode {episode_info} has no absolute number')
                    break

                if range_.start <= episode_info.absolute_number <= range_.end:
                    return title.format(**card_settings)
            elif (isinstance(range_, EpisodeRange)
                and (range_.season_start <= episode_info.season_number <= range_.season_end)
                and (range_.episode_start <= episode_info.episode_number <= range_.episode_end)):
                return title.format(**card_settings)
            elif (isinstance(range_, Season)
                and range_.season_number == episode_info.season_number):
                return title.format(**card_settings)

        # No matching season title range, return default
        if episode_info.season_number == 0:
            return f'Specials'
        return f'Season {episode_info.season_number}'