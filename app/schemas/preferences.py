from pathlib import Path
from typing import Literal, Optional, Union

from pydantic import Field, validator

from app.schemas.base import Base, UNSPECIFIED

CardExtension = Literal['.jpg', '.jpeg', '.png', '.tiff', '.gif', '.webp']
FilesizeUnit = Literal[
    'Bytes', 'Kilobytes', 'Megabytes', 'Gigabytes', 'Terabytes',
    'B', 'KB', 'MB', 'GB', 'TB',
]

Style = Literal[
    'art', 'art blur', 'art grayscale', 'art blur grayscale', 'unique',
    'blur unique', 'grayscale unique', 'blur grayscale unique',
]

class NamedOption(Base):
    name: str
    value: str

class StyleOption(NamedOption):
    style_type: Literal['art', 'unique']

class ToggleOption(NamedOption):
    selected: bool

class MediaServerToggle(ToggleOption):
    ...

class EpisodeDataSourceToggle(ToggleOption):
    ...

class ImageSourceToggle(ToggleOption):
    ...


EpisodeDataSource = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr', 'TMDb']
ImageSource = Literal['Emby', 'Jellyfin', 'Plex', 'TMDb']
MediaServer = Literal['Emby', 'Jellyfin', 'Plex']

class Preferences(Base):
    card_directory: Path
    source_directory: Path
    card_filename_format: str
    card_extension: str
    image_source_priority: list[ImageSource]
    valid_image_sources: list[ImageSource]
    episode_data_source: EpisodeDataSource
    valid_episode_data_sources: list[EpisodeDataSource]
    valid_image_extensions: list[str]
    validate_fonts: bool
    specials_folder_format: str
    season_folder_format: str
    sync_specials: bool
    # supported_language_codes = []

    default_card_type: str
    default_watched_style: Style
    default_unwatched_style: Style

    use_emby: bool
    emby_url: str
    emby_api_key: str
    emby_use_ssl: bool
    emby_username: str
    emby_filesize_limit: Union[int, None]

    use_plex: bool
    plex_url: str
    plex_token: str
    plex_use_ssl: bool
    plex_integrate_with_pmm: bool
    plex_filesize_limit: Union[int, None]

    use_sonarr: bool
    sonarr_url: str
    sonarr_api_key: str
    sonarr_use_ssl: bool

    use_tmdb: bool
    tmdb_api_key: str

class PreferencesBase(Base):
    ...

class EmbyConnection(Base):
    use_emby: bool
    emby_url: str
    emby_api_key: str
    emby_username: str
    emby_filesize_limit: Union[int, None]

class JellyfinConnection(Base):
    use_jellyfin: bool
    jellyfin_url: str
    jellyfin_api_key: str
    jellyfin_username: str
    jellyfin_filesize_limit: Union[int, None]

class PlexConnection(Base):
    use_plex: bool
    plex_url: str
    plex_token: str
    plex_integrate_with_pmm: bool
    plex_filesize_limit: Union[int, None]

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

class UpdateBase(Base):
    url: Optional[str] = Field(default=UNSPECIFIED)

class UpdateMediaServerBase(UpdateBase):
    use_ssl: Optional[bool] = Field(default=False)
    filesize_limit_number: Optional[int] = Field(gt=0, default=UNSPECIFIED)
    filesize_limit_unit: Optional[FilesizeUnit] = Field(default=UNSPECIFIED)

class UpdateEmby(UpdateMediaServerBase):
    api_key: Optional[str] = Field(default=UNSPECIFIED)
    username: Optional[str] = Field(default=UNSPECIFIED)

class UpdateJellyfin(UpdateMediaServerBase):
    api_key: Optional[str] = Field(default=UNSPECIFIED)
    username: Optional[str] = Field(default=UNSPECIFIED)

class UpdatePlex(UpdateMediaServerBase):
    token: Optional[str] = Field(default=UNSPECIFIED)
    integrate_with_pmm: Optional[bool] = Field(default=UNSPECIFIED)

class UpdateSonarr(UpdateBase):
    api_key: Optional[str] = Field(default=UNSPECIFIED)
    use_ssl: Optional[bool] = Field(default=False)
    library_names: Optional[list[str]] = Field(default=UNSPECIFIED)
    library_paths: Optional[list[str]] = Field(default=UNSPECIFIED)

    @validator('library_names', 'library_paths', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

class UpdateTMDb(Base):
    api_key: Optional[str] = Field(default=UNSPECIFIED)
    minimum_width: Optional[int] = Field(default=UNSPECIFIED)
    minimum_height: Optional[int] = Field(default=UNSPECIFIED)
    skip_localized: Optional[bool] = Field(default=UNSPECIFIED)