from modules.Debug import *

# CardType classes
from modules.StandardTitleCard import StandardTitleCard
from modules.StarWarsTitleCard import StarWarsTitleCard

class TitleCard:
    """
    This class describes a title card. This class is responsible for applying a
    given profile to the Episode details and initializing a CardType with those
    attributes.

    It also contains the mapping of card type identifier strings (in YAML) to
    their respective CardType classes.
    """

    """Extensions of the input source image and output title card"""
    INPUT_CARD_EXTENSION: str = '.jpg'
    OUTPUT_CARD_EXTENSION: str = '.jpg'

    """Mapping of card type identifiers to CardType classes"""
    CARD_TYPES = {
        'standard': StandardTitleCard,
        'generic': StandardTitleCard,
        'star wars': StarWarsTitleCard,
    }


    def __init__(self, episode: 'Episode', profile: 'Profile') -> None:
        """
        Constructs a new instance of this class.
        
        :param      episode:    The episode whose TitleCard this corresponds to.

        :param      profile:    The profile to apply to the creation of this 
                                title card.
        """
        
        # Store this card's associated episode/profile.
        self.episode = episode
        self.profile = profile

        # Get temporary absolute number
        if episode.abs_number == None:
            abs_number = episode.episode_number
        else:
            abs_number = episode.abs_number
        
        # Construct this title card's StandardTitleCard from the given arguments
        self.maker = self.episode.card_class(
            source=episode.source,
            output_file=episode.destination,
            title_top_line=profile.convert_title(episode.title_top_line),
            title_bottom_line=profile.convert_title(episode.title_bottom_line),
            season_text=profile.get_season_text(
                episode.season_number, abs_number
            ), episode_text=profile.get_episode_text(
                episode.episode_number, episode.abs_number
            ), font=profile.font,
            font_size=profile.font_size,
            title_color=profile.font_color,
            hide_season=profile.hide_season_title,
        )

        # File associated with this card is the episode's destination
        self.file = episode.destination


    def create(self) -> bool:
        """
        Create this title card. If the card already exists, a new one is not 
        created. Return whether a card was created.

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
        