from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from modules.BaseCardType import (
    BaseCardType, CardDescription, Extra, ImageMagickCommands
)

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


Position = Literal['left', 'surround', 'right']


class FrameTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards in
    a frame or polaroid layout. This is inspired from the official
    Adventure Time title cards from Season 8.
    """

    """API Parameters"""
    API_DETAILS = CardDescription(
        name='Frame',
        identifier='frame',
        example='/internal_assets/cards/frame.jpg',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Position',
                identifier='episode_text_position',
                description=(
                    'Position of the episode text relative to the title text'
                ),
                tooltip=(
                    'Either <v>left</v>, <v>surround</v>, or <v>right</v>. '
                    'Default is <v>surround</v>.'
                ),
            ), Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to use for the episode text',
            ),
        ], description=[
            'Title card styled to look like a Polaroid photo.',
            'The placement and color of the season and episode text can be '
            'adjusted via extras.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'frame'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 31,   # Character count to begin splitting titles
        'max_line_count': 2,    # Maximum number of lines a title can take up
        'top_heavy': False,     # This class uses bottom heavy titling
    }

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Frame Style'

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'guess-sans-medium.otf').resolve())
    DEFAULT_FONT_CASE = 'upper'
    TITLE_COLOR = 'rgb(80, 80, 80)'
    FONT_REPLACEMENTS = {}

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = True

    """Default colors for space outside the frame, and index text"""
    BACKGROUND_COLOR = 'black'

    """Index text font characteristics"""
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'guess-sans-medium.otf'
    EPISODE_TEXT_COLOR = 'rgb(100, 100, 100)'

    """Source path for the gradient image overlayed over all title cards"""
    __FRAME_IMAGE = REF_DIRECTORY / 'frame.png'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season', 'hide_episode', 'font_color',
        'font_file', 'font_interline_spacing', 'font_interword_spacing',
        'font_kerning', 'font_size', 'font_vertical_shift',
        'episode_text_color', 'episode_text_position',
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
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_position: Position = 'surround',
            preferences: Optional['Preferences'] = None,
            **unused,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store source and output file
        self.source_file = source_file
        self.output_file = card_file

        # Escape title, season, and episode text
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season = hide_season_text
        self.hide_episode = hide_episode_text

        # Font customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_vertical_shift = font_vertical_shift

        # Verify/store extras
        self.episode_text_color = episode_text_color
        self.episode_text_position = episode_text_position


    @property
    def _title_font_attributes(self) -> ImageMagickCommands:
        """Subcommands for the font attributes of title text."""

        title_size = 125 * self.font_size
        interline_spacing = -45 + self.font_interline_spacing
        interword_spacing = 0 + self.font_interword_spacing
        kerning = 5 * self.font_kerning

        return [
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {title_size}',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {interword_spacing}',
            f'-kerning {kerning}',
            f'-gravity center',
        ]


    @property
    def _index_font_attributes(self) -> ImageMagickCommands:
        """Subcommand for the font attributes of the index text."""

        return [
            f'-background transparent',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-pointsize 50',
            f'-fill "{self.episode_text_color}"',
        ]


    @property
    def text_commands(self) -> ImageMagickCommands:
        """
        Subcommand for adding all text. This includes the title, season,
        and episode text.
        """

        # Command to add only the title to the source image
        vertical_shift = 675 + self.font_vertical_shift
        title_only_command = [
            # Set font attributes for title text
            *self._title_font_attributes,
            # Add title text
            f'-annotate +0+{vertical_shift} "{self.title_text}"',
        ]

        # If no index text is being added, only add title
        if self.hide_season and self.hide_episode:
            return title_only_command

        # If adding season and/or episode text and title..
        # Get width of title text for positioning
        width, _ = self.image_magick.get_text_dimensions(
            title_only_command, width='max', height='sum'
        )
        offset = (self.WIDTH + width) / 2 + 25

        # Add index text to left or right
        if self.episode_text_position in ('left', 'right'):
            gravity = 'east' if self.episode_text_position == 'left' else 'west'

            return [
                # Align text and image based on positioning
                f'-gravity {gravity} \(',
                # Add index texts
                *self._index_font_attributes,
                f'label:"{self.season_text}"' if not self.hide_season else '',
                f'label:"{self.episode_text}"' if not self.hide_episode else '',
                # Smush vertically
                f'-smush 25 \)',
                # Overlay on left/right of the title text
                f'-geometry +{offset}+{vertical_shift}',
                f'-composite',
                # Add title text
                *title_only_command,
            ]

        # Add index text in surround style
        # Create optional subcommand for adding season text to left of title
        season_command = []
        if not self.hide_season:
            season_command = [
                f'-gravity east \(',
                *self._index_font_attributes,
                f'label:"{self.season_text}" \)',
                f'-gravity east',
                f'-geometry +{offset}+{vertical_shift}',
                f'-composite',
            ]

        # Create optional subcommand for adding episode text to right of title
        episode_command = []
        if not self.hide_episode:
            episode_command = [
                f'-gravity west \(',
                *self._index_font_attributes,
                f'label:"{self.episode_text}" \)',
                f'-geometry +{offset}+{vertical_shift}',
                f'-composite',
            ]

        # Combined command of all subcommands
        return [
            *season_command,
            *episode_command,
            *title_only_command,
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
                extras['episode_text_color'] = FrameTitleCard.EPISODE_TEXT_COLOR


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determines whether the given arguments represent a custom font
        for this card. This CardType only uses custom font cases.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        custom_extras = (
            ('episode_text_color' in extras
                and extras['episode_text_color'] != FrameTitleCard.EPISODE_TEXT_COLOR)
        )

        return (custom_extras
            or ((font.color != FrameTitleCard.TITLE_COLOR)
            or (font.file != FrameTitleCard.TITLE_FONT)
            or (font.kerning != 1.0)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.size != 1.0)
            or (font.vertical_shift != 0))
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

        standard_etf = FrameTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """Create this object's defined Title Card."""

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Apply any defined styles
            *self.style,
            # Resize to fit within frame
            f'-resize 2915x',
            f'-resize x1275\<',
            # Increase contrast of source image
            f'-modulate 100,125',
            # Fill in background
            f'-background "{self.BACKGROUND_COLOR}"',
            # Extend canvas to card size
            f'-gravity center',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            # Overlay frame
            f'"{self.__FRAME_IMAGE.resolve()}"',
            f'-composite',
            # Add all index/title text
            *self.text_commands,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
