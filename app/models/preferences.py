from logging import Logger
from os import environ
from pathlib import Path
from typing import Any, Optional

from pickle import dump, load

from app.schemas.base import UNSPECIFIED, MediaServer
from app.schemas.preferences import CardExtension, ImageSource

from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
from modules.ImageMagickInterface import ImageMagickInterface
from modules.TitleCard import TitleCard
from modules.Version import Version


TCM_ROOT = Path(__file__).parent.parent.parent


class Preferences:
    """
    Class defining global Preferences.
    """

    """Path to the version file for the Web UI"""
    VERSION_FILE = TCM_ROOT / 'modules' / 'ref' / 'version_webui'

    """Default values for global settings"""
    DEFAULT_CARD_FILENAME_FORMAT = (
        '{series_full_name} - S{season_number:02}E{episode_number:02}'
    )
    DEFAULT_CARD_EXTENSION: CardExtension = '.jpg'
    DEFAULT_IMAGE_SOURCE_PRIORITY = [
        {'media_server': 'TMDb', 'interface_id': 0},
        {'media_server': 'Plex', 'interface_id': 0},
        {'media_server': 'Emby', 'interface_id': 0},
        {'media_server': 'Jellyfn', 'interface_id': 0},
    ]
    DEFAULT_EPISODE_DATA_SOURCE = {'media_server': 'Sonarr', 'interface_id': 0}
    VALID_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tiff', '.gif', '.webp')

    """Directory to all internal assets"""
    INTERNAL_ASSET_DIRECTORY = TCM_ROOT / 'app' / 'assets'

    """Directory for all temporary file operations"""
    TEMPORARY_DIRECTORY = TCM_ROOT / 'modules' / '.objects'


    __slots__ = (
        'is_docker', 'asset_directory', 'card_directory', 'source_directory',
        'file', 'card_width', 'card_height', 'card_filename_format',
        'card_extension', 'image_source_priority', 'episode_data_source',
        'valid_image_extensions', 'specials_folder_format',
        'season_folder_format', 'sync_specials', 'remote_card_types',
        'default_card_type', 'excluded_card_types', 'default_watched_style',
        'default_unwatched_style', 'use_tmdb', 'tmdb_api_key',
        'tmdb_minimum_width', 'tmdb_minimum_height', 'tmdb_skip_localized',
        'tmdb_download_logos', 'tmdb_logo_language_priority',
        'supported_language_codes', 'use_magick_prefix', 'current_version',
        'available_version', 'blacklisted_blueprints', 'advanced_scheduling',
        'require_auth', 'task_crontabs', 'simplified_data_table',
        'home_page_size', 'episode_data_page_size',
        'stylize_unmonitored_posters', 'sources_as_table',
        'emby_args', 'jellyfin_args', 'plex_args', 'sonarr_args',
    )


    def __init__(self, file: Path) -> None:
        """
        Initialize this object with the arguments from the given file.

        Args:
            file: Path to the file to parse for existing preferences.
        """

        # Set initial values
        self.is_docker = environ.get('TCM_IS_DOCKER', 'false').lower() == 'true'
        self.__initialize_defaults()

        # Get preferences from file
        self.file = file
        self.file.parent.mkdir(exist_ok=True)

        # Pars file
        self.parse_file(self.read_file())

        # Initialize paths
        self.asset_directory = Path(self.asset_directory)
        self.card_directory = Path(self.card_directory)
        self.source_directory = Path(self.source_directory)
        for folder in (self.asset_directory, self.card_directory,
                       self.source_directory):
            folder.mkdir(parents=True, exist_ok=True)

        # Migrate old settings
        if isinstance(self.episode_data_source, str):
            self.episode_data_source = {
                'media_server': self.episode_data_source, 'interface_id': 0,
            }
            self.commit()
        if (len(self.image_source_priority) > 0
            and isinstance(self.image_source_priority[0], str)):
            self.image_source_priority = [
                {'media_server': source, 'interface_id': 0}
                for source in self.image_source_priority
            ]
            self.commit()


    def __getstate__(self) -> dict:
        """
        Get the state definition of this object for pickling. This
        is all attributes except `remote_card_types`.

        Returns:
            Dictionary representation of this object with any un-
            pickleable attributes excluded.
        """

        # Exclude the remote card types dictionary because the types
        # might not be loaded at runtime; which could cause an error
        # when unpickling
        return {
            attr: getattr(self, attr) for attr in self.__slots__
            if attr not in ('remote_card_types', )
        }


    def __setstate__(self, state: dict) -> None:
        """
        Set the state of this object from the pickled representation.

        Args:
            state: Dictionary representation of the object.
        """

        for attr, value in state.items():
            setattr(self, attr, value)


    def __initialize_defaults(self) -> None:
        """Initialize this object with all default values."""

        if self.is_docker:
            self.asset_directory = Path('/config/assets')
            self.card_directory = Path('/config/cards')
            self.source_directory = Path('/config/source')
        else:
            self.asset_directory = TCM_ROOT / 'assets'
            self.card_directory = TCM_ROOT / 'cards'
            self.source_directory = TCM_ROOT / 'source'

        self.card_width = TitleCard.DEFAULT_WIDTH
        self.card_height = TitleCard.DEFAULT_HEIGHT
        self.card_filename_format = self.DEFAULT_CARD_FILENAME_FORMAT
        self.card_extension = self.DEFAULT_CARD_EXTENSION

        self.image_source_priority = self.DEFAULT_IMAGE_SOURCE_PRIORITY
        self.episode_data_source = self.DEFAULT_EPISODE_DATA_SOURCE
        self.valid_image_extensions = self.VALID_IMAGE_EXTENSIONS

        self.specials_folder_format = 'Specials'
        self.season_folder_format = 'Season {season_number}'

        self.sync_specials = True
        self.simplified_data_table = True
        self.remote_card_types = {}
        self.default_card_type = 'standard'
        self.excluded_card_types = []
        self.default_watched_style = 'unique'
        self.default_unwatched_style = 'unique'

        self.emby_args: dict[int, dict] = {}
        self.jellyfin_args: dict[int, dict] = {}
        self.plex_args: dict[int, dict] = {}
        self.sonarr_args: dict[int, dict] = {}

        self.use_tmdb = False
        self.tmdb_api_key = ''
        self.tmdb_minimum_width = 0
        self.tmdb_minimum_height = 0
        self.tmdb_skip_localized = False
        self.tmdb_download_logos = True
        self.tmdb_logo_language_priority = ['en']

        self.supported_language_codes = []
        self.use_magick_prefix = False
        self.blacklisted_blueprints = set()
        self.advanced_scheduling = False
        self.task_crontabs = {}

        self.require_auth = False
        self.home_page_size = 100
        self.episode_data_page_size = 50
        self.stylize_unmonitored_posters = False
        self.sources_as_table = False


    def read_file(self) -> Optional[object]:
        """
        Read this object's file, returning the loaded object.

        Returns:
            Object unpickled (loaded) from this object's file. None if
            the file does not exist or cannot be unpickled.
        """

        # Skip if file DNE
        if not self.file.exists():
            log.error(f'Preference file "{self.file.resolve()}" does not exist')
            return None

        # Parse file
        try:
            with self.file.open('rb') as file_handle:
                return load(file_handle)
        except Exception as exc:
            log.exception(f'Error occured while loading Preferences', exc)

        return None


    def parse_file(self, obj: object) -> None:
        """
        Initialize this object with the defaults for each attribute.
        """

        # Update each attribute known to this object
        for attribute in self.__slots__:
            if hasattr(obj, attribute):
                setattr(self, attribute, getattr(obj, attribute))

        # Set attributes not parsed from the object
        self.current_version = Version(self.VERSION_FILE.read_text().strip())
        self.available_version: Optional[Version] = None

        # Write object to file
        self.commit()


    def commit(self, *, log: Logger = log) -> None:
        """
        Commit the changes to this object to file.

        Args:
            log: (Keyword) Logger for all log messages.
        """

        # Open the file, dump this object's contents
        with self.file.open('wb') as file_handle:
            dump(self, file_handle)

        log.debug(f'Dumped Preferences to "{self.file.resolve()}"..')


    def update_values(self,
            *,
            log: Logger = log,
            **update_kwargs: dict
        ) -> None:
        """
        Update multiple values at once, and commit the changes
        afterwards.

        Args:
            update_kwargs: Dictionary of values to update.
        """

        # Iterate through updated attributes, set dictionary directly
        for name, value in update_kwargs.items():
            if value != UNSPECIFIED and value != getattr(self, name, '*'):
                setattr(self, name, value)
                if name in ('tmdb_api_key', ):
                    log.debug(f'Preferences.{name} = *****')
                else:
                    log.debug(f'Preferences.{name} = {value}')

        # Commit changes
        self.commit(log=log)


    def determine_imagemagick_prefix(self, *, log: Logger = log) -> None:
        """
        Determine whether to use the "magick " prefix for ImageMagick
        commands.

        Args:
            log: (Keyword) Logger for all log messages.
        """

        # Try variations of the font list command with/out the "magick " prefix
        for prefix, use_magick in zip(('magick ', ''), (True, False)):
            # Create ImageMagickInterface and verify validity
            interface = ImageMagickInterface(use_magick_prefix=use_magick)
            if interface.validate_interface():
                self.use_magick_prefix = use_magick # pylint: disable=W0201
                log.debug(f'Using "{prefix}" ImageMagick command prefix')
                return None

        # If none of the font commands worked, IM might not be installed
        log.critical(f"ImageMagick doesn't appear to be installed")
        return None


    @property
    def valid_image_sources(self) -> list[ImageSource]:
        """
        List of valid image sources.

        Returns:
            List of the names of all valid image sources. Only image
            sources with at least one defined interface are returned.
        """

        return ((['Emby'] if self.emby_args else [])
            + (['Jellyfin'] if self.jellyfin_args else [])
            + (['Plex'] if self.plex_args else [])
            + (['TMDb'] if self.use_tmdb else [])
        )


    @property
    def emby_argument_groups(self) -> list[dict[str, Any]]:
        """
        Argument groups for initializing an `InterfaceGroup` of
        `EmbyInterface` objects.

        Returns:
            List of dictionaries whose keys/values match a
            `EmbyConnection` object. Only enabled interfaces are
            returned.
        """

        return [
            {'interface_id': id_} | interface_args
            for id_, interface_args in self.emby_args.items()
            if interface_args['enabled']
        ]


    @property
    def all_emby_argument_groups(self) -> list[dict[str, Any]]:
        """
        All argument groups for initializing an `InterfaceGroup` of
        `EmbyInterface` objects.

        Returns:
            List of dictionaries whose keys/values match a
            `EmbyConnection` object.
        """

        return [
            {'interface_id': id_} | interface_args
            for id_, interface_args in self.emby_args.items()
        ]


    @property
    def imagemagick_arguments(self) -> dict[str, bool]:
        """Arguments for initializing a ImageMagickInterface"""

        return {
            'use_magick_prefix': self.use_magick_prefix,
        }


    @property
    def jellyfin_argument_groups(self) -> list[dict[str, Any]]:
        """
        Argument groups for initializing an `InterfaceGroup` of
        `JellyfinInterface` objects.

        Returns:
            List of dictionaries whose keys/values match a
            `JellyfinConnection` object. Only enabled interfaces are
            returned.
        """

        return [
            {'interface_id': id_} | interface_args
            for id_, interface_args in self.jellyfin_args.items()
            if interface_args['enabled']
        ]


    @property
    def all_jellyfin_argument_groups(self) -> list[dict[str, Any]]:
        """
        All argument groups for initializing an `InterfaceGroup` of
        `JellyfinInterface` objects.

        Returns:
            List of dictionaries whose keys/values match a
            `JellyfinConnection` object.
        """

        return [
            {'interface_id': id_} | interface_args
            for id_, interface_args in self.jellyfin_args.items()
        ]


    @property
    def plex_argument_groups(self) -> list[dict[str, Any]]:
        """
        Argument groups for initializing an `InterfaceGroup` of
        `PlexInterface` objects.

        Returns:
            List of dictionaries whose keys/values match a
            `PlexConnection` object. Only enabled interfaces are
            returned.
        """

        return [
            {'interface_id': id_} | interface_args
            for id_, interface_args in self.plex_args.items()
            if interface_args['enabled']
        ]


    @property
    def all_plex_argument_groups(self) -> list[dict[str, Any]]:
        """
        All argument groups for initializing an `InterfaceGroup` of
        `PlexInterface` objects.

        Returns:
            List of dictionaries whose keys/values match a
            `PlexConnection` object.
        """

        return [
            {'interface_id': id_} | interface_args
            for id_, interface_args in self.plex_args.items()
        ]


    @property
    def sonarr_argument_groups(self) -> list[dict[str, Any]]:
        """
        Argument groups for initializing an `InterfaceGroup` of
        `SonarrInterface` objects.

        Returns:
            List of dictionaries whose keys/values match a
            `SonarrConnection` object. Only enabled interfaces are
            returned.
        """

        return [
            {'interface_id': id_} | interface_args
            for id_, interface_args in self.sonarr_args.items()
            if interface_args['enabled']
        ]


    @property
    def all_sonarr_argument_groups(self) -> list[dict[str, Any]]:
        """
        All argument groups for initializing an `InterfaceGroup` of
        `SonarrInterface` objects.

        Returns:
            List of dictionaries whose keys/values match a
            `SonarrConnection` object.
        """

        return [
            {'interface_id': id_} | interface_args
            for id_, interface_args in self.sonarr_args.items()
        ]


    @property
    def tmdb_arguments(self) -> dict[str, Any]:
        """Arguments for initializing a TMDbInterface"""

        return {
            'api_key': str(self.tmdb_api_key),
            'minimum_source_width': self.tmdb_minimum_width,
            'minimum_source_height': self.tmdb_minimum_height,
            'blacklist_threshold': 3, # TODO add variable
            'logo_language_priority': self.tmdb_logo_language_priority,
        }


    @property
    def card_properties(self) -> dict[str, str]:
        """
        Properties to utilize and merge in Title Card creation.

        Returns:
            Dictionary of properties.
        """

        return {
            'card_type': self.default_card_type,
            'watched_style': self.default_watched_style,
            'unwatched_style': self.default_unwatched_style,
            'card_filename_format': self.card_filename_format,
        }


    @property
    def export_properties(self) -> dict[str, str]:
        """
        Properties to export in Blueprints.

        Returns:
            Dictionary of the properties that can be used in a
            NewNamedFont model to recreate this object.
        """

        return {
            'card_type': self.default_card_type,
        }


    @property
    def card_dimensions(self) -> str:
        """Card dimensions as a formatted dimensional string."""

        return f'{self.card_width}x{self.card_height}'


    @staticmethod
    def get_filesize(value: int, unit: str) -> Optional[int]:
        """
        Get the filesize for the given value and unit.

        Args:
            value: Value of the filesize limit.
            unit: Unit of the filesize limit.

        Returns:
            The integer value of the filesize equivalent of the given
            arguments (in Bytes). None if value or unit is None.
        """

        # If either value is None, return that
        if value is None or unit is None:
            return None

        return value * {
            'b':  1,         'bytes': 1,
            'kb': 2**10, 'kilobytes': 2**10,
            'mb': 2**20, 'megabytes': 2**20,
            'gb': 2**30, 'gigabytes': 2**30,
            'tb': 2**40, 'terabytes': 2**40,
        }[unit.lower()]


    @staticmethod
    def format_filesize(value: Optional[int]) -> tuple[str, str]:
        """
        Format the given filesize limit into a tuple of filesize value
        and units. Formatted as the highest >1 unit value.

        Args:
            value: Integer value of the filesize (in Bytes).

        Returns:
            Tuple of the string equivalent of the filesize bytes and the
            corresponding unit.
        """

        if value is None or value == 0:
            return '0', 'Bytes'

        for ref_value, unit in (
                (2**40, 'Terabytes'),
                (2**30, 'Gigabytes'),
                (2**20, 'Megabytes'),
                (2**10, 'Kilobytes'),
                (1, 'Bytes')):
            if value > ref_value:
                return f'{value/ref_value:,.1f}', unit

        return '0', 'Bytes'


    def determine_sonarr_library(self,
            directory: str,
            interface_id: int,
        ) -> list[tuple[MediaServer, int, str]]:
        """
        Determine the libraries of the series in the given directory.

        Args:
            directory: Directory whose library is being determined.
            interface_id: ID of the Sonarr interface corresponding to
                whose libraries are being evaluated.

        Returns:
            List of tuples of the media server name, interface ID, and
            the library name.
        """

        return [
            (library['media_server'], library['interface_id'], library)
            for library in self.sonarr_args[interface_id]['libraries']
            if directory.startswith(library['path'])
        ]


    def standardize_style(self, style: str) -> str:
        """
        Standardize the given style string so that style modifiers are
        not order dependent.

        For example, "blur unique" should standardize to the same value
        as "unique blur".

        Args:
            style: Style string being standardized.

        Returns:
            Standardized value. This is an alphabetically sorted space-
            separated lowercase variation of style. If the given style
            was just "blur", then "blur unique" is returned.
        """

        # Add "unique" if not in the style
        standardized = str(style).lower().strip()
        if 'art' not in standardized and 'unique' not in standardized:
            standardized += ' unique'

        # All other styles get typical standardization.
        return ' '.join(sorted(standardized.split(' ')))


    def get_folder_format(self, episode_info: EpisodeInfo) -> str:
        """
        Get the season folder name for the given Episode.

        Args:
            episode_info: EpisodeInfo of the Episode whose folder is
                being evaluated.

        Returns:
            Name of the season subfolder for the given Episode.
        """

        # Format Specials differently
        if episode_info.season_number == 0:
            return self.specials_folder_format.format(**episode_info.indices)

        return self.season_folder_format.format(**episode_info.indices)


    def get_card_type_class(self,
            card_type_identifier: str,
            *,
            log: Logger = log,
        ) -> Optional['CardType']: # type: ignore
        """
        Get the CardType class for the given card type identifier.

        Args:
            card_type_identifier: Identifier of the CardType class.
            log: (Keyword) Logger for all log messages.

        Returns:
            CardType subclass of the given identifier. If this is an
            unknown identifier, None is returned instead.
        """

        # Get the effective card class
        if card_type_identifier in TitleCard.CARD_TYPES:
            return TitleCard.CARD_TYPES[card_type_identifier]
        if card_type_identifier in self.remote_card_types:
            return self.remote_card_types[card_type_identifier]

        log.error(f'Unable to identify card type "{card_type_identifier}"')
        return None
