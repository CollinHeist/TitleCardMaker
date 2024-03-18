from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from modules.BaseCardType import BaseCardType, ImageMagickCommands
from modules.Debug import log
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from models.PreferenceParser import PreferenceParser
    from modules.Font import Font


Country = Literal[
    'Abu Dhabi', 'Australian', 'Austrian', 'Azerbaijan', 'Bahrain', 'Belgian',
    'British', 'Canadian', 'Chinese', 'Dutch', 'Hungarian', 'Italian',
    'Japanese', 'Las Vegas', 'Mexican', 'Miami', 'Monaco', 'Qatar', 'Sao Paulo',
    'Saudi Arabian', 'Singapore', 'Spanish', 'United Arab Emirates',
    'United States', 'generic',
]


class FormulaOneTitleCard(BaseCardType):
    """
    This class describes a CardType that produces Title Cards which are
    styled for Formula 1.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'formula'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 40,
        'max_line_count': 1,
        'style': 'bottom',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Formula1-Bold.otf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Formula1-Bold.otf'
    EPISODE_TEXT_FORMAT = 'ROUND {season_number}'
    EPISODE_TEXT_COLOR = 'white'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Formula 1 Style'

    """Implementation details"""
    DARKEN_COLOR = 'rgba(0,0,0,0.5)'
    FRAME = REF_DIRECTORY / 'frame.png'
    FRAME_FONT = REF_DIRECTORY / 'Formula1-Numbers.otf'
    _COUNTRY_FLAGS = {
        'ABU DHABI': REF_DIRECTORY / 'uae.webp',
        'AUSTRALIAN': REF_DIRECTORY / 'australia.webp',
        'AUSTRIAN': REF_DIRECTORY / 'austria.webp',
        'AZERBAIJAN': REF_DIRECTORY / 'azerbaijan.webp',
        'BAHRAIN': REF_DIRECTORY / 'bahrain.webp',
        'BELGIAN': REF_DIRECTORY / 'belgium.webp',
        'BRITISH': REF_DIRECTORY / 'british.webp',
        'CANADIAN': REF_DIRECTORY / 'canada.webp',
        'CHINESE': REF_DIRECTORY / 'chinese.webp',
        'DUTCH': REF_DIRECTORY / 'dutch.webp',
        'HUNGARIAN': REF_DIRECTORY / 'hungarian.webp',
        'ITALIAN': REF_DIRECTORY / 'italian.webp',
        'JAPANESE': REF_DIRECTORY / 'japan.webp',
        'LAS VEGAS': REF_DIRECTORY / 'unitedstates.webp',
        'MEXICAN': REF_DIRECTORY / 'mexico.webp',
        'MONACO': REF_DIRECTORY / 'monaco.webp',
        'QATAR': REF_DIRECTORY / 'qatar.webp',
        'SAO PAULO': REF_DIRECTORY / 'brazil.webp',
        'SAUDI ARABIAN': REF_DIRECTORY / 'saudiarabia.webp',
        'SINGAPORE': REF_DIRECTORY / 'singapore.webp',
        'SPANISH': REF_DIRECTORY / 'spain.webp',
        'MIAMI': REF_DIRECTORY / 'unitedstates.webp',
        'UNITED ARAB EMIRATES': REF_DIRECTORY / 'uae.webp',
        'UNITED STATES': REF_DIRECTORY / 'unitedstates.webp',
        'GENERIC': REF_DIRECTORY / 'generic.webp',
    }


    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_interline_spacing', 'font_interword_spacing', 'font_file',
        'font_kerning', 'font_size', 'font_vertical_shift', 'country',
        'episode_text_color', 'episode_text_font_size', 'race', 'year',
    )


    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title_text: str,
            season_text: str,
            episode_text: str,
            hide_season_text: bool = False,
            hide_episode_text: bool = False,
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            # font_interline_spacing: int = 0,
            # font_interword_spacing: int = 0,
            # font_kerning: float = 1.0,
            font_size: float = 1.0,
            # font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            country: Country = 'australia',
            episode_text_color: str = TITLE_COLOR,
            episode_text_font_size: float = 1.0,
            flag: Optional[Path] = None,
            race: str = 'GRAND PRIX',
            year: int = 2024,
            preferences: Optional['PreferenceParser'] = None,
            **unused,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text)
        self.hide_season_text = hide_season_text
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_episode_text = hide_episode_text

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        # self.font_interline_spacing = font_interline_spacing
        # self.font_interword_spacing = font_interword_spacing
        # self.font_kerning = font_kerning
        self.font_size = font_size
        # self.font_vertical_shift = font_vertical_shift

        # Extras
        if flag is None or not flag.exists():
            self.country = self._COUNTRY_FLAGS.get(
                country, self.REF_DIRECTORY / 'generic.webp'
            )
        else:
            self.country = flag
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.race = race
        self.year = year


    @property
    def static_commands(self) -> ImageMagickCommands:
        """
        Subcommmands to add the race name to the static overlay, frame,
        and country banner to the image.
        """

        return [
            # Create dark overlay
            f'-gravity center',
            f'\( -size {self.TITLE_CARD_SIZE}',
            f'xc:"{self.DARKEN_COLOR}"',
            f'\) -composite',
            # Add frame
            f'"{self.FRAME.resolve()}"',
            f'-composite',
            # Add country banner
            f'"{self.country.resolve()}"',
            f'-composite',
        ]


    @property
    def race_commands(self) -> ImageMagickCommands:
        """Subcommmands to add the race name to the image."""

        # No race, return empty commands
        if not self.race:
            return []

        # Base commands before text size modification
        font_size = 205 * self.font_size
        commands = [
            f'-gravity center',
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {font_size}',
            f'-annotate +0-222 "{self.race}"',
        ]

        # Scale font size
        width, _ = self.image_magick.get_text_dimensions(commands)
        INNER_WIDTH = 1725 - (50 * 2) # 50px margin on either side
        if width > INNER_WIDTH:
            font_size *= INNER_WIDTH / width
            commands[-2] = f'-pointsize {font_size}'

        return commands


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # No title text, return empty commands
        if len(self.title_text) == 0:
            return []

        # Base commands before text size modification
        font_size = 155 * self.font_size
        commands = [
            f'-gravity north',
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {font_size}',
            f'-annotate +0+800 "{self.title_text}"',
        ]

        # Scale font size dynamically if text is too wide
        width, _ = self.image_magick.get_text_dimensions(commands)
        INNER_WIDTH = 1725 - (50 * 2) # 50px margin on either side
        if width > INNER_WIDTH:
            font_size *= INNER_WIDTH / width
            commands[-2] = f'-pointsize {font_size}'

        return commands


    @property
    def season_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the season text to the image."""

        # No season text, return empty commands
        if self.hide_season_text:
            return []

        return [
            f'-gravity north',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize {170 * self.episode_text_font_size}',
            f'-annotate +0+390',
            f'"{self.season_text}"',
        ]


    @property
    def episode_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the episode text to the image."""

        # No episode text, return empty commands
        if self.hide_episode_text:
            return []

        return [
            f'-gravity north',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize {82 * self.episode_text_font_size}',
            f'-annotate +0+275',
            f'"{self.episode_text}"',
        ]


    @property
    def year_commands(self) -> ImageMagickCommands:
        """Subcommands to add the race year to the image."""

        return [
            f'-gravity southeast',
            f'-font "{self.FRAME_FONT.resolve()}"',
            f'-fill white',
            f'-kerning -10',
            f'-pointsize 165',
            f'-annotate +1915+625 "{self.year}"',
            f'+kerning',
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

        if not custom_font:
            if 'episode_text_color' in extras:
                extras['episode_text_color'] = FormulaOneTitleCard.EPISODE_TEXT_COLOR
            if 'episode_text_font_size' in extras:
                extras['episode_text_font_size'] = 1.0


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        custom_extras = (
            ('episode_text_color' in extras
                and extras['episode_text_color'] != FormulaOneTitleCard.EPISODE_TEXT_COLOR)
            or ('episode_text_font_size' in extras
                and extras['episode_text_font_size'] != 1.0)
        )

        return (custom_extras
            or ((font.color != FormulaOneTitleCard.TITLE_COLOR)
            or (font.file != FormulaOneTitleCard.TITLE_FONT)
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
            True if custom season titles are indicated, False otherwise.
        """

        standard_etf = FormulaOneTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """Create this object's defined Title Card."""

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,

            *self.static_commands,
            *self.race_commands,
            *self.episode_text_commands,
            *self.season_text_commands,
            *self.title_text_commands,
            *self.year_commands,

            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
