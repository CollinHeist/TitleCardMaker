from pathlib import Path

from yaml import safe_load

from modules.Debug import *
from modules.Show import Show
from modules.ShowSummary import ShowSummary
from modules.TMDbInterface import TMDbInterface

class PreferenceParser:
    """
    This class describes a preference parser that reads a given preference
    YAML file and parses it into individual attributes such as whether to use Plex,
    the TMDb API key, etc.
    """

    def __init__(self, file: Path) -> None:
        """
        Constructs a new instance of this object. This reads the given file,
        errors and exits if any required options are missing, and then parses
        the preferences into object attributes.
        
        :param      file:  The preference file to parse.
        """
        
        # Store file
        self.file = file
        self.__yaml = {}

        # Read file
        self.read_file()

        # Check for required source directory
        if not self.__is_specified('options', 'source'):
            error(f'Preference file missing required "options/source" tag.')
            exit(1)
        self.source_directory = Path(self.__yaml['options']['source'])

        ## Setup default values that can be overwritten by YAML
        self.series_files = []
        self.archive_directory = None
        self.create_archive = False
        self.create_summaries = False
        self.summary_background_color = ShowSummary.BACKGROUND_COLOR
        self.logo_filename = ShowSummary.LOGO_FILENAME
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

        # Modify object attributes based off YAML
        self.valid = True
        self.__parse_yaml()


    def __is_specified(self, *attributes: tuple) -> bool:
        """
        Determines whether the given attribute/sub-attribute has been manually 
        specified in the show's YAML.
        
        :param      attribute:      The attribute to check for.
        :param      sub_attribute:  The sub attribute to check for. Necessary if
                                    the given attribute has attributes of its own.
        
        :returns:   True if specified, False otherwise.
        """

        current_level = self.__yaml
        for attribute in attributes:
            # If this level isn't even a dictionary, or the attribute doesn't exist
            if not isinstance(current_level, dict) or attribute not in current_level:
                return False

            if current_level[attribute] == None:
                return False

            # Move to the next level
            current_level = current_level[attribute]

        return True


    def __parse_yaml(self) -> None:
        """
        Parse the raw YAML dictionary into object attributes. This also
        errors to the user if any provided values are overtly invalid (i.e.
        missing where necessary, fails type conversion).
        """

        if self.__is_specified('options', 'series'):
            value = self.__yaml['options']['series']
            if isinstance(value, list):
                self.series_files = value
            else:
                self.series_files = [value]

        if self.__is_specified('archive', 'path'):
            self.archive_directory = Path(self.__yaml['archive']['path'])
            self.create_archive = True

        if self.__is_specified('archive', 'summary', 'create'):
            self.create_summaries = bool(self.__yaml['archive']['summary']['create'])

        if self.__is_specified('archive', 'summary', 'background_color'):
            self.summary_background_color = self.__yaml['archive']['summary']['background_color']

        if self.__is_specified('archive', 'summary', 'logo_filename'):
            self.logo_filename = self.__yaml['archive']['summary']['logo_filename']

        if self.__is_specified('plex', 'url'):
            self.plex_url = self.__yaml['plex']['url']
            self.use_plex = True

        if self.__is_specified('plex', 'token'):
            self.plex_token = self.__yaml['plex']['token']

        if self.__is_specified('sonarr'):
            if not all((self.__is_specified('sonarr', 'url'), self.__is_specified('sonarr', 'api_key'))):
                error(f'Sonarr preferences must contain "url" and "api_key"')
                self.valid = False
            else:
                self.sonarr_url = self.__yaml['sonarr']['url']
                self.sonarr_api_key = self.__yaml['sonarr']['api_key']
                self.use_sonarr = True

        if self.__is_specified('tmdb'):
            if not self.__is_specified('tmdb', 'api_key'):
                error(f'TMDb preferences must contain "api_key"')
                self.valid = False
            else:
                self.tmdb_api_key = self.__yaml['tmdb']['api_key']
                self.use_tmdb = True

        if self.__is_specified('tmdb', 'retry_count'):
            self.tmdb_retry_count = int(self.__yaml['tmdb']['retry_count'])

        if self.__is_specified('tmdb', 'minimum_resolution'):
            try:
                width, height = map(int, self.__yaml['tmdb']['minimum_resolution'].split('x'))
                self.tmdb_minimum_resolution = {'width': width, 'height': height}
            except:
                error(f'Invalid TMDb minimum resolution - specify as WIDTHxHEIGHT')
                self.valid = False

        if self.__is_specified('imagemagick', 'docker_id'):
            self.imagemagick_docker_id = self.__yaml['imagemagick']['docker_id']


    def read_file(self) -> None:
        """
        Reads this associated preference file and store in `__yaml` attribute.

        If reading the YAML fails, the error is printed and the program exits.
        """

        if not self.file.exists():
            info(f'Preference file "{self.file.resolve()}" does not exist')
            exit(1)

        # Read file 
        with self.file.open('r') as file_handle:
            try:
                self.__yaml = safe_load(file_handle)
            except Exception as e:
                error(f'Error reading preference file:\n{e}\n')
                exit(1)

        info(f'Read preference file "{self.file.resolve()}"')


    def iterate_series_files(self) -> [Show]:
        """
        Iterate through all series file listed in the preferences. For each
        series encountered in each file, yield a `Show` object. Files that do
        not exist or have invalid YAML are skipped.
        
        :returns:   An iterable of `Show` objects created by the entry listed
                    in all the known (valid) series files. 
        """

        # For each file in the cards list
        for file in self.series_files:
            file_object = Path(file)

            # If the file doesn't exist, error and skip
            if not file_object.exists():
                error(f'Series file "{file_object.resolve()}" does not exist')
                continue

            # Read file, parse yaml
            with file_object.open('r') as file_handle:
                try:
                    file_yaml = safe_load(file_handle)
                except Exception as e:
                    error(f'Error reading preference file:\n{e}\n')
                    continue

            # Get the libraries listed in this file
            libraries = file_yaml['libraries'] if 'libraries' in file_yaml else {}

            for show_name in file_yaml['series']:
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


