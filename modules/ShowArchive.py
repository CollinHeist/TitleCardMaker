from copy import copy

from modules.Debug import log
from modules.ShowSummary import ShowSummary
import modules.global_objects as global_objects

class ShowArchive:
    """
    This class describes a show archive. This is an object that contains
    modified Show objects, each of which is used to create an update an archive
    directory for a specific type of profile. Collectively every possible
    profile is maintained.

    The following profiles are created depending on whether this show has custom
    season titles, custom fonts, and hidden season titles:

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

    __slots__ = ('series_info', '__base_show', 'shows', 'summaries')


    def __init__(self, archive_directory: 'Path', base_show: 'Show') -> None:
        """
        Constructs a new instance of this class. Creates a list of all
        applicable Show objects for later us.
        
        :param      archive_directory:  The base directory where this
                                        show should generate its archive.
        :param      base_show:          Base Show this Archive is based on.
        """

        # If the base show for this object has archiving disabled, exit
        self.series_info = base_show.series_info
        self.__base_show = base_show

        # Empty lists to be populated with modified Show and ShowSummary objects
        self.shows = []
        self.summaries = []

        # For each applicable sub-profile, create+modify new Show/ShowSummary
        card_class = base_show.card_class
        valid_profiles = base_show.profile.get_valid_profiles(card_class)

        # Go through each valid profile
        for profile_attributes in valid_profiles:
            # Create show object for this profile
            new_show = copy(base_show)

            # Update media directory
            profile_directory = self.PROFILE_DIRECTORY_MAP[
                f'{profile_attributes["seasons"]}-{profile_attributes["font"]}'
            ]

            # For non-standard card classes, modify archive directory name
            if base_show.card_class.ARCHIVE_NAME != 'standard':
                profile_directory += f' - {base_show.card_class.ARCHIVE_NAME}'

            temp_path = archive_directory / base_show.series_info.legal_path
            new_show.media_directory = temp_path / profile_directory

            # Convert this new show's profile
            new_show.profile.convert_profile(
                base_show.card_class,
                **profile_attributes
            )

            # Store this new Show and associated ShowSummary
            self.shows.append(new_show)
            self.summaries.append(
                ShowSummary(
                    new_show,
                    global_objects.pp.summary_background_color
                )
            )


    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object."""

        return (f'<ShowArchive for {self.series_info} with {len(self.shows)} '
                f'profiles>')


    def read_source(self) -> None:
        """Call read_source() on each Show object in this archive."""

        # Read the source of every sub-Show in this Archive
        for show in self.shows:
            show.read_source()


    def find_multipart_episodes(self) -> None:
        """
        Call find_multipart_episodes() on each Show object in this archive.
        """

        # Look for multiparts in every sub-Show in this Archive
        for show in self.shows:
            show.find_multipart_episodes()


    def query_sonarr(self, *args: tuple, **kwargs: dict) -> None:
        """
        Call query_sonarr() on each Show object in this archive.

        :param      args and kwargs:    The arguments to pass directly to
                                        Show.query_sonarr().
        """

        # Query Sonarr for each show (updates episode ID's, namely)
        for show in self.shows:
            show.query_sonarr(*args, **kwargs)


    def update_archive(self, *args: tuple, **kwargs: dict) -> None:
        """
        Create all missing title cards for each Show object in this archive.
        
        :param      args and kwargs:    The arguments to pass directly to
                                        Show.create_missing_title_cards().
        """

        # Create missing cards for each Show object in this archive
        for show in self.shows:
            show.create_missing_title_cards(*args, **kwargs)


    def create_summary(self, tmdb_interface: 'TMDbInterface'=None) -> None:
        """
        Create the ShowSummary image for each archive in this object. And if the
        required logo doesn't exist, attempt to download it.

        :param      tmdb_interface: TMDb interface to query for a logo file, if
                                    there is not an existing one.
        """

        # Go through each ShowSummary object within this Archive
        for summary in self.summaries:
            # If summary already exists, skip
            if summary.output.exists():
                continue

            # If the logo doesn't exist, and we're given a TMDBInterface,
            # attempt to download the best logo
            if not summary.logo.exists() and tmdb_interface:
                # If no logo was returned, skip
                if not (logo:=tmdb_interface.get_series_logo(self.series_info)):
                    return None

                # If a valid logo was returned, download it
                log.debug(f'Downloading logo for {self.series_info}')

                # If the returned logo was SVG, convert to PNG
                if logo.endswith('.svg'):
                    # Download SVG to temp file, convert to PNG
                    tmdb_interface.download_image(
                        logo,
                        summary._TEMP_SVG_FILENAME
                    )
                    summary.convert_svg_to_png()
                else:
                    # Download non-SVG file
                    tmdb_interface.download_image(logo, summary.logo)
            
            # If the logo exists, create summary
            summary.create()

            # If the summary exists, log that
            if summary.output.exists():
                log.debug(f'Created ImageSummary {summary.output.resolve()}')

