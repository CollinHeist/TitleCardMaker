from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional, Union

from modules.ImageMaker import ImageMagickCommands, ImageMaker

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.PreferenceParser import PreferenceParser


_LogoPlacement = Literal['top', 'middle', 'bottom']
_TextPlacement = Literal['top', 'bottom']


class SeasonPoster(ImageMaker):
    """
    This class describes a type of ImageMaker that creates season
    posters. Season posters take images, add a logo and season title.
    """

    """Default size of all season posters"""
    POSTER_WIDTH = 2000
    POSTER_HEIGHT = 3000
    SEASON_POSTER_SIZE = f'{POSTER_WIDTH}x{POSTER_HEIGHT}'

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' /'season_poster'

    """Default font values for the season text"""
    SEASON_TEXT_FONT = REF_DIRECTORY / 'Proxima Nova Semibold.otf'
    SEASON_TEXT_COLOR = '#CFCFCF'

    """Paths for the gradient overlay"""
    GRADIENT_OVERLAY = REF_DIRECTORY / 'gradient.png'

    __slots__ = (
        'source', 'destination', 'logo', 'season_text', 'font', 'font_color',
        'font_size', 'font_kerning', 'logo_placement', 'omit_gradient',
        'omit_logo', 'text_placement', 'font_vertical_shift',
    )


    def __init__(self,
            *,
            source: Path,
            destination: Path,
            logo: Optional[Path],
            season_text: str,
            font: Path = SEASON_TEXT_FONT,
            font_color: str = SEASON_TEXT_COLOR,
            font_size: float = 1.0,
            font_kerning: float = 1.0,
            font_vertical_shift: int = 0,
            logo_placement: _LogoPlacement = 'top',
            omit_gradient: bool = False,
            omit_logo: bool = False,
            text_placement: _TextPlacement = 'top',
            preferences: Optional[Union['PreferenceParser', 'Preferences']] = None,
        ) -> None:
        """Initialize this SeasonPoster object."""

        # Initialize parent object for the ImageMagickInterface
        super().__init__(preferences=preferences)

        # Store provided file attributes
        self.source = source
        self.destination = destination
        self.logo = None if omit_logo else logo

        # Store text attributes
        self.season_text = season_text.upper()

        # Store customized font attributes
        self.font = font
        self.font_color = font_color
        self.font_size = font_size
        self.font_kerning = font_kerning
        self.font_vertical_shift = font_vertical_shift
        self.logo_placement: _LogoPlacement = logo_placement
        self.omit_gradient = omit_gradient
        self.text_placement: _TextPlacement = text_placement


    def __get_logo_height(self) -> int:
        """
        Get the logo height of the logo after it will be resized.

        Returns:
            Integer height (in pixels) of the resized logo.
        """

        # If omitting the logo, return 0
        if self.logo is None:
            return 0

        command = ' '.join([
            f'convert',
            f'"{self.logo.resolve()}"',
            f'-resize 1460x',
            f'-resize x750\>',
            f'-format "%[h]"',
            f'info:',
        ])

        return int(self.image_magick.run_get_output(command))


    @property
    def gradient_commands(self) -> ImageMagickCommands:
        """Subcommands to overlay the gradient to the source image."""

        # If omitting the gradient, return empty commands
        if self.omit_gradient:
            return []

        # Top placement, rotate gradient
        if self.text_placement == 'top':
            return [
                f'\( "{self.GRADIENT_OVERLAY.resolve()}"',
                f'-rotate 180 \)',
                f'-compose Darken',
                f'-composite',
            ]

        # Bottom placement, do not rotate
        return [
            f'"{self.GRADIENT_OVERLAY.resolve()}"',
            f'-compose Darken',
            f'-composite',
        ]


    @property
    def logo_commands(self) -> ImageMagickCommands:
        """Subcommands to overlay the logo to the source image."""

        # If omitting the logo, return empty commands
        if self.logo is None:
            return []

        # Offset and gravity are determined by placement
        gravity = {
            'top': 'north', 'middle': 'center', 'bottom': 'south'
        }[self.logo_placement]
        offset = {'top': 212, 'middle': 0, 'bottom': 356}[self.logo_placement]

        return [
            # Overlay logo
            f'\( "{self.logo.resolve()}"',
            # Fit to 1460px wide
            f'-resize 1460x',
            # Limit to 750px tall
            f'-resize x750\> \)',
            # Begin logo merge
            f'-gravity {gravity}',
            f'-compose Atop',
            f'-geometry +0{offset:+}',
            # Merge logo and source
            f'-composite',
        ]


    @property
    def text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the text to the image."""

        font_size = 20.0 * self.font_size
        kerning = 30 * self.font_kerning

        # Determine season text offset depending on orientation
        if self.text_placement == 'top':
            if self.logo is None or self.logo_placement != 'top':
                text_offset = 212
            else:
                text_offset = 212 + self.__get_logo_height() + 60
        else:
            text_offset = self.POSTER_HEIGHT - 295
        text_offset += self.font_vertical_shift

        return [
            f'-gravity north',
            f'-font "{self.font.resolve()}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {font_size}',
            f'-kerning {kerning}',
            f'-annotate +0+{text_offset} "{self.season_text}"',
        ]


    def create(self) -> None:
        """Create the season poster defined by this object."""

        # Exit if source or logo DNE
        if (not self.source.exists()
            or (self.logo is not None and not self.logo.exists())):
            return None

        # Create parent directories
        self.destination.parent.mkdir(parents=True, exist_ok=True)

        # Create the command
        command = ' '.join([
            f'convert',
            f'-density 300',
            # Resize input image
            f'"{self.source.resolve()}"',
            f'-gravity center',
            f'-resize "{self.SEASON_POSTER_SIZE}^"',
            f'-extent "{self.SEASON_POSTER_SIZE}"',
            # Apply gradient
            *self.gradient_commands,
            # Add logo
            *self.logo_commands,
            # Write season text
            *self.text_commands,
            f'"{self.destination.resolve()}"',
        ])

        self.image_magick.run(command)
        return None
