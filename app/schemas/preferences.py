# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from pathlib import Path
from typing import Literal

from pydantic import DirectoryPath, PositiveInt, constr, validator # pylint: disable=no-name-in-module

from app.schemas.base import Base, InterfaceName, ImageSource, UpdateBase, UNSPECIFIED


"""
Match local identifiers (A-Z and space), remote card types (a-z/a-z, no space),
and local card types (any character .py).
"""
CardTypeIdentifier = constr(regex=r'^([a-zA-Z ]+|[a-zA-Z]+\/[a-zA-Z]+|.+\.py)$')

CardExtension = Literal['.jpg', '.jpeg', '.png', '.tiff', '.gif', '.webp']

Style = Literal[
    'art', 'art blur', 'art grayscale', 'art blur grayscale', 'unique',
    'blur unique', 'grayscale unique', 'blur grayscale unique',
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

class EpisodeDataSourceToggle(Base):
    interface: InterfaceName
    interface_id: int
    selected: bool

class ImageSourceToggle(Base):
    interface: InterfaceName
    interface_id: int
    selected: bool

class LanguageToggle(ToggleOption):
    ...

"""
Base classes
"""
class EpisodeDataSource(Base):
    interface: Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr', 'TMDb']
    interface_id: int = 0

class ImageSourceOption(Base):
    interface: ImageSource
    interface_id: int = 0

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
    image_source_priority: list[ImageSourceOption] = UNSPECIFIED
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
    image_source_priority: list[ImageSourceOption]
    # valid_image_sources: list[ImageSource]
    episode_data_source: EpisodeDataSource
    # valid_episode_data_sources: list[EpisodeDataSource]
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
