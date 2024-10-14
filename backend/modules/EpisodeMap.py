from re import compile as re_compile, IGNORECASE
from typing import Any, Callable, Literal, Optional

from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo
from modules.FormatString import FormatString


class EpisodeMap:
    """
    This class describes an EpisodeMap. In particular a mapping of
    episode indices to manually specified season titles or sources. This
    object basically contains the `seasons` and `episode_ranges`
    attributes for a given Show.
    """

    """How to apply manual source if not explicitly stated"""
    DEFAULT_APPLIES_TO = 'all'

    """Regex to match season/episode number from index range text"""
    INDEX_RANGE_REGEX = re_compile('s(\d+)e(\d+)', IGNORECASE)

    __slots__ = (
        'valid', 'is_custom', '__index_by', 'raw', '__titles', '__sources',
        '__applies', 'unique_season_titles',
    )


    def __init__(self,
            seasons: Optional[dict[str, Any]] = None,
            episode_ranges: Optional[dict[str, Any]] = None
        ) -> None:
        """
        Construct a new instance of an EpisodeMap. This maps titles and
        source images to episodes, and can be initialized with EITHER a
        season map or episode range directly from series YAML; NOT both.

        Args:
            seasons: Optional 'seasons' key from series YAML to
                initialize with.
            episode_ranges: Optional 'episode_ranges' key from series
                YAML to initialize with.
        """

        # Generic object attributes
        self.valid = True
        self.is_custom = False
        self.__index_by = 'season'
        self.raw, self.__titles, self.__sources, self.__applies = {}, {}, {}, {}
        self.unique_season_titles = set()

        # If no custom specification, nothing else to parse
        if not seasons and not episode_ranges:
            return None

        # Validate type of provided mapping
        if seasons and not isinstance(seasons, dict):
            log.error(f'Season map "{seasons}" is invalid')
            self.valid = False
            return None
        if episode_ranges and not isinstance(episode_ranges, dict):
            log.error(f'Episode range "{episode_ranges}" is invalid')
            self.valid = False
            return None

        # Remove hide key from seasons if indicated
        if isinstance(seasons, dict):
            seasons.pop('hide', None)

        # If both mappings are provided, invalidate
        if seasons and episode_ranges:
            log.error(f'Cannot specify both seasons and episode ranges')
            self.valid = False
            return None

        # Specify how to index this Episode Map, parse that YAML
        if seasons and len(seasons) > 0:
            self.__index_by = 'season'
            self.__parse_seasons(seasons)
        if (episode_ranges and len(episode_ranges) > 0
            and str(list(episode_ranges.keys())[0])[0] == 's'):
            self.__index_by = 'index'
            self.__parse_index_episode_range(episode_ranges)
        elif episode_ranges and len(episode_ranges) > 0:
            self.__index_by = 'episode'
            self.__parse_absolute_episode_ranges(episode_ranges)

        # Determine unique set of specified season titles
        self.unique_season_titles = set(val for _, val in self.__titles.items())
        return None


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return (f'<EpisodeRange {self.__titles=}, {self.__sources=}, '
                f'{self.__applies=}, {self.__index_by=}>')


    @property
    def custom_hash(self) -> str:
        """Custom hash string for this object."""

        return f'{self.__titles}|{self.__sources}|{self.__applies}'


    def __parse_seasons(self, seasons: dict[str, Any]) -> None:
        """
        Parse the given season map, filling this object's title, source,
        and applies dictionaries. Also update's object validity.

        Args:
            seasons: 'series' key from series YAML to parse.
        """

        # Go through each season of mapping
        for season_number, mapping in seasons.items():
            # Skip hide key
            if season_number == 'hide':
                continue

            # Ensure season number is a number
            if not isinstance(season_number, int):
                log.warning(f'Invalid season number "{season_number}"')
                self.valid = False
                continue

            # Parse title/source mapping
            if isinstance(mapping, dict):
                if (value := mapping.get('title')):
                    self.raw[season_number] = str(value)
                    self.__titles[season_number] = str(value)
                    self.is_custom = True
                if (value := mapping.get('source')):
                    self.__sources[season_number] = value
                if (value := mapping.get('source_applies_to', '').lower()):
                    if value not in ('all', 'unwatched'):
                        # Invalid applies, error and exit
                        log.error(f'Source applies to "{value}" of season '
                                  f'{season_number} is invalid')
                        self.valid = False
                        continue
                    self.__applies[season_number] = value
            else:
                self.raw[season_number] = str(mapping)
                self.__titles[season_number] = str(mapping)
                self.is_custom = True


    def __parse_index_episode_range(self,
            episode_ranges: dict[str, Any],
        ) -> None:
        """
        Parse the given episode range map, filling this object's title,
        source, and applies dictionaries. Also update's object validity.

        Args:
            episode_ranges: 'episode_ranges' key from series YAML to
                parse.
        """

        # Go through each index range of mapping
        for episode_range, mapping in episode_ranges.items():
            # Parse start and end of the range
            try:
                start, end = episode_range.split('-')
                start_season, start_episode =\
                    map(int, self.INDEX_RANGE_REGEX.match(start).groups())
                end_season, end_episode =\
                    map(int, self.INDEX_RANGE_REGEX.match(end).groups())

                # Error if range spans multiple seasons
                assert start_season == end_season,'Cannot span multiple seasons'
            # Some error occurred while parsing this range
            except Exception as e:
                self.valid = False
                log.error(f'Invalid episode range "{episode_range}"')
                log.debug(e)
                continue

            # Assign attributes for each index in this range
            for episode_number in range(start_episode, end_episode+1):
                key = f's{start_season}e{episode_number}'
                # Title specified directly
                if isinstance(mapping, str):
                    self.raw[episode_range] = str(mapping)
                    self.__titles[key] = mapping
                    self.is_custom = True
                # Season specification is more complex
                elif isinstance(mapping, dict):
                    # Title specified (via key)
                    if (value := mapping.get('title')):
                        self.raw[episode_range] = str(value)
                        self.__titles[key] = value
                        self.is_custom = True
                    # Source specified (via key)
                    if (value := mapping.get('source')):
                        self.__sources[key] = value
                    # Source application specified (via key)
                    if (value := mapping.get('source_applies_to', '').lower()):
                        if value not in ('all', 'unwatched'):
                            # Invalid applies, error and exit
                            log.error(f'Source applies to "{value}" of episodes '
                                        f'{episode_range} is invalid')
                            self.valid = False
                            continue
                        self.__applies[key] = value


    def __parse_absolute_episode_ranges(self,
            episode_ranges: dict[str, Any],
        ) -> None:
        """
        Parse the given episode range map, filling this object's title,
        source, and applies dictionaries. Also update's object validity.

        Args:
            episode_ranges: 'episode_ranges' key from series YAML to
                parse.
        """

        # Go through each episode range of mapping
        for episode_range, mapping in episode_ranges.items():
            try:
                start, end = map(int, episode_range.split('-'))
            except Exception as e:
                self.valid = False
                log.error(f'Invalid episode range "{episode_range}"')
                log.debug(e)
                continue

            # Assign attributes for every episode in this range
            for episode_number in range(start, end+1):
                if isinstance(mapping, str):
                    self.raw[episode_range] = str(mapping)
                    self.__titles[episode_number] = mapping
                    self.is_custom = True
                elif isinstance(mapping, dict):
                    if (value := mapping.get('title')):
                        self.raw[episode_range] = str(value)
                        self.__titles[episode_number] = value
                        self.is_custom = True
                    if (value := mapping.get('source')):
                        self.__sources[episode_number] = value
                    if (value := mapping.get('source_applies_to', '').lower()):
                        if value not in ('all', 'unwatched'):
                            # Invalid applies, error and exit
                            log.error(f'Source applies to "{value}" of episodes'
                                      f' {episode_range} is invalid')
                            self.valid = False
                            continue
                        self.__applies[episode_number] = value


    def reset(self) -> None:
        """Reset this object go have generic titles."""

        # Always reset titles/applies - never reset sources
        self.raw, self.__titles, self.__applies = {}, {}, {}

        # If no manual sources have been specified, reset index by flag
        if len(self.__sources) == 0:
            self.__index_by = 'season'


    def get_generic_season_title(self, *,
            season_number: Optional[int] = None,
            episode_info: Optional[EpisodeInfo] = None,
            default: Optional[Callable[[EpisodeInfo], str]] = None,
        ) -> str:
        """
        Get the generic season title for the given entry.

        Args:
            season_number: Season number to get the generic title of.
            episode_info: EpisodeInfo to the get season title of.
            default: Optional function to get default season titles
                from.

        Returns:
            'Specials' for season 0 episodes, 'Season {n}' otherwise.
            If `default` is provided, then the result of that function
            is returned.

        Raises:
            ValueError if neither season_number nor episode_info is
            provided.
        """

        # Ensure at least one argument was provided
        if season_number is None and episode_info is None:
            raise ValueError(f'Must provide season_number or episode_info')

        # Get episode's season number if not provided directly
        if season_number is None:
            season_number = episode_info.season_number

        # Call default function if provided
        if default is not None:
            return default(episode_info=episode_info)

        return 'Specials' if season_number == 0 else f'Season {season_number}'


    def get_all_season_titles(self) -> dict[str, str]:
        """
        Get the dictionary of season titles.

        Returns:
            Dictionary of indices to season titles.
        """

        return self.__titles if self.__index_by == 'season' else {}


    def __get_value(self,
            episode_info: EpisodeInfo,
            which: Literal['season_titles', 'source', 'applies_to'],
            default: Callable[[EpisodeInfo], str],
        ) -> str:
        """
        Get the value for the given Episode from the target associated with
        'which' (i.e. the season title/source/applies map).

        Args:
            episode_info: Episode to get the value of.
            which: Which dictionary to get the value from.
            default: Function to call if the given Episode does not
                exist in the indicated map. It's return is returned.

        Returns:
            If the Episode exists, returns the value from the indicated
            map. If it does not exist, returns the return of default
            with EpisodeInfo passed.
        """

        # Get target to look through
        target = {'season_title':   self.__titles,
                  'source':         self.__sources,
                  'applies_to':     self.__applies}[which]

        # Index by season
        if self.__index_by == 'season':
            if (base_ := target.get(episode_info.season_number)) is not None:
                # Format this season's title with the episode characteristics
                return FormatString(
                    base_,
                    data=episode_info.characteristics
                ).result

            return default(episode_info=episode_info)

        # Index by index
        if self.__index_by == 'index':
            if (base_title := target.get(episode_info.index)) is not None:
                return FormatString(
                    base_title,
                    data=episode_info.characteristics,
                ).result

            return default(episode_info=episode_info)

        # Index by absolute episode number
        # If there's no absolute number, use episode number instead
        if (index_number := episode_info.abs_number) is None:
            index_number = episode_info.episode_number

        # Return custom from target
        if (base_title := target.get(index_number)) is not None:
            return FormatString(
                base_title,
                data=episode_info.characteristics
            ).result

        # Use default if index doesn't fall into specified target
        return default(episode_info=episode_info)


    def get_season_title(self,
            episode_info: EpisodeInfo,
            *,
            default: Optional[Callable[[EpisodeInfo], str]] = None,
        ) -> str:
        """
        Get the season title for the given Episode.

        Args:
            episode_info: Episode to get the season title of.
            default: Optional function to get default season titles
                from.

        Returns:
            Season title defined by this map for this Episode.
        """

        # Get season title for this episode - use default if provided
        def_func = self.get_generic_season_title if default is None else default
        season_title = self.__get_value(episode_info, 'season_title', def_func)

        # Warn if default value was returned and indexing by absolute number
        if self.__index_by == 'episode':
            if (episode_info.abs_number is None
                and episode_info.season_number != 0):
                log.warning(f'Episode range specified, but {episode_info} has '
                            f'no absolute episode number')
            elif episode_info.abs_number not in self.__titles:
                log.warning(f'{episode_info} does not fall into given episode '
                            f'ranges')
        # Warn if default was returned and indexing by index
        elif (self.__index_by == 'index'
            and episode_info.index not in self.__titles):
            log.warning(f'{episode_info} does not fall into given episode ranges')

        return season_title


    def get_source(self, episode_info: EpisodeInfo) -> str:
        """
        Get the specified source filename for the given Episode.

        Args:
            episode_info: Episode to get the source filename of.

        Returns:
            Source filename defined by this map for this Episode.
        """

        source = self.__get_value(episode_info, 'source', lambda *_, **__: None)

        # Attempt to format string for this episode index
        if isinstance(source, str):
            try:
                return FormatString(
                    source,
                    data=episode_info.characteristics,
                ).result
            except Exception as e:
                log.warning(f'Cannot format source "{source}" - {e}')
                return source

        return source


    def get_applies_to(self, episode_info: EpisodeInfo) -> str:
        """
        Get the specified applies to value of for the given Episode.

        Args:
            episode_info: Episode to get the applies to value of.

        Returns:
            Applies to value defined by this map for this Episode; either 'all'
            or 'unwatched'.
        """

        return self.__get_value(
            episode_info, 'applies_to',
            lambda *_, **__: self.DEFAULT_APPLIES_TO
        )
