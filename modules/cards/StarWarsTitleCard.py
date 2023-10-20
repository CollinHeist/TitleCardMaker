from pathlib import Path
from typing import Optional

from modules.BaseCardType import BaseCardType, ImageMagickCommands


class StarWarsTitleCard(BaseCardType):
    """
    This class describes a type of ImageMaker that produces title cards
    in the theme of Star Wars cards as designed by Reddit user
    /u/Olivier_286.
    """

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
    EPISODE_TEXT_FORMAT = 'EPISODE {episode_number_cardinal}'
    EPISODE_TEXT_COLOR = '#AB8630'
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'HelveticaNeue.ttc'
    EPISODE_NUMBER_FONT = REF_DIRECTORY / 'HelveticaNeue-Bold.ttf'

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = False

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Star Wars Style'

    """Path to the reference star image to overlay on all source images"""
    __STAR_GRADIENT_IMAGE = REF_DIRECTORY / 'star_gradient.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'episode_text',
        'hide_episode_text', 'font_color', 'font_file',
        'font_interline_spacing', 'font_interword_spacing', 'font_size',
        'episode_text_color', 'episode_prefix',
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
            font_size: float = 1.0,
            blur: bool = False,
            grayscale: bool = False,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            preferences: Optional['Preferences'] = None, # type: ignore
            **unused,
        ) -> None:
        """
        Initialize the CardType object.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store source and output file
        self.source_file = source_file
        self.output_file = card_file

        # Store episode title
        self.title_text = self.image_magick.escape_chars(title_text.upper())

        # Font customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_size = font_size

        # Attempt to detect prefix text
        self.hide_episode_text = hide_episode_text or len(episode_text) == 0
        if self.hide_episode_text:
            self.episode_prefix, self.episode_text = None, None
        else:
            if ' ' in episode_text:
                prefix, text = episode_text.upper().split(' ', 1)
                self.episode_prefix, self.episode_text = map(
                    self.image_magick.escape_chars,
                    (prefix, text)
                )
            else:
                self.episode_text = None
                self.episode_prefix = self.image_magick.escape_chars(
                    episode_text
                )

        # Extras
        self.episode_text_color = episode_text_color


    @property
    def title_text_command(self) -> ImageMagickCommands:
        """Subcommands to add the episode title text to an image."""

        size = 124 * self.font_size
        interline_spacing = 20 + self.font_interline_spacing

        return [
            f'-font "{self.font_file}"',
            f'-gravity northwest',
            f'-pointsize {size}',
            f'-kerning 0.5',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-fill "{self.font_color}"',
            f'-annotate +320+829 "{self.title_text}"',
        ]


    @property
    def episode_text_command(self) -> ImageMagickCommands:
        """Subcommands to add the episode text to an image."""

        # Hiding episode text, return blank command
        if self.hide_episode_text:
            return []

        return [
            # Global font options
            f'-gravity west',
            f'-pointsize 53',
            f'-kerning 19',
            f'+interword-spacing',
            f'-fill "{self.episode_text_color}"',
            f'-background transparent',
            # Create prefix text
            f'\( -font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'label:"{self.episode_prefix}"',
            # Create actual episode text
            f'-font "{self.EPISODE_NUMBER_FONT.resolve()}"',
            f'label:"{self.episode_text}"',
            # Combine prefix and episode text
            f'+smush 65 \)',
            # Add combined text to image
            f'-geometry +325-140',
            f'-composite',
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

        # Generic font, reset episode text and box colors
        if not custom_font:
            if 'episode_text_color' in extras:
                extras['episode_text_color'] =\
                    StarWarsTitleCard.EPISODE_TEXT_COLOR


    @staticmethod
    def is_custom_font(font: 'Font') -> bool: # type: ignore
        """
        Determines whether the given arguments represent a custom font
        for this card.

        Args:
            font: The Font being evaluated.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.color != StarWarsTitleCard.TITLE_COLOR)
            or (font.file != StarWarsTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.size != 1.0)
        )


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> bool:
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

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles
            *self.resize_and_style,
            # Overlay star gradient
            f'"{self.__STAR_GRADIENT_IMAGE.resolve()}"',
            f'-composite',
            # Add title text
            *self.title_text_command,
            # Add episode text
            *self.episode_text_command,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
