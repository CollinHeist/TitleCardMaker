from collections import namedtuple
from logging import Logger
from os import environ
from pathlib import Path
from typing import Any, Optional

from pickle import dump, load

from app.schemas.base import UNSPECIFIED

from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
from modules.ImageMagickInterface import ImageMagickInterface
from modules.TitleCard import TitleCard
from modules.Version import Version


EpisodeDataSource = namedtuple('EpisodeDataSource', ('value', 'label'))
Emby = EpisodeDataSource('emby', 'Emby')
Jellyfin = EpisodeDataSource('jellyfin', 'Jellyfin')
Plex = EpisodeDataSource('plex', 'Plex')
Sonarr = EpisodeDataSource('sonarr', 'Sonarr')
TMDb = EpisodeDataSource('tmdb', 'TMDb')

TCM_ROOT = Path(__file__).parent.parent.parent

class Preferences:
    """
    Class defining global Preferences.
    """

    """Path to the version file for the Web UI"""
    VERSION_FILE = TCM_ROOT / 'modules' / 'ref' / 'version_webui'

    """Default values for global settings"""
    DEFAULT_CARD_FILENAME_FORMAT = (
        '{series_full_name} S{season_number:02}E{episode_number:02}'
    )
    DEFAULT_CARD_EXTENSION = '.jpg'
    DEFAULT_IMAGE_SOURCE_PRIORITY = ['TMDb', 'Plex', 'Jellyfin', 'Emby']
    DEFAULT_EPISODE_DATA_SOURCE = 'Sonarr'
    VALID_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tiff', '.gif', '.webp')

    """Directory to all internal assets"""
    INTERNAL_ASSET_DIRECTORY = TCM_ROOT / 'app' / 'assets'

    """Directory for all temporary file operations"""
    TEMPORARY_DIRECTORY = TCM_ROOT / 'modules' / '.objects'

    """Attributes that should not be explicitly logged"""
    PRIVATE_ATTRIBUTES = (
        'emby_url', 'emby_api_key', 'jellyfin_url', 'jellyfin_api_key',
        'plex_url', 'plex_token', 'sonarr_url', 'sonarr_api_key', 'tmdb_api_key'
    )


    def __init__(self, file: Path) -> None:
        """
        Initialize this object with the arguments from the given file.

        Args:
            file: Path to the file to parse for existing preferences.
        """

        # Get preferences from file
        self.file = file
        self.file.parent.mkdir(exist_ok=True)
        obj = self.read_file()

        # Initialize object based on parsed file
        self.parse_file(obj)

        # Override fixed attributes
        if self.is_docker:
            self.asset_directory = Path('/config/assets')
        else:
            self.asset_directory = TCM_ROOT / 'assets'
        self.asset_directory.mkdir(parents=True, exist_ok=True)


    def read_file(self) -> Optional[object]:
        """
        Read this object's file, returning the loaded object.

        Returns:
            Object unpickled (loaded) from this object's file.
        """

        # Skip if file DNE
        if not self.file.exists():
            log.error(f'Preference file "{self.file.resolve()}" does not exist')
            return None

        # Parse file
        try:
            with self.file.open('rb') as file_handle:
                return load(file_handle)
        except Exception as e:
            log.exception(f'Error occured while loading Preferences', e)

        return None


    def parse_file(self, obj: object) -> None:
        """
        Initialize this object with the defaults for each attribute.
        """

        # Set attributes not parsed from the object
        self.current_version = Version(self.VERSION_FILE.read_text().strip())
        self.available_version: Optional[Version] = None
        self.is_docker = environ.get('TCM_IS_DOCKER', 'false').lower() == 'true'

        # Default arguments
        default_asset_directory = '/config/assets' if self.is_docker else TCM_ROOT / 'assets'
        default_card_directory = '/config/cards' if self.is_docker else TCM_ROOT / 'cards'
        default_source_directory = '/config/source' if self.is_docker else TCM_ROOT / 'source'
        DEFAULTS = {
            'asset_directory':  default_asset_directory,
            'card_directory': default_card_directory,
            'source_directory': default_source_directory,
            'card_width': TitleCard.DEFAULT_WIDTH,
            'card_height': TitleCard.DEFAULT_HEIGHT,
            'card_filename_format': self.DEFAULT_CARD_FILENAME_FORMAT,
            'card_extension': self.DEFAULT_CARD_EXTENSION,
            'image_source_priority': self.DEFAULT_IMAGE_SOURCE_PRIORITY,
            'episode_data_source': self.DEFAULT_EPISODE_DATA_SOURCE,
            'valid_image_extensions': self.VALID_IMAGE_EXTENSIONS,
            'specials_folder_format': 'Specials',
            'season_folder_format': 'Season {season_number}',
            'sync_specials': True,
            'remote_card_types': {},
            'default_card_type': 'standard',
            'excluded_card_types': [],
            'default_watched_style': 'unique',
            'default_unwatched_style': 'unique',
            'use_emby': False,
            'emby_url': '',
            'emby_api_key': '',
            'emby_username': None,
            'emby_use_ssl': True,
            'emby_filesize_limit_number': None,
            'emby_filesize_limit_unit': None,
            'use_jellyfin': False,
            'jellyfin_url': '',
            'jellyfin_api_key': '',
            'jellyfin_username': None,
            'jellyfin_use_ssl': True,
            'jellyfin_filesize_limit_number': None,
            'jellyfin_filesize_limit_unit': None,
            'use_plex': False,
            'plex_url': '',
            'plex_token': '',
            'plex_use_ssl': True,
            'plex_integrate_with_pmm': False,
            'plex_filesize_limit_number': 10,
            'plex_filesize_limit_unit': 'Megabytes',
            'use_sonarr': False,
            'sonarr_url': '',
            'sonarr_api_key': '',
            'sonarr_use_ssl': True,
            'sonarr_libraries': {},
            'use_tmdb': False,
            'tmdb_api_key': '',
            'tmdb_minimum_width': 0,
            'tmdb_minimum_height': 0,
            'tmdb_skip_localized': False,
            'tmdb_download_logos': True,
            'tmdb_logo_language_priority': ['en'],
            'supported_language_codes': [],
            'use_magick_prefix': False,
        }

        # Update each attribute known to this object
        for attribute, value in DEFAULTS.items():
            if hasattr(obj, attribute):
                setattr(self, attribute, getattr(obj, attribute))
            else:
                setattr(self, attribute, value)

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
            if value != UNSPECIFIED:
                setattr(self, name, value)
                if name in self.PRIVATE_ATTRIBUTES:
                    log.debug(f'Preferences.{name} = *****')
                else:
                    log.debug(f'Preferences.{name} = {value}')

        # Commit changes
        self.commit(log=log)

        return None


    def determine_imagemagick_prefix(self) -> None:
        """
        Determine whether to use the "magick " prefix for ImageMagick
        commands.
        """

        # Try variations of the font list command with/out the "magick " prefix
        for prefix, use_magick in zip(('magick ', ''), (True, False)):
            # Create ImageMagickInterface and verify validity
            interface = ImageMagickInterface(use_magick)
            if interface.validate_interface():
                self.use_magick_prefix = use_magick
                log.debug(f'Using "{prefix}" ImageMagick command prefix')
                return None

        # If none of the font commands worked, IM might not be installed
        log.critical(f"ImageMagick doesn't appear to be installed")
        return None


    @property
    def emby_filesize_limit(self) -> int:
        return self.get_filesize(
            self.emby_filesize_limit_number,
            self.emby_filesize_limit_unit,
        )

    @property
    def jellyfin_filesize_limit(self) -> int:
        return self.get_filesize(
            self.jellyfin_filesize_limit_number,
            self.jellyfin_filesize_limit_unit,
        )

    @property
    def plex_filesize_limit(self) -> int:
        return self.get_filesize(
            self.plex_filesize_limit_number,
            self.plex_filesize_limit_unit,
        )


    @property
    def emby_arguments(self) -> dict[str, Any]:
        return {
            'url': self.emby_url,
            'api_key': self.emby_api_key,
            'username': self.emby_username,
            'verify_ssl': self.emby_use_ssl,
            'filesize_limit': self.emby_filesize_limit,
        }

    @property
    def imagemagick_arguments(self) -> dict[str, bool]:
        return {
            'use_magick_prefix': self.use_magick_prefix,
        }

    @property
    def jellyfin_arguments(self) -> dict[str, Any]:
        return {
            'url': self.jellyfin_url,
            'api_key': self.jellyfin_api_key,
            'username': self.jellyfin_username,
            'verify_ssl': self.jellyfin_use_ssl,
            'filesize_limit': self.jellyfin_filesize_limit,
        }

    @property
    def plex_arguments(self) -> dict[str, Any]:
        return {
            'url': self.plex_url,
            'token': self.plex_token,
            'verify_ssl': self.plex_use_ssl,
            'integrate_with_pmm': self.plex_integrate_with_pmm,
            'filesize_limit': self.plex_filesize_limit,
        }

    @property
    def sonarr_arguments(self) -> dict[str, Any]:
        return {
            'url': self.sonarr_url,
            'api_key': self.sonarr_api_key,
            'verify_ssl': self.sonarr_use_ssl,
        }

    @property
    def tmdb_arguments(self) -> dict[str, Any]:
        return {
            'api_key': self.tmdb_api_key,
            'minimum_source_width': self.tmdb_minimum_width,
            'minimum_source_height': self.tmdb_minimum_height,
            'blacklist_threshold': 3, # TODO add variable
            'logo_language_priority': self.tmdb_logo_language_priority,
        }

    @property
    def valid_image_sources(self) -> set[str]:
        return set(
            (['Emby'] if self.use_emby else [])
            + (['Jellyfin'] if self.use_jellyfin else [])
            + (['Plex'] if self.use_plex else [])
            + (['TMDb'] if self.use_tmdb else [])
        )

    @property
    def valid_episode_data_sources(self) -> list[str]:
        return (
            (['Emby'] if self.use_emby else [])
            + (['Jellyfin'] if self.use_jellyfin else [])
            + (['Plex'] if self.use_plex else [])
            + (['TMDb'] if self.use_tmdb else [])
            + (['Sonarr'] if self.use_sonarr else [])
        )

    @property
    def enabled_media_servers(self) -> list[str]:
        return (
            (['Emby'] if self.use_emby else [])
            + (['Jellyfin'] if self.use_jellyfin else [])
            + (['Plex'] if self.use_plex else [])
        )

    @property
    def card_properties(self) -> dict[str, str]:
        return {
            'card_type': self.default_card_type,
            'watched_style': self.default_watched_style,
            'unwatched_style': self.default_unwatched_style,
            'card_filename_format': self.card_filename_format,
        }
    
    @property
    def export_properties(self) -> dict:
        return {
            'card_type': self.default_card_type,
        }
    
    @property
    def card_dimensions(self) -> str:
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


    def determine_sonarr_library(self, directory: str) -> Optional[str]:
        """
        Determine the library of the series in the given directory. This
        uses this object's sonarr_libraries attribute.

        Args:
            directory: Directory whose library is being determined.

        Returns:
            Name of the directory's matching library. None if no library
            can be determined.
        """

        for library, path in self.sonarr_libraries.items():
            if directory.startswith(path):
                return library

        return None
    

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

        Returns:
            CardType subclass of the given identifier. If this is an
            unknown identifier, None is returned instead.
        """

        # Get the effective card class
        if card_type_identifier in TitleCard.CARD_TYPES:
            return TitleCard.CARD_TYPES[card_type_identifier]
        elif card_type_identifier in self.remote_card_types:
            return self.remote_card_types[card_type_identifier]

        log.error(f'Unable to identify card type "{card_type_identifier}"')
        return None