from pathlib import Path
from re import findall

from tqdm import tqdm

from modules.Debug import log, TQDM_KWARGS
from modules.ImageMagickInterface import ImageMagickInterface
from modules.ImageMaker import ImageMaker
from modules.PlexInterface import PlexInterface
from modules.SeriesYamlWriter import SeriesYamlWriter
from modules.Show import Show
from modules.ShowSummary import ShowSummary
from modules.Template import Template
from modules.TitleCard import TitleCard
from modules.TMDbInterface import TMDbInterface
from modules.YamlReader import YamlReader

class PreferenceParser(YamlReader):
    """
    This class describes a preference parser that reads a given preference YAML
    file and parses it into individual attributes.
    """

    """Valid image source identifiers"""
    VALID_IMAGE_SOURCES = ('tmdb', 'plex')

    """Valid episode data source identifiers"""
    VALID_EPISODE_DATA_SOURCES = ('sonarr', 'plex', 'tmdb')

    """Directory for all temporary objects created/maintained by the Maker"""
    TEMP_DIR = Path(__file__).parent / '.objects'


    def __init__(self, file: Path) -> None:
        """
        Constructs a new instance of this object. This reads the given file,
        errors and exits if any required options are missing, and then parses
        the preferences into object attributes.
        
        :param      file:   The preference file to parse.
        """

        # Initialize parent YamlReader object
        super().__init__(log_function=log.critical)

        # Create temporary directory if DNE
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Store and read file
        self.file = file
        self.read_file()

        # Check for required source directory
        if (value := self._get('options', 'source', type_=Path)) is None:
            log.critical(f'Preference file missing required options/source '
                         f'attribute')
            exit(1)
        self.source_directory = value

        # Setup default values that can be overwritten by YAML
        self.series_files = []
        self._parse_card_type('standard') # Sets self.card_type
        self.card_filename_format = TitleCard.DEFAULT_FILENAME_FORMAT
        self.card_extension = TitleCard.DEFAULT_CARD_EXTENSION
        self.image_source_priority = ('tmdb', 'plex')
        self.episode_data_source = 'sonarr'
        self.validate_fonts = True
        self.season_folder_format = 'Season {season}'
        self.sync_specials = True
        self.archive_directory = None
        self.create_archive = False
        self.archive_all_variations = True
        self.create_summaries = True
        self.summary_background = ShowSummary.BACKGROUND_COLOR
        self.summary_minimum_episode_count = 1
        self.summary_created_by = None
        self.use_plex = False
        self.plex_url = None
        self.plex_token = 'NA'
        self.integrate_with_pmm_overlays = False
        self.global_watched_style = 'unique'
        self.global_unwatched_style = 'unique'
        self.plex_yaml_writer = None
        self.plex_yaml_update_args = {'filter_libraries': []}
        self.use_sonarr = False
        self.sonarr_url = None
        self.sonarr_api_key = None
        self.sonarr_yaml_writer = None
        self.sonarr_yaml_update_args = {'plex_libraries': {}, 'filter_tags': [],
                                        'monitored_only': False}
        self.use_tmdb = False
        self.tmdb_api_key = None
        self.tmdb_retry_count = TMDbInterface.BLACKLIST_THRESHOLD
        self.tmdb_minimum_resolution = {'width': 0, 'height': 0}
        self.imagemagick_container = None

        # Modify object attributes based off YAML, assume valid to start
        self.__parse_yaml()

        # Whether to use magick prefix
        self.use_magick_prefix = False
        self.__determine_imagemagick_prefix()


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'<PreferenceParser {self.file=}, {self.valid=}>'


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

        lower_str = lambda v: str(v).lower()

        if (value := self._get('options', 'series')) is not None:
            if isinstance(value, list):
                self.series_files = value
            else:
                self.series_files = [value]
        else:
            log.warning(f'No series YAML files indicated, no cards will be '
                        f'created')

        if (value := self._get('options', 'card_type', type_=lower_str)) !=None:
            self._parse_card_type(value)

        if (value := self._get('options', 'card_extension', type_=str)) != None:
            extension = ('' if value[0] == '.' else '.') + value
            if extension not in ImageMaker.VALID_IMAGE_EXTENSIONS:
                log.critical(f'Card extension "{extension}" is invalid')
                self.valid = False
            else:
                self.card_extension = extension

        if (value := self._get('options', 'filename_format', type_=str)) !=None:
            if not TitleCard.validate_card_format_string(value):
                self.valid = False
            else:
                self.card_filename_format = value

        if (value := self._get('options',
                               'image_source_priority', type_=str)) is not None:
            lower_strip = lambda s: str(s).lower().strip()
            sources = tuple(map(lower_strip, value.split(', ')))
            if not all(_ in self.VALID_IMAGE_SOURCES for _ in sources):
                log.critical(f'Image source priority "{value}" is invalid')
                self.valid = False
            else:
                self.image_source_priority = sources

        if (value := self._get('options',
                               'episode_data_source', type_=str)) is not None:
            if (value := value.lower()) in self.VALID_EPISODE_DATA_SOURCES:
                self.episode_data_source = value
            else:
                log.critical(f'Episode data source "{value}" is invalid')
                self.valid = False

        if (value := self._get('options', 'validate_fonts', type_=bool)) !=None:
            self.validate_fonts = value

        if (value := self._get('options', 'season_folder_format',
                               type_=str)) is not None:
            self.season_folder_format = value

        if (value := self._get('options', 'sync_specials', type_=bool)) != None:
            self.sync_specials = value

        if (value := self._get('archive', 'path', type_=Path)) != None:
            self.archive_directory = value
            self.create_archive = True

        if (value := self._get('archive', 'all_variations', type_=bool)) !=None:
            self.archive_all_variations = value

        if (value := self._get('archive', 'summary', 'create',
                               type_=bool)) != None:
            self.create_summaries = value

        if (value := self._get('archive', 'summary', 'created_by',
                               type_=str)) is not None:
            self.summary_created_by = value

        if (value := self._get('archive', 'summary', 'background',
                               type_=str)) != None:
            self.summary_background = value

        if ((value := self._get('archive', 'summary', 'minimum_episodes',
                               type_=int)) != None):
            self.summary_minimum_episode_count = value

        if (value := self._get('plex', 'url', type_=str)) != None:
            self.plex_url = value
            self.use_plex = True

        if (value := self._get('plex', 'token', type_=str)) != None:
            self.plex_token = value

        if (value := self._get('plex', 'watched_style', type_=lower_str))!=None:
            if value not in Show.VALID_STYLES:
                options = '", "'.join(Show.VALID_STYLES)
                log.critical(f'Invalid watched style, must be one of "{opts}"')
                self.valid = False
            else:
                self.global_watched_style = value

        if (value := self._get('plex', 'unwatched_style',
                               type_=lower_str)) != None:
            if value == 'ignore':
                log.critical(f'Unwatched style "ignore" is now "unique"')
                self.valid = False
            elif value not in Show.VALID_STYLES:
                opts = '", "'.join(Show.VALID_STYLES)
                log.critical(f'Invalid unwatched style, must be one of "{opts}"')
                self.valid = False
            else:
                self.global_unwatched_style = value

        if (value := self._get('plex', 'integrate_with_pmm_overlays',
                               type_=bool)) is not None:
            self.integrate_with_pmm_overlays = value

        if self._is_specified(*(attrs := ('plex', 'sync')), 'file'):
            self.plex_yaml_writer = SeriesYamlWriter(
                self._get(*attrs, 'file', type_=Path),
                self._get(*attrs, 'mode', type_=str, default='sync'),
                self._get(*attrs, 'compact_mode', type_=bool, default=True),
                self._get(*attrs, 'volumes', default={}),
            )
            self.plex_yaml_update_args = {
                'filter_libraries': self._get('plex', 'sync', 'libraries',
                                              default=[]),
            }

        if self._is_specified('sonarr'):
            if (not self._is_specified('sonarr', 'url')
                or not self._is_specified('sonarr', 'api_key')):
                log.critical(f'Sonarr preferences must contain "url" and '
                             f'"api_key"')
                self.valid = False
            else:
                self.sonarr_url = self._get('sonarr', 'url', type_=str)
                self.sonarr_api_key = self._get('sonarr', 'api_key', type_=str)
                self.use_sonarr = True

        if self._is_specified(*(attrs := ('sonarr', 'sync')), 'file'):
            self.sonarr_yaml_writer = SeriesYamlWriter(
                self._get(*attrs, 'file', type_=Path),
                self._get(*attrs, 'mode', type_=str, default='sync'),
                self._get(*attrs, 'compact_mode', type_=bool, default=True),
                self._get(*attrs, 'volumes', default={}),
            )
            self.sonarr_yaml_update_args = {
                'plex_libraries': self._get('sonarr', 'sync', 'plex_libraries',
                                            default={}),
                'filter_tags': self._get('sonarr', 'sync', 'tags', default=[]),
                'monitored_only': self._get('sonarr', 'sync', 'monitored_only',
                                            default=False),
            }
        
        if (value := self._get('tmdb', 'api_key', type_=str)) != None:
            self.tmdb_api_key = value
            self.use_tmdb = True

        if (value := self._get('tmdb', 'retry_count', type_=int)) != None:
            self.tmdb_retry_count = int(value)

        if (value := self._get('tmdb', 'minimum_resolution', type_=str)) !=None:
            try:
                width, height = map(int, value.lower().split('x'))
                self.tmdb_minimum_resolution = {'width': width, 'height':height}
            except Exception:
                log.critical(f'Invalid minimum resolution - specify as '
                             f'WIDTHxHEIGHT')
                self.valid = False

        if (value := self._get('imagemagick', 'container', type_=str)) != None:
            self.imagemagick_container = value

        # Warn for renamed settings
        if self._is_specified('options', 'source_priority'):
            log.critical(f'Options "source_priority" setting has been renamed '
                         f'to "image_source_priority"')
            self.valid = False

        if self._is_specified('options', 'zero_pad_seasons'):
            log.critical(f'Options "zero_pad_seasons" setting has been '
                         f'incorporated into "season_folder_format"')
            self.valid = False

        if self._is_specified('options', 'hide_season_folders'):
            log.critical(f'Options "hide_season_folders" setting has been '
                         f'incorporated into "season_folder_format"')
            self.valid = False

        if self._is_specified('archive', 'summary', 'background_color'):
            log.critical(f'Archive summary "background_color" option has been '
                         f'renamed to "background"')
            self.valid = False

        if self._is_specified('plex', 'unwatched'):
            log.critical(f'Plex "unwatched" setting has been renamed to '
                         f'"unwatched_style"')
            self.valid = False


    def __apply_template(self, templates: dict, series_yaml: dict,
                         series_name: str) -> bool:
        """
        Apply the correct Template object (if indicated) to the given series
        YAML. This effectively "fill out" the indicated template, and updates
        the series YAML directly.
        
        :param      templates:      Dictionary of Template objects to
                                    potentially apply.
        :param      series_yaml:    The YAML of the series to modify.
        :param      series_name:    The name of the series being modified.
        
        :returns:   True if the given series contained all the required template
                    variables for application, False if it did not.
        """

        # No templates defined, skip
        if templates == {} or 'template' not in series_yaml:
            return True

        # Get the specified template for this series
        if isinstance((series_template := series_yaml['template']), str):
            # Assume if only a string, then its the template name
            series_template = {'name': series_template}
            series_yaml['template'] = series_template

        # Warn and return if no template name given
        if not (template_name := series_template.get('name', None)):
            log.error(f'Missing template name for "{series_name}"')
            return False

        # Warn and return if template name not mapped
        if not (template := templates.get(template_name, None)):
            log.error(f'Template "{template_name}" not defined')
            return False

        # Apply using Template object
        return template.apply_to_series(series_name, series_yaml)


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


    def iterate_series_files(self) -> list[Show]:
        """
        Iterate through all series file listed in the preferences. For each
        series encountered in each file, yield a Show object. Files that do not
        exist or have invalid YAML are skipped.
        
        :returns:   An iterable of Show objects created by the entry listed in
                    all the known (valid) series files. 
        """

        # For each file in the cards list
        for file_ in (pbar := tqdm(self.series_files, **TQDM_KWARGS)):
            # Create Path object for this file
            file = Path(file_)

            # Update progress bar for this file
            pbar.set_description(f'Reading {file.name}')

            # If the file doesn't exist, error and skip
            if not file.exists():
                log.error(f'Series file "{file.resolve()}" does not '
                          f'exist')
                continue

            # Read file, parse yaml
            if (file_yaml := self._read_file(file)) == {}:
                continue

            # Skip if there are no series to yield
            if file_yaml is None or file_yaml.get('series') is None:
                log.warning(f'Series file "{file.resolve()}" has no entries')
                continue

            # Get library map for this file; error+skip missing library paths
            if (library_map := file_yaml.get('libraries', {})):
                if not isinstance(library_map, dict):
                    log.error(f'Invalid library specification for series file '
                              f'"{file.resolve()}"')
                    continue
                if not all('path' in library_map[lib] for lib in library_map):
                    log.error(f'Libraries are missing required "path" in series'
                              f' file "{file.resolve()}"')
                    continue

            # Get font map for this file
            font_map = file_yaml.get('fonts', {})

            # Get templates for this file, validate they're all dictionaries
            templates = {}
            value = file_yaml.get('templates', {})
            if isinstance(value, dict):
                for name, template in value.items():
                    # If not specified as dictionary, error and skip
                    if not isinstance(template, dict):
                        log.error(f'Invalid template specification for "{name}"'
                                  f' in series file "{file.resolve()}"')
                        continue
                    templates[name] = Template(name, template)

            # Go through each series in this file
            for show_name in tqdm(file_yaml['series'], desc='Creating Shows',
                                  **TQDM_KWARGS):
                # Apply template to series
                valid = self.__apply_template(
                    templates, file_yaml['series'][show_name], show_name,
                )

                # Skip if series is not valid
                if not valid:
                    continue

                # Yield the Show object created from this entry
                yield Show(
                    show_name,
                    file_yaml['series'][show_name],
                    library_map,
                    font_map,
                    self.source_directory,
                    self,
                )

                # If archiving is disabled, skip
                if not self.create_archive:
                    continue

                # Get all specified variations for this show
                variations = file_yaml['series'][show_name].pop(
                    'archive_variations', []
                )
                
                if not isinstance(variations, list):
                    log.error(f'Invalid archive variations for {show_name}')
                    continue

                # Yield each variation
                for variation in variations:
                    # Apply template to variation
                    if not self.__apply_template(templates,variation,show_name):
                        continue

                    # Get priority union of variation and base series
                    file_yaml['series'][show_name].pop('archive_name', None)
                    Template('', {}).recurse_priority_union(
                        variation, file_yaml['series'][show_name]
                    )

                    # Remove any library-specific details
                    variation.pop('library', None)
                    variation.pop('media_directory', None)
                    
                    yield Show(
                        show_name,
                        variation,
                        library_map,
                        font_map,
                        self.source_directory,
                        self,
                    )

    @property
    def check_tmdb(self):
        return 'tmdb' in self.image_source_priority

    @property
    def check_plex(self):
        return 'plex' in self.image_source_priority

    @property
    def check_plex_before_tmdb(self) -> bool:
        """Whether to check Plex source before TMDb"""

        priorities = self.image_source_priority
        if 'plex' in priorities:
            if 'tmdb' in priorities:
                return priorities.index('plex') < priorities.index('tmdb')

            return True

        return False

                
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
        season number if indicated by the preference file, and returning an
        empty string if season folders are hidden.
        
        :param      season_number:  The season number to get the folder name of.
        
        :returns:   The season folder name. Empty string if folders are hidden,
                    'Specials' for season 0, and either a zero-padded or not
                    zero-padded version of "Season {x}" otherwise.
        """

        # If season folders are hidden, return empty string
        if (self.season_folder_format is None
            or len(self.season_folder_format.strip()) == 0): 
            return ''

        # Season 0 is always Specials (never padded)
        if season_number == 0:
            return 'Specials'

        # Format season folder as indicated (zero-padding, whatever..)
        try:
            return self.season_folder_format.format(season=season_number)
        except Exception:
            log.critical('Invalid season folder format')
            exit(1)

