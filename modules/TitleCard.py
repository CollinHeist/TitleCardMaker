from modules.Debug import info, warn, error

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
        
    """Default filename format for all title cards"""
    DEFAULT_FILENAME_FORMAT = '{full_name} - S{season:02}E{episode:02}'

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
        
        
    @staticmethod
    def get_output_filename(format_string: str, series_info: 'SeriesInfo', 
                            datafile_entry: dict,
                            media_directory: 'Path') -> 'Path':
        """
        Get the output filename for a title card described by the given values.
        
        :param      format_string:      Format string that specifies how to 
                                        construct the filename.
        :param      series_info:        Series info pertaining to this entry
        :param      datafile_entry:     Episode data of an entry, as returned
                                        by a DataFileInterface. 
        :param      media_directory:    Top-level media directory.
        
        :returns:   Path for the full title card destination.
        """
        
        # Get season number for this entry
        season_number = datafile_entry['season_number']
        
        # Get the season folder for this entry's season
        if season_number == 0:
            season_folder = 'Specials'
        else:
            season_folder = f'Season {season_number}'
        
        # Get filename from the given format string
        filename = format_string.format(
            name=series_info.name,
            full_name=series_info.full_name,
            year=series_info.year,
            season=season_number,
            episode=datafile_entry['episode_number'],
            title=datafile_entry['title'].full_title,
        )
        
        # Add card extension
        filename += TitleCard.OUTPUT_CARD_EXTENSION
        
        return media_directory / season_folder / filename
        
        
    @staticmethod
    def validate_card_format_string(format_string: str) -> bool:
        """
        Return whether the given card filename format string is valid or
        not.
        
        :param      format_string:  Format string being validated.
        
        :returns:   True if the given string can be formatted correctly,
                    False otherwise.
        """
        
        try:
            format_string.format(
                name='TestName', full_name='TestName (2000)', year=2000,
                season=1, episode=1, title='Episode Title',
            )
            return True
        except ValueError as e:
            error(f'Card format string is invalid - "{e}"')
            return False
            

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
        