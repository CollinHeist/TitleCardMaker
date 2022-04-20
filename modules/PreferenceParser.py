from pathlib import Path

from tqdm import tqdm
from yaml import safe_load

from modules.Debug import log
from modules.ImageMagickInterface import ImageMagickInterface
from modules.ImageMaker import ImageMaker
from modules.Show import Show
from modules.ShowSummary import ShowSummary
from modules.TitleCard import TitleCard
from modules.TMDbInterface import TMDbInterface
from modules.YamlReader import YamlReader

class PreferenceParser(YamlReader):
    """
    This class describes a preference parser that reads a given preference YAML
    file and parses it into individual attributes.
    """

    def __init__(self, file: Path) -> None:
        """
        Constructs a new instance of this object. This reads the given file,
        errors and exits if any required options are missing, and then parses
        the preferences into object attributes.
        
        :param      file:   The preference file to parse.
        """

        super().__init__()
        
        # Store and read file
        self.file = file
        self.read_file()

        # Check for required source directory
        if not (source_directory := self['options', 'source']):
            breakpoint()
            log.critical(f'Preference file missing required options/source '
                         f'attribute')
            exit(1)
        self.source_directory = Path(source_directory)

        # Setup default values that can be overwritten by YAML
        self.series_files = []
        self.card_type = 'standard'
        self.card_filename_format = TitleCard.DEFAULT_FILENAME_FORMAT
        self.card_extension = TitleCard.DEFAULT_CARD_EXTENSION
        self.validate_fonts = True
        self.zero_pad_seasons = False
        self.archive_directory = None
        self.create_archive = False
        self.create_summaries = False
        self.summary_background_color = ShowSummary.BACKGROUND_COLOR
        self.logo_filename = ShowSummary.LOGO_FILENAME
        self.summary_minimum_episode_count = 1
        self.use_plex = False
        self.plex_url = None
        self.plex_token = 'NA'
        self.use_sonarr = False
        self.sonarr_url = None
        self.sonarr_api_key = None
        self.sonarr_sync_specials = True
        self.use_tmdb = False
        self.tmdb_api_key = None
        self.tmdb_retry_count = TMDbInterface.BLACKLIST_THRESHOLD
        self.tmdb_minimum_resolution = {'width': 0, 'height': 0}
        self.imagemagick_container = None

        # Modify object attributes based off YAML, assume valid to start
        self.valid = True
        self.__parse_yaml()

        # Whether to use magick prefix
        self.use_magick_prefix = False
        self.__determine_imagemagick_prefix()


    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object."""

        return f'<PreferenceParser {self.file=}>'


    def __determine_imagemagick_prefix(self) -> None:
        """
        Determine whether to use the "magick " prefix for ImageMagick commands.
        If a prefix cannot be determined, a critical message is logged and the
        program exits with an error.
        """

        # Try variations of the font list command with/out the "magick " prefix
        for prefix, use_magick in zip(('', 'magick '), (False, True)):
            # Create ImageMagickInterface object to test font command
            imi = ImageMagickInterface(self.imagemagick_container, use_magick)

            # Run font list command
            font_output = imi.run_get_output(f'convert -list font')

            # Check for standard font output to determine if it worked
            if all(_ in font_output for _ in ('Font:', 'family:', 'style:')):
                # Font command worked, exit function
                self.use_magick_prefix = use_magick
                log.debug(f'Using "{prefix}" ImageMagick command prefix')
                return None

        # If none of the font commands worked, IM might not be installed
        log.critical(f"ImageMagick doesn't appear to be installed")
        exit(1)


    def __parse_yaml(self) -> None:
        """
        Parse the raw YAML dictionary into object attributes. This also errors
        to the user if any provided values are overtly invalid (i.e. missing
        where necessary, fails type conversion).
        """

        if (value := self['options', 'series']):
            if isinstance(value, list):
                self.series_files = value
            else:
                self.series_files = [value]
        else:
            log.warning(f'No series YAML files indicated, no cards will be '
                        f'created')

        if (value := self['options', 'card_type']):
            if value not in TitleCard.CARD_TYPES:
                log.critical(f'Default card type "{value}" is unrecognized')
                self.valid = False
            else:
                self.card_type = value

        if (new_format := self['options', 'filename_format']):
            if not TitleCard.validate_card_format_string(new_format):
                self.valid = False
            else:
                self.card_filename_format = new_format

        if (extension := self['options', 'card_extension']):
            extension = ('' if extension[0] == '.' else '.') + extension.lower()
            if extension not in ImageMaker.VALID_IMAGE_EXTENSIONS:
                log.critical(f'Card extension "{extension}" is invalid')
                self.valid = False
            else:
                self.card_extension = extension

        if (value := self['options', 'validate_fonts']):
            self.validate_fonts = bool(value)

        if (value := self['options', 'zero_pad_seasons']):
            self.zero_pad_seasons = bool(value)

        if (value := self['archive', 'path']):
            self.archive_directory = Path(value)
            self.create_archive = True

        if (value := self['archive', 'summary', 'create']):
            self.create_summaries = bool(value)

        if (value := self['arhive', 'summary', 'background_color']):
            self.summary_background_color = value

        if (value := self['archive', 'summary', 'logo_filename']):
            self.logo_filename = value

        if (value := self['archive', 'summary', 'minimum_episodes']):
            try:
                self.summary_minimum_episode_count = int(value)
            except ValueError:
                log.critical(f'Invalid summary minimum count "{value}"')
                self.valid = False

        if (value := self['plex', 'url']):
            self.plex_url = value
            self.use_plex = True

        if (value := self['plex', 'token']):
            self.plex_token = value

        if self['sonarr']:
            if not all((self['sonarr', 'url'], self['sonarr', 'api_key'])):
                log.critical(f'Sonarr preferences must contain "url" and '
                             f'"api_key"')
                self.valid = False
            else:
                self.sonarr_url = self['sonarr', 'url']
                self.sonarr_api_key = self['sonarr', 'api_key']
                self.use_sonarr = True

        if (value := self['sonarr', 'sync_specials']):
            self.sonarr_sync_specials = bool(value)

        if (value := self['tmdb', 'api_key']):
            self.tmdb_api_key = value
            self.use_tmdb = True

        if (value := self['tmdb', 'retry_count']):
            self.tmdb_retry_count = int(value)

        if (value := self['tmdb', 'minimum_resolution']):
            try:
                width, height = map(int, value.lower().split('x'))
                self.tmdb_minimum_resolution = {'width': width, 'height':height}
            except Exception:
                log.critical(f'Invalid minimum resolution - specify as '
                             f'WIDTHxHEIGHT')
                self.valid = False

        if (value := self['imagemagick', 'container']):
            self.imagemagick_container = value


    def read_file(self) -> None:
        """
        Reads this associated preference file and store in `__yaml` attribute.

        If reading the YAML fails, the error is printed and the program exits.
        """

        # If the file doesn't exist, error and exit
        if not self.file.exists():
            log.critical(f'Preference file "{self.file.resolve()}" does not '
                         f'exist')
            exit(1)

        # Read file 
        self._base_yaml = self._read_file(self.file)

        # Log reading, return that YAML
        log.info(f'Read preference file "{self.file.resolve()}"')


    def iterate_series_files(self) -> [Show]:
        """
        Iterate through all series file listed in the preferences. For each
        series encountered in each file, yield a Show object. Files that do not
        exist or have invalid YAML are skipped.
        
        :returns:   An iterable of Show objects created by the entry listed in
                    all the known (valid) series files. 
        """

        # For each file in the cards list
        for file in (pbar := tqdm(self.series_files)):
            # Create Path object for this file
            file_object = Path(file)

            # Update progress bar for this file
            pbar.set_description(f'Reading {file_object.name}')

            # If the file doesn't exist, error and skip
            if not file_object.exists():
                log.error(f'Series file "{file_object.resolve()}" does not '
                          f'exist')
                continue

            # Read file, parse yaml
            with file_object.open('r') as file_handle:
                try:
                    file_yaml = safe_load(file_handle)
                except Exception as e:
                    log.error(f'Error reading series file:\n{e}\n')
                    continue

            # Skip if there are no series to yield
            if file_yaml is None or 'series' not in file_yaml:
                log.warning(f'Series file has no entries')
                continue

            # Get library map for this file; error+skip missing library paths
            if (library_map := file_yaml.get('libraries', {})):
                if not all('path' in library_map[lib] for lib in library_map):
                    log.error(f'Libraries in series file "{file_object.resolve()}'
                              f'"are missing their "path" attributes.')
                    continue

            # Get font map for this file
            font_map = file_yaml.get('fonts', {})

            # Go through each series in this file
            for show_name in tqdm(file_yaml['series'], leave=False,
                                  desc='Creating Shows'):
                # Yield the Show object created from this entry
                yield Show(
                    show_name,
                    file_yaml['series'][show_name],
                    library_map,
                    font_map,
                    self.source_directory,
                )

                
    def meets_minimum_resolution(self, width: int, height: int) -> bool:
        """
        Return whether the given dimensions meet the minimum resolution
        requirements indicated in the preference file.
        
        :param      width:   The width of the image.
        :param      height:  The height of the image.
        
        :returns:   True if the dimensions are suitable, False otherwise.
        """

        width_ok = (width >= self.tmdb_minimum_resolution['width'])
        height_ok = (height >= self.tmdb_minimum_resolution['height'])

        return width_ok and height_ok


    def get_season_folder(self, season_number: int) -> str:
        """
        Get the season folder name for the given season number, padding the
        season number if indicated by the preference file.
        
        :param      season_number:  The season number.
        
        :returns:   The season folder. This is 'Specials' for 0, and either a
                    zero-padded or not zero-padded version of "Season {x}".
        """

        # Season 0 is always Specials
        if season_number == 0:
            return 'Specials'

        # Zero pad the season number if indicated
        if self.zero_pad_seasons:
            return f'Season {season_number:02}'

        # Return non-zero-padded season name
        return f'Season {season_number}'
