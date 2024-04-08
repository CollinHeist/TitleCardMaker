from pathlib import Path
from typing import TYPE_CHECKING, Callable

from modules.Debug import log
from modules import global_objects

if TYPE_CHECKING:
    from modules.Show import Show


class ShowArchive:
    """
    This class describes a show archive. This is an object that contains
    modified Show objects, each of which is used to create an update an
    archive directory for a specific type of profile. Collectively every
    possible profile is maintained.

    The following profiles are created depending on whether this show
    has custom season titles, custom fonts, and hidden season titles:

        Custom |        | Hidden |
        Season | Custom | Season | Output
        Title  |  Font  | Titles | Directories
        -------|--------|--------|-------------
            0  |    0   |    0   | Generic Season Titles, Generic Font
            0  |    0   |    1   | 000 + No Season Titles, Generic Font
            0  |    1   |    0   | 000 + Generic Season Titles, Custom Font
            0  |    1   |    1   | 010 + No Season Titles, Custom Font
            1  |    0   |    0   | 000 + Custom Season Titles, Generic Font
            1  |    0   |    1   | 100 + No Season Titles, Generic Font
            1  |    1   |    0   | 100 + Generic Season Titles, Custom Font
            1  |    1   |    1   | 110 + No Season Titles, Custom Font
    """

    """Map of season/font attributes and matching directory titles"""
    PROFILE_DIRECTORY_MAP: dict = {
        'custom-custom':   'Custom Season Titles, Custom Font',
        'custom-generic':  'Custom Season Titles, Generic Font',
        'generic-custom':  'Generic Season Titles, Custom Font',
        'generic-generic': 'Generic Season Titles, Generic Font',
        'hidden-custom':   'No Season Titles, Custom Font',
        'hidden-generic':  'No Season Titles, Generic Font',
    }

    __slots__ = ('series_info', 'shows', 'summaries')


    def __init__(self,
            archive_directory: Path,
            base_show: 'Show',
        ) -> None:
        """
        Constructs a new instance of this class. Creates a list of all
        applicable Show objects for later us.

        Args:
            archive_directory: The base directory where this show should
                generate its archive.
            base_show: Base Show this Archive is based on.
        """

        # If the base show for this object has archiving disabled, exit
        self.series_info = base_show.series_info

        # Empty lists to be populated with modified Show and Summary objects
        self.shows = []
        self.summaries = []

        # For each applicable sub-profile, create+modify new Show/Summary
        card_class = base_show.card_class
        valid_profiles = base_show.profile.get_valid_profiles(
            card_class, base_show.archive_all_variations, base_show.extras,
        )

        # Go through each valid profile
        for attributes in valid_profiles:
            # Get directory name for this profile
            if base_show.archive_name is None:
                # Get directory base from the directory map
                key = f'{attributes["seasons"]}-{attributes["font"]}'
                profile_directory = self.PROFILE_DIRECTORY_MAP[key]

                # For non-standard card classes, modify profile directory name
                if base_show.card_class.ARCHIVE_NAME != 'standard':
                    profile_directory+=f' - {base_show.card_class.ARCHIVE_NAME}'
            # Manually specified archive name
            else:
                profile_directory = base_show.archive_name

            # Get modified media directory within the archive directory
            temp_path = archive_directory /base_show.series_info.full_clean_name
            new_media_directory = temp_path / profile_directory

            # Create modified Show object for this profile
            new_show = base_show._make_archive(new_media_directory)

            # Convert this new show's profile if no manual archive name
            if base_show.archive_name is None:
                new_show.profile.convert_profile(**attributes)
                if not new_show.profile._Profile__use_custom_seasons:
                    new_show.episode_text_format = \
                        new_show.card_class.EPISODE_TEXT_FORMAT

            # Override any extras
            new_show.profile.convert_extras(new_show.card_class,new_show.extras)

            # Store this new Show and associated Summary
            self.shows.append(new_show)
            self.summaries.append(
                global_objects.pp.summary_class(
                    new_show,
                    global_objects.pp.summary_background,
                    global_objects.pp.summary_created_by,
                )
            )

        if self.shows:
            self.shows[0]._is_sub_archive = False


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'"{self.series_info.full_name}"'


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return (f'<ShowArchive for {self.series_info} with {len(self.shows)} '
                f'profiles>')


    def __getattr__(self, show_function: Callable) -> Callable:
        """
        Get an arbitrary function for this object. This returns a wrapped
        version of the given function that calls that function on all
        Show objects within this Archive.

        Args:
            show_function: The function to wrap.

        Returns:
            Wrapped callable that is the indicated function called on
            each Show object within this Archive.
        """

        # Define wrapper that calls given function on all Shows of this object
        def wrapper(*args, **kwargs) -> None:
            # Iterate through each show and call the given function
            for show in self.shows:
                getattr(show, show_function)(*args, **kwargs)

        # Return "attribute" that is the wrapped function applied to all shows
        # within this archive
        return wrapper


    def create_summary(self) -> None:
        """Create the Summary image for each archive in this object."""

        # Go through each Summary object within this Archive
        for summary in self.summaries:
            # If summary already exists, skip
            if summary.output.exists() or not summary.logo.exists():
                continue

            # Create summary image
            summary.create()

            # If the summary exists, log that
            if summary.output.exists():
                log.debug(f'Created Summary {summary.output.resolve()}')
