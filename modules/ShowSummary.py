from math import ceil
from pathlib import Path
from random import sample

from modules.Debug import log
from modules.StandardTitleCard import StandardTitleCard
from modules.ImageMaker import ImageMaker

class ShowSummary(ImageMaker):
    """
    This class describes a show summary. A show summary is a random subset of
    title cards from a show's profile, montaged into (at most) a 3x3 grid, with
    a logo at the top. The intention is to quickly visually identify the title
    cards.

    This class is a type of ImageMaker.
    """

    """Default color for the background of the summary image"""
    BACKGROUND_COLOR = '#1A1A1A'

    """Default filename of logo files"""
    LOGO_FILENAME = 'logo.png'

    """Temporary path for SVG files being converted"""
    _TEMP_SVG_FILENAME = ImageMaker.TEMP_DIR / 'logo.svg'

    """Paths to intermediate images created in the process of making a summary."""
    __MONTAGE_PATH = ImageMaker.TEMP_DIR / 'montage.png'
    __MONTAGE_WITH_HEADER_PATH = ImageMaker.TEMP_DIR / 'header.png'
    __RESIZED_LOGO_PATH = ImageMaker.TEMP_DIR / 'resized_logo.png'
    __LOGO_AND_HEADER_PATH = ImageMaker.TEMP_DIR / 'logo_and_header.png'
    
    """Path to the 'created by' image to add to all show summaries"""
    __CREATED_BY_PATH: Path = Path(__file__).parent / 'ref' / 'created_by.png'


    def __init__(self, show: 'Show') -> None:
        """
        Constructs a new instance of this object. This initialized a
        ImageMagickInterface object, and searches the provided show object
        for existing title cards to use in `create()`.
        
        :param      show:  The show object of which to create a summary for.
        """

        # Initialize parent object (for the ImageMagickInterface)
        super().__init__()
        
        # This summary's logo is an attribute of the provided show
        self.show = show
        self.logo = show.logo

        # Output file is stored in the top-level media directory (usually an archive folder)
        self.output = show.media_directory / 'Summary.jpg'

        # Initialize variables that will be set upon image selection
        self.inputs = []
        self.number_rows = 0


    def __select_images(self) -> None:
        """
        Select the images that are to be incorporated into the show summary.
        This updates the object's inputs and number_rows attributes.
        """
        
        # Filter out episodes that don't have an existing title card
        available_episodes = list(filter(
            lambda e: self.show.episodes[e].destination.exists(),
            self.show.episodes
        ))

        # Warn if this show has no episodes to work with
        if (episode_count := len(available_episodes)) == 0:
            return None

        # Skip if the number of available episodes is below the minimum
        minimum = self.preferences.summary_minimum_episode_count
        if episode_count < minimum:
            log.info(f'Skipping ShowSummary - {self.show} has {episode_count} '
                     f'episodes, minimum setting is {minimum}')
            return None

        # Get a random subset of images to create the summary with
        # Sort that subset my season/episode number so the montage is ordered
        episode_keys = sorted(
            sample(available_episodes, min(episode_count, 9)),
            key=lambda k: int(k.split('-')[0])*1000+int(k.split('-')[1])
        )

        # Get the full filepath for each of the selected images
        get_destination = lambda e_key: self.show.episodes[e_key].destination
        self.inputs = [
            str(get_destination(e).resolve()) for e in episode_keys
        ]

        # The number of rows is necessary to determine how to scale y-values
        self.number_rows = ceil(len(episode_keys) / 3)


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
        Pad 80 pixels of blank space around the image, and add a header of text
        that says "EPISODE TITLE CARDS".
        
        :param      montage:    The montage of images to add a header to.
        
        :returns:   Path to the created image.
        """

        command = ' '.join([
            f'convert "{montage.resolve()}"',
            f'-resize 50%',
            f'-background "{self.BACKGROUND_COLOR}"',
            f'-gravity north',
            f'-splice 0x840',
            f'-font "{StandardTitleCard.EPISODE_COUNT_FONT}"',
            f'-fill "{StandardTitleCard.SERIES_COUNT_TEXT_COLOR}"',
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
        high space. If the resulting logo is wider than 3400 pixels, it is
        scaled.
        
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
        Gets the height of the provided logo.
        
        :param      logo:  The path to the logo image.
        
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
        
        :param      montage:    Path to the montage image to add the logo to.
        :param      logo:       Path to the logo image to add to the montage.

        :returns:   Path to the created images.
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
        Adds the "CREATED BY COLLINHEIST" text (image at `__CREATED_BY_PATH`) to
        the bottom of the image.
        
        :param      montage_and_logo:   Path to the montage with the logo
                                        already applied.
        
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


    def convert_svg_to_png(self) -> Path:
        """
        Convert the temporary SVG logo (located at _TEMP_SVG_FILENAME) and write
        it to this ShowSummary's logo file.
        
        :returns:   Path to the created file (this summary's logo file).
        """

        # If the temp file doesn't exist, return
        if not self._TEMP_SVG_FILENAME.exists():
            return None

        # Convert file to PNG
        command = ' '.join([
            f'convert',
            f'-density 512',
            f'-resize x1024',
            f'-background None',
            f'"{self._TEMP_SVG_FILENAME.resolve()}"',
            f'"{self.logo.resolve()}"',
        ])

        self.image_magick.run(command)
        
        # Delete SVG file
        self.image_magick.delete_intermediate_images(self._TEMP_SVG_FILENAME)

        return self.logo


    def create(self) -> None:
        """
        Create the ShowSummary defined by this show object. Image selection is
        done at the start of this function.
        """

        # Select images for montaging
        self.__select_images()

        # If there are no title cards to montage
        if len(self.inputs) == 0:
            return None

        # Exit if a logo does not exist
        if not self.logo.exists():
            log.warning('Cannot create ShowSummary - no logo found')
            return None

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

        # Delete temporary files
        self.image_magick.delete_intermediate_images(
            montage, montage_and_header, logo, montage_and_logo
        )


