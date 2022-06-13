from pathlib import Path

from modules.Debug import log
from modules.ImageMaker import ImageMaker

class SeasonPoster(ImageMaker):
    """
    This class describes a type of ImageMaker that creates season posters.
    Season posters take images, add a logo and season title.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' /'season_poster'

    """Default font values for the season text"""
    SEASON_TEXT_FONT = REF_DIRECTORY / 'Proxima Nova Semibold.otf'
    SEASON_TEXT_COLOR = '#CFCFCF'

    """Paths for the gradient overlay"""
    GRADIENT_OVERLAY = REF_DIRECTORY / 'gradient.png'

    __slots__ = ('source', 'destination', 'logo', 'season_text', 'font',
                 'font_color', 'font_size', 'font_kerning')


    def __init__(self, source: Path, logo: Path, destination: Path, 
                 season_text: str, font: Path=SEASON_TEXT_FONT,
                 font_color: str=SEASON_TEXT_COLOR, font_size: float=1.0,
                 font_kerning: float=1.0) -> None:
        """
        Constructs a new instance.
        
        :param      source:         The source file.
        :param      logo:           The logo file.
        :param      destination:    The destination of this poster.
        :param      season_text:    The season text.
        :param      font:           Font file for season text.
        :param      font_color:     Font color for season text.
        :param      font_size:      Scalar of season text.
        :param      kerning:        Scalar of season text kerning.
        """

        # Initialize parent object
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

        # Create the command
        command = ' '.join([
            f'convert',
            f'-density 300',
            f'"{self.source.resolve()}"',           # Resize input image
            f'-gravity center',         
            f'-resize "2000x3000^"',                    # Force into 2000x3000
            f'-extent "2000x3000"',
            f'"{self.GRADIENT_OVERLAY.resolve()}"', # Apply gradient
            f'-compose Darken',                         # Darken mode
            f'-composite',                              # Merge images
            f'\( "{self.logo.resolve()}"',          # Add logo
            f'-resize 1460x \)',                        # Fit to 730px wide
            f'-gravity south',                          # Begin merge placement
            f'-compose Atop',       
            f'-geometry +0+356',                        # Offset 178px from base
            f'-composite',                              # Merge images
            f'-font "{self.font.resolve()}"',       # Write season text
            f'-fill "{self.font_color}"',
            f'-pointsize {font_size}',
            f'-kerning {kerning}',
            f'-annotate +0+212 "{self.season_text}"',
            f'"{self.destination.resolve()}"',
        ])

        self.image_magick.run(command)

