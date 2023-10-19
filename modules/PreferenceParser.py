from collections import namedtuple
from pathlib import Path
from sys import exit as sys_exit
from typing import Any, Iterator, Optional, Union

from fastapi import HTTPException
from num2words import CONVERTER_CLASSES as SUPPORTED_LANGUAGE_CODES
from tqdm import tqdm

from modules.CleanPath import CleanPath
from modules.Debug import log, TQDM_KWARGS
from modules.EmbyInterface import EmbyInterface
from modules.Font import Font
from modules.ImageMagickInterface import ImageMagickInterface
from modules.ImageMaker import ImageMaker
from modules.JellyfinInterface import JellyfinInterface
from modules.Manager import Manager
from modules.PlexInterface import PlexInterface
from modules.SeriesInfo import SeriesInfo
from modules.SeriesYamlWriter import SeriesYamlWriter
from modules.Show import Show
from modules.SonarrInterface import SonarrInterface
from modules.StandardSummary import StandardSummary
from modules.StyleSet import StyleSet
from modules.StylizedSummary import StylizedSummary
from modules.TautulliInterface import TautulliInterface
from modules.Template import Template
from modules.TitleCard import TitleCard
from modules.TMDbInterface import TMDbInterface
from modules.Version import Version
from modules.YamlReader import YamlReader

YamlWriterSet = namedtuple(
    'YamlWriterSet', ('interface_id', 'writer', 'update_args')
)

