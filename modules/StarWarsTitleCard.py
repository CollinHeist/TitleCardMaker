from pathlib import Path

from num2words import num2words

from modules.CardType import CardType

class StarWarsTitleCard(CardType):
    """
    This class describes a type of ImageMaker that produces title cards in the
    theme of Star Wars cards as designed by reddit user /u/Olivier_286. These
    cards are not as customizeable as the standard template.
    """

    """Path to the font to use for the episode title"""
    TITLE_FONT =str((Path(__file__).parent/'ref'/'Monstice-Base.ttf').resolve())

    """Color to use for the episode title"""
    TITLE_COLOR = '#DAC960'

    """Color of the episode/episode number text"""
    EPISODE_TEXT_COLOR = '#AB8630'

    """Standard font replacements for the title font"""
    FONT_REPLACEMENTS = {'Ō': 'O', 'ō': 'o'}

    """After how many characters to split an episode title into two lines"""
    MAX_LINE_LENGTH = 18

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = False

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Star Wars Style'

    """Path to the reference star image to overlay on all source images"""
    __STAR_GRADIENT_IMAGE = Path(__file__).parent / 'ref' / 'star_gradient.png'

    """Path to the source+gradient image"""
    __SOURCE_WITH_STARS = Path(__file__).parent/'.objects'/'source_gradient.png'

    """Path to the font to use for the episode/episode number text """
    EPISODE_TEXT_FONT = Path(__file__).parent / 'ref' / 'HelveticaNeue.ttc'
    EPISODE_NUMBER_FONT = Path(__file__).parent / 'ref'/'HelveticaNeue-Bold.ttf'

    
    def __init__(self, source: Path, output_file: Path, title_top_line: str,
                 title_bottom_line: str, episode_text: str,
                 *args: tuple, **kwargs: dict) -> None:
        """
        Constructs a new instance.
        
        :param      source:        The source
        :param      output_file:   The output file
        :param      title:         The title
        :param      episode_text:  The episode text
        :param      args:          The arguments
        :param      kwargs:        The keywords arguments
        """
        
        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__()

        # Store source and output file
        self.source_file = source
        self.output_file = output_file

        # Store episode title
        if title_top_line in ('', None):
            self.title = f'{title_bottom_line}'.upper().strip()
        else:
            self.title =f'{title_top_line}\n{title_bottom_line}'.upper().strip()

        # Modify episode text to remove "Episode"-like text, replace numbers
        # with text, strip spaces, and convert to uppercase
        self.episode_text = self.__modify_episode_text(episode_text)


    def __modify_episode_text(self, text: str) -> str:
        """
        Amend the given episode text (such as "EPISODE 1" or "CHAPTER 1") to fit
        the theme of this card. This removes preface text like episode, chapter,
        or part; and converts numeric episode numbers to their text equivalent.
        For example:

        >>> self.__modify_episode_text('Episode 9')
        'NINE'
        >>> self.__modify_episode_text('PART 14')
        'FOURTEEN'
        
        :param      text:  The episode text to modify.
        
        :returns:   The modified episode text with preface text removed, 
                    numbers replaced with words, and converted to uppercase. If
                    numbers cannot be replaced, that step is skipped.
        """

        # Convert to uppercase, remove space padding
        modified_text = text.upper().strip()

        # Remove preface text
        for to_remove in ['CHAPTER', 'EPISODE', 'PART']:
            modified_text = modified_text.replace(to_remove, '')

        try:
            return num2words(int(modified_text.strip())).upper()
        except ValueError:
            return modified_text.strip()


    def __add_star_gradient(self, source: Path) -> Path:
        """
        Add the star gradient to the given source image.
        
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
        ImageMagick commands to add the "EPISODE" prefix text to an image.
        
        :returns:   List of ImageMagick commands.
        """

        return [
            f'-gravity west',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-fill "{self.EPISODE_TEXT_COLOR}"',
            f'-pointsize 53',
            f'-kerning 19',
            f'-annotate +325-140 "EPISODE"',
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
            f'convert {gradient_source.resolve()}',
            *self.__add_title_text(),
            *self.__add_episode_prefix(),
            *self.__add_episode_number_text(),
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output_file


    @staticmethod
    def split_title(title: str) -> (str, str):
        """
        Splits a title.
        
        :param      title:  The title
        
        :returns:   { description_of_the_return_value }
        """

        return CardType._split_at_width(
            title,
            StarWarsTitleCard.MAX_LINE_LENGTH
        )


    @staticmethod
    def is_custom_font(*args, **kwargs) -> bool:
        """
        Determines whether the given arguments represent a custom font for this
        card. This CardType does not use custom fonts, so this is always False.
        
        :param      args and kwargs:    Generic arguments to permit generalized
                                        function calls for any CardType.
        
        :returns:   False, as fonts are not customizable with this card.
        """

        return False


    @staticmethod
    def is_custom_season_titles(*args, **kwargs) -> bool:
        """
        Determines if custom season titles.
        
        :param      args and kwargs:    Generic arguments to permit generalized
                                        function calls for any CardType.
        
        :returns:  False, as season titles are not customizable with this card.
        """

        return False


    def create(self) -> None:
        """Create the title card as defined by this object."""

        star_image = self.__add_star_gradient(self.source_file)

        # Create the output directory and any necessary parents 
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Add text to starry image, result is output
        output_file = self.__add_text(star_image)

        # Delete all intermediate images
        self.image_magick.delete_intermediate_images(star_image)

        