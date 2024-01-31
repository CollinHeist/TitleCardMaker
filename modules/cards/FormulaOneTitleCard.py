from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from modules.BaseCardType import (
    BaseCardType, CardDescription, Extra, ImageMagickCommands,
)
from modules.Debug import log

if TYPE_CHECKING:
    from app.models.preferences import Preferences
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

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Formula 1',
        identifier='f1',
        example='/internal_assets/cards/formula.webp',
        creators=['CollinHeist', '/u/heeisenbeerg'],
        source='builtin',
        supports_custom_fonts=False,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Country',
                identifier='country',
                description='Which flag to utilize on the Title Card',
                tooltip=(
                    'One of <v>Abu Dhabi</v>, <v>Australian</v>, '
                    '<v>Austrian</v>, <v>Azerbaijan</v>, <v>Bahrain</v>, '
                    '<v>Belgian</v>, <v>British</v>, <v>Canadian</v>, '
                    '<v>Chinese</v>, <v>Dutch</v>, <v>Hungarian</v>, '
                    '<v>Italian</v>, <v>Japanese</v>, <v>Las Vegas</v>, '
                    '<v>Mexican</v>, <v>Miami</v>, <v>Monaco</v>, <v>Qatar</v>,'
                    ' <v>Sao Paulo</v>, <v>Saudi Arabian</v>, <v>Singapore</v>,'
                    ' <v>Spanish</v>, <v>United Arab Emirates</v>, or '
                    '<v>United States</v>. By default this is parsed from the '
                    'season title.'
                ),
            ),
            Extra(
                name='Race Name',
                identifier='race',
                description='Name of the race',
                tooltip='Defaults to <v>Grand Prix</v>.',
            ),
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>'
            ),
        ],
        description=[
            'Title Card designed for displaying race details for Formula 1. ',
            'The intention is that a custom seeason title of the relevant '
            'country/flag (e.g. japanese) is set, and then the appropriate '
            'flag will automatically be selected.', 'This card type is not '
            'widely applicable for non-F1 Series.',
        ],
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'formula'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 25,   # Character count to begin splitting titles
        'max_line_count': 2,    # Maximum number of lines a title can take up
        'top_heavy': False,      # This class uses top heavy titling
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
    _FRAME = REF_DIRECTORY / 'frame_2024.png'
    _COUNTRY = {
        'Abu Dhabi': REF_DIRECTORY / 'uae.webp',
        'Australian': REF_DIRECTORY / 'australia.webp',
        'Austrian': REF_DIRECTORY / 'austria.webp',
        'Azerbaijan': REF_DIRECTORY / 'azerbaijan.webp',
        'Bahrain': REF_DIRECTORY / 'bahrain.webp',
        'Belgian': REF_DIRECTORY / 'belgium.webp',
        'British': REF_DIRECTORY / 'british.webp',
        'Canadian': REF_DIRECTORY / 'canada.webp',
        'Chinese': REF_DIRECTORY / 'chinese.webp',
        'Dutch': REF_DIRECTORY / 'dutch.webp',
        'Hungarian': REF_DIRECTORY / 'hungarian.webp',
        'Italian': REF_DIRECTORY / 'italian.webp',
        'Japanese': REF_DIRECTORY / 'japan.webp',
        'Las Vegas': REF_DIRECTORY / 'unitedstates.webp',
        'Mexican': REF_DIRECTORY / 'mexico.webp',
        'Monaco': REF_DIRECTORY / 'monaco.webp',
        'Qatar': REF_DIRECTORY / 'qatar.webp',
        'Sao Paulo': REF_DIRECTORY / 'brazil.webp',
        'Saudi Arabian': REF_DIRECTORY / 'saudiarabia.webp',
        'Singapore': REF_DIRECTORY / 'singapore.webp',
        'Spanish': REF_DIRECTORY / 'spain.webp',
        'Miami': REF_DIRECTORY / 'unitedstates.webp',
        'United Arab Emirates': REF_DIRECTORY / 'uae.webp',
        'United States': REF_DIRECTORY / 'unitedstates.webp',
        'generic': REF_DIRECTORY / 'generic.webp',
    }


    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_interline_spacing', 'font_interword_spacing', 'font_file',
        'font_kerning', 'font_size', 'font_vertical_shift', 'country',
        'episode_text_color', 'episode_text_font_size', 'race',
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
            race: str = 'GRAND PRIX',
            preferences: Optional['Preferences'] = None,
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
        self.country = self._COUNTRY.get(
            country, self.REF_DIRECTORY / 'generic.webp'
        )
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.race = race


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
            f'"{self._FRAME.resolve()}"',
            f'-composite',
            # Add country banner
            f'"{self.country.resolve()}"',
            f'-composite',
        ]


    @property
    def race_commands(self) -> ImageMagickCommands:
        """Subcommmands to add the race name to the title text."""

        if not self.race:
            return []

        return [
            f'-gravity north',
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {205 * self.font_size}',
            f'-annotate +0+575 "{self.race}"',
        ]


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # If no title text, return empty commands
        if len(self.title_text) == 0:
            return []

        return [
            f'-gravity north',
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {155 * self.font_size}',
            f'-annotate +0+800 "{self.title_text}"',
        ]


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

            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
