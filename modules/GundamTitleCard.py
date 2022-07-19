from pathlib import Path
from re import match

from modules.CardType import CardType
from modules.Debug import log

class GundamTitleCard(CardType):
    """
    This class describes a type of CardType that produces title cards in the
    style of the Gundam series of cards produced by Reddit user
    /u/battleoflight.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'gundam'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 15,   # Character count to begin splitting titles
        'max_line_count': 5,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses top heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Amuro.otf').resolve())
    TITLE_COLOR = '#FFFFFF'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'Ep. {episode_number}'
    EPISODE_TEXT_COLOR = '#FFFFFF'
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Amuro.otf'

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = False

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Gundam Style'

    BLUR_PROFILE = '0x30'

    """Path to the reference star image to overlay on all source images"""
    __GRADIENT_OVERLAY = REF_DIRECTORY / 'stars-overlay.png'


    __slots__ = ('source_file', 'output_file', 'logo', 'title', 'episode_text',
                 'blur')

    
    def __init__(self, source: Path, output_file: Path, title: str,
                 episode_text: str, season_number: int=1, episode_number: int=1,
                 blur: bool=False, logo: str=None, **kwargs) -> None:
        """
        Initialize the CardType object.
        
        :param      source:         Source image for this card.
        :param      output_file:    Output filepath for this card.
        :param      title:          The title for this card.
        :param      episode_text:   The episode text for this card.
        :param      season_number:  Season number of the episode associated with
                                    this card.
        :param      episode_number: Episode number of the episode associated
                                    with this card.
        :param      blur:           Whether to blur the source image.
        :param      logo:           Filepath (or file format) to the logo file.
        :param      kwargs:         Unused arguments to permit generalized
                                    function calls for any CardType.
        """
        
        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__()

        # Store source and output file
        self.source_file = source
        self.output_file = output_file

        # Look for logo if it's a format string
        if isinstance(logo, str):
            try:
                logo = logo.format(season_number=season_number,
                                   episode_number=episode_number)
            except Exception:
                pass
            
            # Use either original or modified logo file
            self.logo = Path(logo)
        else:
            self.logo = None

        # Store text
        self.title = self.image_magick.escape_chars(title.upper())
        self.episode_text = self.image_magick.escape_chars(episode_text)

        # Store blur flag
        self.blur = blur


    @staticmethod
    def is_custom_font(font: 'Font') -> bool:
        """
        Determines whether the given arguments represent a custom font for this
        card. This CardType does not use custom fonts, so this is always False.
        
        :param      font:   The Font being evaluated.
        
        :returns:   False, as fonts are not customizable with this card.
        """

        return False


    @staticmethod
    def is_custom_season_titles(episode_text_format: str,
                                *args, **kwargs) -> bool:
        """
        Determines whether the given attributes constitute custom or generic
        season titles.
        
        :param      episode_text_format:    The episode text format in use.
        :param      args and kwargs:        Generic arguments to permit 
                                            generalized function calls for any
                                            CardType.
        
        :returns:   True if custom season titles are indicated, False otherwise.
        """

        return episode_text_format != GundamTitleCard.EPISODE_TEXT_FORMAT


    def create(self) -> None:
        """Create the title card as defined by this object."""

        # If no logo is specified, create empty logo command
        if self.logo is None:
            logo_command = '',
        elif not self.logo.exists():
            # Logo specified, but DNE, error and exit
            log.error(f'Logo file "{self.logo.resolve()}" does not exist')
            return None
        else:
            # Logo specified and exists, create command to resize and add image
            logo_command = [
                f'-gravity north',
                f'\( "{self.logo.resolve()}"',
                f'-resize x450',
                f'-resize 1775x450\> \)',
                f'-geometry +649+50',
                f'-composite',
            ]

        command = ' '.join([
            f'convert',
            f'"{self.source_file.resolve()}"',          # Resize source image
            f'-resize "x1800"',
            f'-extent "3200x1800"',
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            f'"{self.__GRADIENT_OVERLAY.resolve()}"',   # Add gradient overlay
            f'-flatten',                                # Combine images
            *logo_command,                              # Optionally add logo
            f'-gravity south',                          # Add episode text
            f'-font "{self.TITLE_FONT}"',
            f'-pointsize 100',
            f'-fill "#FFFFFF"',
            f'-annotate +649+50 "{self.episode_text}"',
            f'-gravity center',                         # Add title text
            f'-pointsize 165',
            f'-annotate +649+0 "{self.title}"',
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        