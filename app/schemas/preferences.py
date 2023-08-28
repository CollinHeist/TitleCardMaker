# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument,no-name-in-module
from pathlib import Path
from typing import Literal, Optional

from pydantic import (
    AnyUrl, DirectoryPath, Field, NonNegativeInt, PositiveInt, SecretStr,
    constr, root_validator, validator
)
from pydantic.error_wrappers import ValidationError

from app.schemas.base import Base, UpdateBase, UNSPECIFIED


"""
Match local identifiers (A-Z and space), remote card types (a-z/a-z, no space),
and local card types (any character .py).
"""
CardTypeIdentifier = constr(regex=r'^([a-zA-Z ]+|[a-zA-Z]+\/[a-zA-Z]+|.+\.py)$')
"""
Match hexstrings of A-F and 0-9.
"""
Hexstring = constr(regex=r'^[a-fA-F0-9]+$')

CardExtension = Literal['.jpg', '.jpeg', '.png', '.tiff', '.gif', '.webp']
FilesizeUnit = Literal[
    'b', 'kb', 'mb', 'gb', 'tb', 'B', 'KB', 'MB', 'GB', 'TB'
    'bytes', 'kilobytes', 'megabytes', 'gigabytes', 'terabytes',
    'Bytes', 'Kilobytes', 'Megabytes', 'Gigabytes', 'Terabytes',
]

Style = Literal[
    'art', 'art blur', 'art grayscale', 'art blur grayscale', 'unique',
    'blur unique', 'grayscale unique', 'blur grayscale unique',
]

LanguageCode = Literal[
    'ar', 'bg', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es', 'fa', 'fr', 'he',
    'hu', 'id', 'it', 'ja', 'ko', 'my', 'pl', 'pt', 'ro', 'ru', 'sk', 'sr',
    'th', 'tr', 'uk', 'vi', 'zh',
]

"""
Creation classes
"""
class NamedOption(Base):
    name: str
    value: str

class StyleOption(NamedOption):
    style_type: Literal['art', 'unique']

class ToggleOption(NamedOption):
    selected: bool

# class MediaServerToggle(ToggleOption):
#     ...

class EpisodeDataSourceToggle(ToggleOption):
    ...

class ImageSourceToggle(ToggleOption):
    ...

class LanguageToggle(ToggleOption):
    ...

EpisodeDataSource = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr', 'TMDb']
ImageSource = Literal['Emby', 'Jellyfin', 'Plex', 'TMDb']
MediaServer = Literal['Emby', 'Jellyfin', 'Plex']

"""
Base classes
"""
class SonarrLibrary(Base):
    name: str
    path: str

class TautulliConnection(Base):
    tautulli_url: AnyUrl
    tautulli_api_key: SecretStr = Field(..., min_length=1)
    tautulli_use_ssl: bool = True
    tautulli_agent_name: str = Field(..., min_length=1)

