from pathlib import Path
from re import match

from num2words import num2words

from modules.CardType import CardType
from modules.Debug import log

class StarWarsTitleCard(CardType):
    """
    This class describes a type of ImageMaker that produces title cards in the
    theme of Star Wars cards as designed by reddit user /u/Olivier_286. These
    cards are not as customizable as the standard template.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'star_wars'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 16,   # Character count to begin splitting titles
        'max_line_count': 5,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses top heavy titling
    }

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Star Wars Style'

    """Path to the font to use for the episode title"""
    TITLE_FONT = str((REF_DIRECTORY/'Monstice-Base.ttf').resolve())

    """Color to use for the episode title"""
    TITLE_COLOR = '#DAC960'

    """Color of the episode/episode number text"""
    EPISODE_TEXT_COLOR = '#AB8630'

    """Standard font replacements for the title font"""
    FONT_REPLACEMENTS = {'Ō': 'O', 'ō': 'o'}

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = False

    """Path to the reference star image to overlay on all source images"""
    __STAR_GRADIENT_IMAGE = REF_DIRECTORY / 'star_gradient.png'

    """Path to the font to use for the episode/episode number text """
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'HelveticaNeue.ttc'
    EPISODE_NUMBER_FONT = REF_DIRECTORY / 'HelveticaNeue-Bold.ttf'

    """Paths to intermediate files that are deleted after the card is created"""
    __SOURCE_WITH_STARS = CardType.TEMP_DIR / 'source_gradient.png'

    
    def __init__(self, source: Path, output_file: Path, title: str,
                 episode_text: str, *args: tuple, **kwargs: dict) -> None:
        """
        Constructs a new instance.
        
        :param      source:             Source image for this card.
        :param      output_file:        Output filepath for this card.
        :param      title:              The title for this card.
        :param      episode_text:       The episode text for this card.
        :param      args and kwargs:    Unused arguments to permit generalized
                                        function calls for any CardType.
        """
        
        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__()

        # Store source and output file
        self.source_file = source
        self.output_file = output_file

        # Store episode title
        self.title = self.image_magick.escape_chars(title.upper())
        
        # Modify episode text to remove "Episode"-like text, replace numbers
        # with text, strip spaces, and convert to uppercase
        self.episode_prefix = 'EPISODE'
        self.episode_text = self.image_magick.escape_chars(
            self.__modify_episode_text(episode_text)
        )


    def __modify_episode_text(self, text: str) -> str:
        """
        Modify the given episode text (such as "EPISODE 1" or "CHAPTER 1") to fit
        the theme of this card. This removes preface text like episode, chapter,
        or part; and converts numeric episode numbers to their text equivalent.
        For example:

        >>> self.__modify_episode_text('Episode 9')
        'NINE'
        >>> self.__modify_episode_text('PART 14')
        'FOURTEEN'
        
        :param      text:   The episode text to modify.
        
        :returns:   The modified episode text with preface text removed, numbers
                    replaced with words, and converted to uppercase. If numbers
                    cannot be replaced, that step is skipped.
        """

        # Convert to uppercase, remove space padding
        modified_text = text.upper().strip()

        # Remove preface text - if CHAPTER or EPISODE, set object episode prefix
        if match(rf'CHAPTER\s*(\d+)', modified_text):
            self.episode_prefix = 'CHAPTER'
            modified_text = modified_text.replace('CHAPTER', '')
        elif match(rf'EPISODE\s*(\d+)', modified_text):
            self.episode_prefix = 'EPISODE'
            modified_text = modified_text.replace('EPISODE', '')
        elif match(rf'PART\s*(\d+)', modified_text):
            modified_text = modified_text.replace('PART', '')

        try:
            # Only digit episode text remains, return as a number (i.e. "two")
            return num2words(int(modified_text.strip())).upper()
        except ValueError:
            # Not just a digit, return as-is
            return modified_text.strip()


    def __add_star_gradient(self, source: Path) -> Path:
        """
        Add the static star gradient to the given source image.
        
        :param      source: The source image to modify.
        
        :returns:   Path to the created image.
        """

        command = ' '.join([
            f'convert "{source.resolve()}"',
            f'+profile "*"',    # To avoid profile conversion warnings
            f'-gravity center', # For images that aren't in 4x3, center crop
            f'-resize "{self.TITLE_CARD_SIZE}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            f'"{self.__STAR_GRADIENT_IMAGE.resolve()}"',
            f'-background None',
            f'-layers Flatten',
            f'"{self.__SOURCE_WITH_STARS.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__SOURCE_WITH_STARS


    def __add_title_text(self) -> list:
        """
        ImageMagick commands to add the episode title text to an image.
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-font "{self.TITLE_FONT}"',
            f'-gravity northwest',
            f'-pointsize 124',
            f'-kerning 0.5',
            f'-interline-spacing 20',
            f'-fill "{self.TITLE_COLOR}"',
            f'-annotate +320+829 "{self.title}"',
        ]


    def __add_episode_prefix(self) -> list:
        """
        ImageMagick commands to add the episode prefix text to an image. This is
        either "EPISODE" or "CHAPTER".
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-gravity west',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-fill "{self.EPISODE_TEXT_COLOR}"',
            f'-pointsize 53',
            f'-kerning 19',
            f'-annotate +325-140 "{self.episode_prefix}"',
        ]


    def __add_episode_number_text(self) -> list:
        """
        ImageMagick commands to add the episode text to an image.
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-gravity west',
            f'-font "{self.EPISODE_NUMBER_FONT.resolve()}"',
            f'-pointsize 53',
            f'-kerning 19',
            f'-annotate +720-140 "{self.episode_text}"',
        ]


    def __add_text(self, gradient_source: Path) -> Path:
        """
        Add the title, "EPISODE" prefix, and episode text to the give image.
        
        :param      gradient_source:    Source image with starry gradient
                                        overlaid.
        
        :returns:   Path to the created image.
        """

        command = ' '.join([
            f'convert "{gradient_source.resolve()}"',
            *self.__add_title_text(),
            *self.__add_episode_prefix(),
            *self.__add_episode_number_text(),
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output_file


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

        generic_formats = ('EPISODE {episode_number}', 'PART {episode_number}')

        return episode_text_format not in generic_formats


    def create(self) -> None:
        """Create the title card as defined by this object."""

        # Add the starry gradient to the source image
        star_image = self.__add_star_gradient(self.source_file)

        # Create the output directory and any necessary parents 
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Add text to starry image, result is output
        output_file = self.__add_text(star_image)

        # Delete all intermediate images
        self.image_magick.delete_intermediate_images(star_image)

        