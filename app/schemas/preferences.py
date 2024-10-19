# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from pydantic import (
    DirectoryPath,
    FilePath,
    PositiveInt,
    conint,
    constr,
    validator,
)

from app.schemas.base import (
    Base,
    ImageSource,
    InterfaceType,
    UpdateBase,
    UNSPECIFIED,
)

from modules.FormatString import FormatString
from modules.TMDbInterface2 import TMDbInterface


"""
Match local identifiers (A-Z and any character), remote card types (a-z/.*, no
space), and local card types (any character(s).py).
"""
CardTypeIdentifier = constr(regex=r'^([a-zA-Z].*|[a-zA-Z].*\/[a-zA-Z].*|.+\.py)$')

"""
Page dimension string for specifying {rows}x{columns}.
"""
PageSizeDimensions = constr(
    strip_whitespace=True,
    to_lower=True,
    regex=r'^\d+x\d+$',
)

CardExtension = Literal[
    '.jpg', '.jpeg', '.jxl', '.png', '.tiff', '.gif', '.webp'
]

Style = Literal[
    'art', 'art blur', 'art grayscale', 'art blur grayscale', 'unique',
    'blur unique', 'grayscale unique', 'blur grayscale unique',
]

LanguageCode = Literal[TMDbInterface.LANGUAGE_CODES]

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

class EpisodeDataSourceToggle(Base):
    interface: InterfaceType
    interface_id: int
    name: str
    selected: bool

class ImageSourceToggle(EpisodeDataSourceToggle):
    ...

EpisodeDataSource = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr', 'TMDb']
MediaServer = Literal['Emby', 'Jellyfin', 'Plex']

"""
Base classes
"""
class ImageSourceOption(Base):
    interface: ImageSource
    interface_id: int = 0

"""
Update classes
"""
class UpdatePreferences(UpdateBase):
    card_directory: DirectoryPath = UNSPECIFIED
    source_directory: DirectoryPath = UNSPECIFIED
    completely_delete_series: bool = UNSPECIFIED
    card_width: PositiveInt = UNSPECIFIED
    card_height: PositiveInt = UNSPECIFIED
    card_filename_format: str = UNSPECIFIED
    card_extension: CardExtension = UNSPECIFIED
    imagemagick_executable: Optional[FilePath] = UNSPECIFIED
    card_quality: conint(ge=1, le=100) = UNSPECIFIED
    library_unique_cards: bool = UNSPECIFIED
    image_source_priority: list[int] = UNSPECIFIED
    episode_data_source: int = UNSPECIFIED
    specials_folder_format: str = UNSPECIFIED
    season_folder_format: str = UNSPECIFIED
    sync_specials: bool = UNSPECIFIED
    delete_missing_episodes: bool = UNSPECIFIED
    delete_unsynced_series: bool = UNSPECIFIED
    simplified_data_table: bool = UNSPECIFIED
    default_card_type: CardTypeIdentifier = UNSPECIFIED
    excluded_card_types: list[CardTypeIdentifier] = UNSPECIFIED
    default_watched_style: Style = UNSPECIFIED
    default_unwatched_style: Style = UNSPECIFIED
    default_templates: list[int] = UNSPECIFIED
    default_fonts: dict[str, int] = UNSPECIFIED
    global_extras: dict[str, dict[str, str]] = UNSPECIFIED
    home_page_size: PositiveInt = UNSPECIFIED
    episode_data_page_size: PositiveInt = UNSPECIFIED
    source_preview_page_dimensions: PageSizeDimensions = UNSPECIFIED
    title_card_preview_page_dimensions: PageSizeDimensions = UNSPECIFIED
    stylize_unmonitored_posters: bool = UNSPECIFIED
    home_page_table_view: bool = UNSPECIFIED
    colorblind_mode: bool = UNSPECIFIED
    reduced_animations: bool = UNSPECIFIED
    interactive_card_previews: bool = UNSPECIFIED
    display_live_messages: bool = UNSPECIFIED

    @validator('card_filename_format', pre=True)
    def validate_card_filename_format(cls, v: str) -> str:
        try:
            FormatString(
                v,
                data=dict(
                    series_name='test', series_full_name='test (2000)',
                    year=2000, title='Test Title', season_number=1,
                    episode_number=1, absolute_number=1,
                    absolute_episode_number=1, emby_id='0:TV:abc123',
                    imdb_id='tt1234', jellyfin_id='0:TV:abc123', tmdb_id=123,
                    tvdb_id=123, tvrage_id=123,
                )
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
    def validate_folder_formats(cls, v: str) -> str:
        try:
            FormatString(
                v,
                data={
                    'season_number': 1, 'episode_number': 1, 'absolute_number':1
                }
            )
        except KeyError as exc:
            raise ValueError(
                'Invalid folder format - use "season_number", "episode_numer" '
                'and/or "absolute_number"'
            ) from exc

        return v

    @validator('source_preview_page_dimensions', 'title_card_preview_page_dimensions')
    def validate_page_dimensions(cls, v: str) -> str:
        rows, columns = v.split('x')
        if int(rows) * int(columns) > 100:
            raise ValueError('A maximum of 100 items can be displayed per-page')
        return v

"""
Return classes
"""
class Preferences(Base):
    card_directory: Path
    source_directory: Path
    completely_delete_series: bool
    card_width: PositiveInt
    card_height: PositiveInt
    card_filename_format: str
    card_extension: str
    card_quality: int
    imagemagick_executable: Optional[Path]
    library_unique_cards: bool
    image_source_priority: list[int]
    episode_data_source: Optional[int]
    specials_folder_format: str
    season_folder_format: str
    sync_specials: bool
    delete_missing_episodes: bool
    delete_unsynced_series: bool
    simplified_data_table: bool
    is_docker: bool
    default_card_type: CardTypeIdentifier
    excluded_card_types: list[CardTypeIdentifier]
    default_watched_style: Style
    default_unwatched_style: Style
    default_templates: list[int]
    default_fonts: dict[str, int]
    global_extras: dict[str, dict[str, str]]
    home_page_size: PositiveInt
    episode_data_page_size: PositiveInt
    source_preview_page_dimensions: PageSizeDimensions
    title_card_preview_page_dimensions: PageSizeDimensions
    stylize_unmonitored_posters: bool
    home_page_table_view: bool
    colorblind_mode: bool
    reduced_animations: bool
    interactive_card_previews: bool
    display_live_messages: bool

class DatabaseBackup(Base):
    filename: str
    filesize: int
    schema_version: str

class SettingsBackup(Base):
    filename: str
    filesize: int

class SystemBackup(Base):
    database: DatabaseBackup
    settings: SettingsBackup
    timestamp: datetime
    version: str
    folder_name: str
