from copy import deepcopy
from pathlib import Path

from modules.Debug import *
from modules.Show import Show
from modules.ShowSummary import ShowSummary

class ShowArchive:
    """
    This class describes a show archive. This is an object that contains
    modified `Show` objects, each of which is used to create an update an
    archive directory for a specific type of profile. Collectively every
    possible profile is maintained.

    The following profiles are created depending on whether this show has
    custom season titles, custom fonts, and hidden season titles:

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

    PROFILE_DIRECTORY_MAP: dict = {
        'custom-custom':   'Custom Season Titles, Custom Font',
        'custom-generic':  'Custom Season Titles, Generic Font',
        'generic-custom':  'Generic Season Titles, Custom Font',
        'generic-generic': 'Generic Season Titles, Generic Font',
        'hidden-custom':   'No Season Titles, Custom Font',
        'hidden-generic':  'No Season Titles, Generic Font',
    }

    def __init__(self, archive_directory: Path, base_show: 'Show') -> None:

        """
        Constructs a new instance of this class. Creates a list of all
        applicable Show objects for later us.
        
        :param      archive_directory:  The base directory where this
                                        show should generate its archive. i.e.
                                        `/Documents/` would operate on 
                                        `/Documents/Title (Year)/...`.

        :param      args and kwargs:    Arguments passed directly to initialize 
                                        a `Show` object with.
        """
        
        # Empty lists to be populated with modified Show and ShowSummary objects
        self.shows = []
        self.summaries = []

        self.__base_show = base_show
        if not base_show.archive:
            return

        # For each applicable sub-profile, create and modify new show/show summary
        for profile_attributes in base_show.profile._get_valid_profiles():
            # Create show object for this profile
            new_show = deepcopy(base_show)

            # Update media directory, update profile and parse source
            profile_string = f'{profile_attributes["seasons"]}-{profile_attributes["font"]}'
            new_show.media_directory = (
                archive_directory / new_show.full_name / self.PROFILE_DIRECTORY_MAP[profile_string]
            )
            new_show.profile.convert_profile_string(**profile_attributes)
            new_show.read_source()

            self.shows.append(new_show)
            self.summaries.append(ShowSummary(new_show))


    def read_source(self) -> None:
        """
        Calls `read_source()` on each show contained within this archive.
        """

        for show in self.shows:
            show.read_source()


    def update_archive(self, *args: tuple, **kwargs: dict) -> None:
        """
        Call `create_missing_title_cards()` on each archive-specific
        `Show` object in this object. This effectively creates all missing
        title cards for each profile.
        
        :param      args:    The arguments

        :param      kwargs:  The keywords arguments
        """
        info(f'Updating archive for "{self.__base_show.full_name}"')
        for show in self.shows:
            show.create_missing_title_cards(*args, **kwargs)


    def create_summary(self) -> None:
        """
        Creates a summary.
        """

        for show in self.summaries:
            show.create()

