from abc import abstractmethod
from math import ceil
from pathlib import Path
from random import sample
from typing import Optional

from modules.Debug import log
from modules.ImageMaker import ImageMaker


class BaseSummary(ImageMaker):
    """
    This class describes a type of ImageMaker that specializes in
    creating Show summaries. These are montage images that display a
    random selection of  title cards for a given Show object in order to
    give a quick visual indicator as to the style of the cards.

    This object cannot be instantiated directly, and only provides very
    few methods that can/should be used by all Summary subclasses.
    """

    """Directory where all reference files are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'summary'

    BACKGROUND_COLOR = '#1A1A1A'

    """Path to the 'created by' image to add to all show summaries"""
    _CREATED_BY_PATH = REF_DIRECTORY / 'created_by.png'

    """Configuration for the created by image creation"""
    HEADER_FONT = REF_DIRECTORY.parent / 'Proxima Nova Regular.otf'
    __CREATED_BY_FONT = REF_DIRECTORY.parent / 'star_wars' / 'HelveticaNeue.ttc'
    __TCM_LOGO = REF_DIRECTORY / 'logo.png'
    __CREATED_BY_TEMPORARY_PATH = ImageMaker.TEMP_DIR / 'user_created_by.png'

    __slots__ = ('show', 'logo', 'created_by', 'output', 'inputs','number_rows')


    @abstractmethod
    def __init__(self,
            show: 'Show', # type: ignore
            created_by: Optional[str] = None,
        ) -> None:
        """
        Initialize this object.

        Args:
            show: The Show object to create the Summary for.
            background: Background color or image to use for the
                summary. Can also be a "format string" that is
                "{series_background}" to use the given Show object's
                backdrop.
            created_by: Optional string to use in custom "Created by .."
                tag at the botom of this Summary.
        """

        # Initialize parent ImageMaker
        super().__init__()

        # Store object attributes
        self.show = show
        self.logo = show.logo
        self.created_by = created_by

        # Summary output is just below show media directory
        self.output = show.media_directory / 'Summary.jpg'

        # Initialize variables that will be set upon image selection
        self.inputs = []
        self.number_rows = 0


    def _select_images(self, maximum_images: int = 9) -> bool:
        """
        Select the images that are to be incorporated into the show
        summary. This updates the object's inputs and number_rows
        attributes.

        Args:
            maximum_images: maximum number of images to select.

        Returns:
            Whether the ShowSummary should/can be created.
        """

        # Filter out episodes that don't have an existing title card
        available_episodes = list(filter(
            lambda e: self.show.episodes[e].destination.exists(),
            self.show.episodes
        ))

        # Filter specials if indicated
        if self.preferences.summary_ignore_specials:
            available_episodes = list(filter(
                lambda e: self.show.episodes[e].episode_info.season_number != 0,
                available_episodes
            ))

        # Warn if this show has no episodes to work with
        if (episode_count := len(available_episodes)) == 0:
            return False

        # Skip if the number of available episodes is below the minimum
        minimum = self.preferences.summary_minimum_episode_count
        if episode_count < minimum:
            log.debug(f'Skipping Summary, {self.show} has {episode_count} '
                      f'episodes, minimum setting is {minimum}')
            return False

        # Get a random subset of images to create the summary with
        # Sort that subset my season/episode number so the montage is ordered
        episode_keys = sorted(
            sample(available_episodes, min(episode_count, maximum_images)),
            key=lambda k: int(k.split('-')[0])*1000+int(k.split('-')[1])
        )

        # Get the full filepath for each of the selected images
        self.inputs = [
            str(self.show.episodes[e].destination.resolve())
            for e in episode_keys
        ]

        # The number of rows is necessary to determine how to scale y-values
        self.number_rows = ceil(len(episode_keys) / 3)

        return True


    def _create_created_by(self, created_by: str) -> Path:
        """
        Create a custom "Created by" tag image. This image is formatted
        like: "Created by {input} with {logo} TitleCardMaker". The image
        is exactly  the correct size (i.e. fit to width of text).

        Returns:
            Path to the created image.
        """

        command = ' '.join([
            f'convert',
            # Create blank background
            f'-background transparent',
            # Create "Created by" image/text
            f'-font "{self.__CREATED_BY_FONT.resolve()}"',
            f'-pointsize 100',
            f'-fill "#CFCFCF"',
            f'label:"Created by"',
            # Create "{username}" image/text
            f'-fill "#DA7855"',
            f'label:"{created_by}"',
            # Create "with" image/text
            f'-fill "#CFCFCF"',
            f'label:"with"',
            # Resize TCM logo
            f'\( "{self.__TCM_LOGO.resolve()}"',
            f'-resize x100 \)',
            # Create "TitleCardMaker" image/text
            f'-fill "#5493D7"',
            f'label:"TitleCardMaker"',
            # Combine all text images with 30px padding
            f'+smush 30',
            f'"{self.__CREATED_BY_TEMPORARY_PATH.resolve()}"'
        ])

        self.image_magick.run(command)

        return self.__CREATED_BY_TEMPORARY_PATH
