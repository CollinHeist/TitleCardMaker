from Debug import *
from TitleCardMaker import TitleCardMaker

class TitleCard:
    """
    This class describes a title card.
    """

    NO_TITLE_CARD_CREATED: int = 0
    TITLE_CARD_CREATED: int = 1

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

        # Construct this title card's TitleCardMaker from the given Episode and Profile
        self.maker = TitleCardMaker(
            episode.source,
            episode.destination,
            profile.convert_title(episode.title_top_line),
            profile.convert_title(episode.title_bottom_line),
            profile.get_season_text(episode.season_number),
            profile.get_episode_text(episode.episode_number),
            profile.font,
            profile.font_size,
            profile.color,
            profile.hide_season_title,
        )

        self.file = episode.destination


    def create(self, database_interface: 'DatabaseInterface'=None) -> int:
        """
        Create this title card. If the card already exists, a new one
        is not created.
        """

        # If the card already exists, exit
        if self.file.exists():
            return self.NO_TITLE_CARD_CREATED

        # If the input source doesn't exist, warn and exit
        if not self.episode.source.exists():
            warn(f'Source image {self.episode.source.resolve()} does not exist', 2)
            return self.NO_TITLE_CARD_CREATED

        info(f'Creating title card for {self.episode.destination.name}', 2)
        self.maker.create()

        return self.TITLE_CARD_CREATED
        