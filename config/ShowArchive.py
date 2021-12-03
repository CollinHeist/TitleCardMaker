from pathlib import Path

from Show import Show

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
        'none-custom':     'No Season Titles, Custom Font',
        'none-generic':    'No Season Titles, Generic Font',
    }

    def __init__(self, archive_directory: Path, *args: tuple,
                 **kwargs: dict) -> None:

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
        
        base_show = Show(*args, **kwargs)

        self.shows = []
        for profile_string in base_show.profile._get_valid_profile_strings():
            # Create show object for this profile
            show = Show(*args, **kwargs)

            # Update media directory, update profile and parse source
            show.media_directory = (
                archive_directory / show.full_name / self.PROFILE_DIRECTORY_MAP[profile_string]
            )
            show.profile.convert_profile_string(profile_string)
            show.read_source()

            self.shows.append(show)


    def update_archive(self, *args: tuple, **kwargs: dict) -> int:
        """
        Call `create_missing_title_cards()` on each archive-specific
        `Show` object in this object. This effectively creates all missing
        title cards for each profile.
        
        :param      args:    The arguments

        :param      kwargs:  The keywords arguments
        """
        for show in self.shows:
            show.create_missing_title_cards(*args, **kwargs)

