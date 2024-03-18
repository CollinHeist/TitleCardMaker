from pathlib import Path
from typing import TYPE_CHECKING, Optional

from modules.BaseCardType import BaseCardType, ImageMagickCommands

if TYPE_CHECKING:
    from modules.Font import Font


class OlivierTitleCard(BaseCardType):
    """
    This class describes a type of ImageMaker that produces title cards
    in the style of those designed by Reddit user /u/Olivier_286.
    """

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
    STROKE_COLOR = 'black'

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = False

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Olivier Style'

    """Gradient image"""
    GRADIENT = REF_DIRECTORY.parent / 'overline' / 'small_gradient.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'hide_episode_text',
        'episode_prefix', 'episode_text', 'font_color', 'font_file',
        'font_interline_spacing', 'font_interword_spacing', 'font_kerning',
        'font_size', 'font_stroke_width', 'font_vertical_shift', 'omit_gradient',
        'stroke_color', 'episode_text_color', 'episode_text_font_size',
        'episode_text_vertical_shift',
    )

    def __init__(self,
            source_file: Path,
            card_file: Path,
            title_text: str,
            episode_text: str,
            hide_episode_text: bool = False,
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_stroke_width: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            episode_text_vertical_shift: int = 0,
            omit_gradient: bool = True,
            stroke_color: str = STROKE_COLOR,
            preferences: Optional['Preferences'] = None, # type: ignore
            **unused,
        ) -> None:
        """
        Construct a new instance of this card.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store source and output file
        self.source_file = source_file
        self.output_file = card_file

        # Store attributes of the text
        self.title_text = self.image_magick.escape_chars(title_text)

        # Determine episode prefix, modify text to remove prefix
        self.episode_prefix = None
        self.hide_episode_text = hide_episode_text or len(episode_text) == 0
        if not self.hide_episode_text and ' ' in episode_text:
            prefix, number = episode_text.split(' ', 1)
            self.episode_prefix = prefix.upper()
            episode_text = number
        else:
            episode_text = episode_text
        self.episode_text = self.image_magick.escape_chars(episode_text.upper())

        # Font customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.omit_gradient = omit_gradient
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.episode_text_vertical_shift = episode_text_vertical_shift
        self.stroke_color = stroke_color


    @property
    def gradient_commands(self) -> ImageMagickCommands:
        """
        Subcommand to overlay the gradient to this image. This rotates
        and repositions the gradient overlay based on the text position.
        """

        if self.omit_gradient:
            return []

        return [
            f'\( "{self.GRADIENT.resolve()}"',
            f'-rotate 90 \)',
            f'-geometry -{(self.WIDTH - self.HEIGHT) / 2}+0',
            f'-composite',
        ]


    @property
    def title_text_command(self) -> ImageMagickCommands:
        """
        Get the ImageMagick commands to add the episode title text to an
        image.
        """

        font_size = 124 * self.font_size
        stroke_width = 8.0 * self.font_stroke_width
        kerning = 0.5 * self.font_kerning
        interline_spacing = -20 + self.font_interline_spacing
        vertical_shift = 785 + self.font_vertical_shift

        return [
            f'\( -font "{self.font_file}"',
            f'-gravity northwest',
            f'-pointsize {font_size}',
            f'-kerning {kerning}',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width}',
            f'-annotate +320+{vertical_shift} "{self.title_text}" \)',
            f'\( -fill "{self.font_color}"',
            f'-stroke "{self.font_color}"',
            f'-strokewidth 0',
            f'-annotate +320+{vertical_shift} "{self.title_text}" \)',
        ]


    @property
    def episode_prefix_command(self) -> ImageMagickCommands:
        """
        Get the ImageMagick commands to add the episode prefix text to
        an image.
        """

        # No episode prefix/text, return empty command
        if self.episode_prefix is None or self.hide_episode_text:
            return []

        size = 60 * self.episode_text_font_size
        kerning = 19 * self.episode_text_font_size
        stroke_width = 5 * self.episode_text_font_size
        vertical_shift = -150 + self.episode_text_vertical_shift

        return [
            f'-gravity west',
            f'-font "{self.EPISODE_PREFIX_FONT.resolve()}"',
            f'-pointsize {size}',
            f'-kerning {kerning}',
            f'-fill black',
            f'-stroke black',
            f'-strokewidth {stroke_width}',
            f'-annotate +325{vertical_shift:+} "{self.episode_prefix}"',
            f'-fill "{self.episode_text_color}"',
            f'-stroke "{self.episode_text_color}"',
            f'-strokewidth 0',
            f'-annotate +325{vertical_shift:+} "{self.episode_prefix}"',
        ]


    @property
    def episode_number_text_command(self) -> ImageMagickCommands:
        """
        Get the ImageMagick commands to add the episode number text to
        an image.
        """

        # No episode text, return empty command
        if self.hide_episode_text:
            return []

        # Vertical shift
        kerning = 19 * self.episode_text_font_size
        size = 60 * self.episode_text_font_size
        stroke_width = 7 * self.episode_text_font_size
        vertical_shift = -150 + self.episode_text_vertical_shift

        # Get variable horizontal offset based of episode prefix
        text_offset = {'EPISODE': 425, 'CHAPTER': 425, 'PART': 275}
        if self.episode_prefix is None:
            offset = 0
        elif self.episode_prefix in text_offset:
            offset = text_offset[self.episode_prefix] \
                * self.episode_text_font_size
        else:
            offset_per_char = text_offset['EPISODE'] / len('EPISODE')
            offset = offset_per_char * len(self.episode_prefix) * 1.10\
                * self.episode_text_font_size

        return [
            f'-gravity west',
            f'-font "{self.EPISODE_NUMBER_FONT.resolve()}"',
            f'-pointsize {size}',
            f'-kerning {kerning}',
            f'-fill black',
            f'-stroke black',
            f'-strokewidth {stroke_width}',
            f'-annotate +{325+offset}{vertical_shift:+} "{self.episode_text}"',
            f'-fill "{self.episode_text_color}"',
            f'-stroke "{self.episode_text_color}"',
            f'-strokewidth 1',
            f'-annotate {325+offset:+}{vertical_shift:+} "{self.episode_text}"',
        ]


    @staticmethod
    def modify_extras(
            extras: dict,
            custom_font: bool,
            custom_season_titles: bool,
        ) -> None:
        """
        Modify the given extras based on whether font or season titles
        are custom.

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
            if 'episode_text_font_size' in extras:
                extras['episode_text_font_size'] = 1.0
            if 'episode_text_vertical_shift' in extras:
                extras['episode_text_vertical_shift'] = 0
            if 'stroke_color' in extras:
                extras['stroke_color'] = 'black'


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determine whether the given arguments represent a custom font
        for this card.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        custom_extras = (
            ('episode_text_color' in extras
                and extras['episode_text_color'] != OlivierTitleCard.EPISODE_TEXT_COLOR)
            or ('episode_text_font_size' in extras
                and extras['episode_text_font_size'] != 1.0)
            or ('episode_text_vertical_shift' in extras
                and extras['episode_text_vertical_shift'] != 0)
            or ('stroke_color' in extras
                and extras['stroke_color'] != 'black')
        )

        return (custom_extras
            or ((font.color != OlivierTitleCard.TITLE_COLOR)
            or (font.file != OlivierTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
            or (font.stroke_width != 1.0)
            or (font.vertical_shift != 0))
        )


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> bool:
        """
        Determine whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if the episode map or episode text format is custom,
            False otherwise.
        """

        standard_etf = OlivierTitleCard.EPISODE_TEXT_FORMAT.upper()

        return episode_text_format.upper() != standard_etf


    def create(self) -> None:
        """Create the title card as defined by this object."""

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            *self.resize_and_style,
            # Overlay gradient
            *self.gradient_commands,
            # Add text
            *self.title_text_command,
            *self.episode_prefix_command,
            *self.episode_number_text_command,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
