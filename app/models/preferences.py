from collections import namedtuple
from os import environ
from pathlib import Path
from typing import Any, Union

from pickle import dump

from modules.Debug import log
from modules.ImageMagickInterface import ImageMagickInterface
from modules.StyleSet import StyleSet

EpisodeDataSource = namedtuple('EpisodeDataSource', ('value', 'label'))
Emby = EpisodeDataSource('emby', 'Emby')
Jellyfin = EpisodeDataSource('jellyfin', 'Jellyfin')
Plex = EpisodeDataSource('plex', 'Plex')
Sonarr = EpisodeDataSource('sonarr', 'Sonarr')
TMDb = EpisodeDataSource('tmdb', 'TMDb')

TCM_ROOT = Path(__file__).parent.parent.parent

class Preferences:

    DEFAULT_CARD_FILENAME_FORMAT = ('{full_name} S{season_number:02}'
                                    'E{episode_number:02}')
    DEFAULT_CARD_EXTENSION = '.jpg'
    DEFAULT_IMAGE_SOURCE_PRIORITY = ['TMDb', 'Plex', 'Jellyfin', 'Emby']
    DEFAULT_EPISODE_DATA_SOURCE = 'Sonarr'
    VALID_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tiff', '.gif', '.webp')
    

    def __init__(self) -> None:
        self.asset_directory = Path(__file__).parent.parent / 'assets'
        self.card_directory = TCM_ROOT / 'cards'
        self.source_directory = TCM_ROOT / 'source'

        self.card_filename_format = self.DEFAULT_CARD_FILENAME_FORMAT
        self.card_extension = self.DEFAULT_CARD_EXTENSION
        self.image_source_priority = self.DEFAULT_IMAGE_SOURCE_PRIORITY
        self.episode_data_source = self.DEFAULT_EPISODE_DATA_SOURCE
        self.valid_image_extensions = self.VALID_IMAGE_EXTENSIONS

        self.specials_folder_format = 'Specials'
        self.season_folder_format = 'Season {season_number}'
        self.sync_specials = True

        self.default_card_type = 'standard'
        self.default_watched_style = 'unique'
        self.default_unwatched_style = 'unique'

        self.use_emby = False
        self.emby_url = 'http://192.168.0.11:8096/emby' #''
        self.emby_api_key = 'e25b06a1aee34fc0949c35d74f379d03' #''
        self.emby_username = 'CollinHeist' #''
        self.emby_use_ssl = False
        self.emby_filesize_limit_number = None
        self.emby_filesize_limit_unit = None

        self.use_jellyfin = False
        self.jellyfin_url = ''
        self.jellyfin_api_key = ''
        self.jellyfin_username = ''
        self.jellyfin_use_ssl = False
        self.jellyfin_filesize_limit_number = None
        self.jellyfin_filesize_limit_unit = None

        self.use_plex = True #False
        self.plex_url = 'http://192.168.0.29:32400/' #''
        self.plex_token = 'pzfzWxW-ygxzJJc-t_Pw' #''
        self.plex_use_ssl = False
        self.plex_integrate_with_pmm = False
        self.plex_filesize_limit_number = 10
        self.plex_filesize_limit_unit = 'MB'

        self.use_sonarr = True #False
        self.sonarr_url = 'http://192.168.0.29:8989/api/v3/' #''
        self.sonarr_api_key = 'd43fdeb9c3744f58b1ffbaf5dc21e55a' #''
        self.sonarr_use_ssl = False
        self.sonarr_libraries = {}

        self.use_tmdb = True #False
        self.tmdb_api_key = 'b1dbf02a14b523a94401e3e6ee521353' #''
        self.tmdb_minimum_width = 800 #0
        self.tmdb_minimum_height = 400 #0
        self.tmdb_skip_localized = False
        self.supported_language_codes = []

        self.is_docker = environ.get('TCM_IS_DOCKER', 'false').lower() == 'true'
        self.use_magick_prefix = False
        self.imagemagick_container = 'ImageMagick' #None
        self.imagemagick_timeout = 60
        self.__determine_imagemagick_prefix()


    def __setattr__(self, name, value) -> None:
        self.__dict__[name] = value
        log.debug(f'preferences.__dict__[{name}] = {value}')
        self._rewrite_preferences()


    def _rewrite_preferences(self) -> None:
        with Path('/mnt/user/Media/TitleCardMaker/app/prefs.json').open('wb') as fh:
            dump(self, fh)


    def __determine_imagemagick_prefix(self) -> None:
        """
        Determine whether to use the "magick " prefix for ImageMagick commands.
        If a prefix cannot be determined, a critical message is logged and the
        program exits with an error.
        """

        # Try variations of the font list command with/out the "magick " prefix
        for prefix, use_magick in zip(('', 'magick '), (False, True)):
            # Create ImageMagickInterface and verify validity
            interface = ImageMagickInterface(
                self.imagemagick_container,
                use_magick,
                self.imagemagick_timeout
            )
            if interface.validate_interface():
                self.use_magick_prefix = use_magick
                log.debug(f'Using "{prefix}" ImageMagick command prefix')
                return None

        # If none of the font commands worked, IM might not be installed
        log.critical(f"ImageMagick doesn't appear to be installed")
        self.valid = False


    def update_values(self, **update_kwargs) -> None:
        for name, value in update_kwargs.items():
            self.__dict__[name] = value
        self._rewrite_preferences()


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
        }


    @property
    def valid_image_sources(self) -> list[str]:
        return set(
            (['Emby'] if self.use_emby else [])
            + (['Plex'] if self.use_plex else [])
            + (['TMDb'] if self.use_tmdb else [])
        )


    @property
    def valid_episode_data_sources(self) -> list[str]:
        return (
            (['Emby'] if self.use_emby else [])
            + (['Plex'] if self.use_plex else [])
            + (['TMDb'] if self.use_tmdb else [])
            + (['Sonarr'] if self.use_sonarr else [])
        )


    @property
    def enabled_media_servers(self) -> list[str]:
        return (
            (['Emby'] if self.use_emby else [])
            + (['Plex'] if self.use_plex else [])
        )


    @staticmethod
    def get_filesize(value: int, unit: str) -> Union[int, None]:
        # If either value is None, return that
        if value is None or unit is None:
            return None

        return value * {
            'B': 1, 'Bytes': 1,
            'KB':  2**10, 'Kilobytes': 2**10,
            'MB':  2**20, 'Megabytes': 2**20,
            'GB':  2**30, 'Gigabytes': 2**30,
            'TB':  2**40, 'Terabytes': 2**40,
        }[unit]


    def determine_sonarr_library(self, directory: str) -> Union[str, None]:
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