from modules.Debug import log

class EpisodeMap:
    """
    This class describes an EpisodeMap. In particular a mapping of episode
    indices to manually specified season titles or sources. This object
    basically contains the `seasons` and `episode_ranges` attributes for a given
    Show.
    """
    
    """How to apply manual source if not explicitly stated"""
    DEFAULT_APPLIES_TO = 'all'


    __slots__ = ('valid', 'is_custom', '__index_by', '__titles', '__sources',
                 '__applies')

    
    def __init__(self, seasons: dict=None,
                 episode_ranges: dict=None) -> None:
        """
        Construct a new instance of an EpisodeMap. This maps titles and source
        images to episodes, and can be initialized with EITHER a season map or
        episode range directly from series YAML; NOT both.
        
        :param      seasons:        Optional 'seasons' key from series YAML to
                                    initialize with.
        :param      episode_ranges: Optional 'episode_ranges' key from series 
                                    YAML to initialize with.
        """
        
        # Assume object is valid until invalidated, and generic until customized
        self.valid = True
        self.is_custom = False
        
        # Default indexing is by season number
        self.__index_by = 'season'
        
        # If no custom seasons/episode ranges, generate defaults
        self.__titles, self.__sources, self.__applies = {}, {}, {}
        if not seasons and not episode_ranges:
            return None
        
        # Validate type of provided mapping
        if seasons and not isinstance(seasons, dict):
            log.error(f'Season map "{seasons}" is invalid')
            self.valid = False
            return None
        if episode_ranges and not isinstance(episode_ranges, dict):
            log.error(f'Episode ranges "{episode_ranges}" is invalid')
            self.valid = False
            return None

        # If both mappings are provided, invalidate 
        if seasons and episode_ranges:
            log.error(f'Cannot specify both seasons and episode ranges')
            self.valid = False
            return None
        
        # Specify how to index this Episode Map, parse that YAML
        if seasons:
            self.__index_by = 'season'
            self.__parse_seasons(seasons)
        elif episode_ranges:
            self.__index_by = 'episode'
            self.__parse_episode_ranges(episode_ranges)
            
    
    def __parse_seasons(self, seasons: dict) -> None:
        """
        Parse the given season map, filling this object's title, source, and
        applies dictionaries. Also update's object validity.

        :param      seasons:    'series' key from series YAML to parse.
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
                return None
            
            # Parse title/source mapping
            if isinstance(mapping, str):
                self.__titles[season_number] = mapping
                self.is_custom = True
            elif isinstance(mapping, dict):
                if (value := mapping.get('title')):
                    self.__titles[season_number] = value
                    self.is_custom = True
                if (value := mapping.get('source')):
                    self.__sources[season_number] = value
                if (value := mapping.get('source_applies_to', '').lower()):
                    if value not in ('all', 'unwatched'):
                        # Invalid applies, error and exit
                        log.error(f'Source applies to "{value}" of season '
                                  f'{season_number} is invalid')
                        self.valid = False
                        return None
                    self.__applies[season_number] = value
        
        
    def __parse_episode_ranges(self, episode_ranges: dict) -> None:
        """
        Parse the given episode range map, filling this object's title, source,
        and applies dictionaries. Also update's object validity.

        :param      episode_ranges: 'episode_ranges' key from series YAML to
                                    parse.
        """
        
        # Go through each episode range of mapping
        for episode_range, mapping in episode_ranges.items():
            try:
                start, end = map(int, episode_range.split('-'))
            except Exception:
                log.error(f'Invalid episode range "{episode_range}"')
                return None
            
            # Assign title for every episode in this range
            for episode_number in range(start, end+1):
                if isinstance(mapping, str):
                    self.__titles[episode_number] = mapping
                    self.is_custom = True
                elif isinstance(mapping, dict):
                    if (value := mapping.get('title')):
                        self.__titles[episode_number] = value
                        self.is_custom = True
                    if (value := mapping.get('source')):
                        self.__sources[episode_number] = value
                    if (value := mapping.get('source_applies_to', '').lower()):
                        if value not in ('all', 'unwatched'):
                            # Invalid applies, error and exit
                            log.error(f'Source applies to "{value}" of episodes '
                                      f'{episode_range} is invalid')
                            self.valid = False
                            return None
                        self.__applies[episode_number] = value
                    
                    
    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object."""

        return (f'<EpisodeRange {self.__titles=}, {self.__sources=}, '
               f'{self.__applies=}, {self.__index_by=}>')
    
    
    def get_generic_season_title(self, episode_info: 'EpisodeInfo') -> str:
        """
        Get the generic season title associated with the given Episode index.
        
        :param      episode_info:   EpisodeInfo to the get season title of.
        
        :returns:   'Specials' for season 0 episodes, 'Season {n}' otherwise.
        """
        
        season = episode_info.season_number
        return 'Specials' if season == 0 else f'Season {season}'


    def __get_value(self, episode_info: 'EpisodeInfo', which: str,
                    default: callable):
        """
        Get the value for the given Episode from the target associated with
        'which' (i.e. the season title/source/applies map).
        
        :param      episode_info:   Episode to get the value of.
        :param      which:          Which dictionary to get the value from.
        :param      default:        Function to call if the given Episode does
                                    not exist in the indicated map. It's return
                                    is returned.
        
        :returns:   If the Episode exists, returns the value from the indicated
                    map. If it does not exist, returns the return of default
                    with EpisodeInfo passed.
        """

        # Get target to look through
        if which == 'season_title':
            target = self.__titles
        elif which == 'source':
            target = self.__sources
        else:
            target = self.__applies

        # Index by season
        if self.__index_by == 'season':
            if episode_info.season_number in target:
                return target[episode_info.season_number]

            return default(episode_info)
        
        # Index by absolute episode number
        if (episode_info.abs_number is None
            or episode_info.abs_number not in target):
            return default(episode_info)
        
        return target[episode_info.abs_number]
    
    
    def get_season_title(self, episode_info: 'EpisodeInfo') -> str:
        """
        Get the season title for the given Episode.

        :param      episode_info:   Episode to get the season title of.

        :returns:   Season title defined by this map for this Episode.
        """

        season_title = self.__get_value(episode_info, 'season_title',
                                        self.get_generic_season_title)

        if self.__index_by == 'episode':
            if (episode_info.abs_number is None
                and episode_info.season_number != 0):
                log.warning(f'Episode range specified, but {episode_info} '
                            f'has no absolute episode number')
            elif episode_info.abs_number not in self.__titles:
                log.warning(f'{episode_info} does not fall into specified '
                            f'episode range')

        return season_title


    def get_source(self, episode_info: 'EpisodeInfo') -> str:
        """
        Get the specified source filename for the given Episode.

        :param      episode_info:   Episode to get the source filename of.

        :returns:   Source filename defined by this map for this Episode.
        """

        return self.__get_value(episode_info, 'source', lambda _: None)
    
    
    def get_applies_to(self, episode_info: 'EpisodeInfo') -> str:
        """
        Get the specified applies to value of for the given Episode.

        :param      episode_info:   Episode to get the applies to value of.

        :returns:   Applies to value defined by this map for this Episode; 
                    either 'all' or 'unwatched'.
        """

        return self.__get_value(episode_info, 'applies_to',
                                lambda _: self.DEFAULT_APPLIES_TO)
        