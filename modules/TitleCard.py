from modules.Debug import *
from modules.TitleCardMaker import TitleCardMaker

class TitleCard:
    """
    This class describes a title card. This class is responsible for
    applying a given profile to the Episode details and initializing a
    TitleCardMaker with those details. After initialization, `create()`
    is just a glorified wrapper for `TitleCardMaker.create()`.
    """

    """Extensions of the input source image and output title card"""
    INPUT_CARD_EXTENSION: str = '.jpg'
    OUTPUT_CARD_EXTENSION: str = '.jpg'

    def __init__(self, episode: 'Episode', profile: 'Profile') -> None:
        """
        Constructs a new instance of this class.
        
        :param      episode:    The episode whose TitleCard this corresponds to.

        :param      profile:    The profile to apply to the creation of
                                this title card. This ensures the correct
                                season text, and font characteristics are used.
        """
        
        self.episode = episode
        self.profile = profile
        
        # Construct this title card's TitleCardMaker from the given Episode and Profile
        self.maker = TitleCardMaker(
            episode.source,
            episode.destination,
            profile.convert_title(episode.title_top_line),
            profile.convert_title(episode.title_bottom_line),
            profile.get_season_text(episode.season_number, episode.abs_number),
            profile.get_episode_text(episode.episode_number,episode.abs_number),
            profile.font,
            profile.font_size,
            profile.font_color,
            profile.hide_season_title,
        )

        self.file = episode.destination


    def create(self) -> bool:
        """
        Create this title card. If the card already exists, a new one
        is not created. Return whether a card was created.

        :returns:   True if a title card was created, otherwise False.
        """

        # If the card already exists, exit
        if self.file.exists():
            return False

        # If the input source doesn't exist, warn and exit
        if not self.episode.source.exists():
            # warn(f'Source image {self.episode.source.resolve()} does not exist', 2)
            return False
            
        info(f'Creating title card for {self.episode.destination.name}', 2)
        self.maker.create()

        return True
        