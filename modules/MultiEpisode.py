from pathlib import Path

# from modules.Debug import info, warn, error

class MultiEpisode:
    def __init__(self, episode_infos: ['EpisodeInfo'], card_class: 'CardType',
                 base_source: Path, destination: Path, **extras: dict) -> None:
        """
        
        """
        
        # If episode infos is 0-length, error
        if len(episode_infos) == 0:
            raise ValueError(f'No EpisodeInfo objects provided')
        
        # Verify all episodes are from the same season
        if not all(episode_info.season_number == episode_infos[0].season_number
                   for episode_info in episode_infos):
            raise ValueError(f'Given set of EpisodeInfo objects must be from'
                             f' the same season.')
        
        # Get the episode range for the given episode set
        episode_numbers = tuple(map(lambda e: e.episode_number, episode_infos))
        self.start_episode = min(episode_numbers)
        self.end_episode = max(episode_numbers)
        
        # If all episode have absolute numbers, get their absolute range
        self.start_abs, self.end_abs = None, None
        if all(e.abs_number != None for e in episode_infos):
            abs_numbers = tuple(map(lambda e: e.abs_number, episode_infos))
            self.start_abs = min(abs_numbers)
            self.end_abs = max(abs_numbers)
        
        # Get the first episde in the set
        for episode_info in episode_infos:
            if episode_info.episode_number == self.start_episode:
                first_episode = episode_info
                break
                   
        # Set object attributes
        self.episode_info = first_episode
        self.card_class = card_class

        # Set source/destination paths
        source_name = (f's{first_episode.season_number}'
                       f'e{first_episode.episode_number}'
                       f'{TitleCard.INPUT_CARD_EXTENSION}')
        self.source = base_source / source_name
        self.destination = destination

        # Store extra characteristics
        self.extra_characteristics = extras
        
        
    @staticmethod
    def modify_format_string(episode_format_string: str) -> str:
        """
        
        """
        
        if ' {abs_number}' in episode_format_string:
            # Split for absolute numbers
            pre, post = episode_format_string.split(' {abs_number}')

            return pre + 'S {abs_start}-{abs_end}' + post
        elif ' {episode_number}' in episode_format_string:
            # Split for episode numbers
            pre, post = episode_format_string.split(' {episode_number}')

            return pre + 'S {episode_start}-{episode_end}' + post
        else:
            raise ValueError('Format string is missing "{abs_number}" or "{episode_number}" text')