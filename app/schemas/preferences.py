from pathlib import Path
from typing import Literal, Optional

from pydantic import (
    AnyUrl, DirectoryPath, Field, NonNegativeInt, PositiveInt, SecretStr,
    constr, root_validator, validator
)
from pydantic.error_wrappers import ValidationError

from app.schemas.base import (
    Base, UpdateBase, UNSPECIFIED, validate_argument_lists_to_dict
)

from modules.Debug import log

"""
Match local identifiers (A-Z and space), remote card types (a-z/a-z, no space),
and local card types (any character .py).
""" 
CardTypeIdentifier = constr(regex=r'^([a-zA-Z ]+|[a-zA-Z]+\/[a-zA-Z]+|.+\.py)$')
"""
Match hexstrings of A-F and 0-9 
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
class TautulliConnection(Base):
    tautulli_url: AnyUrl = Field(...)
    tautulli_api_key: SecretStr = Field(..., min_length=1)
    tautulli_use_ssl: bool = Field(default=True)
    tautulli_agent_name: str = Field(..., min_length=1)

"""
Update classes
"""
class UpdatePreferences(UpdateBase):
    card_directory: DirectoryPath = Field(default=UNSPECIFIED)
    source_directory: DirectoryPath = Field(default=UNSPECIFIED)
    card_width: PositiveInt = Field(default=UNSPECIFIED)
    card_height: PositiveInt = Field(default=UNSPECIFIED)
    card_filename_format: str = Field(default=UNSPECIFIED)
    card_extension: CardExtension = Field(default=UNSPECIFIED)
    image_source_priority: list[ImageSource] = Field(default=UNSPECIFIED)
    episode_data_source: EpisodeDataSource = Field(default=UNSPECIFIED)
    specials_folder_format: str = Field(default=UNSPECIFIED)
    season_folder_format: str = Field(default=UNSPECIFIED)
    sync_specials: bool = Field(default=UNSPECIFIED)
    default_card_type: CardTypeIdentifier = Field(default=UNSPECIFIED)
    excluded_card_types: list[CardTypeIdentifier] = Field(default=UNSPECIFIED)
    default_watched_style: Style = Field(default=UNSPECIFIED)
    default_unwatched_style: Style = Field(default=UNSPECIFIED)

    @validator('card_filename_format', pre=True)
    def validate_card_filename_format(cls, v):
        try:
            v.format(
                series_name='test', series_full_name='test (2000)',
                year=2000, season_number=1, episode_number=1, absolute_number=1,
                emby_id='abc123', imdb_id='tt1234', jellyfin_id='abc123',
                tmdb_id=123, tvdb_id=123, tvrage_id=123,
            )
        except KeyError as e:
            raise ValueError(f'Invalid Card filename format - missing data {e}')

        return v

    @validator('image_source_priority', 'excluded_card_types', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v
    
    @validator('specials_folder_format', 'season_folder_format', pre=True)
    def validate_folder_formats(cls, v):
        try:
            v.format(season_number=1, episode_number=1, absolute_number=1)
        except KeyError:
            raise ValueError(f'Invalid folder format - use "season_number", '
                             f'"episode_numer" and/or "absolute_number"')

        return v
    
class UpdateServerBase(UpdateBase):
    url: AnyUrl = Field(default=UNSPECIFIED)

class UpdateMediaServerBase(UpdateServerBase):
    use_ssl: bool = Field(default=UNSPECIFIED)
    filesize_limit_number: int = Field(gt=0, default=UNSPECIFIED)
    filesize_limit_unit: FilesizeUnit = Field(default=UNSPECIFIED)

    @validator('filesize_limit_unit', pre=False)
    def validate_list(cls, v): 
        if isinstance(v, str):
            return {
                'b':         'Bytes',
                'bytes':     'Bytes',
                'kb':        'Kilobytes',
                'kilobytes': 'Kilobytes',
                'mb':        'Megabytes',
                'megabytes': 'Megabytes',
                'gb':        'Gigabytes',
                'gigabytes': 'Gigabytes',
                'tb':        'Terabytes',
                'terabytes': 'Terabytes',
            }[v.lower()]

    @root_validator(pre=True)
    def validate_filesize(cls, values):
        if (values.get('filesize_limit_number', UNSPECIFIED) != UNSPECIFIED
            and not values.get('filesize_limit_unit',UNSPECIFIED) !=UNSPECIFIED):
            raise ValidationError(f'Filesize limit number requires unit')
        
        return values

class UpdateEmby(UpdateMediaServerBase):
    api_key: Hexstring = Field(default=UNSPECIFIED)
    username: Optional[str] = Field(default=UNSPECIFIED)

class UpdateJellyfin(UpdateMediaServerBase):
    api_key: Hexstring = Field(default=UNSPECIFIED)
    username: Optional[str] = Field(default=UNSPECIFIED, min_length=1)

class UpdatePlex(UpdateMediaServerBase):
    token: str = Field(default=UNSPECIFIED)
    integrate_with_pmm: bool = Field(default=UNSPECIFIED)

class UpdateSonarr(UpdateServerBase):
    api_key: Hexstring = Field(default=UNSPECIFIED)
    use_ssl: bool = Field(default=UNSPECIFIED)
    library_names: list[str] = Field(default=UNSPECIFIED)
    library_paths: list[str] = Field(default=UNSPECIFIED)

    @validator('library_names', 'library_paths', pre=True)
    def validate_list(cls, v):
        # Filter out empty strings - all arguments can accept empty lists
        return [val for val in ([v] if isinstance(v, str) else v) if val != '']
    
    @root_validator
    def validate_paired_lists(cls, values):
        return validate_argument_lists_to_dict(
            values, 'library names and paths',
            'library_names', 'library_paths',
            output_key='libraries'
        )

class UpdateTMDb(UpdateBase):
    api_key: Hexstring = Field(default=UNSPECIFIED)
    minimum_width: NonNegativeInt = Field(default=UNSPECIFIED)
    minimum_height: NonNegativeInt = Field(default=UNSPECIFIED)
    skip_localized: bool = Field(default=UNSPECIFIED)
    download_logos: bool = Field(default=UNSPECIFIED)
    logo_language_priority: list[LanguageCode] = Field(default=UNSPECIFIED)

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
    card_width: int
    card_height: int
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
    # supported_language_codes = []

    default_card_type: CardTypeIdentifier
    excluded_card_types: list[CardTypeIdentifier]
    default_watched_style: Style
    default_unwatched_style: Style

class EmbyConnection(Base):
    use_emby: bool
    emby_url: AnyUrl
    emby_api_key: SecretStr #Hexstring
    emby_username: Optional[str]
    emby_filesize_limit: Optional[int]

class JellyfinConnection(Base):
    use_jellyfin: bool
    jellyfin_url: AnyUrl
    jellyfin_api_key: SecretStr #Hexstring
    jellyfin_username: Optional[str]
    jellyfin_filesize_limit: Optional[int]

class PlexConnection(Base):
    use_plex: bool
    plex_url: AnyUrl
    plex_token: SecretStr
    plex_integrate_with_pmm: bool
    plex_filesize_limit: Optional[int]

class SonarrLibrary(Base):
    name: str
    path: str

class SonarrConnection(Base):
    use_sonarr: bool
    sonarr_url: AnyUrl
    sonarr_api_key: SecretStr #Hexstring
    sonarr_libraries: dict[str, str]

class TMDbConnection(Base):
    use_tmdb: bool
    tmdb_api_key: SecretStr #Hexstring
    tmdb_minimum_width: NonNegativeInt
    tmdb_minimum_height: NonNegativeInt
    tmdb_skip_localized: bool
    tmdb_download_logos: bool
    tmdb_logo_language_priority: list[LanguageCode]