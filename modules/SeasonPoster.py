from cgitb import text
from pathlib import Path

from modules.Debug import log
from modules.ImageMaker import ImageMaker

class SeasonPoster(ImageMaker):
    """
    This class describes a type of ImageMaker that creates season posters.
    Season posters take images, add a logo and season title.
    """

    """Default size of all season posters"""
    SEASON_POSTER_SIZE = '2000x3000'

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' /'season_poster'

    """Default font values for the season text"""
    SEASON_TEXT_FONT = REF_DIRECTORY / 'Proxima Nova Semibold.otf'
    SEASON_TEXT_COLOR = '#CFCFCF'

    """Paths for the gradient overlay"""
    GRADIENT_OVERLAY = REF_DIRECTORY / 'gradient.png'

    __slots__ = ('source', 'destination', 'logo', 'season_text', 'font',
                 'font_color', 'font_size', 'font_kerning', 'top_placement',
                 'omit_gradient')


    def __init__(self, source: Path, logo: Path, destination: Path, 
                 season_text: str, font: Path=SEASON_TEXT_FONT,
                 font_color: str=SEASON_TEXT_COLOR, font_size: float=1.0,
                 font_kerning: float=1.0, top_placement: bool=False,
                 omit_gradient: bool=False) -> None:
        """
        Initialize this SeasonPoster object. This stores these attributes.

        Args:
            source: Path to the source image to use for the poster.
            logo: Path to the logo file to use on the poster.
            destination: Path to the desination file to write the poster at.
            season_text: Season text to utilize on the poster.
            font: Path to the font file to use for the season text.
            font_color: Font color to use for the season text.
            font_size: Font size scalar to use for the season text.
            font_kerning: Font kerning scalar to use for the season text.
            top_placement: Whether to place the logo and season text on the top
                of the created poster (True), or the bottom (False).
            omit_gradient: Whether to omit the gradient overlay.
        """

        # Initialize parent object for the ImageMagickInterface
        super().__init__()
        
        # Store provided file attributes
        self.source = source
        self.destination = destination
        self.logo = logo

        # Store text attributes
        self.season_text = season_text.upper()

        # Store customized font attributes
        self.font = font
        self.font_color = font_color
        self.font_size = font_size
        self.font_kerning = font_kerning
        self.top_placement = top_placement
        self.omit_gradient = omit_gradient


    def __get_logo_height(self, logo: Path) -> int:
        """
        Get the logo height of the logo after it will be resized.

        Args:
            logo: Path to the logo being resized.

        Returns:
            Integer height (in pixels) of the resized logo.
        """
        
        command = ' '.join([
            f'convert',
            f'"{logo.resolve()}"',
            f'-resize 1460x',
            f'-resize x750\>',
            f'-format "%[h]"',
            f'info:',
        ])

        return int(self.image_magick.run_get_output(command))


    def create(self) -> None:
        """Create the season poster defined by this object."""

        # Exit if source or logo DNE
        if not self.source.exists() or not self.logo.exists():
            return None

        # Create parent directories
        self.destination.parent.mkdir(parents=True, exist_ok=True)

        # Get the scaled values for this poster
        font_size = 20.0 * self.font_size
        kerning = 30 * self.font_kerning

        # How to add gradient; rotated if using top placement/optionally omitted
        if self.omit_gradient:
            gradient_command = []
        elif self.top_placement:
            gradient_command = [
                f'\( "{self.GRADIENT_OVERLAY.resolve()}"',
                f'-rotate 180 \)',
                f'-compose Darken',
                f'-composite',
            ]
        else:
            gradient_command = [
                f'"{self.GRADIENT_OVERLAY.resolve()}"',
                f'-compose Darken',
                f'-composite',
            ]

        # Top/bottom placement determines gravity and offsets
        merge_gravity = 'north' if self.top_placement else 'south'

        # Determine logo placement offset depending on  orientation
        logo_offset = '+212' if self.top_placement else '+356'

        # Determine season text offset depending on orientation
        if self.top_placement:
            text_offset = 212 + self.__get_logo_height(self.logo) + 60
        else:
            text_offset = 212

        # Create the command
        command = ' '.join([
            f'convert',
            f'-density 300',
            f'"{self.source.resolve()}"',           # Resize input image
            f'-gravity center',                         # Crop around center
            f'-resize "{self.SEASON_POSTER_SIZE}^"',    # Force into 2000x3000
            f'-extent "{self.SEASON_POSTER_SIZE}"',
            *gradient_command,                      # Apply gradient
            f'\( "{self.logo.resolve()}"',          # Add logo
            f'-resize 1460x',                           # Fit to 1460px wide
            f'-resize x750\> \)',                       # Limit to 750px tall
            f'-gravity {merge_gravity}',                # Begin logo merge
            f'-compose Atop',
            f'-geometry +0{logo_offset}',               # Offset from top/bottom
            f'-composite',                              # Merge images
            f'-font "{self.font.resolve()}"',       # Write season text
            f'-fill "{self.font_color}"',
            f'-pointsize {font_size}',
            f'-kerning {kerning}',
            f'-annotate +0+{text_offset} "{self.season_text}"',
            f'"{self.destination.resolve()}"',
        ])

        self.image_magick.run(command)