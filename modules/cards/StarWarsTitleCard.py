from pathlib import Path
from re import match
from typing import Optional

from num2words import num2words

from modules.BaseCardType import BaseCardType
from modules.Debug import log

SeriesExtra = Optional

class StarWarsTitleCard(BaseCardType):
    """
    This class describes a type of ImageMaker that produces title cards
    in the theme of Star Wars cards as designed by reddit user
    /u/Olivier_286.
    """

    """API Parameters"""
    API_DETAILS = {
        'name': 'Star Wars',
        'example': '/assets/cards/star wars.jpg',
        'creators': ['/u/Olivier_286', 'CollinHeist'],
        'source': 'local',
        'supports_custom_fonts': False,
        'supports_custom_seasons': False,
        'supported_extras': [
        ], 'description': [
            'Title cards intended for Star Wars (or more generically Space-themed) shows.',
            'Similar to the Olivier title card, these cards feature left-aligned title and episode text',
            'A star-filled gradient overlay is applied to the source image.',
        ],
    }

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'star_wars'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 16,   # Character count to begin splitting titles
        'max_line_count': 5,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses top heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Monstice-Base.ttf').resolve())
    TITLE_COLOR = '#DAC960'
    FONT_REPLACEMENTS = {'Ō': 'O', 'ō': 'o'}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'EPISODE {episode_number}'
    EPISODE_TEXT_COLOR = '#AB8630'
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'HelveticaNeue.ttc'
    EPISODE_NUMBER_FONT = REF_DIRECTORY / 'HelveticaNeue-Bold.ttf'

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = False

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Star Wars Style'

    """Path to the reference star image to overlay on all source images"""
    __STAR_GRADIENT_IMAGE = REF_DIRECTORY / 'star_gradient.png'

    """Paths to intermediate files that are deleted after the card is created"""
    __SOURCE_WITH_STARS = BaseCardType.TEMP_DIR / 'source_gradient.png'

    __slots__ = (
        'source_file', 'output_file', 'title', 'hide_episode_text', 
        'episode_prefix', 'episode_text', 'blur'
    )

    def __init__(self, source: Path, output_file: Path, title: str,
            episode_text: str,
            blur: bool=False,
            grayscale: bool=False,
            **unused) -> None:
        """
        Initialize the CardType object.

        Args:
            source: Source image for this card.
            output_file: Output filepath for this card.
            title: The title for this card.
            episode_text: The episode text for this card.
            blur: Whether to blur the source image.
            grayscale: Whether to make the source image grayscale.
            kwargs: Unused arguments.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        # Store source and output file
        self.source_file = source
        self.output_file = output_file

        # Store episode title
        self.title = self.image_magick.escape_chars(title.upper())

        # Modify episode text to remove "Episode"-like text, replace numbers
        # with text, strip spaces, and convert to uppercase
        self.hide_episode_text = len(episode_text) == 0
        if self.hide_episode_text:
            self.episode_prefix = None
            self.episode_text = self.image_magick.escape_chars(episode_text)
        else:
            self.episode_prefix = 'EPISODE'
            self.episode_text = self.image_magick.escape_chars(
                self.__modify_episode_text(episode_text)
            )


    def __modify_episode_text(self, text: str) -> str:
        """
        Modify the given episode text (such as "EPISODE 1" or
        "CHAPTER 1") to fit the theme of this card. This removes preface
        text like episode, chapter, or part; and converts numeric
        episode numbers to their text equivalent. For example:

        >>> self.__modify_episode_text('Episode 9')
        'NINE'
        >>> self.__modify_episode_text('PART 14')
        'FOURTEEN'

        Args:
            text: The episode text to modify.

        Returns:
            The modified episode text with preface text removed, numbers
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
            self.episode_prefix = 'PART'
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

        Args:
            source: The source image to modify.

        Returns:
            Path to the created image.
        """

        command = ' '.join([
            f'convert "{source.resolve()}"',
            *self.resize_and_style,
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

        Returns:
            List of ImageMagick commands.
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
        ImageMagick commands to add the episode prefix text to an image.
        This is either "EPISODE" or "CHAPTER".

        Returns:
            List of ImageMagick commands.
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

        Returns:
            List of ImageMagick commands.
        """

        # Get variable horizontal offset based of episode prefix
        text_offset = {'EPISODE': 720, 'CHAPTER': 720, 'PART': 570}
        offset = text_offset[self.episode_prefix]

        return [
            f'-gravity west',
            f'-font "{self.EPISODE_NUMBER_FONT.resolve()}"',
            f'-pointsize 53',
            f'-kerning 19',
            f'-annotate +{offset}-140 "{self.episode_text}"',
        ]


    def __add_only_title(self, gradient_source: Path) -> Path:
        """
        Add the title to the given image.

        Args:
            gradient_source: Source image with starry gradient overlaid.

        Returns:
            List of ImageMagick commands.
        """

        command = ' '.join([
            f'convert "{gradient_source.resolve()}"',
            *self.__add_title_text(),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output_file


    def __add_all_text(self, gradient_source: Path) -> Path:
        """
        Add the title, "EPISODE" prefix, and episode text to the given
        image.

        Args:
            gradient_source: Source image with starry gradient overlaid.

        Returns:
            List of ImageMagick commands.
        """

        command = ' '.join([
            f'convert "{gradient_source.resolve()}"',
            *self.__add_title_text(),
            *self.__add_episode_prefix(),
            *self.__add_episode_number_text(),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output_file


    @staticmethod
    def is_custom_font(font: 'Font') -> bool:
        """
        Determines whether the given arguments represent a custom font
        for this card.

        Args:
            font: The Font being evaluated.

        Returns:
            False, as fonts are not customizable with this card.
        """

        return False


    @staticmethod
    def is_custom_season_titles(custom_episode_map: bool, 
                                episode_text_format: str) -> bool:
        """
        Determines whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        standard_etf = StarWarsTitleCard.EPISODE_TEXT_FORMAT.upper()

        return episode_text_format.upper() != standard_etf


    def create(self) -> None:
        """Create the title card as defined by this object."""

        # Add the starry gradient to the source image
        star_image = self.__add_star_gradient(self.source_file)

        # Add text to starry image, result is output
        if self.hide_episode_text:
            self.__add_only_title(star_image)
        else:
            self.__add_all_text(star_image)

        # Delete all intermediate images
        self.image_magick.delete_intermediate_images(star_image)