class PreferenceParser(YamlReader):
    """
    This class describes a preference parser that reads a given
    preference YAML file and parses it into individual attributes.
    """

    """Valid image source identifiers"""
    VALID_IMAGE_SOURCES = ('emby', 'jellyfin', 'plex', 'tmdb')

    """Valid episode data source identifiers"""
    VALID_EPISODE_DATA_SOURCES = ('emby', 'jellyfin', 'sonarr', 'plex', 'tmdb')
    DEFAULT_EPISODE_DATA_SOURCE = 'sonarr'

    """Default season folder format string"""
    DEFAULT_SEASON_FOLDER_FORMAT = 'Season {season}'

    """Default directory for temporary database objects"""
    DEFAULT_TEMP_DIR = Path(__file__).parent / '.objects'

    """File containing the executing version of TitleCardMaker"""
    VERSION_FILE = Path(__file__).parent / 'ref' / 'version'


    def __init__(self, file: Path, is_docker: bool = False) -> None:
        """
        Constructs a new instance of this object. This reads the given
        file, errors and exits if any required options are missing, and
        then parses the preferences into object attributes.

        Args:
            file: The file to parse for preferences.
            is_docker: Whether executing within a Docker container.

        Raises:
            SystemExit (1): Any required YAML options are missing from
            `file`.
        """

        # Initialize parent YamlReader object - errors are critical
        super().__init__(log_function=log.critical)
        self.valid = True
        self.version = Version(self.VERSION_FILE.read_text().strip())
        self.is_docker = is_docker

        # Store and read file
        self.file = file
        self.read_file()

        # Database object directory, create if DNE
        self.DEFAULT_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        if is_docker:
            self.database_directory = self.file.parent / '.objects'
        else:
            self.database_directory = self.DEFAULT_TEMP_DIR
        self.database_directory.mkdir(parents=True, exist_ok=True)

        # Check for required source directory
        if (value := self.get('options', 'source', type_=str)) is None:
            log.critical(f'Preference file missing required options/source '
                         f'attribute')
            sys_exit(1)
        self.source_directory = CleanPath(value).sanitize()

        # Setup default values that can be overwritten by YAML
        self.series_files = []
        self.execution_mode = Manager.DEFAULT_EXECUTION_MODE
        self._parse_card_type(TitleCard.DEFAULT_CARD_TYPE) # Sets self.card_type
        self.card_filename_format = TitleCard.DEFAULT_FILENAME_FORMAT
        self.card_extension = TitleCard.DEFAULT_CARD_EXTENSION
        self.card_dimensions = TitleCard.DEFAULT_CARD_DIMENSIONS
        self.image_source_priority = ('tmdb', 'plex', 'emby', 'jellyfin')
        self.episode_data_source = self.DEFAULT_EPISODE_DATA_SOURCE
        self.validate_fonts = True
        self.season_folder_format = self.DEFAULT_SEASON_FOLDER_FORMAT
        self.sync_specials = True
        self.supported_language_codes = ['en']

        self.archive_directory = None
        self.create_archive = False
        self.archive_all_variations = True
        self.create_summaries = True
        self.summary_class = StylizedSummary
        self.summary_background = self.summary_class.BACKGROUND_COLOR
        self.summary_minimum_episode_count = 3
        self.summary_created_by = None
        self.summary_ignore_specials = False

        self.use_emby = False
        self.emby_url = None
        self.emby_api_key = None
        self.emby_username = None
        self.emby_verify_ssl = True
        self.emby_filesize_limit = self.filesize_as_bytes(
            EmbyInterface.DEFAULT_FILESIZE_LIMIT
        )
        self.emby_style_set = StyleSet()
        self.emby_yaml_writers = []
        self.emby_yaml_update_args = []

        self.use_jellyfin = False
        self.jellyfin_url = None
        self.jellyfin_api_key = None
        self.jellyfin_username = None
        self.jellyfin_verify_ssl = True
        self.jellyfin_filesize_limit = self.filesize_as_bytes(
            JellyfinInterface.DEFAULT_FILESIZE_LIMIT
        )
        self.jellyfin_style_set = StyleSet()
        self.jellyfin_yaml_writers = []
        self.jellyfin_yaml_update_args = []

        self.use_plex = False
        self.plex_url = None
        self.plex_token = 'NA'
        self.plex_verify_ssl = True
        self.integrate_with_pmm_overlays = False
        self.plex_filesize_limit = self.filesize_as_bytes(
            PlexInterface.DEFAULT_FILESIZE_LIMIT
        )
        self.plex_style_set = StyleSet()
        self.plex_yaml_writers = []
        self.plex_yaml_update_args = []

        self.sonarr_kwargs = []
        self.sonarr_yaml_writers = []

        self.use_tmdb = False
        self.tmdb_api_key = None
        self.tmdb_retry_count = TMDbInterface.BLACKLIST_THRESHOLD
        self.tmdb_minimum_resolution = {'width': 0, 'height': 0}
        self.tmdb_skip_localized_images = False
        self.tmdb_logo_language_priority = ['en']

        self.use_tautulli = False
        self.tautulli_url = None
        self.tautulli_api_key = None
        self.tautulli_verify_ssl = True
        self.tautulli_username = None
        self.tautulli_update_script = None
        self.tautulli_agent_name = TautulliInterface.DEFAULT_AGENT_NAME
        self.tautulli_script_timeout = TautulliInterface.DEFAULT_SCRIPT_TIMEOUT

        self.imagemagick_container = None
        self.imagemagick_timeout = ImageMagickInterface.COMMAND_TIMEOUT_SECONDS

        # Determine default media server
        if (not self._is_specified('emby')
            and not self._is_specified('plex')
            and not self._is_specified('jellyfin')):
            log.warning(f'No Media Servers indicated - TitleCardMaker will not '
                        f'automatically load any cards')
            self.default_media_server = 'plex'
        if (self._is_specified('emby')
            and not self._is_specified('plex')
            and not self._is_specified('jellyfin')):
            self.default_media_server = 'emby'
        elif (self._is_specified('jellyfin')
            and not self._is_specified('emby')
            and not self._is_specified('plex')):
            self.default_media_server = 'jellyfin'
        elif (self._is_specified('plex')
            and not self._is_specified('emby')
            and not self._is_specified('jellyfin')):
            self.default_media_server = 'plex'
        else:
            self.default_media_server = None

        # Modify object attributes based off YAML, updating validiry
        self.__parse_yaml()
        self.__parse_sync()

        # Whether to use magick prefix
        self.use_magick_prefix = False
        self.__determine_imagemagick_prefix()


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        attributes = ', '.join(f'{attr}={getattr(self, attr)!r}'
                               for attr in self.__dict__
                               if not attr.startswith('_'))

        return f'<PreferenceParser {attributes}>'


    def __determine_imagemagick_prefix(self) -> None:
        """
        Determine whether to use the "magick " prefix for ImageMagick
        commands. If a prefix cannot be determined, a critical message
        is logged and this object's validity is set to False.
        """

        # Try variations of the font list command with/out the "magick " prefix
        for prefix, use_magick in zip(('', 'magick '), (False, True)):
            # Create ImageMagickInterface and verify validity
            interface = ImageMagickInterface(
                self.imagemagick_container, use_magick, self.imagemagick_timeout
            )
            if interface.validate_interface():
                self.use_magick_prefix = use_magick
                log.debug(f'Using "{prefix}" ImageMagick command prefix')
                return None

        # If none of the font commands worked, IM might not be installed
        log.critical(f"ImageMagick doesn't appear to be installed")
        self.valid = False
        return None


    def __parse_sync(self) -> None:
        """
        Parse the YAML sync sections of this preference file. This
        updates the lists of SeriesYamlWriter objects for each
        applicable interface.
        """

        # Inner function to create and add SeriesYamlWriter objects (and)
        # their update args dictionaries to this object's lists
        def append_writer_and_args(sync_type, interface_id, sync, static):
            # Combine static and given sync YAML
            sync_yaml = YamlReader(static | sync, log_function=log.warning)

            # Skip if file wasn't specified
            if (file := sync_yaml.get('file', type_=CleanPath)) is None:
                return None

            # Create SeriesYamlWriter with this config
            file = file.sanitize()
            writer = SeriesYamlWriter(
                file,
                sync_yaml.get('mode', type_=str, default='append'),
                sync_yaml.get('compact_mode', type_=bool, default=True),
                sync_yaml.get('volumes', type_=dict, default={}),
                sync_yaml.get('add_template', type_=str, default=None),
                sync_yaml.get('card_directory', type_=CleanPath, default=None),
            )

            # If invalid after initialization, error and exit
            if not writer.valid:
                log.error(f'Cannot sync to "{file.resolve()}" - invalid sync')
                return None

            # Parse args applicable to all interfaces
            update_args = {}
            if (value := sync_yaml.get('exclusions', type_=list)) is not None:
                update_args['exclusions'] = value
            if (value := sync_yaml.get('required_tags', type_=list)) is not None:
                update_args['required_tags'] = value

            # Parse args applicable only to specific interfaces
            if sync_type in ('emby', 'jellyfin', 'plex'):
                if (value := sync_yaml.get('libraries', type_=list)) is not None:
                    update_args['filter_libraries'] = value
            elif sync_type == 'sonarr':
                if (value := sync_yaml.get('plex_libraries', type_=dict)) is not None:
                    update_args['plex_libraries'] = value
                if (value := sync_yaml.get('monitored_only', type_=bool)) is not None:
                    update_args['monitored_only'] = value
                if (value := sync_yaml.get('downloaded_only', type_=bool)) is not None:
                    update_args['downloaded_only'] = value
                if (value := sync_yaml.get('series_type', type_=str)) is not None:
                    if value in SonarrInterface.VALID_SERIES_TYPES:
                        update_args['series_type'] = value
                    else:
                        vals = ", ".join(SonarrInterface.VALID_SERIES_TYPES)
                        log.error(f'Cannot filter by series_type "{value}" - '
                                  f'must be one of {vals}')
                        sync_yaml.valid = False

            # Skip if YAML was invalidated at any point
            if not sync_yaml.valid:
                log.error(f'Cannot sync to "{file.resolve()}" - invalid sync')
                return None

            # Add to either Plex or Sonarr lists
            if sync_type == 'emby':
                self.emby_yaml_writers.append(writer)
                self.emby_yaml_update_args.append(update_args)
            elif sync_type == 'jellyfin':
                self.jellyfin_yaml_writers.append(writer)
                self.jellyfin_yaml_update_args.append(update_args)
            elif sync_type == 'plex':
                self.plex_yaml_writers.append(writer)
                self.plex_yaml_update_args.append(update_args)
            else:
                self.sonarr_yaml_writers.append(
                    YamlWriterSet(interface_id, writer, update_args)
                )

            return None

        # Create Emby SeriesYamlWriter objects
        if (emby_sync := self.get('emby', 'sync')) is not None:
            # Singular sync specification
            if isinstance(emby_sync, dict):
                append_writer_and_args('emby', 0, emby_sync, {})
            # List of syncs
            elif isinstance(emby_sync, list) and len(emby_sync) > 0:
                base_sync = emby_sync[0]
                for sync in emby_sync:
                    append_writer_and_args('emby', 0, sync, base_sync)
            else:
                log.error(f'Invalid Emby sync: {emby_sync}')

        # Create Jellyfin SeriesYamlWriter objects
        if (jellyfin_sync := self.get('jellyfin', 'sync')) is not None:
            # Singular sync specification
            if isinstance(jellyfin_sync, dict):
                append_writer_and_args('jellyfin', 0, jellyfin_sync, {})
            # List of syncs
            elif isinstance(jellyfin_sync, list) and len(jellyfin_sync) > 0:
                base_sync = jellyfin_sync[0]
                for sync in jellyfin_sync:
                    append_writer_and_args('jellyfin', 0, sync, base_sync)
            else:
                log.error(f'Invalid Jellyfin sync: {jellyfin_sync}')

        # Create Plex SeriesYamlWriter objects
        if (plex_sync := self.get('plex', 'sync')) is not None:
            # Singular sync specification
            if isinstance(plex_sync, dict):
                append_writer_and_args('plex', 0, plex_sync, {})
            # List of syncs
            elif isinstance(plex_sync, list) and len(plex_sync) > 0:
                base_sync = plex_sync[0]
                for sync in plex_sync:
                    append_writer_and_args('plex', 0, sync, base_sync)
            else:
                log.error(f'Invalid Plex sync: {plex_sync}')

        # Create Sonarr SeriesYamlWriter objects
        if self._is_specified('sonarr'):
            # Singular server
            if (isinstance(self.get('sonarr'), dict)
                and (sonarr_sync := self.get('sonarr', 'sync')) is not None):
                # Singular sync specification
                if isinstance(sonarr_sync, dict):
                    append_writer_and_args('sonarr', 0, sonarr_sync, {})
                # List of syncs
                elif isinstance(sonarr_sync, list) and len(sonarr_sync) > 0:
                    base_sync = sonarr_sync[0]
                    for sync in sonarr_sync:
                        append_writer_and_args('sonarr', 0, sync, base_sync)
                else:
                    log.error(f'Invalid Sonarr sync: {sonarr_sync}')
            # Multiple sonarr interfaces, check for sync on each
            elif isinstance(self.get('sonarr'), list):
                for interface_id, server in enumerate(self.get('sonarr')):
                    reader = YamlReader(server)
                    # Singular sync for this server
                    if isinstance((sync := reader.get('sync')), dict):
                        append_writer_and_args('sonarr', interface_id, sync, {})
                    # List of syncs for this server
                    elif isinstance(sync, list) and len(sync) > 0:
                        base_sync = sync[0]
                        for sub_sync in sync:
                            append_writer_and_args(
                                'sonarr', interface_id, sub_sync, base_sync
                            )


    def __parse_yaml_options(self) -> None:
        """
        Parse the 'options' section of the raw YAML dictionary into
        attributes.
        """

        # Skip if sections omitted
        if not self._is_specified('options'):
            return None

        if (value := self.get('options', 'execution_mode',
                               type_=self.TYPE_LOWER_STR)) is not None:
            if value in Manager.VALID_EXECUTION_MODES:
                self.execution_mode = value
            else:
                log.critical(f'Execution mode "{value}" is invalid')
                self.valid = False

        if (value := self.get('options', 'series')) is not None:
            if isinstance(value, list):
                self.series_files = value
            else:
                self.series_files = [value]
        else:
            log.warning(f'No series YAML files indicated, no cards will be '
                        f'created')

        if (value := self.get('options', 'card_type', type_=str)) is not None:
            self._parse_card_type(value)

        if (value := self.get('options', 'card_extension', type_=str)) is not None:
            extension = ('' if value[0] == '.' else '.') + value
            if extension in ImageMaker.VALID_IMAGE_EXTENSIONS:
                self.card_extension = extension
            else:
                log.critical(f'Card extension "{extension}" is invalid')
                self.valid = False

        if (value := self.get('options', 'card_dimensions', type_=str)) is not None:
            try:
                width, height = map(int, value.lower().split('x'))
                assert width > 0 and height > 0
                if not (16 / 9 - 0.1) <= width / height <= (16 / 9 + 0.1):
                    log.warning(f'Card dimensions aspect ratio is not 16:9')
                if width < 200 or height < 200:
                    log.warning(f'Card dimensions are very small')
                self.card_dimensions = value
            except ValueError:
                log.critical(f'Invalid card dimensions - specify as WIDTHxHEIGHT')
                self.valid = False
            except AssertionError:
                log.critical(f'Invalid card dimensions - both dimensions must '
                             f'be larger than 0px')
                self.valid = False

        if (value := self.get('options', 'filename_format', type_=str)) is not None:
            if TitleCard.validate_card_format_string(value):
                self.card_filename_format = value
            else:
                self.valid = False

        if (value := self.get('options', 'image_source_priority',
                               type_=self.TYPE_LOWER_STR)) is not None:
            if (sources := self.parse_image_source_priority(value)) is None:
                log.critical(f'Image source priority "{value}" is invalid')
                self.valid = False
            else:
                self.image_source_priority = sources

        if (value := self.get('options', 'episode_data_source',
                               type_=self.TYPE_LOWER_STR)) is not None:
            if value in self.VALID_EPISODE_DATA_SOURCES:
                self.episode_data_source = value
            else:
                log.critical(f'Episode data source "{value}" is invalid')
                self.valid = False

        if (value := self.get('options', 'validate_fonts', type_=bool)) is not None:
            self.validate_fonts = value

        if (value := self.get('options', 'season_folder_format',
                               type_=str)) is not None:
            self.season_folder_format = value
            self.get_season_folder(1)

        if (value := self.get('options', 'sync_specials', type_=bool)) is not None:
            self.sync_specials = value

        if (value := self.get('options', 'language_codes', type_=list)) is not None:
            value = set(value) | set(('en', ))
            if all(code in SUPPORTED_LANGUAGE_CODES for code in value):
                self.supported_language_codes = value
            else:
                codes = ', '.join(SUPPORTED_LANGUAGE_CODES)
                log.critical(f'Not all language codes are recognized')
                log.info(f'Must be one of {codes}')
                self.valid = False

        return None


    def __parse_yaml_archive(self) -> None:
        """
        Parse the 'archive' section of the raw YAML dictionary into
        attributes.
        """

        # Skip if section omitted
        if not self._is_specified('archive'):
            return None

        if (value := self.get('archive', 'path', type_=Path)) is not None:
            self.archive_directory = value
            self.create_archive = True

        if (value := self.get('archive', 'all_variations', type_=bool)) is not None:
            self.archive_all_variations = value

        if (value := self.get('archive', 'summary', 'create',
                               type_=bool)) is not None:
            self.create_summaries = value

        if (value := self.get('archive', 'summary', 'type',
                               type_=self.TYPE_LOWER_STR)) is not None:
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

        if (value := self.get('archive', 'summary', 'created_by',
                               type_=str)) is not None:
            self.summary_created_by = value

        if (value := self.get('archive', 'summary', 'background',
                               type_=str)) is not None:
            self.summary_background = value

        if (value := self.get('archive', 'summary', 'minimum_episodes',
                               type_=int)) is not None:
            self.summary_minimum_episode_count = value

        if (value := self.get('archive', 'summary', 'ignore_specials',
                               type_=bool)) is not None:
            self.summary_ignore_specials = value

        return None


    def __parse_yaml_emby(self) -> None:
        """
        Parse the 'emby' section of the raw YAML dictionary into
        attributes.
        """

        # Skip if section omitted
        if not self._is_specified('emby'):
            return None

        if (not self._is_specified('emby', 'url')
            or not  self._is_specified('emby', 'api_key')
            or not  self._is_specified('emby', 'username')):
            log.critical(f'Must specify Emby "url", "api_key", and "username"')
            self.valid = False

        if (value := self.get('emby', 'url', type_=str)) is not None:
            self.emby_url = value
            self.use_emby = True

        if (value := self.get('emby', 'api_key', type_=str)) is not None:
            self.emby_api_key = value

        if (value := self.get('emby', 'username', type_=str)) is not None:
            self.emby_username = value

        if (value := self.get('emby', 'verify_ssl', type_=bool)) is not None:
            self.emby_verify_ssl = value

        if (value := self.get('emby', 'filesize_limit',
                               type_=self.filesize_as_bytes)) is not None:
            self.emby_filesize_limit = value

        self.emby_style_set = StyleSet(
            self.get('emby', 'watched_style', type_=str, default='unique'),
            self.get('emby', 'unwatched_style', type_=str, default='unique'),
        )
        self.valid &= self.emby_style_set.valid

        return None


    def __parse_yaml_jellyfin(self) -> None:
        """
        Parse the 'jellyfin' section of the raw YAML dictionary into
        attributes.
        """

        # Skip if section omitted
        if not self._is_specified('jellyfin'):
            return None

        if (not self._is_specified('jellyfin', 'url')
            or not  self._is_specified('jellyfin', 'api_key')
            or not  self._is_specified('jellyfin', 'username')):
            log.critical(f'Must specify Jellyfin "url", "api_key", and '
                         f'"username"')
            self.valid = False

        if (value := self.get('jellyfin', 'url', type_=str)) is not None:
            self.jellyfin_url = value
            self.use_jellyfin = True

        if (value := self.get('jellyfin', 'api_key', type_=str)) is not None:
            self.jellyfin_api_key = value

        if (value := self.get('jellyfin', 'username', type_=str)) is not None:
            self.jellyfin_username = value

        if (value := self.get('jellyfin', 'verify_ssl', type_=bool)) is not None:
            self.jellyfin_verify_ssl = value

        if (value := self.get('jellyfin', 'filesize_limit',
                               type_=self.filesize_as_bytes)) is not None:
            self.jellyfin_filesize_limit = value

        self.jellyfin_style_set = StyleSet(
            self.get('jellyfin', 'watched_style', type_=str, default='unique'),
            self.get('jellyfin', 'unwatched_style', type_=str, default='unique'),
        )
        self.valid &= self.jellyfin_style_set.valid

        return None


    def __parse_yaml_plex(self) -> None:
        """
        Parse the 'plex' section of the raw YAML dictionary into
        attributes.
        """

        # Skip if section omitted
        if not self._is_specified('plex'):
            return None

        if (value := self.get('plex', 'url', type_=str)) is not None:
            self.plex_url = value
            self.use_plex = True

        if (value := self.get('plex', 'token', type_=str)) is not None:
            self.plex_token = value

        if (value := self.get('plex', 'verify_ssl', type_=bool)) is not None:
            self.plex_verify_ssl = value

        if (value := self.get('plex', 'integrate_with_pmm_overlays',
                               type_=bool)) is not None:
            self.integrate_with_pmm_overlays = value

        if (value := self.get('plex', 'filesize_limit',
                               type_=self.filesize_as_bytes)) is not None:
            self.plex_filesize_limit = value

            if value > self.filesize_as_bytes('10 MB'):
                log.warning(f'Plex will reject all images larger than 10 MB')

        self.plex_style_set = StyleSet(
            self.get('plex', 'watched_style', type_=str, default='unique'),
            self.get('plex', 'unwatched_style', type_=str, default='unique'),
        )
        self.valid &= self.plex_style_set.valid

        return None


    def __parse_yaml_sonarr(self) -> None:
        """
        Parse the 'sonarr' section of the raw YAML dictionary into
        attributes.
        """

        # Skip if section omitted
        if not self._is_specified('sonarr'):
            return None

        # Inner function to parse a single instance of server YAML
        def parse_server(yaml: dict[str, Any]):
            reader = YamlReader(yaml)

            # Server must provide URL and API key
            if ((url := reader.get('url', type_=str)) is None or
                (api_key := reader.get('api_key', type_=str)) is None):
                log.critical(f'Sonarr server must contain "url" and "api_key"')
                self.valid = False
            else:
                verify_ssl = reader.get('verify_ssl', type_=bool, default=True)
                downloaded_only = reader.get(
                    'downloaded_only', type_=bool, default=False
                )
                self.sonarr_kwargs.append({
                    'url': url, 'api_key': api_key, 'verify_ssl': verify_ssl,
                    'downloaded_only': downloaded_only,
                })

        # If multiple servers were specified, parse all specificiations
        if isinstance(self.get('sonarr'), list):
            for server in self.get('sonarr'):
                parse_server(server)
        # Single server specification
        elif isinstance(self.get('sonarr'), dict):
            parse_server(self.get('sonarr'))
        else:
            log.critical(f'Invalid Sonarr preferences')
            self.valid = False

        return None


    def __parse_yaml_tmdb(self) -> None:
        """
        Parse the 'tmdb' section of the raw YAML dictionary into
        attributes.
        """

        # Skip if section omitted
        if not self._is_specified('tmdb'):
            return None

        if (value := self.get('tmdb', 'api_key', type_=str)) is not None:
            self.tmdb_api_key = value
            self.use_tmdb = True

        if (value := self.get('tmdb', 'retry_count', type_=int)) is not None:
            if value < 0:
                log.critical(f'Cannot have a negative TMDb retry count')
                self.valid = False
            else:
                self.tmdb_retry_count = value

        if (value := self.get('tmdb', 'minimum_resolution', type_=str)) is not None:
            try:
                width, height = map(int, value.lower().split('x'))
                self.tmdb_minimum_resolution = {'width': width, 'height':height}
            except Exception:
                log.critical(f'Invalid minimum resolution - specify as '
                             f'WIDTHxHEIGHT')
                self.valid = False

        if (value := self.get('tmdb', 'skip_localized_images',
                               type_=bool)) is not None:
            self.tmdb_skip_localized_images = value

        if (value := self.get('tmdb', 'logo_language_priority',
                               type_=str)) is not None:
            codes = list(map(lambda s: str(s).lower().strip(), value.split(',')))
            if all(code in TMDbInterface.LANGUAGE_CODES for code in codes):
                self.tmdb_logo_language_priority = codes
            else:
                opts = '"' + '", "'.join(TMDbInterface.LANGUAGE_CODES) + '"'
                log.critical(f'Invalid TMDb logo language codes - must be comma'
                             f'-separated list of any of the following: {opts}')
                self.valid = False

        return None


    def __parse_yaml_tautulli(self) -> None:
        """
        Parse the 'tautulli' section of the raw YAML dictionary into
        attributes.
        """

        # Skip if section omitted
        if not self._is_specified('tautulli'):
            return None

        # Parse required attributes
        if ((url := self.get('tautulli', 'url', type_=str)) is not None
            and (api_key := self.get('tautulli', 'api_key', type_=str)) is not None
            and (script := self.get('tautulli', 'update_script',
                                     type_=Path)) is not None):
            self.tautulli_url = url
            self.tautulli_api_key = api_key
            self.tautulli_update_script = script
            self.use_tautulli = True
        else:
            log.critical(f'tautulli preferences must contain "url", "api_key", '
                         f'and "update_script"')
            self.valid = False

        if (value := self.get('tautulli', 'verify_ssl', type_=bool)) is not None:
            self.tautulli_verify_ssl = value

        if (value := self.get('tautulli', 'username', type_=str)) is not None:
            self.tautulli_username = value

        if (value := self.get('tautulli', 'agent_name', type_=str)) is not None:
            self.tautulli_agent_name = value

        if (value := self.get('tautulli', 'script_timeout',type_=int)) is not None:
            self.tautulli_script_timeout = value

        return None


    def __parse_yaml_imagemagick(self) -> None:
        """
        Parse the 'imagemagick' section of the raw YAML dictionary into
        attributes.
        """

        # Skip if section omitted
        if not self._is_specified('imagemagick'):
            return None

        # Warn if ImageMagick provided in a Docker environment
        if self.is_docker:
            log.warning(f'Specifying the "imagemagick" section is not '
                        f'recommended when using TitleCardMaker in Docker')

        if (value := self.get('imagemagick', 'container',
                               type_=str)) is not None:
            self.imagemagick_container = value

        if (value := self.get('imagemagick', 'timeout',type_=int)) is not None:
            self.imagemagick_timeout = value

        return None


    def __parse_yaml(self) -> None:
        """
        Parse the raw YAML dictionary into object attributes. This also
        errors to the user if any provided values are overtly invalid
        (i.e. missing where necessary, fails type conversion).
        """

        # Parse each section
        self.__parse_yaml_options()
        self.__parse_yaml_archive()
        self.__parse_yaml_emby()
        self.__parse_yaml_jellyfin()
        self.__parse_yaml_plex()
        self.__parse_yaml_sonarr()
        self.__parse_yaml_tmdb()
        self.__parse_yaml_tautulli()
        self.__parse_yaml_imagemagick()

        # Warn for renamed settings


    def __validate_libraries(self,
            library_yaml: dict[str, str],
            file: Path,
        ) -> bool:
        """
        Validate the given libraries YAML.

        Args:
            library_yaml: YAML from the 'libraries' key to validate.
            file: File whose YAML is being evaluated - for logging only.

        Returns:
            True if the given YAML is valid, False otherwise.
        """

        err = f'in series YAML file "{file.resolve()}"'

        # Libraries must be a dictionary
        if not isinstance(library_yaml, dict):
            log.error(f'Invalid library specification {err}')
            return False

        # Validate all given libraries
        for name, spec in library_yaml.items():
            # All libraries must be dictionaries
            if not isinstance(spec, dict):
                log.error(f'Library "{name}" is invalid {err}')
                return False

            # All libraries must provide paths
            if spec.get('path') is None:
                log.error(f'Library "{name}" is missing required "path" {err}')
                return False

            # Libraries must specify a media server if there is no default
            if (self.default_media_server is None
                and spec.get('media_server') is None):
                log.error(f'Library "{name}" is missing required "media_server"'
                          f' {err}')
                return False

            # Media server must be Plex or Emby
            if (spec.get('media_server', self.default_media_server)
                not in ('emby', 'jellyfin', 'plex')):
                log.error(f'Library "{name}" specifies an invalid media_server')
                return False

        return True


    def __validate_fonts(self,
            font_yaml: dict[str, Union[str, float]],
            file: Path
        ) -> bool:
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


    @staticmethod
    def apply_template(
            templates: dict[str, Template],
            series_yaml: dict[str, Any],
            series_name: str, *,
            raise_exc: bool = False
        ) -> bool:
        """
        Apply the correct Template object (if indicated) to the given
        series YAML. This effectively "fill out" the indicated template,
        and updates the series YAML directly.

        Args:
            templates: Dictionary of Template objects to potentially
                apply.
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
            template_name = series_template
            series_template = {'template_name': series_template}
            series_yaml['template'] = series_template
        # Warn and return if no template name given
        elif not (template_name := series_template.get('name', None)):
            if raise_exc:
                raise HTTPException(
                    status_code=422,
                    detail=f'Missing Template name for "{series_name}"',
                )
            log.error(f'Missing template name for "{series_name}"')
            return False

        # Warn and return if template name not mapped
        if not (template := templates.get(template_name, None)):
            if raise_exc:
                raise HTTPException(
                    status_code=404,
                    detail=f'Template "{template_name}" not defined'
                )
            template_names = '"' + '", "'.join(templates.keys()) + '"'
            log.error(f'Template "{template_name}" not defined')
            log.info(f'Defined templates are {template_names}')
            return False

        # Parse title/year from the series to add as "built-in" template data
        try:
            series_info = SeriesInfo(series_name, series_yaml.get('year'))
        except Exception as e:
            if raise_exc:
                raise HTTPException(
                    status_code=422,
                    detail=f'Error identifying series info of {series_name}',
                ) from e
            log.exception(f'Error identifying series info of {series_name}', e)
            log.debug(f'Series YAML: {series_yaml}')
            series_info = None

        # Apply using Template object
        return template.apply_to_series(
            series_info, series_yaml, raise_exc=raise_exc
        )


    @staticmethod
    def finalize_show_yaml(
            show_name: str,
            show_yaml: dict[str, Any],
            templates: dict[str, Template],
            library_map: dict[str, Any],
            font_map: dict[str, Any], *,
            default_media_server: str = 'plex',
            raise_exc: bool = False
        ) -> Optional[dict]:
        """
        Apply the indicated template, and merge the specified
        library/font to the given show YAML.

        Args:
            show_yaml: Base show YAML with potential template/library/
                font identifiers.
            library_map: Library map of library names/identifiers to
                library specifications.
            font_map: Font map of font names/identifiers to custom font
                specifications.

        Returns:
            Modified YAML, None if the modification failed.
        """

        # Apply template to series, stop if invalid
        if not PreferenceParser.apply_template(templates, show_yaml, show_name,
                                               raise_exc=raise_exc):
            return None

        # Parse library from map
        if (len(library_map) > 0
            and (library_name := show_yaml.get('library')) is not None):
            # If library identifier is not in the map, error and exit
            if (library_yaml := library_map.get(library_name)) is None:
                library_names = '"' + '", "'.join(library_map.keys()) + '"'
                log.error(f'Library "{library_name}" of series "{show_name}" is'
                          f' not present in libraries list')
                log.info(f'Listed library names are {library_names}')
                return None
            # Library identifier in map, merge YAML
            Template.recurse_priority_union(show_yaml, library_yaml)
            server = library_yaml.get('media_server', default_media_server)
            show_yaml['library'] = {
                'name': library_yaml.get('library_name', library_name),
                'path': CleanPath(library_yaml.get('path')).sanitize(),
                'media_server': server,
            }

        # Parse font from map (if given font is just an identifier)
        if (len(font_map) > 0
            and (font_name := show_yaml.get('font')) is not None
            and isinstance(font_name, str)):
            # If font identifier is not in map, error and exit
            if (font_yaml := font_map.get(font_name)) is None:
                font_names = '"' + '", "'.join(font_map.keys()) + '"'
                log.error(f'Font "{font_name}" of series "{show_name}" is '
                            f'not present in font list')
                log.info(f'Listed font names are {font_names}')
                return None
            # Font identifer in map, merge YAML
            show_yaml['font'] = {}
            Template.recurse_priority_union(show_yaml['font'], font_yaml)

        return show_yaml


    def read_file(self) -> None:
        """
        Read this associated preference file and store in `_base_yaml`
        attribute and critically error if reading fails.
        """

        # If the file doesn't exist, error and exit
        if not self.file.exists():
            log.critical(f'Preference file "{self.file.resolve()}" does not '
                         f'exist')
            sys_exit(1)

        # Read file
        self._base_yaml = self._read_file(self.file, critical=True)
        log.info(f'Read preference file "{self.file.resolve()}"')


    def iterate_series_files(self) -> Iterator[Show]:
        """
        Iterate through all series file listed in the preferences. For
        each series encountered in each file, yield a Show object. Files
        that do not exist or have invalid YAML are skipped.

        Returns:
            An iterable of Show objects created by the entry listed in
            all the known (valid) series files.
        """

        # Reach each file in the list of series YAML files
        for file_ in (pbar := tqdm(self.series_files, **TQDM_KWARGS)):
            # Create Path object for this file
            try:
                file = CleanPath(file_).sanitize()
            except Exception as e:
                log.exception(f'Invalid series file "{file_}"', e)
                continue

            # Update progress bar for this file
            pbar.set_description(f'Reading {file.name}')
            log.info(f'Reading series YAML file "{file.resolve()}"..')

            # If the file doesn't exist, error and skip
            if not file.exists():
                log.error(f'Series file "{file.resolve()}" does not exist')

                # If on Docker and missing file was relative, warn first
                if (self.is_docker
                    and len(file.parts) > 1 and file.parts[1] == 'maker'):
                    log.warning(f'Did you mean "/config/{file.name}"?')
                continue

            # Read file, parse yaml
            if ((file_yaml := self._read_file(file, critical=False)) == {}
                or file_yaml is None or file_yaml.get('series', None) is None):
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
            for show_name in tqdm(file_yaml['series'], desc='Reading entries',
                                  **TQDM_KWARGS):
                # Skip if not a dictionary
                if not isinstance(file_yaml['series'][show_name], dict):
                    log.error(f'Skipping "{show_name}" from "{file_}"')
                    continue

                # Apply template and merge libraries+font maps
                show_yaml = self.finalize_show_yaml(
                    file_yaml['series'][show_name].get('name', show_name),
                    file_yaml['series'][show_name],
                    templates,
                    library_map,
                    font_map,
                    default_media_server=self.default_media_server,
                )

                # If returned YAML is None (invalid) skip series
                if show_yaml is None:
                    log.error(f'Skipping "{show_name}" from "{file_}"')
                    continue

                yield Show(show_name, show_yaml, self.source_directory, self)

                # Get all specified variations for this show
                variations = show_yaml.pop('archive_variations', [])
                if not isinstance(variations, list):
                    log.error(f'Invalid archive variations for {show_name}')
                    continue

                # Yield each variation
                show_yaml.pop('archive_name', None)
                show_yaml.pop('archive', None)
                for variation in variations:
                    # Apply template and merge libraries+font maps to variation
                    variation = self.finalize_show_yaml(
                        show_name, variation, templates, library_map, font_map,
                        default_media_server=self.default_media_server,
                    )

                    # Skip if finalization failed
                    if variation is None:
                        log.error(f'Skipping archive variation of "{show_name}"'
                                  f' from "{file_}"')
                        continue

                    # Get priority union of variation and base series
                    Template.recurse_priority_union(variation, show_yaml)

                    # Remove any library-specific details
                    variation.pop('media_directory', None)
                    variation.pop('library', None)

                    yield Show(show_name, variation, self.source_directory,self)


    @property
    def use_sonarr(self) -> bool:
        """Whether Sonarr is in use."""

        return len(self.sonarr_kwargs) > 0


    @property
    def tautulli_interface_args(self) -> dict[str, Union[str, int]]:
        """Arguments for initializing a TautulliInterface"""

        return {
            'url': self.tautulli_url,
            'api_key': self.tautulli_api_key,
            'verify_ssl': self.tautulli_verify_ssl,
            'update_script': self.tautulli_update_script,
            'agent_name': self.tautulli_agent_name,
            'script_timeout': self.tautulli_script_timeout,
            'username': self.tautulli_username,
        }

    @property
    def emby_interface_kwargs(self) -> dict[str, Union[str, bool, int]]:
        """Arguments for initializing a EmbyInterface"""

        return {
            'url': self.emby_url,
            'api_key': self.emby_api_key,
            'username': self.emby_username,
            'verify_ssl': self.emby_verify_ssl,
            'filesize_limit': self.emby_filesize_limit,
        }

    @property
    def jellyfin_interface_kwargs(self) -> dict[str, Union[str, bool, int]]:
        """Arguments for initializing a JellyfinInterface"""

        return {
            'url': self.jellyfin_url,
            'api_key': self.jellyfin_api_key,
            'username': self.jellyfin_username,
            'verify_ssl': self.jellyfin_verify_ssl,
            'filesize_limit': self.jellyfin_filesize_limit,
        }

    @property
    def plex_interface_kwargs(self) -> dict[str, Union[str, bool, int]]:
        """Arguments for initializing a PlexInterfa"""

        return {
            'url': self.plex_url,
            'x_plex_token': self.plex_token,
            'verify_ssl': self.plex_verify_ssl,
            'integrate_with_pmm_overlays': self.integrate_with_pmm_overlays,
            'filesize_limit': self.plex_filesize_limit,
        }

    @property
    def tmdb_interface_kwargs(self) -> dict[str, str]:
        """Arguments for initializing a TMDbInterface"""

        return {
            'api_key': self.tmdb_api_key,
        }


    def parse_image_source_priority(self, value: str) -> Optional[list[str]]:
        """
        Parse the given image source priority value into a list of
        sources.

        Args:
            value: Value of "image_source_priority" YAML attribute being
                parsed.

        Returns:
            Sorted list of image sources. None if the given value is
            invalid.
        """

        if isinstance(value, str):
            sources = tuple(value.replace(' ', '').split(','))
            if all(_ in self.VALID_IMAGE_SOURCES for _ in sources):
                return sources
        elif isinstance(value, list):
            if all(_ in self.VALID_IMAGE_SOURCES for _ in value):
                return value

        return None


    def meets_minimum_resolution(self, width: int, height: int) -> bool:
        """
        Determine whether the given dimensions meet the minimum
        resolution requirements indicated in the preference file.

        Args:
            width: The width of the image.
            height: The height of the image.

        Returns:
            True if the dimensions are suitable, False otherwise.
        """

        return (
            width >= self.tmdb_minimum_resolution['width']
            and height >= self.tmdb_minimum_resolution['height']
        )


    def get_season_folder(self, season_number: int) -> str:
        """
        Get the season folder name for the given season number, padding
        the season number if indicated by the preference file, and
        returning an empty string if season folders are hidden.

        Args:
            season_number: The season number to get the folder name of.

        Returns:
            The season folder name. Empty string if folders are hidden,
            'Specials' for season 0, and either a zero-padded or not
            zero- padded version of "Season {x}" otherwise.

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
            sys_exit(1)


    def filesize_as_bytes(self, filesize: Optional[str]) -> Optional[int]:
        """
        Convert the given filesize string to its integer byte equivalent.

        Args:
            filesize: Filesize string to parse. Should be formatted like
                '{integer} {unit}' - e.g. 2 KB, 4 GiB, 1 B, etc.

        Returns:
            Number of bytes indicated by the given filesize string.
        """

        # If no limit was provided, return None
        if filesize is None:
            return None

        units = {
            'B': 1, 'KB':  2**10, 'MB':  2**20, 'GB':  2**30, 'TB':  2**40,
            '': 1, 'KIB': 10**3, 'MIB': 10**6, 'GIB': 10**9, 'TIB':10**12
        }

        number, unit = map(str.strip, filesize.split())
        value, unit_scale = float(number), units[unit.upper()]

        return int(value * unit_scale)
