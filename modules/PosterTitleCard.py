from pathlib import Path
from re import match

from modules.BaseCardType import BaseCardType
from modules.Debug import log

class PosterTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards in the
    style of the Gundam series of cards produced by Reddit user
    /u/battleoflight.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'poster_card'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 16,   # Character count to begin splitting titles
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

    """This card doesn't use unique sources (uses posters)"""
    USES_UNIQUE_SOURCES = False

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Poster Style'

    """Custom blur profile for the poster"""
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
        
        Args:
            source: Source image for this card.
            output_file: Output filepath for this card.
            title: The title for this card.
            episode_text: The episode text for this card.
            season_number: Season number of the episode associated with this
                card.
            episode_number: Episode number of the episode associated with this
                card.
            blur: Whether to blur the source image.
            logo: Filepath (or file format) to the logo file.
            kwargs: Unused arguments to permit generalized function calls for
                any CardType.
        """
        
        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__()

        # Store source and output file
        self.source_file = source
        self.output_file = output_file

        # Look for logo if it's a format string
        if isinstance(logo, str):
            # Attempt to modify as if it's a format string
            try:
                logo = logo.format(season_number=season_number,
                                   episode_number=episode_number)
            except Exception:
                # Bad format strings will be caught during card creation
                pass

            self.logo = Path(logo)
        elif isinstance(logo, Path):
            self.logo = logo
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
        
        Args:
            font: The Font being evaluated.
        
        returns:
            False, as fonts are not customizable with this card.
        """

        return False


    @staticmethod
    def is_custom_season_titles(episode_text_format: str,
                                *args, **kwargs) -> bool:
        """
        Determines whether the given attributes constitute custom or generic
        season titles.
        
        Args:
            episode_text_format: The episode text format in use.
            args and kwargs: Generic arguments to permit  generalized function
                calls for any CardType.
        
        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        return episode_text_format != PosterTitleCard.EPISODE_TEXT_FORMAT


    def create(self) -> None:
        """Create the title card as defined by this object."""

        # If no logo is specified, create empty logo command
        if self.logo is None:
            title_offset = 0
            logo_command = ''
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

            # Adjust title offset to center in smaller space (due to logo)
            title_offset = (450 / 2) - (50 / 2)

        # Single command to create card
        command = ' '.join([
            f'convert',
            # Resize and optionally blur source image
            f'"{self.source_file.resolve()}"',
            f'-resize "x1800"',
            f'-extent "3200x1800"',
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            # Add gradient overlay
            f'"{self.__GRADIENT_OVERLAY.resolve()}"',
            f'-flatten',
            # Optionally add logo
            *logo_command,
            # Add episode text
            f'-gravity south',
            f'-font "{self.TITLE_FONT}"',
            f'-pointsize 75',
            f'-fill "#FFFFFF"',
            f'-annotate +649+50 "{self.episode_text}"',
            # Add title text
            f'-gravity center',                         
            f'-pointsize 165',
            f'-interline-spacing -40', 
            f'-annotate +649+{title_offset} "{self.title}"',
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)