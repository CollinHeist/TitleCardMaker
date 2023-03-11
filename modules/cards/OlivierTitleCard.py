from pathlib import Path
from typing import Any, Optional

from modules.BaseCardType import BaseCardType
from modules.Debug import log

SeriesExtra = Optional

class OlivierTitleCard(BaseCardType):
    """
    This class describes a type of ImageMaker that produces title cards in the
    style of those designed by Reddit user /u/Olivier_286.
    """

    """API Parameters"""
    API_DETAILS = {
        'name': 'Olivier',
        'example': '/assets/cards/olivier.jpg',
        'creators': ['/u/Olivier_286', 'CollinHeist'],
        'source': 'local',
        'supports_custom_fonts': True,
        'supports_custom_seasons': True,
        'supported_extras': [
            {'name': 'Episode Text Color',
             'identifier': 'episode_text_color',
             'description': 'Color to utilize for the episode text'},
            {'name': 'Stroke Text Color',
             'identifier': 'stroke_color',
             'description': 'Custom color to use for the stroke on the title text'},
        ], 'description': [
            'Title card with left-aligned title and episode text.',
            'This card is structurally very similar to the StarWarsTitleCard, except it allows for custom fonts and does not feature the star gradient overlay.',
        ],
    }

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'olivier'
    SW_REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'star_wars'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 16,   # Character count to begin splitting titles
        'max_line_count': 5,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses top heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Montserrat-Bold.ttf').resolve())
    TITLE_COLOR = 'white'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'EPISODE {episode_number_cardinal}'
    EPISODE_TEXT_COLOR = 'white'
    EPISODE_PREFIX_FONT = SW_REF_DIRECTORY / 'HelveticaNeue.ttc'
    EPISODE_NUMBER_FONT = SW_REF_DIRECTORY / 'HelveticaNeue-Bold.ttf'

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = False

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Olivier Style'

    __slots__ = (
        'source_file', 'output_file', 'title', 'hide_episode_text', 
        'episode_prefix', 'episode_text', 'font', 'title_color',
        'episode_text_color', 'font_size', 'stroke_width', 'kerning',
        'vertical_shift', 'interline_spacing', 'stroke_color',
    )

    def __init__(self, source: Path, output_file: Path, title: str,
            episode_text: str, font: str, title_color: str,
            font_size: float=1.0,
            stroke_width: float=1.0,
            vertical_shift: int=0,
            interline_spacing: int=0,
            kerning: float=1.0,
            blur: bool=False,
            grayscale: bool=False,
            episode_text_color: SeriesExtra[str]=EPISODE_TEXT_COLOR,
            stroke_color: SeriesExtra[str]='black',
            **unused) -> None:
        """
        Construct a new instance of this card.

        Args:
            source: Source image to base the card on.
            output_file: Output file where to create the card.
            title: Title text to add to created card.
            episode_text: Episode text to add to created card.
            font: Font name or path (as string) to use for episode title.
            title_color: Color to use for title text.
            interline_spacing: Pixel count to adjust title interline spacing by.
            kerning: Scalar to apply to kerning of the title text.
            font_size: Scalar to apply to title font size.
            stroke_width: Scalar to apply to black stroke of the title text.
            vertical_shift: Pixel count to adjust the title vertical offset by.
            blur: Whether to blur the source image.
            grayscale: Whether to make the source image grayscale.
            episode_text_color: Color to use for the episode text.
            stroke_color: Color to use for the back-stroke color.
            unused: Unused arguments.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        # Store source and output file
        self.source_file = source
        self.output_file = output_file

        # Store attributes of the text
        self.title = self.image_magick.escape_chars(title)
        self.hide_episode_text = len(episode_text) == 0

        # Determine episode prefix, modify text to remove prefix
        self.episode_prefix = None
        if not self.hide_episode_text and ' ' in episode_text:
            prefix, number = episode_text.split(' ', 1)
            self.episode_prefix = prefix.upper()
            episode_text = number
        else:
            episode_text = episode_text
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())

        # Font customizations
        self.font = font
        self.title_color = title_color
        self.font_size = font_size
        self.stroke_width = stroke_width
        self.vertical_shift = vertical_shift
        self.interline_spacing = interline_spacing
        self.kerning = kerning

        # Optional extras
        self.episode_text_color = episode_text_color
        self.stroke_color = stroke_color


    @property
    def title_text_command(self) -> list[str]:
        """
        Get the ImageMagick commands to add the episode title text to an image.

        Returns:
            List of ImageMagick commands.
        """

        font_size = 124 * self.font_size
        stroke_width = 8.0 * self.stroke_width
        kerning = 0.5 * self.kerning
        interline_spacing = -20 + self.interline_spacing
        vertical_shift = 785 + self.vertical_shift

        return [
            f'\( -font "{self.font}"',
            f'-gravity northwest',
            f'-pointsize {font_size}',
            f'-kerning {kerning}',
            f'-interline-spacing {interline_spacing}',
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width}',
            f'-annotate +320+{vertical_shift} "{self.title}" \)',
            f'\( -fill "{self.title_color}"',
            f'-stroke "{self.title_color}"',
            f'-strokewidth 0',
            f'-annotate +320+{vertical_shift} "{self.title}" \)',
        ]


    @property
    def episode_prefix_command(self) -> list[str]:
        """
        Get the ImageMagick commands to add the episode prefix text to an image.

        Returns:
            List of ImageMagick commands.
        """

        # No episode prefix/text, return empty command
        if self.episode_prefix is None or self.hide_episode_text:
            return []

        return [
            f'-gravity west',
            f'-font "{self.EPISODE_PREFIX_FONT.resolve()}"',
            f'-pointsize 60',
            f'-kerning 19',
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 5',
            f'-annotate +325-150 "{self.episode_prefix}"',
            f'-fill "{self.episode_text_color}"',
            f'-stroke "{self.episode_text_color}"',
            f'-strokewidth 0',
            f'-annotate +325-150 "{self.episode_prefix}"',
        ]


    @property
    def episode_number_text_command(self) -> list[str]:
        """
        Get the ImageMagick commands to add the episode number text to an image.

        Returns:
            List of ImageMagick commands.
        """

        # No episode text, return empty command
        if self.hide_episode_text:
            return []

        # Get variable horizontal offset based of episode prefix
        text_offset = {'EPISODE': 425, 'CHAPTER': 425, 'PART': 275}
        if self.episode_prefix is None:
            offset = 0
        elif self.episode_prefix in text_offset.keys():
            offset = text_offset[self.episode_prefix]
        else:
            offset_per_char = text_offset['EPISODE'] / len('EPISODE')
            offset = offset_per_char * len(self.episode_prefix) * 1.10

        return [
            f'-gravity west',
            f'-font "{self.EPISODE_NUMBER_FONT.resolve()}"',
            f'-pointsize 60',
            f'-kerning 19',
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 7',
            f'-annotate +{325+offset}-150 "{self.episode_text}"',
            f'-fill "{self.episode_text_color}"',
            f'-stroke "{self.episode_text_color}"',
            f'-strokewidth 1',
            f'-annotate +{325+offset}-150 "{self.episode_text}"',
        ]


    @staticmethod
    def modify_extras(extras: dict[str, Any], custom_font: bool,
                      custom_season_titles: bool) -> None:
        """
        Modify the given extras based on whether font or season titles are
        custom.

        Args:
            extras: Dictionary to modify.
            custom_font: Whether the font are custom.
            custom_season_titles: Whether the season titles are custom.
        """

        # Generic font, reset custom episode text color and stroke color
        if not custom_font:
            if 'episode_text_color' in extras:
                extras['episode_text_color'] =\
                    OlivierTitleCard.EPISODE_TEXT_COLOR
            if 'stroke_color' in extras:
                extras['stroke_color'] = 'black'


    @staticmethod
    def is_custom_font(font: 'Font') -> bool:
        """
        Determine whether the given arguments represent a custom font for this
        card.

        Args:
            font: The Font being evaluated.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.file != OlivierTitleCard.TITLE_FONT)
            or (font.size != 1.0)
            or (font.color != OlivierTitleCard.TITLE_COLOR)
            or (font.vertical_shift != 0)
            or (font.interline_spacing != 0)
            or (font.kerning != 1.0)
            or (font.stroke_width != 1.0))


    @staticmethod
    def is_custom_season_titles(custom_episode_map: bool, 
                                episode_text_format: str) -> bool:
        """
        Determine whether the given attributes constitute custom or generic
        season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if the episode map or episode text format is custom, False
            otherwise.
        """

        standard_etf = OlivierTitleCard.EPISODE_TEXT_FORMAT.upper()

        return episode_text_format.upper() != standard_etf


    def create(self) -> None:
        """Create the title card as defined by this object."""

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            *self.resize_and_style,
            *self.title_text_command,
            *self.episode_prefix_command,
            *self.episode_number_text_command,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)