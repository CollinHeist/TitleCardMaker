from Debug import *
from TitleCardMaker import TitleCardMaker

class TitleCard:

    INPUT_CARD_EXTENSION: str = '.jpg'
    OUTPUT_CARD_EXTENSION: str = '.jpg'

    def __init__(self, episode: 'Episode', profile: 'Profile') -> None:
        """
        Constructs a new instance.
        
        :param      episode:  The episode

        :param      profile:  The profile
        """
        
        self.episode = episode
        self.profile = profile

        # Construct this title card's TitleCardMaker
        self.maker = TitleCardMaker(
            episode.source,
            episode.destination,
            episode.title_top_line,
            episode.title_bottom_line,
            profile.get_season_text(profile.get_season_text(episode.season_number)),
            profile.get_episode_text(episode.episode_number),
            profile.font,
            profile.color,
            profile.hide_season_title,
        )

        self.file = episode.destination
        self.exists = self.file.exists()


    def create(self, database_interface: 'DatabaseInterface'=None) -> None:
        """
        Create this title card. If the card already exists, a new one
        is not created.
        """

        # If the card already exists, exit
        if self.exists:
            return

        # If the input source doesn't exist, warn and exit
        if not self.episode.source.exists():

            warn(f'Source image {self.episode.source.resolve()} does not exist')
            return

        info(f'Creating title card for {self.episode.destination.name}')
        self.maker.create()
        