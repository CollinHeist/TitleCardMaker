from pathlib import Path
from re import IGNORECASE, compile as re_compile
from typing import Literal, Optional, Union

from pydantic import constr, Field, root_validator, validator

from app.schemas.base import Base, UNSPECIFIED, validate_argument_lists_to_dict

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

Dimensions = constr(regex=r'^(\d+)x(\d+)$')

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

EpisodeDataSource = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr', 'TMDb']
ImageSource = Literal['Emby', 'Jellyfin', 'Plex', 'TMDb']
MediaServer = Literal['Emby', 'Jellyfin', 'Plex']
    
"""
Base classes
"""
...

"""
Update classes
"""
class UpdatePreferences(Base):
    card_directory: str = Field(default=UNSPECIFIED, min_length=1)
    source_directory: str = Field(default=UNSPECIFIED, min_length=1)
    card_dimensions: Dimensions = Field(default=UNSPECIFIED)
    card_filename_format: str = Field(default=UNSPECIFIED)
    card_extension: CardExtension = Field(default=UNSPECIFIED)
    image_source_priority: list[ImageSource] = Field(default=UNSPECIFIED)
    episode_data_source: EpisodeDataSource = Field(default=UNSPECIFIED)
    specials_folder_format: str = Field(default=UNSPECIFIED)
    season_folder_format: str = Field(default=UNSPECIFIED)
    sync_specials: bool = Field(default=UNSPECIFIED)
    default_card_type: str = Field(default=UNSPECIFIED, min_length=1)
    default_watched_style: Style = Field(default=UNSPECIFIED)
    default_unwatched_style: Style = Field(default=UNSPECIFIED)

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('image_source_priority', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @root_validator
    def delete_unspecified_args(cls, values):
        delete_keys = [key for key, value in values.items() if value == UNSPECIFIED]
        for key in delete_keys:
            del values[key]

        return values

class UpdateBase(Base):
    url: str = Field(default=UNSPECIFIED)

class UpdateMediaServerBase(UpdateBase):
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

class UpdateEmby(UpdateMediaServerBase):
    api_key: str = Field(default=UNSPECIFIED)
    username: str = Field(default=UNSPECIFIED, min_length=1)

class UpdateJellyfin(UpdateMediaServerBase):
    api_key: str = Field(default=UNSPECIFIED)
    username: str = Field(default=UNSPECIFIED, min_length=1)

class UpdatePlex(UpdateMediaServerBase):
    token: str = Field(default=UNSPECIFIED)
    integrate_with_pmm: bool = Field(default=UNSPECIFIED)

class UpdateSonarr(UpdateBase):
    api_key: str = Field(default=UNSPECIFIED)
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

class UpdateTMDb(Base):
    api_key: str = Field(default=UNSPECIFIED)
    minimum_width: int = Field(default=UNSPECIFIED, ge=0)
    minimum_height: int = Field(default=UNSPECIFIED, ge=0)
    skip_localized: bool = Field(default=UNSPECIFIED)

"""
Return classes
"""
class Preferences(Base):
    card_directory: Path
    source_directory: Path
    card_dimensions: Dimensions
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

    default_card_type: str
    default_watched_style: Style
    default_unwatched_style: Style

class EmbyConnection(Base):
    use_emby: bool
    emby_url: str
    emby_api_key: str
    emby_username: str = Field(min_length=1)
    emby_filesize_limit: Optional[int]

class JellyfinConnection(Base):
    use_jellyfin: bool
    jellyfin_url: str
    jellyfin_api_key: str
    jellyfin_username: str = Field(min_length=1)
    jellyfin_filesize_limit: Optional[int]

class PlexConnection(Base):
    use_plex: bool
    plex_url: str
    plex_token: str
    plex_integrate_with_pmm: bool
    plex_filesize_limit: Optional[int]

class SonarrConnection(Base):
    use_sonarr: bool
    sonarr_url: str
    sonarr_api_key: str
    sonarr_libraries: dict

class TMDbConnection(Base):
    use_tmdb: bool
    tmdb_api_key: str
    tmdb_minimum_width: int
    tmdb_minimum_height: int
    tmdb_skip_localized: bool