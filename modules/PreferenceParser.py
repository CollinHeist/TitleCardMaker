from pathlib import Path

from tqdm import tqdm
from yaml import safe_load

from modules.Debug import log
from modules.Show import Show
from modules.ShowSummary import ShowSummary
from modules.TitleCard import TitleCard
from modules.TMDbInterface import TMDbInterface

class PreferenceParser:
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
        
        # Store file
        self.file = file
        self.__yaml = {}

        # Read file
        self.read_file()

        # Check for required source directory
        if not self.__is_specified('options', 'source'):
            log.critical(f'Preference file missing required "options/source"'
                         f'tag')
            exit(1)
        self.source_directory = Path(self.__yaml['options']['source'])

        # Setup default values that can be overwritten by YAML
        self.series_files = []
        self.card_type = 'standard'
        self.card_filename_format = TitleCard.DEFAULT_FILENAME_FORMAT
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
        self.use_tmdb = False
        self.tmdb_api_key = None
        self.tmdb_retry_count = TMDbInterface.BLACKLIST_THRESHOLD
        self.tmdb_minimum_resolution = {'width': 0, 'height': 0}
        self.imagemagick_docker_id = None

        # Modify object attributes based off YAML, assume valid to start
        self.valid = True
        self.__parse_yaml()


    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object."""

        return f'<PreferenceParser file={self.file}>'


    def __is_specified(self, *attributes: tuple) -> bool:
        """
        Determines whether the given attribute/sub-attribute has been manually 
        specified in the show's YAML.
        
        :param      attributes: Any number of attributes to check for. Each
                                subsequent argument is checked for as a sub-
                                attribute of the prior one.
        
        :returns:   True if ALL attributes are specified, False otherwise.
        """

        current = self.__yaml
        for attribute in attributes:
            # If this level isn't even a dictionary or the attribute DNE - False
            if not isinstance(current, dict) or attribute not in current:
                return False

            # If this level has sub-attributes, but is blank (None) - False
            if current[attribute] == None:
                return False

            # Move to the next level
            current = current[attribute]

        # All given attributes have been checked without exit, must be specified
        return True


    def __parse_yaml(self) -> None:
        """
        Parse the raw YAML dictionary into object attributes. This also errors
        to the user if any provided values are overtly invalid (i.e. missing
        where necessary, fails type conversion).
        """

        if self.__is_specified('options', 'series'):
            value = self.__yaml['options']['series']
            if isinstance(value, list):
                self.series_files = value
            else:
                self.series_files = [value]

        if self.__is_specified('options', 'card_type'):
            value = self.__yaml['options']['card_type']
            if value not in TitleCard.CARD_TYPES:
                log.critical(f'Default card type "{value}" is unrecognized')
                self.valid = False
            else:
                self.card_type = value

        if self.__is_specified('options', 'filename_format'):
            new_format = self.__yaml['options']['filename_format']
            if not TitleCard.validate_card_format_string(new_format):
                self.valid = False
            else:
                self.card_filename_format = new_format

        if self.__is_specified('archive', 'path'):
            self.archive_directory = Path(self.__yaml['archive']['path'])
            self.create_archive = True

        if self.__is_specified('archive', 'summary', 'create'):
            summary_yaml = self.__yaml['archive']['summary']
            self.create_summaries = bool(summary_yaml['create'])

        if self.__is_specified('archive', 'summary', 'background_color'):
            summary_yaml = self.__yaml['archive']['summary']
            self.summary_background_color = summary_yaml['background_color']

        if self.__is_specified('archive', 'summary', 'logo_filename'):
            summary_yaml = self.__yaml['archive']['summary']
            self.logo_filename = summary_yaml['logo_filename']

        if self.__is_specified('archive', 'summary', 'minimum_episodes'):
            value = self.__yaml['archive']['summary']['minimum_episodes']
            try:
                self.summary_minimum_episode_count = int(value)
            except ValueError:
                log.critical(f'Invalid summary minimum count "{value}"')
                self.valid = False

        if self.__is_specified('plex', 'url'):
            self.plex_url = self.__yaml['plex']['url']
            self.use_plex = True

        if self.__is_specified('plex', 'token'):
            self.plex_token = self.__yaml['plex']['token']

        if self.__is_specified('sonarr'):
            if not all((self.__is_specified('sonarr', 'url'),
                        self.__is_specified('sonarr', 'api_key'))):
                log.critical(f'Sonarr preferences must contain "url" and '
                             f'"api_key"')
                self.valid = False
            else:
                self.sonarr_url = self.__yaml['sonarr']['url']
                self.sonarr_api_key = self.__yaml['sonarr']['api_key']
                self.use_sonarr = True

        if self.__is_specified('tmdb'):
            if not self.__is_specified('tmdb', 'api_key'):
                log.critical(f'TMDb preferences must contain "api_key"')
                self.valid = False
            else:
                self.tmdb_api_key = self.__yaml['tmdb']['api_key']
                self.use_tmdb = True

        if self.__is_specified('tmdb', 'retry_count'):
            self.tmdb_retry_count = int(self.__yaml['tmdb']['retry_count'])

        if self.__is_specified('tmdb', 'minimum_resolution'):
            try:
                min_res = self.__yaml['tmdb']['minimum_resolution']
                width, height = map(int, min_res.split('x'))
                self.tmdb_minimum_resolution = {'width': width, 'height':height}
            except:
                log.critical(f'Invalid minimum resolution - specify as '
                             f'WIDTHxHEIGHT')
                self.valid = False

        if self.__is_specified('imagemagick', 'docker_id'):
            self.imagemagick_docker_id = self.__yaml['imagemagick']['docker_id']


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
        with self.file.open('r') as file_handle:
            try:
                self.__yaml = safe_load(file_handle)
            except Exception as e:
                log.critical(f'Error reading preference file:\n{e}\n')
                exit(1)

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
            if 'series' not in file_yaml:
                log.info(f'Series file has no entries')
                continue

            # Get library map for this file; error+skip missing library paths
            libraries = file_yaml.get('libraries', {})
            if not all('path' in libraries[library] for library in libraries):
                log.error(f'Libraries in series file "{file_object.resolve()}" '
                          f'are missing their "path" attributes.')
                continue

            # Go through each series in this file
            for show_name in tqdm(file_yaml['series'], leave=False,
                                  desc='Creating Shows'):
                # Yield the Show object created from this entry
                yield Show(
                    show_name,
                    file_yaml['series'][show_name],
                    libraries,
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

