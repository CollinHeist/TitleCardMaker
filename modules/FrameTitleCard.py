from pathlib import Path
from typing import Literal

from modules.BaseCardType import BaseCardType
from modules.Debug import log

Position = Literal['left', 'surround', 'right']

class FrameTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards in a
    frame or polaroid layout. This is inspired from the official Adventure Time
    title cards from Season 8. 
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'frame'

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
        'source_file', 'output_file', 'title', 'season_text', 'episode_text',
        'hide_season', 'hide_episode', 'font', 'font_size', 'font_color',
        'vertical_shift', 'interline_spacing', 'kerning', 'episode_text_color',
        'episode_text_position',
    )
    
    def __init__(self, source: Path, output_file: Path, title: str, 
                 season_text: str, episode_text: str, hide_season: bool,
                 font: str, font_size: float, title_color: str,
                 vertical_shift: int=0,
                 interline_spacing: int=0,
                 kerning: float=1.0,
                 blur: bool=False,
                 grayscale: bool=False,
                 episode_text_color: str=EPISODE_TEXT_COLOR,
                 episode_text_position: Position='surround',
                 **unused) -> None:
        """
        Construct a new instance.
        
        Args:
            source: Source image for this card.
            output_file: Output filepath for this card.
            title: The title for this card.
            season_text: The season text for this card.
            episode_text: The episode text for this card.
            font: Font name or path (as string) to use for episode title.
            font_size: Scalar to apply to the title font size.
            title_color: Color to use for title text.
            hide_season: Whether to hide the season text on this card.
            vertical_shift: Vertical shift to apply to the title and kanji
                text.
            interline_spacing: Offset to interline spacing of the title text
            blur: Whether to blur the source image.
            grayscale: Whether to make the source image grayscale.
            episode_text_color: (Extra) Custom color to utilize for the episode
                text.
            episode_text_position: (Extra) How to position the episode text
                relative to the title text.
            unused: Unused arguments.
        """
        
        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        # Store source and output file
        self.source_file = source
        self.output_file = output_file

        # Escape title, season, and episode text
        prep = lambda s: s.upper().strip()
        self.title = self.image_magick.escape_chars(title)
        self.season_text = self.image_magick.escape_chars(prep(season_text))
        self.episode_text = self.image_magick.escape_chars(prep(episode_text))

        self.hide_season = hide_season or len(self.season_text) == 0
        self.hide_episode = len(self.episode_text) == 0

        # Font customizations
        self.font = font
        self.font_size = font_size
        self.font_color = title_color
        self.vertical_shift = vertical_shift
        self.interline_spacing = interline_spacing
        self.kerning = kerning

        # Verify/store extras
        self.episode_text_color = episode_text_color
        if episode_text_position.lower() not in ('left', 'surround', 'right'):
            log.error(f'episode_text_position must be "left", "surround", or '
                      f'"right"')
            self.valid = False
        else:
            self.episode_text_position = episode_text_position.lower()


    @property
    def _title_font_attributes(self) -> list[str]:
        """
        Subcommands for the font attributes of title text.

        Returns:
            List of ImageMagick commands.
        """

        title_size = 125 * self.font_size
        interline_spacing = -45 + self.interline_spacing
        kerning = 5 * self.kerning

        return [
            f'-font "{self.font}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {title_size}',
            f'-interline-spacing {interline_spacing}',
            f'-kerning {kerning}',
            f'-gravity center',
        ]


    @property
    def _index_font_attributes(self) -> list[str]:
        """
        Subcommand for the font attributes of the index text.

        Returns:
            List of ImageMagick commands.
        """

        return [
            f'-background transparent',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-pointsize 50',
            f'-fill "{self.episode_text_color}"',
        ]


    @property
    def text_command(self) -> list[str]:
        """
        Subcommand for adding all text. This includes the title, season, and
        episode text.

        Returns:
            List of ImageMagick commands.
        """

        # Command to add only the title to the source image
        vertical_shift = 675 + self.vertical_shift
        title_only_command = [
            # Set font attributes for title text
            *self._title_font_attributes,
            # Add title text
            f'-annotate +0+{vertical_shift} "{self.title}"',
        ]

        # If no index text is being added, only add title
        if self.hide_season and self.hide_episode:
            return title_only_command

        # If adding season and/or episode text and title..
        # Get width of title text for positioning 
        width = self.get_text_dimensions(title_only_command,
                                         width='max', height='sum')['width']
        offset = 3200/2 + width/2 + 25
        
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
    def is_custom_font(font: 'Font') -> bool:
        """
        Determines whether the given arguments represent a custom font for this
        card. This CardType only uses custom font cases.
        
        Args:
            font: The Font being evaluated.
        
        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.file != FrameTitleCard.TITLE_FONT)
            or (font.size != 1.0)
            or (font.color != FrameTitleCard.TITLE_COLOR)
            or (font.vertical_shift != 0)
            or (font.interline_spacing != 0)
            or (font.kerning != 1.0)
            or (font.stroke_width != 1.0))


    @staticmethod
    def is_custom_season_titles(custom_episode_map: bool, 
                                episode_text_format: str) -> bool:
        """
        Determines whether the given attributes constitute custom or generic
        season titles.
        
        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.
        
        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        standard_etf = FrameTitleCard.EPISODE_TEXT_FORMAT.upper()
        
        return (custom_episode_map or
                episode_text_format.upper() != standard_etf)


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this object's
        defined title card.
        """

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
            *self.text_command,
            # Write to output file
            f'"{self.output_file.resolve()}"',
        ])
        
        self.image_magick.run(command)