from modules.Debug import *

# CardType classes
from modules.AnimeCard import AnimeCard
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
        'anime': AnimeCard,
        'star wars': StarWarsTitleCard,
    }

    def __init__(self, episode: 'Episode', profile: 'Profile',
                 title_characteristics: dict,
                 **extra_characteristics: dict) -> None:
        """
        Constructs a new instance of this class.
        
        :param      episode:    The episode whose TitleCard this corresponds to.
        :param      profile:    The profile to apply to the creation of this 
                                title card.
        :param      title_characteristics:  Dictionary of characteristics from
                                            the CardType class for this Episode
                                            to pass to apply_profile().
        :param      extra_characteristics:  Any extra keyword arguments to pass
                                            directly to the creation of the
                                            CardType object.
        """
        
        # Store this card's associated episode/profile.
        self.episode = episode
        self.profile = profile

        # If the episode has no absolute number, use the season number instead
        if episode.abs_number == None:
            abs_number = episode.episode_number
        else:
            abs_number = episode.abs_number
        
        # Construct this episode's CardType instance
        self.maker = self.episode.card_class(
            source=episode.source,
            output_file=episode.destination,
            title=episode.title.apply_profile(profile, **title_characteristics),
            season_text=profile.get_season_text(
                episode.season_number, abs_number
            ), episode_text=profile.get_episode_text(
                episode.episode_number, episode.abs_number
            ), font=profile.font,
            font_size=profile.font_size,
            title_color=profile.font_color,
            hide_season=profile.hide_season_title,
            **extra_characteristics,
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
            return False
            
        self.maker.create()

        return True
        