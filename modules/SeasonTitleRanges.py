from collections import namedtuple
from logging import Logger

from re import IGNORECASE, compile as re_compile
from typing import Callable, Optional, Union

from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
from modules.FormatString import FormatString


AbsoluteRange = namedtuple('AbsoluteRange', ('start', 'end'))
EpisodeRange = namedtuple(
    'EpisodeRange',
    ('season_start', 'episode_start', 'season_end', 'episode_end')
)
Season = namedtuple('Season', ('season_number'))


class SeasonTitleRanges:
    """
    Class definining ranges over which custom season titles are applied.
    These ranges take the form of an AbsoluteRange, EpisodeRange, or
    Season.
    """

    """Regex to identify which type of range is specified"""
    ABSOLUTE_RANGE_REGEX = re_compile(r'^(\d+)-(\d+)$', IGNORECASE)
    EPISODE_RANGE_REGEX = re_compile(r'^s(\d+)e(\d+)-s(\d+)e(\d+)$', IGNORECASE)
    SEASON_REGEX = re_compile(r'^(\d+)$', IGNORECASE)

    __slots__ = ('titles', 'fallback')


    def __init__(self,
            /,
            ranges: dict[str, str],
            *,
            fallback: Optional[Callable[[EpisodeInfo], str]] = None,
            log: Logger = log,
        ) -> None:
        """
        Create a SeasonTitleRanges object with the given ranges.

        Args:
            ranges: Dictionary of season titles. Keys must be either
                absolute, episode, or season ranges. Values are
                format strings for the season titles.
            fallback: Optional function to use to generate season text
                when there is no custom specification. If omitted, then
                the generic text of "Specials" and "Season {x}" are
                used. This is equivalent to:
            log: Logger for all log messages.
        """

        # Parse ranges into objects
        self.titles: dict[Union[AbsoluteRange, EpisodeRange, Season], str] = {}
        for key, title in list(ranges.items())[::-1]:
            if (match := self.ABSOLUTE_RANGE_REGEX.match(key)) is not None:
                self.titles[AbsoluteRange(*map(int, match.groups()))] = title
            elif (match := self.EPISODE_RANGE_REGEX.match(key)) is not None:
                self.titles[EpisodeRange(*map(int, match.groups()))] = title
            elif (match := self.SEASON_REGEX.match(key)) is not None:
                self.titles[Season(*map(int, match.groups()))] = title
            else:
                log.warning(f'Unrecognized season title "{key}": "{title}"')

        self.fallback = fallback


    def get_season_text(self,
            episode_info: EpisodeInfo,
            card_settings: dict,
        ) -> str:
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
        ep = episode_info
        for range_, title in self.titles.items():
            # Absolute range, evaluate on absolute number only
            if isinstance(range_, AbsoluteRange):
                # Episode has no absolute number, skip
                if ep.absolute_number is None:
                    break

                if range_.start <= ep.absolute_number <= range_.end:
                    return FormatString(title, data=card_settings).result
            # Entire season, evaluate on season number only
            elif (isinstance(range_, Season)
                and range_.season_number == ep.season_number):
                return FormatString(title, data=card_settings).result
            # Episode range, evaluate season and episode number
            elif isinstance(range_, EpisodeRange):
                # Evaluate if within a single season
                if (range_.season_start == range_.season_end
                    # Episode falls within season range
                    and range_.season_start <= ep.season_number <= range_.season_end
                    # Episode falls within episode range
                    and range_.episode_start <= ep.episode_number <= range_.episode_end):
                    return FormatString(title, data=card_settings).result
                # Spans multiple seasons and episode falls within season range
                if (range_.season_start < range_.season_end
                    and range_.season_start <= ep.season_number <= range_.season_end):
                    # Part of start season, falls within episode range
                    if range_.season_start == ep.season_number:
                        if range_.episode_start <= ep.episode_number:
                            return FormatString(title, data=card_settings).result
                    # Part of end season, falls within episode range
                    elif range_.season_end == ep.season_number:
                        if ep.episode_number <= range_.episode_end:
                            return FormatString(title, data=card_settings).result
                    # After start season, episode number is irrelevant
                    elif range_.season_start < ep.season_number:
                        return FormatString(title, data=card_settings).result

        # No matching season title range
        # Return fallback if specified
        if self.fallback is not None:
            return FormatString(
                self.fallback(episode_info), data=card_settings
            ).result

        # No fallback, return default titles
        if episode_info.season_number == 0:
            return f'Specials'

        return f'Season {episode_info.season_number}'
