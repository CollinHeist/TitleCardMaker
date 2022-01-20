from math import ceil
from pathlib import Path
from random import sample

from modules.Debug import *
from modules.Show import Show
from modules.TitleCardMaker import TitleCardMaker
from modules.ImageMaker import ImageMaker

class ShowSummary(ImageMaker):
    """
    This class describes a show summary. A show summary is a random subset of title
    cards from a show's profile, montaged into (at most) a 3x3 grid, with a logo at
    the top. The intention is to quickly visually identify the title cards.

    This class is a type of ImageMaker.
    """

    """Default color for the background of the summary image"""
    BACKGROUND_COLOR: str = '#1A1A1A'

    """Paths to intermediate images created in the process of making a summary."""
    __MONTAGE_PATH: Path = Path(__file__).parent / '.objects' / 'montage.png'
    __MONTAGE_WITH_HEADER_PATH: Path = Path(__file__).parent / '.objects' / 'header.png'
    __RESIZED_LOGO_PATH: Path = Path(__file__).parent / '.objects' / 'resized_logo.png'
    __LOGO_AND_HEADER_PATH: Path = Path(__file__).parent / '.objects' / 'logo_and_header.png'
    
    """Path to the 'created by' image to add to all show summaries"""
    __CREATED_BY_PATH: Path = Path(__file__).parent / 'ref' / 'created_by.png'

    def __init__(self, show: Show) -> None:
        """
        Constructs a new instance of this object. This initialized a
        ImageMagickInterface object, and searches the provided show object
        for existing title cards to use in `create()`.
        
        :param      show:  The show
        """

        # Initialize parent object (for the ImageMagickInterface)
        super().__init__()
        
        # This summary's logo is an attribute of the provided show
        self.show = show
        self.logo = show.logo

        # Filter out episodes that don't have an existing title card
        available_episodes = list(filter(
            lambda e: show.episodes[e].destination.exists(),
            show.episodes
        ))

        # Warn if this show has no episodes to work with
        episode_count = len(available_episodes)
        if episode_count == 0:
            warn(f'Cannot create Show Summary for {show.full_name} - has no episodes')

        # Get a random subset of images to create the summary with
        # Sort that subset my season/episode number so the montage appears chronological
        episode_keys = sorted(
            sample(available_episodes, min(episode_count, 9)),
            key=lambda k: int(k.split('-')[0])*1000+int(k.split('-')[1])
        )
        self.inputs = [
            str(show.episodes[episode].destination.resolve()) for episode in episode_keys
        ]

        # The number of rows is necessary to determine how to scale y-values
        self.number_rows = ceil(len(episode_keys) / 3)

        # Output file is stored in the top-level media directory (usually an archive folder)
        self.output = show.media_directory / 'Summary.jpg'


    def _create_montage(self) -> Path:
        """
        Create a (max) 3x3 montage of input images.
        
        :returns:   Path to the created image.
        """

        command = ' '.join([
            f'montage',
            f'-background "{self.BACKGROUND_COLOR}"',
            f'-density 300',
            f'-tile 3x3',
            f'-geometry +80+80',
            f'-shadow',
            f'"'+'" "'.join(self.inputs)+'"', # Wrap each filename in ""
            f'"{self.__MONTAGE_PATH.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__MONTAGE_PATH


    def _add_header(self, montage: Path) -> Path:
        """
        Pad 80 pixels of blank space around the image, and add a
        header of text that says "EPISODE TITLE CARDS".
        
        :param      montage:    The montage of images to adjust.
        
        :returns:   Path to the created image.
        """

        command = ' '.join([
            f'convert "{montage.resolve()}"',
            f'-resize 50%',
            f'-background "{self.BACKGROUND_COLOR}"',
            f'-gravity north',
            f'-splice 0x840',
            f'-font "{TitleCardMaker.EPISODE_COUNT_DEFAULT_FONT}"',
            f'-fill "{TitleCardMaker.SERIES_COUNT_DEFAULT_COLOR}"',
            f'-pointsize 100',
            f'-kerning 4.52',
            f'-annotate +0+700 "EPISODE TITLE CARDS"',
            f'-gravity east',
            f'-splice 80x0',
            f'-gravity south',
            f'-splice 0x{80+int(80*self.number_rows/3)}', # was 0x160
            f'-gravity west',
            f'-splice 80x0',
            f'"{self.__MONTAGE_WITH_HEADER_PATH.resolve()}"'
        ])

        self.image_magick.run(command)

        return self.__MONTAGE_WITH_HEADER_PATH


    def _resize_logo(self) -> Path:
        """
        Resize this associated show's logo to fit into at least a a 500 pixel
        high space. If the resulting logo is wider than 3400 pixels, it is scaled
        
        :returns:   Path to the resized logo.
        """

        command = ' '.join([
            f'convert',
            f'"{self.logo.resolve()}"',
            f'-resize x500 -resize 3400x500\>',
            f'"{self.__RESIZED_LOGO_PATH.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__RESIZED_LOGO_PATH


    def _get_logo_height(self, logo: Path) -> int:
        """
        Gets the logo height.
        
        :param      logo:  The path to the resized logo.
        
        :returns:   The logo height.
        """

        command = ' '.join([
            f'identify',
            f'-format "%h"',
            f'"{logo.resolve()}"',
        ])

        return int(self.image_magick.run_get_stdout(command))


    def _add_logo(self, montage: Path, logo: Path) -> Path:
        """
        Add the logo to the top of the montage image.
        
        :param      montage:  The montage
        :param      logo:     The logo
        """

        logo_height = self._get_logo_height(logo)

        command = ' '.join([
            f'composite',
            f'-gravity north',
            f'-geometry +0+{150+(500-logo_height)//2}',
            f'"{logo.resolve()}"',
            f'"{montage.resolve()}"',
            f'"{self.__LOGO_AND_HEADER_PATH.resolve()}"'
        ])

        self.image_magick.run(command)

        return self.__LOGO_AND_HEADER_PATH


    def _add_created_by(self, montage_and_logo: Path) -> Path:
        """
        Adds the "CREATED BY COLLINHEIST" text (image at 
        `__CREATED_BY_PATH`) to the bottom of the image.
        
        :param      montage_and_logo:  The montage and logo
        
        :returns:   Path to the created (output) image.
        """

        y_offset = (self.number_rows == 2) * 35 + (self.number_rows == 1) * 15
        command = ' '.join([
            f'composite',
            f'-gravity south',
            f'-geometry +0+{25+y_offset}',
            f'"{self.__CREATED_BY_PATH.resolve()}"',
            f'"{montage_and_logo.resolve()}"',
            f'"{self.output.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output


    def create(self) -> None:
        """
        Create the ShowSummary defined by this show object. The previously
        randomly selected images will be used, and all ImageMagick commands will
        be run through an `ImageMagickInterface`.
        """

        info(f'Creating ShowSummary for "{self.show.full_name}"')

        # If the summary already exists, or there are no title cards to montage
        if self.output.exists() or len(self.inputs) == 0:
            return

        # Exit if a logo does not exist
        if not self.logo.exists():
            warn('Cannot create ShowSummary; no logo found', 1)
            return

        # Create montage of title cards
        montage = self._create_montage()

        # Add header text and pad image with blank space
        montage_and_header = self._add_header(montage)

        # Resize show logo
        logo = self._resize_logo()

        # Add logo to the montage
        montage_and_logo = self._add_logo(montage_and_header, logo)

        # Add created by tag - summary is completed
        self._add_created_by(montage_and_logo)
        
        info(f'Created ImageSummary', 1)

        # Delete temporary files
        self.image_magick.delete_intermediate_images(
            montage, montage_and_header, logo, montage_and_logo
        )


