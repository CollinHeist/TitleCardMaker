from pathlib import Path

from modules.Debug import log
from modules.BaseSummary import BaseSummary

class StylizedSummary(BaseSummary):
    """
    This class describes a type of Summary image maker. This is a more stylized
    summary (compared to the StandardSummary) that uses a (max) 4x3 grid of
    images, and creates a reflection of that grid. There is a logo at the top,
    as well.

    This type of Summary does not support any background aside from black.
    """

    """Default (and only allowed) background color for this Summary"""
    BACKGROUND_COLOR = 'black'

    """Paths to intermediate images created by this object"""
    __MONTAGE_PATH = BaseSummary.TEMP_DIR / 'montage.png'
    __RESIZED_LOGO_PATH = BaseSummary.TEMP_DIR / 'resized_logo.png'


    def __init__(self, show: 'Show', background: str=BACKGROUND_COLOR,
                 created_by: str=None) -> None:
        """
        Construct a new instance of this object.

        Args:
            show: Show object to create the Summary for.
            background: Background color or image to use for the summary. This
                is ignored and 'black' is always used.
            created_by: Optional string to use in custom "Created by .." tag at
                the botom of this Summary. Defaults to None.
        """

        # Initialize parent Summary object
        super().__init__(show, created_by)


    def __create_montage(self) -> Path:
        """
        Create a montage of input images.
        
        Returns:
            Path to the created image.
        """

        command = ' '.join([
            f'montage',
            f'-set colorspace sRGB',
            f'-background "{self.BACKGROUND_COLOR}"',
            f'-tile 3x{self.number_rows}',
            f'-geometry 800x450\>+5+5',
            f'"'+'" "'.join(self.inputs)+'"',
            f'"{self.__MONTAGE_PATH.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__MONTAGE_PATH


    def __resize_logo(self, max_width: int) -> Path:
        """
        Resize this associated show's logo to fit into at least a 350 pixel
        high space. If the resulting logo is wider than the given width, it is
        scaled.
        
        Returns:
            Path to the resized logo.
        """

        command = ' '.join([
            f'convert',
            f'"{self.logo.resolve()}"',
            f'-resize x350',
            f'-resize {max_width}x350\>',
            f'"{self.__RESIZED_LOGO_PATH.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__RESIZED_LOGO_PATH


    def create(self) -> None:
        """
        Create the Summary defined by this object. Image selection is done at
        the start of this function.
        """

        # Exit if a logo does not exist
        if not self.logo.exists():
            log.warning('Cannot create Summary - no logo found')
            return None

        # Select images for montaging
        if not self._select_images(12) or len(self.inputs) == 0:
            return None

        # Create montage
        montage = self.__create_montage()

        # Get dimensions of montage
        dimensions = self.get_image_dimensions(montage)
        width, height = dimensions['width'], dimensions['height']

        # Resize logo
        resized_logo = self.__resize_logo(width)

        # Get dimension of logo
        logo_height = self.get_image_dimensions(resized_logo)['height']

        # Get/create created by tag
        if self.created_by is None:
            created_by = self._CREATED_BY_PATH
        else:
            created_by = self._create_created_by(self.created_by)
            
        command = ' '.join([
            f'convert "{montage.resolve()}"',
            f'\( +clone',                       # Create reflection of montage
            f'-flip',
            f'-blur 0x8',                       # Blur reflection
            f'-fill black',                     # Darken reflection
            f'-colorize 75% \)',
            f'-append',
            f'-size {width+200}x{height+700}',  # Create colored background
            f'xc:"{self.BACKGROUND_COLOR}"',          
            f'+swap',                           # Reverse reflection/montage(s)
            f'-gravity north',                  # Put montage+reflection on bg
            f'-geometry +0+400',
            f'-composite',
            f'\( {created_by.resolve()}',       # Append created by image
            f'-resize x75',
            f'\( +clone',                       # Create created by reflection
            f'-flip',
            f'-blur 0x2',
            f'-fill black',                     # Darken reflection
            f'-colorize 75% \)',
            f'-append \)',
            f'-gravity south',
            f'-geometry +0+50',
            f'-composite',
            f'-gravity north',
            f'"{resized_logo.resolve()}"',      # Add logo
            f'-geometry +0+{400//2-logo_height//2}',
            f'-composite',
            f'"{self.output.resolve()}"',
        ])

        self.image_magick.run(command)

        # Delete intermediate images
        if self.created_by is None:
            images = [montage]
        else:
            images = [montage, created_by]
        self.image_magick.delete_intermediate_images(*images)    