"""
Update classes
"""
class UpdatePreferences(UpdateBase):
    card_directory: DirectoryPath = UNSPECIFIED
    source_directory: DirectoryPath = UNSPECIFIED
    card_width: PositiveInt = UNSPECIFIED
    card_height: PositiveInt = UNSPECIFIED
    card_filename_format: str = UNSPECIFIED
    card_extension: CardExtension = UNSPECIFIED
    image_source_priority: list[ImageSource] = UNSPECIFIED
    episode_data_source: EpisodeDataSource = UNSPECIFIED
    specials_folder_format: str = UNSPECIFIED
    season_folder_format: str = UNSPECIFIED
    sync_specials: bool = UNSPECIFIED
    simplified_data_table: bool = UNSPECIFIED
    default_card_type: CardTypeIdentifier = UNSPECIFIED
    excluded_card_types: list[CardTypeIdentifier] = UNSPECIFIED
    default_watched_style: Style = UNSPECIFIED
    default_unwatched_style: Style = UNSPECIFIED
    home_page_size: PositiveInt = UNSPECIFIED
    episode_data_page_size: PositiveInt = UNSPECIFIED
    stylize_unmonitored_posters: bool = UNSPECIFIED
    sources_as_table: bool = UNSPECIFIED

    @validator('card_filename_format', pre=True)
    def validate_card_filename_format(cls, v):
        try:
            v.format(
                series_name='test', series_full_name='test (2000)',
                year=2000, title='Test Title', season_number=1, episode_number=1,
                absolute_number=1, emby_id='abc123', imdb_id='tt1234',
                jellyfin_id='abc123', tmdb_id=123, tvdb_id=123, tvrage_id=123,
            )
        except KeyError as exc:
            raise ValueError(
                f'Invalid Card filename format - missing data {exc}'
            ) from exc

        return v

    @validator('image_source_priority', 'excluded_card_types', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @validator('specials_folder_format', 'season_folder_format', pre=True)
    def validate_folder_formats(cls, v):
        try:
            v.format(season_number=1, episode_number=1, absolute_number=1)
        except KeyError as exc:
            raise ValueError(
                f'Invalid folder format - use "season_number", "episode_numer" '
                f'and/or "absolute_number"'
            ) from exc

        return v

class UpdateServerBase(UpdateBase):
    url: AnyUrl = UNSPECIFIED

class UpdateMediaServerBase(UpdateServerBase):
    use_ssl: bool = UNSPECIFIED
    filesize_limit_number: int = Field(gt=0, default=UNSPECIFIED)
    filesize_limit_unit: FilesizeUnit = UNSPECIFIED

    @validator('filesize_limit_unit', pre=False)
    def validate_list(cls, v):
        if isinstance(v, str):
            return {
                'b':         'Bytes',     'bytes':     'Bytes',
                'kb':        'Kilobytes', 'kilobytes': 'Kilobytes',
                'mb':        'Megabytes', 'megabytes': 'Megabytes',
                'gb':        'Gigabytes', 'gigabytes': 'Gigabytes',
                'tb':        'Terabytes', 'terabytes': 'Terabytes',
            }[v.lower()]
        return v

    @root_validator(skip_on_failure=True, pre=True)
    def validate_filesize(cls, values):
        if (values.get('filesize_limit_number', UNSPECIFIED) != UNSPECIFIED
            and not values.get('filesize_limit_unit',UNSPECIFIED) !=UNSPECIFIED):
            raise ValidationError(f'Filesize limit number requires unit')

        return values

class UpdateEmby(UpdateMediaServerBase):
    api_key: Hexstring = UNSPECIFIED
    username: Optional[str] = UNSPECIFIED

class UpdateJellyfin(UpdateMediaServerBase):
    api_key: Hexstring = UNSPECIFIED
    username: Optional[str] = Field(default=UNSPECIFIED, min_length=1)

class UpdatePlex(UpdateMediaServerBase):
    token: str = UNSPECIFIED
    integrate_with_pmm: bool = UNSPECIFIED

class UpdateSonarr(UpdateServerBase):
    api_key: Hexstring = UNSPECIFIED
    use_ssl: bool = UNSPECIFIED
    downloaded_only: bool = UNSPECIFIED
    libraries: list[SonarrLibrary] = UNSPECIFIED

    @validator('libraries', pre=False)
    def validate_list(cls, v):
        # Filter out empty strings - all arguments can accept empty lists
        return [library for library in v if library.name and library.path]

class UpdateTMDb(UpdateBase):
    api_key: Hexstring = UNSPECIFIED
    minimum_width: NonNegativeInt = UNSPECIFIED
    minimum_height: NonNegativeInt = UNSPECIFIED
    skip_localized: bool = UNSPECIFIED
    download_logos: bool = UNSPECIFIED
    logo_language_priority: list[LanguageCode] = UNSPECIFIED

    @validator('logo_language_priority', pre=True)
    def validate_list(cls, v):
        # Split comma separated language codes into list of codes
        return list(map(lambda s: str(s).lower().strip(), v.split(',')))

"""
Return classes
"""
class Preferences(Base):
    card_directory: Path
    source_directory: Path
    card_width: PositiveInt
    card_height: PositiveInt
    card_filename_format: str
    card_extension: str
    image_source_priority: list[ImageSource]
    valid_image_sources: list[ImageSource]
    episode_data_source: EpisodeDataSource
    valid_episode_data_sources: list[EpisodeDataSource]
    valid_image_extensions: list[str]
    specials_folder_format: str
    season_folder_format: str
    sync_specials: bool
    simplified_data_table: bool
    is_docker: bool
    default_card_type: CardTypeIdentifier
    excluded_card_types: list[CardTypeIdentifier]
    default_watched_style: Style
    default_unwatched_style: Style
    home_page_size: PositiveInt
    episode_data_page_size: PositiveInt
    stylize_unmonitored_posters: bool
    sources_as_table: bool

class EmbyConnection(Base):
    use_emby: bool
    emby_url: AnyUrl
    emby_api_key: SecretStr
    emby_username: Optional[str]
    emby_filesize_limit: Optional[int]

class JellyfinConnection(Base):
    use_jellyfin: bool
    jellyfin_url: AnyUrl
    jellyfin_api_key: SecretStr
    jellyfin_username: Optional[str]
    jellyfin_filesize_limit: Optional[int]

class PlexConnection(Base):
    use_plex: bool
    plex_url: AnyUrl
    plex_token: SecretStr
    plex_integrate_with_pmm: bool
    plex_filesize_limit: Optional[int]

class SonarrConnection(Base):
    use_sonarr: bool
    sonarr_url: AnyUrl
    sonarr_api_key: SecretStr
    sonarr_libraries: list[SonarrLibrary]

class TMDbConnection(Base):
    use_tmdb: bool
    tmdb_api_key: SecretStr
    tmdb_minimum_width: NonNegativeInt
    tmdb_minimum_height: NonNegativeInt
    tmdb_skip_localized: bool
    tmdb_download_logos: bool
    tmdb_logo_language_priority: list[LanguageCode]
