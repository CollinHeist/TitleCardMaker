from pathlib import Path
from typing import Any, Literal, Optional

from modules.BaseCardType import BaseCardType, ImageMagickCommands
from modules.Debug import log


SeriesExtra = Optional
TitleTextPosition = Literal['left', 'right']
TextPosition = Literal[
    'upper left', 'upper right', 'right', 'lower right', 'lower left', 'left',
]


class DividerTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards
    similar to the AnimeTitleCard (same font), but featuring a vertical
    divider between the season and episode text. This card allows the
    positioning of text on the image to be adjusted. The general design
    was inspired by the title card interstitials in Overlord (season 3).
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'anime'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 18,   # Character count to begin splitting titles
        'max_line_count': 4,    # Maximum number of lines a title can take up
        'top_heavy': False,     # This class uses bottom heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Flanker Griffo.otf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'source'
    FONT_REPLACEMENTS = {'♡': '', '☆': '', '✕': 'x'}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'Episode {episode_number}'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Standard class has standard archive name"""
    ARCHIVE_NAME = 'Divider Style'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'season_text',
        'episode_text', 'hide_season_text', 'hide_episode_text', 'font_color',
        'font_file', 'font_interline_spacing', 'font_kerning', 'font_size',
        'font_stroke_width', 'stroke_color', 'title_text_position',
        'text_position', 'font_vertical_shift'
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
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_stroke_width: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            stroke_color: str = 'black',
            title_text_position: TitleTextPosition = 'left',
            text_position: TextPosition = 'lower right',
            preferences: Optional['Preferences'] = None, # type: ignore
            **unused,
        ) -> None:
        """
        Construct a new instance of this Card.
        """

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text or len(season_text) == 0
        self.hide_episode_text = hide_episode_text or len(episode_text) == 0

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.stroke_color = stroke_color
        if str(title_text_position).lower() not in ('left', 'right'):
            log.error(f'Invalid "title_text_position" - must be left, or right')
            self.valid = False
        self.title_text_position = str(title_text_position).lower()
        if (str(text_position).lower()
            not in ('upper left', 'upper right', 'right', 'lower left',
                    'lower right', 'left')):
            log.error(f'Invalid "text_position" - must be upper left, upper '
                      f'right, right, lower left, lower right, or left')
            self.valid = False
        self.text_position = str(text_position).lower()


    @property
    def index_text_command(self) -> ImageMagickCommands:
        """
        Subcommand for adding the index text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        gravity = 'west' if self.title_text_position == 'left' else 'east'

        # Hiding all index text, return empty command
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Hiding season or episode text, only add that and divider bar
        if self.hide_season_text or self.hide_episode_text:
            text = self.episode_text if self.hide_season_text else self.season_text
            return [
                f'-gravity {gravity}',
                f'-pointsize {100 * self.font_size}',
                f'label:"{text}"',
            ]
        # Showing all text, add all text and divider
        return [
            f'-gravity {gravity}',
            f'-pointsize {100 * self.font_size}',
            f'label:"{self.season_text}\n{self.episode_text}"',
        ]


    @property
    def title_text_command(self) -> ImageMagickCommands:
        """
        Subcommand for adding the title text to the source image.

        Returns:
            List of ImageMagick commands.
        """

        # No title text, return blank commands
        if len(self.title_text) == 0:
            return []

        gravity = 'east' if self.title_text_position == 'left' else 'west'
        return [
            f'-gravity {gravity}',
            f'-pointsize {100 * self.font_size}',
            f'label:"{self.title_text}"',
        ]


    @property
    def divider_height(self) -> int:
        """
        Get the height of the divider between the index and title text.

        Returns:
            Height of the divider to create.
        """

        # No need for divider, use blank command
        if (len(self.title_text) == 0
            or (self.hide_season_text and self.hide_episode_text)):
            return 0

        return max(
            # Height of the index text
            self.get_text_dimensions([
                    f'-font "{self.font_file}"',
                    f'-interline-spacing {self.font_interline_spacing}',
                    *self.index_text_command,
                ], width='max', height='sum'
            )[1],
            # Height of the title text
            self.get_text_dimensions([
                    f'-font "{self.font_file}"',
                    f'-interline-spacing {self.font_interline_spacing}',
                    *self.title_text_command,
                ], width='max', height='sum'
            )[1]
        )


    def divider_command(self,
            divider_height: int,
            font_color: str) -> ImageMagickCommands:
        """
        Subcommand to add the dividing rectangle to the image.

        Args:
            divider_height: Height of the divider to create.
            font_color: Color of the text to create the divider in.

        Returns:
            List of ImageMagick commands.
        """

        # No need for divider, use blank command
        if (len(self.title_text) == 0
            or (self.hide_season_text and self.hide_episode_text)):
            return []

        return [
            f'\( -size 7x{divider_height-25}',
            f'xc:"{font_color}" \)',
            f'+size',
            f'-gravity center',
            f'+smush 25',
        ]


    def text_command(self,
            divider_height: int, font_color: str) -> ImageMagickCommands:
        """
        Subcommand to add all text - index, title, and the divider - to
        the image.

        Args:
            divider_height: Height of the divider to create.
            font_color: Color of the text being created.

        Returns:
            List of ImageMagick commands.
        """

        # Title on left, add text as: title divider index
        if self.title_text_position == 'left':
            return [
                *self.title_text_command,
                *self.divider_command(divider_height, font_color),
                *self.index_text_command,
            ]

        # Title on right, add text as index divider title
        return [
            *self.index_text_command,
            *self.divider_command(divider_height, font_color),
            *self.title_text_command,
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

        # Generic font, reset stroke color
        if not custom_font:
            if 'stroke_color' in extras:
                extras['stroke_color'] = 'black'


    @staticmethod
    def is_custom_font(font: 'Font') -> bool: # type: ignore
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.color != DividerTitleCard.TITLE_COLOR)
            or (font.file != DividerTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
            or (font.stroke_width != 1.0)
        )


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool, episode_text_format: str) -> bool:
        """
        Determine whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        standard_etf = DividerTitleCard.EPISODE_TEXT_FORMAT.upper()

        return (custom_episode_map
                or episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        interline_spacing = -20 + self.font_interline_spacing
        kerning = 0 * self.font_kerning
        stroke_width = 8 * self.font_stroke_width

        # The gravity of the text composition is based on the text position
        gravity = {
            'upper left':  'northwest',
            'upper right': 'northeast',
            'right':       'east',
            'lower right': 'southeast',
            'lower left':  'southwest',
            'left':        'west',
        }[self.text_position]

        # Get the height for the divider character based on the max text height
        divider_height = self.divider_height

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Add blurred stroke behind the title text
            f'-background transparent',
            f'-bordercolor transparent',
            f'-font "{self.font_file}"',
            f'-kerning {kerning}',
            f'-strokewidth {stroke_width}',
            f'-interline-spacing {interline_spacing}',
            f'\( -stroke "{self.stroke_color}"',
            *self.text_command(divider_height, self.stroke_color),
            # Combine text images
            f'+smush 25',
            # Add border so the blurred text doesn't get sharply cut off
            f'-border 50x{50+self.font_vertical_shift}',
            f'-blur 0x5 \)',
            # Overlay blurred text in correct position
            f'-gravity {gravity}',
            f'-composite',
            # Add title text
            f'\( -fill "{self.font_color}"',
            # Use basically transparent color so text spacing matches
            f'-stroke "rgba(1, 1, 1, 0.01)"',
            *self.text_command(divider_height, self.font_color),
            f'+smush 25',
            f'-border 50x{50+self.font_vertical_shift} \)',
            # Overlay title text in correct position
            f'-gravity {gravity}',
            f'-composite',
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)
