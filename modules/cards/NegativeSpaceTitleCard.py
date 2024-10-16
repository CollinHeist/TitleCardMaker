from pathlib import Path
from typing import Literal, Optional, TYPE_CHECKING

from modules.BaseCardType import (
    BaseCardType, CardTypeDescription, Extra, ImageMagickCommands,
)
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


TextSide = Literal['left', 'right']


class NegativeSpaceTitleCard(BaseCardType):
    """
    CardType that produces title cards ... TODO
    """

    """API Parameters"""
    API_DETAILS: CardTypeDescription = CardTypeDescription(
        name='',
        identifier='',
        example='/internal_assets/cards/...',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[],
        description=[]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'negative_space'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 20,
        'max_line_count': 5,
        'style': 'top',
    }

    """Characteristics of the default title font"""
    TITLE_FONT: str = str((REF_DIRECTORY / 'Futura.ttc').resolve())
    TITLE_COLOR: str = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = TITLE_COLOR
    EPISODE_TEXT_FONT = TITLE_FONT

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE: bool = False

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME: str = 'Negative Space Style'

    """Implementation Details"""
    DEFAULT_TEXT_SIDE: TextSide = 'left'

    __slots__ = (
        'source_file', 'output_file', 'title_text', 'episode_text',
        'hide_episode_text', 'font_file', 'font_size', 'font_color',
        'font_interline_spacing', 'font_interword_spacing', 'font_kerning',
        'font_vertical_shift', 'episode_text_color', 'episode_text_font_size',
        'number_horizontal_offset', 'number_vertical_offset', 'text_side',
    )


    def __init__(self, *,
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
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,

            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            number_horizontal_offset: int = 0,
            number_vertical_offset: int = 0,
            text_side: TextSide = DEFAULT_TEXT_SIDE,

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
        if episode_text == 'random':
            from random import randint
            episode_text = str(randint(0, int('9' * randint(1, 3))))
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_episode_text = hide_episode_text

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = 0 + font_interline_spacing
        self.font_interword_spacing = -55 + font_interword_spacing
        self.font_kerning = 1.0 * font_kerning
        self.font_size = font_size
        self.font_vertical_shift = 0 + font_vertical_shift

        # Extras
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.number_horizontal_offset = number_horizontal_offset
        self.number_vertical_offset = number_vertical_offset
        self.text_side: TextSide = text_side


    def title_text_commands(self,
            color: Optional[str] = None,
        ) -> ImageMagickCommands:
        """Subcommand for adding title text to the source image."""

        # No title text
        if not self.title_text:
            return []

        color = color or self.font_color
        gravity = 'west' if self.text_side == 'left' else 'east'

        # Determine x offset
        offset = 350
        # if self.episode_text and self.episode_text[0] == '0':
        #     offset = 120

        return [
            f'-font "{self.font_file}"',
            f'-gravity {gravity}',
            f'-fill "{color}"',
            f'-pointsize {150 * self.font_size}',
            f'-kerning {self.font_kerning}',
            f'-interline-spacing {self.font_interword_spacing}',
            f'-annotate {offset:+}+0 "{self.title_text}"',
        ]


    def numeral_commands(self,
            color: Optional[str] = None,
        ) -> ImageMagickCommands:
        """
        Get the subcommand for adding the numeral text to the source
        image.

        Args:
            color: Override color for the numeral text.

        Returns:
            List of ImageMagick commands.
        """

        # If not showing numeral text, return
        if self.hide_episode_text:
            return []

        color = color or self.episode_text_color
        gravity = 'west' if self.text_side == 'left' else 'east'

        # Determine horizontal offset
        x = 0
        if self.episode_text[0] == '1':
            x = -50
        x += self.number_horizontal_offset

        return [
            f'-font "{self.EPISODE_TEXT_FONT}"',
            f'-gravity {gravity}',
            f'-fill "{color}"',
            f'-pointsize {1250 * self.episode_text_font_size}',
            f'-kerning -125', # -150
            f'-annotate {x:+}{self.number_vertical_offset:+}',
            f'"{self.episode_text}"',
        ]


    def create_text_image(self) -> Path:
        """
        Create the image containing the numeral and title text.

        Returns:
            Path to the created image. This is a temporary image which
            must be deleted afterwards.
        """

        # Get random filename for intermediate image
        image = self.image_magick.get_random_filename(self.source_file)

        self.image_magick.run([
            f'convert',
            f'-size "{self.TITLE_CARD_SIZE}"',
            f'xc:transparent',
            *self.numeral_commands(),
            *self.title_text_commands(),
            f'"{image.resolve()}"',
        ])

        return image


    def create_difference_mask(self) -> Path:
        """
        Create the difference mask in which the source image should be
        mapped to the white pixels, and the text mapped to the black.

        Returns:
            Path to the created image. This is a temporary image which
            must be deleted afterwards.
        """

        # Get random filename for intermediate image - this must be a
        # JPEG image for the mask to work
        image = self.image_magick.get_random_filename(
            self.source_file, extension='jpg'
        )

        # Create mask
        self.image_magick.run([
            f'convert',
            f'-size "{self.TITLE_CARD_SIZE}"',
            # First image is the filled number mask where white is the
            # episode number, and the background is black
            f'\(',
            f'xc:black',
            *self.numeral_commands('white'),
            f'\)',
            # Second image is the filled title mask where black is the
            # title text, and the background is white
            f'\(',
            f'xc:white',
            *self.title_text_commands('black'),
            f'\)',
            # Create difference composite mask of the two images
            f'-compose difference',
            f'-composite',
            f'"{image.resolve()}"',
        ])

        return image


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
            ...


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
            # TODO
        )

        return (custom_extras
            or ((font.color != NegativeSpaceTitleCard.TITLE_COLOR)
            or (font.file != NegativeSpaceTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
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

        return (
            custom_episode_map
            or episode_text_format != NegativeSpaceTitleCard.EPISODE_TEXT_FORMAT
        )


    def create(self) -> None:
        """Create this object's defined Title Card."""

        # Masked Alpha Composition layers are ordered as:
        # [Replace Black Parts of Mask] | [Replace White Parts of Mask] | [Mask]

        # These are TemporaryPath objects which will be deleted
        text_image = self.create_text_image()
        difference_mask = self.create_difference_mask()

        self.image_magick.run([
            f'convert',
            # Layer 0 is the text
            f'"{text_image.resolve()}"',
            # Layer 1 is the source image
            f'\(',
            f'"{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            f'\)',
            # Layer 2 is the mask
            f'"{difference_mask.resolve()}"',
            # Use masked alpha composition to combine images
            f'-composite',
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.delete_intermediate_images(
            text_image, difference_mask
        )
