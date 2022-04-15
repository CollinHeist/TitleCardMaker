from re import match, sub, IGNORECASE

from modules.Debug import log
import modules.preferences as global_preferences

# CardType classes
from modules.AnimeTitleCard import AnimeTitleCard
from modules.StandardTitleCard import StandardTitleCard
from modules.StarWarsTitleCard import StarWarsTitleCard

class TitleCard:
    """
    This class describes a title card. This class is responsible for applying a
    given profile to the Episode details and initializing a CardType with those
    attributes.

    It also contains the mapping of card type identifier strings to their
    respective CardType classes.
    """

    """Extensions of the input source image and output title card"""
    INPUT_CARD_EXTENSION = '.jpg'
    OUTPUT_CARD_EXTENSION = '.jpg'

    """Default filename format for all title cards"""
    DEFAULT_FILENAME_FORMAT = '{full_name} - S{season:02}E{episode:02}'

    """Mapping of card type identifiers to CardType classes"""
    CARD_TYPES = {
        'standard': StandardTitleCard,
        'generic': StandardTitleCard,
        'anime': AnimeTitleCard,
        'star wars': StarWarsTitleCard,
    }

    """Mapping of illegal filename characters and their replacements"""
    __ILLEGAL_CHARACTERS = {
        '?': '!',
        '<': '',
        '>': '',
        ':':' -',
        '"': '',
        '/': '+',
        '\\': '+',
        '|': '',
        '*': '-',
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
                                            to pass to Title.apply_profile().
        :param      extra_characteristics:  Any extra keyword arguments to pass
                                            directly to the creation of the
                                            CardType object.
        """

        # Store this card's associated episode and profile
        self.episode = episode
        self.profile = profile

        # Apply the given profile to the Episode's Title
        self.converted_title = episode.episode_info.title.apply_profile(
            profile, **title_characteristics
        )   
        
        # Construct this episode's CardType instance
        self.maker = self.episode.card_class(
            source=episode.source,
            output_file=episode.destination,
            title=self.converted_title,
            season_text=profile.get_season_text(episode.episode_info),
            episode_text=profile.get_episode_text(episode),
            hide_season=profile.hide_season_title,
            **profile.font.get_attributes(),
            **extra_characteristics,
        )

        # File associated with this card is the episode's destination
        self.file = episode.destination


    @staticmethod
    def __replace_illegal_characters(filename: str) -> str:
        """
        Replace the given filename's illegal characters with their legal
        counterparts.
        
        :param      filename:   The filename (as a string) to modify.
        
        :returns:   The modified filename.
        """

        return filename.translate(str.maketrans(TitleCard.__ILLEGAL_CHARACTERS))

        
    @staticmethod
    def get_output_filename(format_string: str, series_info: 'SeriesInfo', 
                            episode_info: 'EpisodeInfo',
                            media_directory: 'Path') -> 'Path':
        """
        Get the output filename for a title card described by the given values.
        
        :param      format_string:      Format string that specifies how to 
                                        construct the filename.
        :param      series_info:        SeriesInfo for this entry.
        :param      episode_info:       EpisodeInfo to get filename of.
        :param      media_directory:    Top-level media directory.
        
        :returns:   Path for the full title card destination.
        """
        
        # Get the season folder for this entry's season
        season_folder = global_preferences.pp.get_season_folder(
            episode_info.season_number
        )
        
        # Get filename from the given format string, with illegals removed
        filename = TitleCard.__replace_illegal_characters(
            format_string.format(
                name=series_info.name,
                full_name=series_info.full_name,
                year=series_info.year,
                season=episode_info.season_number,
                episode=episode_info.episode_number,
                title=episode_info.title.full_title,
            )
        )
        
        # Add card extension
        filename += TitleCard.OUTPUT_CARD_EXTENSION
        
        return media_directory / season_folder / filename


    @staticmethod
    def get_multi_output_filename(format_string: str, series_info: 'SeriesInfo',
                                  multi_episode: 'MultiEpisode',
                                  media_directory: 'Path') -> 'Path':
        """
        Get the output filename for a title card described by the given values,
        and that represents a range of Episodes (not just one).
        
        :param      format_string:      Format string that specifies how to
                                        construct the filename.
        :param      series_info:        Series info for this entry.
        :param      multi_episode:      MultiEpisode object to get filename of.
        :param      media_directory:    Top-level media directory.

        :returns:   Path to the full title card destination.
        """

        # If there is an episode key to modify, do so
        if '{episode' in format_string:
            # Replace existing episode number reference with episode start number
            mod_format_string=format_string.replace('{episode','{episode_start')

            # Episode number formatting with prefix
            episode_text = match(
                r'.*?(e?{episode_start.*?})',
                mod_format_string,
                IGNORECASE
            ).group(1)

            # Duplicate episode text format for end text format
            end_episode_text=episode_text.replace('episode_start','episode_end')

            # Range of episode numbers
            range_text = f'{episode_text}-{end_episode_text}'

            # Completely modified format string with keys for start/end episodes
            modified_format_string = sub(r'e?{episode_start.*?}', range_text,
                                         mod_format_string, flags=IGNORECASE)
        else:
            # No episode key to modify, format the original string
            modified_format_string = format_string

        # # Get the season folder for these episodes
        season_folder = global_preferences.pp.get_season_folder(
            multi_episode.season_number
        )

        # Get filename from the modified format string
        filename = TitleCard.__replace_illegal_characters(
            modified_format_string.format(
                name=series_info.name,
                full_name=series_info.full_name,
                year=series_info.year,
                season=multi_episode.season_number,
                episode_start=multi_episode.episode_start,
                episode_end=multi_episode.episode_end,
                title=multi_episode.episode_info.title.full_title,
            )
        )

        # Add card extension
        filename += TitleCard.OUTPUT_CARD_EXTENSION
        
        return media_directory / season_folder / filename


    @staticmethod
    def validate_card_format_string(format_string: str) -> bool:
        """
        Return whether the given card filename format string is valid or not.
        
        :param      format_string:  Format string being validated.
        
        :returns:   True if the given string can be formatted, False otherwise.
        """
        
        try:
            # Attempt to format using all the standard keys
            format_string.format(
                name='TestName', full_name='TestName (2000)', year=2000,
                season=1, episode=1, title='Episode Title',
            )
            return True
        except Exception as e:
            # Invalid format string, log
            log.error(f'Card format string is invalid - "{e}"')
            return False


    def create(self) -> bool:
        """
        Create this title card. If the card already exists, a new one is not 
        created. Return whether a card was created.

        :returns:   True if a title card was created, False otherwise.
        """

        # If the card already exists, exit
        if self.file.exists():
            return False

        # If the input source doesn't exist, exit
        if not self.episode.source.exists():
            return False
            
        # Create card, return whether it was successful
        self.maker.create()
        
        if self.file.exists():
            log.debug(f'Created card "{self.file.resolve()}"')
            return True

        log.debug(f'Could not create card "{self.file.resolve()}"')
        return False
        