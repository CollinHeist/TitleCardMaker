from pathlib import Path
from typing import Literal, Union

from app.schemas.base import Base

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