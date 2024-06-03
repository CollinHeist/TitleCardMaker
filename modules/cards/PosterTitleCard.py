from pathlib import Path
from typing import TYPE_CHECKING, Optional

from modules.BaseCardType import BaseCardType
from modules.CleanPath import CleanPath
from modules.Debug import log

if TYPE_CHECKING:
    from modules.PreferenceParser import PreferenceParser
    from modules.Font import Font

SeriesExtra = Optional

class PosterTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards in
    the style of the Gundam series of cards produced by Reddit user
    /u/battleoflight.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'poster_card'

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

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Poster Style'

    """Custom blur profile for the poster"""
    BLUR_PROFILE = '0x30'

    """Path to the reference star image to overlay on all source images"""
    __GRADIENT_OVERLAY = REF_DIRECTORY / 'stars-overlay.png'

    __slots__ = (
        'source_file', 'output_file', 'logo', 'title_text', 'episode_text',
        'font_color', 'font_file', 'font_interline_spacing',
        'font_interword_spacing', 'font_size', 'episode_text_color',
    )


    def __init__(self,
            source_file: Path,
            card_file: Path,
            title_text: str,
            episode_text: str,
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_size: float = 1.0,
            blur: bool = False,
            grayscale: bool = False,
            season_number: int = 1,
            episode_number: int = 1,
            logo: SeriesExtra[str] = None,
            episode_text_color: Optional[str] = None,
            preferences: Optional['PreferenceParser'] = None,
            **unused,
        ) -> None:
        """
        Construct a new instance of this card.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store indicated files
        self.source_file = source_file
        self.output_file = card_file

        # No logo file specified
        if logo is None:
            self.logo = None
        # Attempt to modify as if it's a format string
        else:
            try:
                logo = logo.format(season_number=season_number,
                                   episode_number=episode_number)
                logo = Path(CleanPath(logo).sanitize())
            except Exception as e:
                # Bad format strings will be caught during card creation
                self.valid = False
                log.exception(f'Invalid logo file "{logo}"', e)

            # Explicitly specicifed logo 
            if logo.exists():
                self.logo = logo
            # Try to find logo alongside source image
            elif (source_file.parent / logo.name).exists():
                self.logo = source_file.parent / logo.name
            # Assume non-existent explicitly specified filename
            else:
                self.logo = logo

        # Store text
        self.title_text = self.image_magick.escape_chars(title_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)

        # Font characteristics
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_size = font_size

        # Extras
        if episode_text_color is None:
            self.episode_text_color = font_color
        else:
            self.episode_text_color = episode_text_color


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

        # Generic font, reset custom episode text color
        if not custom_font:
            if 'episode_text_color' in extras:
                extras['episode_text_color'] =\
                    PosterTitleCard.EPISODE_TEXT_COLOR


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determines whether the given arguments represent a custom font
        for this card. This CardType does not use custom fonts, so this
        is always False.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        returns:
            False, as fonts are not customizable with this card.
        """

        custom_extras = (
            ('episode_text_color' in extras
                and extras['episode_text_color'] != PosterTitleCard.EPISODE_TEXT_COLOR)
        )

        return (custom_extras
            or ((font.color != PosterTitleCard.TITLE_COLOR)
            or (font.file != PosterTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.size != 1.0))
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
            episode_text_format: The episode text format in use.
            args and kwargs: Generic arguments to permit  generalized
                function calls for any CardType.

        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        return episode_text_format != PosterTitleCard.EPISODE_TEXT_FORMAT


    def create(self) -> None:
        """Create the title card as defined by this object."""

        # Source DNE, error and exit
        if not self.source_file.exists():
            log.error(f'Poster "{self.source_file.resolve()}" does not exist')
            return None

        # If no logo is specified, create empty logo command
        if self.logo is None:
            title_offset = 0
            logo_command = ''
        # Logo specified but does not exist - error and exit
        elif not self.logo.exists():
            log.error(f'Logo file "{self.logo.resolve()}" does not exist')
            return None
        # Logo specified and exists, create command to resize and add image
        else:
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
            # Resize poster
            f'"{self.source_file.resolve()}"',
            f'-resize "x1800"',
            # Extend image canvas to full size
            f'-extent "{self.TITLE_CARD_SIZE}"',
            # Apply style modifiers
            *self.style,
            # Add gradient overlay
            f'"{self.__GRADIENT_OVERLAY.resolve()}"',
            f'-flatten',
            # Optionally add logo
            *logo_command,
            # Add episode text
            f'-gravity south',
            f'-font "{self.font_file}"',
            f'-pointsize {75 * self.font_size}',
            f'-fill "{self.episode_text_color}"',
            f'-annotate +649+50 "{self.episode_text}"',
            # Add title text
            f'-gravity center',
            f'-pointsize {165 * self.font_size}',
            f'-interline-spacing {-40 + self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-fill "{self.font_color}"',
            f'-annotate +649+{title_offset} "{self.title_text}"',
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
