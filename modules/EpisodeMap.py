class EpisodeMap:
    
    DEFAULT_APPLIES_TO = 'all'
    
    def __init__(self, seasons: dict=None,
                 episode_ranges: dict=None) -> dict:
        
        # Assume object is valid until invalidated
        self.valid = True
        
        # Default indexing is by season number
        self.__index_by = 'season'
        
        # If no custom seasons/episode ranges, generate defaults
        self.__titles, self.__sources, self.__applies = {}, {}, {}
        if not seasons and not episode_ranges:
            return None
        
        # If both mappings are provided, invalidate 
        if seasons and episode_ranges:
            print(f'Cannot specify both seasons and episode ranges')
            self.valid = False
            return None
        
        # Validate type of provided mapping
        if seasons and not isinstance(seasons, dict):
            print(f'Invalid "seasons"')
            self.valid = False
            return None
        if episode_ranges and not isinstance(episode_ranges, dict):
            print(f'Invalid "episode_ranges"')
            self.valid = False
            return None
        
        if seasons:
            self.__index_by = 'season'
            self.__parse_seasons(seasons)
        elif episode_ranges:
            self.__index_by = 'episode'
            self.__parse_episode_ranges(episode_ranges)
            
    
    def __parse_seasons(self, seasons: dict) -> None:
        """
        
        """
        
        # Go through each season of mapping
        for season_number, mapping in seasons.items():
            # Ensure season number is a number
            if not isinstance(season_number, int):
                print(f'Invalid season "{season_number}"')
                self.valid = False
                return None
            
            if isinstance(mapping, str):
                self.__titles[season_number] = mapping
            elif isinstance(value, dict):
                if (value := mapping.get('title')):
                    self.__titles[season_number] = value
                if (value := mapping.get('source')):
                    self.__sources[season_number] = value
                if (value := mapping.get('source_applies_to', '').lower()):
                    if value not in ('all', 'unwatched'):
                        log.error(f'Source applies to "{value}" of season '
                                  f'{season_number} is invalid')
                        self.valid = False
                        return None
                    self.__applies[season_number] = value
        
        
    def __parse_episode_ranges(self, episode_ranges: dict) -> None:
        """
        
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
                elif isinstance(mapping, dict):
                    if (value := mapping.get('title'))
                        self.__titles[episode_number] = value
                    if (value := mapping.get('source')):
                        self.__sources[episode_number] = value
                    if (value := mapping.get('source_applies_to', '').lower()):
                        if value not in ('all', 'unwatched'):
                            log.error(f'Source applies to "{value}" of episodes '
                                      f'{episode_range} is invalid')
                            self.valid = False
                            return None
                        self.__applies[episode_number] = value
                    
                    
    def __repr__(self) -> str:
        return (f'<EpisodeRange {self.__titles=}, {self.__sources=}, '
               f'{self.__applies=}>')
    
    
    def __get_generic_season_title(self, episode_info: 'EpisodeInfo') -> str:
        """
        Get the generic season title associated with the given Episode.
        
        :param      episode_info:   EpisodeInfo to the get season title of.
        
        :returns:   'Specials' for season 0 episodes, 'Season {n}' otherwise.
        """
        
        season = episode_number.season_number
        return 'Specials' if season == 0 else f'Season {season}'
    
    
    def get_season_title(self, episode_info: 'EpisodeInfo') -> str:
        """
        
        """
        
        # Index by season, return matching season title
        if self.__index_by == 'season':
            if episode_info.season_number in self.__titles:
                return self.__titles[episode_info.season_number]
            return self.__get_generic_season_title(episode_info)
        
        # Index by absolute episode number
        if episode_info.abs_number == None:
            # Episode has no absolute number
            if episode_info.season_number != 0:
                log.warning(f'Episode range specified, but {episode_info} '
                            f'has no absolute episode number')

            return self.__get_generic_season_title(episode_info)
        elif episode_info.abs_number not in self.__titles:
            log.warning(f'{episode_info} does not fall into specified '
                        f'episode range')
            return self.__get_generic_season_title(episode_info)
        
        return self.__titles[episode_info.abs_number]
    
    
    def get_applies_to(self, episode_info: 'EpisodeInfo') -> str:
        """
        
        """
        
        # Index by season
        if self.__index_by == 'season':
            if episode_info.season_number in self.__applies:
                return self.__applies[episode_info.season_number]
            return self.DEFAULT_APPLIES_TO
        
        # Index by absolute episode number
        if (episode_info.abs_number == None
            or episode_info.abs_number not in self.__applies):
            return self.DEFAULT_APPLIES_TO
        
        return self.__applies[episode_info.abs_number]