from pathlib import Path
from typing import Iterable

from tqdm import tqdm

from modules.Debug import log, TQDM_KWARGS
from modules.Font import Font
from modules.ImageMagickInterface import ImageMagickInterface
from modules.ImageMaker import ImageMaker
from modules.Manager import Manager
from modules.SeriesInfo import SeriesInfo
from modules.SeriesYamlWriter import SeriesYamlWriter
from modules.Show import Show
from modules.StandardSummary import StandardSummary
from modules.StylizedSummary import StylizedSummary
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

    """Default directory for temporary database objects"""
    DEFAULT_TEMP_DIR = Path(__file__).parent / '.objects'


    def __init__(self, file: Path, is_docker: bool=False) -> None:
        """
        Constructs a new instance of this object. This reads the given file,
        errors and exits if any required options are missing, and then parses
        the preferences into object attributes.
        
        Args:
            file: The file to parse for preferences.
            is_docker: Whether executing within a Docker container.
        """

        # Initialize parent YamlReader object - errors are critical
        super().__init__(log_function=log.critical)
        
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
        self.execution_mode = Manager.DEFAULT_EXECUTION_MODE
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
        self.summary_class = StylizedSummary
        self.summary_background = self.summary_class.BACKGROUND_COLOR
        self.summary_minimum_episode_count = 1
        self.summary_created_by = None
        self.use_plex = False
        self.plex_url = None
        self.plex_token = 'NA'
        self.plex_verify_ssl = True
        self.integrate_with_pmm_overlays = False
        self.global_watched_style = 'unique'
        self.global_unwatched_style = 'unique'
        self.plex_yaml_writers = []
        self.plex_yaml_update_args = []
        self.use_sonarr = False
        self.sonarr_url = None
        self.sonarr_api_key = None
        self.sonarr_verify_ssl = True
        self.sonarr_yaml_writers = []
        self.sonarr_yaml_update_args = []
        self.use_tmdb = False
        self.tmdb_api_key = None
        self.tmdb_retry_count = TMDbInterface.BLACKLIST_THRESHOLD
        self.tmdb_minimum_resolution = {'width': 0, 'height': 0}
        self.tmdb_skip_localized_images = False
        self.imagemagick_container = None
        self.imagemagick_timeout = ImageMagickInterface.COMMAND_TIMEOUT_SECONDS

        # Modify object attributes based off YAML, updating validiry
        self.__parse_yaml()
        self.__parse_sync()

        # Whether to use magick prefix
        self.use_magick_prefix = False
        self.__determine_imagemagick_prefix()

        # Database object directory, create if DNE
        if is_docker and not (self.DEFAULT_TEMP_DIR / 'loaded.json').exists():
            self.database_directory = self.file.parent / '.objects'
        else:
            self.database_directory = self.DEFAULT_TEMP_DIR
        self.database_directory.mkdir(parents=True, exist_ok=True)


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
            # Create ImageMagickInterface and verify validity
            if ImageMagickInterface(self.imagemagick_container, use_magick,
                                    self.imagemagick_timeout).verify_interface():
                self.use_magick_prefix = use_magick
                log.debug(f'Using "{prefix}" ImageMagick command prefix')
                return None

        # If none of the font commands worked, IM might not be installed
        log.critical(f"ImageMagick doesn't appear to be installed")
        exit(1)


    def __parse_sync(self) -> None:
        """
        Parse the YAML sync sections of this preference file. This updates the
        lists of SeriesYamlWriter objects for Plex and Sonarr.
        """
        
        # Inner function to create and add SeriesYamlWriter objects (and)
        # their update args dictionaries to this object's lists
        def append_writer_and_args(sync_type, sync, static):
            # Combine static and given sync YAML
            sync_yaml = YamlReader(static | sync, log_function=log.warning)

            # Skip if file wasn't specified
            if (file := sync_yaml._get('file', type_=Path)) is None:
                return None

            # Create SeriesYamlWriter with this config
            writer = SeriesYamlWriter(
                file,
                sync_yaml._get('mode', type_=str, default='append'),
                sync_yaml._get('compact_mode', type_=bool, default=True),
                sync_yaml._get('volumes', type_=dict, default={}),
                sync_yaml._get('add_template', type_=str, default=None),
            )

            # If invalid after initialization, error and exit
            if not writer.valid:
                log.error(f'Cannot sync to "{file.resolve()}" - invalid sync')
                return None

            # Parse update args
            update_args = {}
            if (value := sync_yaml._get('libraries', type_=list)) is not None:
                update_args['filter_libraries'] = value
            if (value := sync_yaml._get('exclusions', type_=list)) is not None:
                update_args['exclusions'] = value
            if (value := sync_yaml._get('plex_libraries', type_=dict)) != None:
                update_args['plex_libraries'] = value
            if (value := sync_yaml._get('required_tags', type_=list)) != None:
                update_args['required_tags'] = value
            if (value := sync_yaml._get('monitored_only', 
                                        type_=bool)) is not None:
                update_args['monitored_only'] = value

            # Skip if YAML was invalidated at any point
            if not sync_yaml.valid:
                log.error(f'Cannot sync to "{file.resolve()}" - invalid sync')
                return None

            # Add to either Plex or Sonarr lists
            if sync_type == 'plex':
                self.plex_yaml_writers.append(writer)
                self.plex_yaml_update_args.append(update_args)
            else:
                self.sonarr_yaml_writers.append(writer)
                self.sonarr_yaml_update_args.append(update_args)

        # Create Plex SeriesYamlWriter objects
        if (plex_sync := self._get('plex', 'sync')) is not None:
            # Singular sync specification
            if isinstance(plex_sync, dict):
                append_writer_and_args('plex', plex_sync, {})
            # List of syncs, no globals
            elif isinstance(plex_sync, list) and len(plex_sync) > 0:
                base_sync = plex_sync[0]
                for sync in plex_sync:
                    append_writer_and_args('plex', sync, base_sync)
            else:
                log.error(f'Invalid plex sync: {plex_sync}')

        # Create Sonarr SeriesYamlWriter objects
        if (sonarr_sync := self._get('sonarr', 'sync')) is not None:
            # Singular sync specification
            if isinstance(sonarr_sync, dict):
                append_writer_and_args('sonarr', sonarr_sync, {})
            # List of syncs, no globals
            elif isinstance(sonarr_sync, list) and len(sonarr_sync) > 0:
                base_sync = sonarr_sync[0]
                for sync in sonarr_sync:
                    append_writer_and_args('sonarr', sync, base_sync)
            else:
                log.error(f'Invalid sonarr sync: {plex_sync}')
            

    def __parse_yaml(self) -> None:
        """
        Parse the raw YAML dictionary into object attributes. This also errors
        to the user if any provided values are overtly invalid (i.e. missing
        where necessary, fails type conversion).
        """

        lower_str = lambda v: str(v).lower()

        if (value := self._get('options', 'execution_mode',
                               type_=lower_str)) is not None:
            if value not in Manager.VALID_EXECUTION_MODES:
                log.critical(f'Execution mode "{value}" is invalid')
                self.valid = False
            else:
                self.execution_mode = value

        if (value := self._get('options', 'series')) is not None:
            if isinstance(value, list):
                self.series_files = value
            else:
                self.series_files = [value]
        else:
            log.warning(f'No series YAML files indicated, no cards will be '
                        f'created')

        if (value := self._get('options', 'card_type', type_=str)) !=None:
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
            sources = tuple(map(lower_strip, value.split(',')))
            if not all(_ in self.VALID_IMAGE_SOURCES for _ in sources):
                log.critical(f'Image source priority "{value}" is invalid')
                self.valid = False
            else:
                self.image_source_priority = sources

        if (value := self._get('options', 'episode_data_source',
                               type_=lower_str)) is not None:
            if value in self.VALID_EPISODE_DATA_SOURCES:
                self.episode_data_source = value
            else:
                log.critical(f'Episode data source "{value}" is invalid')
                self.valid = False

        if (value := self._get('options', 'validate_fonts', type_=bool)) !=None:
            self.validate_fonts = value

        if (value := self._get('options', 'season_folder_format',
                               type_=str)) is not None:
            self.season_folder_format = value
            self.get_season_folder(1)

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

        if (value := self._get('archive', 'summary', 'type',
                               type_=lower_str)) is not None:
            if value == 'standard':
                self.summary_class = StandardSummary
                self.summary_background = self.summary_class.BACKGROUND_COLOR
            elif value == 'stylized':
                self.summary_class = StylizedSummary
                self.summary_background = self.summary_class.BACKGROUND_COLOR
            else:
                log.critical(f'Summary type "{value}" is invalid - must be '
                             f'"standard" or "stylized"')
                self.valid = False

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

        if (value := self._get('plex', 'verify_ssl', type_=bool)) is not None:
            self.plex_verify_ssl = value

        if (value := self._get('plex', 'watched_style', type_=lower_str))!=None:
            if value not in Show.VALID_STYLES:
                opt = '", "'.join(Show.VALID_STYLES)
                log.critical(f'Invalid watched style, must be one of "{opt}"')
                self.valid = False
            else:
                self.global_watched_style = value

        if (value := self._get('plex', 'unwatched_style',
                               type_=lower_str)) != None:
            if value not in Show.VALID_STYLES:
                opt = '", "'.join(Show.VALID_STYLES)
                log.critical(f'Invalid unwatched style, must be one of "{opt}"')
                self.valid = False
            else:
                self.global_unwatched_style = value

        if (value := self._get('plex', 'integrate_with_pmm_overlays',
                               type_=bool)) is not None:
            self.integrate_with_pmm_overlays = value

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

        if (value := self._get('sonarr', 'verify_ssl', type_=bool)) is not None:
            self.sonarr_verify_ssl = value
        
        if (value := self._get('tmdb', 'api_key', type_=str)) != None:
            self.tmdb_api_key = value
            self.use_tmdb = True

        if (value := self._get('tmdb', 'retry_count', type_=int)) != None:
            self.tmdb_retry_count = value

        if (value := self._get('tmdb', 'minimum_resolution', type_=str)) !=None:
            try:
                width, height = map(int, value.lower().split('x'))
                self.tmdb_minimum_resolution = {'width': width, 'height':height}
            except Exception:
                log.critical(f'Invalid minimum resolution - specify as '
                             f'WIDTHxHEIGHT')
                self.valid = False

        if (value := self._get('tmdb', 'skip_localized_images',
                               type_=bool)) is not None:
            self.tmdb_skip_localized_images = value

        if (value := self._get('imagemagick', 'container', type_=str)) != None:
            self.imagemagick_container = value

        if (value := self._get('imagemagick', 'timeout',type_=int)) is not None:
            self.imagemagick_timeout = value

        # Warn for renamed settings
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

        if self._is_specified('sonarr', 'sync', 'tags'):
            log.critical(f'Sonarr sync "tags" option has been renamed '
                         f'"required_tags".')
            self.valid = False


    def __validate_libraries(self, library_yaml: dict[str: str],
                             file: Path) -> bool:
        """
        Validate the given libraries YAML.

        Args:
            library_yaml: YAML from the 'libraries' key to validate.
            file: File whose YAML is being evaluated - for logging only.

        Returns:
            True if the given YAML is valid, False otherwise.
        """

        # Libraries must be a dictionary
        if not isinstance(library_yaml, dict):
            log.error(f'Invalid library specification for series file '
                      f'"{file.resolve()}"')
            return False
        
        # Validate all given libraries
        for name, spec in library_yaml.items():
            # All libraries must be dictionaries
            if not isinstance(spec, dict):
                log.error(f'Library "{name}" is invalid for series file '
                          f'"{file.resolve()}"')
                return False

            # All libraries must provide paths
            if spec.get('path') is None:
                log.error(f'Library "{name}" is missing required "path" in '
                          f'series file "{file.resolve()}"')
                return False

        return True


    def __validate_fonts(self, font_yaml: dict[str: 'str | float'],
                         file: Path) -> bool:
        """
        Validate the given font YAML.

        Args:
            font_yaml: Font map YAML to validate.
            file: File whose YAML is being evaluated - for logging only.

        Returns:
            True if the given YAML is valid, False otherwise.
        """

        # Font map must be a dictionary
        if not isinstance(font_yaml, dict):
            log.error(f'Invalid font specification for series file '
                      f'"{file.resolve()}"')
            return False

        # Validate all given fonts
        for name, spec in font_yaml.items():
            # All fonts must be dictionaries
            if not isinstance(spec, dict):
                log.error(f'Font "{name}" is invalid for series file '
                          f'"{file.resolve()}"')
                return False

            # All fonts must provide valid font attributes
            for attrib in spec.keys():
                if attrib not in Font.VALID_ATTRIBUTES:
                    log.error(f'Font "{name}" has unrecognized attribute '
                              f'"{attrib}"')
                    return False

        return True

    
    def __apply_template(self, templates: dict[str, Template],series_yaml: dict,
                         series_name: str) -> bool:
        """
        Apply the correct Template object (if indicated) to the given series
        YAML. This effectively "fill out" the indicated template, and updates
        the series YAML directly.

        Args:
            templates: Dictionary of Template objects to potentially apply.
            series_yaml: The YAML of the series to modify.
            series_name: The name of the series being modified.
        
        Returns:
            True if the given series contained all the required template
            variables for application, False if it did not.
        """

        # No templates defined for this series, skip
        if 'template' not in series_yaml:
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

        # Parse title/year from the series to add as "built-in" template data
        try:
            series_info = SeriesInfo(series_name, series_yaml.get('year', None))
            built_in_data = {'title': series_info.name, 'year':series_info.year}
            series_yaml['template'] = built_in_data | series_yaml['template']
        except Exception:
            pass

        # Apply using Template object
        return template.apply_to_series(series_name, series_yaml)


    def __finalize_show_yaml(self, show_name: str, show_yaml: dict,
                             templates: list[Template], library_map: dict,
                             font_map: dict) -> 'dict | None':
        """
        Apply the indicated template, and merge the specified library/font to
        the given show YAML.

        Args:
            show_yaml: Base show YAML with potential template/library/font
                identifiers.
            library_map: Library map of library names/identifiers to library
                specifications.
            font_map: Font map of font names/identifiers to custom font
                specifications.

        Returns:
            Modified YAML, None if the modification failed.
        """
        
        # Apply template to series, stop if invalid
        if not self.__apply_template(templates, show_yaml, show_name):
            return None
        
        # Parse library from map
        if (len(library_map) > 0
            and (library_name := show_yaml.get('library')) is not None):
            if (library_yaml := library_map.get(library_name)) is None:
                log.error(f'Library "{library_name}" of series "{show_name}" is'
                          f' not present in libraries list')
                return None
            else:
                Template.recurse_priority_union(show_yaml, library_yaml)
                show_yaml['library'] = {
                    'name': library_yaml.get('plex_name', library_name),
                    'path': Path(library_yaml.get('path'))
                }
                
        # Parse font from map (if given font is just an identifier)
        if (len(font_map) > 0
            and (font_name := show_yaml.get('font')) is not None
            and isinstance(font_name, str)):
            # If font identifier is not in map
            if (font_yaml := font_map.get(font_name)) is None:
                log.error(f'Font "{font_name}" of series "{show_name}" is '
                            f'not present in font list')
                return None
            else:
                show_yaml['font'] = {}
                Template.recurse_priority_union(show_yaml['font'], font_yaml)
        
        return show_yaml
    
    
    def read_file(self) -> None:
        """
        Read this associated preference file and store in `_base_yaml` attribute
        and critically error if reading fails.
        """

        # If the file doesn't exist, error and exit
        if not self.file.exists():
            log.critical(f'Preference file "{self.file.resolve()}" does not '
                         f'exist')
            exit(1)

        # Read file 
        self._base_yaml = self._read_file(self.file, critical=True)

        # Log reading, return that YAML
        log.info(f'Read preference file "{self.file.resolve()}"')


    def iterate_series_files(self) -> Iterable[Show]:
        """
        Iterate through all series file listed in the preferences. For each
        series encountered in each file, yield a Show object. Files that do not
        exist or have invalid YAML are skipped.

        Returns:
            An iterable of Show objects created by the entry listed in all the
            known (valid) series files. 
        """

        # Reach each file in the list of series YAML files
        for file_ in (pbar := tqdm(self.series_files, **TQDM_KWARGS)):
            # Create Path object for this file
            try:
                file = Path(file_)
            except Exception:
                log.error(f'Invalid series file "{file_}"')
                continue

            # Update progress bar for this file
            pbar.set_description(f'Reading {file.name}')

            # If the file doesn't exist, error and skip
            if not file.exists():
                log.error(f'Series file "{file.resolve()}" does not exist')
                continue

            # Read file, parse yaml
            if (file_yaml := self._read_file(file, critical=False)) == {}:
                continue

            # Skip if there are no series provided
            if file_yaml is None or file_yaml.get('series') is None:
                log.warning(f'Series file "{file.resolve()}" has no entries')
                continue

            # Validate the libraries provided in this file
            library_map = file_yaml.get('libraries', {})
            if not self.__validate_libraries(library_map, file):
                continue

            # Get font map for this file
            font_map = file_yaml.get('fonts', {})
            if not self.__validate_fonts(font_map, file):
                continue

            # Construct Template objects for this file
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
                # Skip if not a dictionary
                if not isinstance(file_yaml['series'][show_name], dict):
                    log.error(f'Skipping "{show_name}" from "{file_}"')
                    continue

                # Apply template and merge libraries+font maps
                show_yaml = self.__finalize_show_yaml(
                    show_name,
                    file_yaml['series'][show_name],
                    templates,
                    library_map,
                    font_map,
                )

                # If returned YAML is None (invalid) skip series
                if show_yaml is None:
                    log.error(f'Skipping "{show_name}" from "{file_}"')
                    continue

                yield Show(show_name, show_yaml, self.source_directory, self)

                # If archiving is disabled, skip
                if not self.create_archive:
                    continue

                # Get all specified variations for this show
                variations = show_yaml.pop('archive_variations', [])
                if not isinstance(variations, list):
                    log.error(f'Invalid archive variations for {show_name}')
                    continue

                # Yield each variation
                show_yaml.pop('archive_name', None)
                for variation in variations:
                    # Apply template and merge libraries+font maps to variation
                    variation = self.__finalize_show_yaml(
                        show_name, variation, templates, library_map, font_map,
                    )

                    # Get priority union of variation and base series
                    Template.recurse_priority_union(variation, show_yaml)
                    
                    # Remove any library-specific details
                    variation.pop('media_directory', None)
                    variation.pop('library', None)
                    
                    yield Show(show_name, variation, self.source_directory,self)

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

    @property
    def plex_interface_kwargs(self) -> dict[str: 'Path | str | bool']:
        return {
            'database_directory': self.database_directory,
            'url': self.plex_url,
            'x_plex_token': self.plex_token,
            'verify_ssl': self.plex_verify_ssl,
        }

    @property
    def sonarr_interface_kwargs(self) -> dict[str: 'str | bool']:
        return {
            'url': self.sonarr_url,
            'api_key': self.sonarr_api_key,
            'verify_ssl': self.sonarr_verify_ssl,
        }

    @property
    def tmdb_interface_kwargs(self) -> dict[str: 'Path | str']:
        return {
            'database_directory': self.database_directory,
            'api_key': self.tmdb_api_key,
        }

                
    def meets_minimum_resolution(self, width: int, height: int) -> bool:
        """
        Determine whether the given dimensions meet the minimum resolution
        requirements indicated in the preference file.

        Args:
            width: The width of the image.
            height: The height of the image.
        
        Returns:
            True if the dimensions are suitable, False otherwise.
        """

        width_ok = (width >= self.tmdb_minimum_resolution['width'])
        height_ok = (height >= self.tmdb_minimum_resolution['height'])

        return width_ok and height_ok


    def get_season_folder(self, season_number: int) -> str:
        """
        Get the season folder name for the given season number, padding the
        season number if indicated by the preference file, and returning an
        empty string if season folders are hidden.
        
        Args:
            season_number: The season number to get the folder name of.
        
        Returns:
            The season folder name. Empty string if folders are hidden,
            'Specials' for season 0, and either a zero-padded or not zero-
            padded version of "Season {x}" otherwise.

        Raises:
            SystemExit if the season folder formatting fails.
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
        except Exception as e:
            log.critical(f'Invalid season folder format - {e}')
            exit(1)