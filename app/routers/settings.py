from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, Body, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_preferences
from app.schemas.preferences import CardExtension, EpisodeDataSource, \
    EpisodeDataSourceToggle, ImageSource, ImageSourceToggle, Preferences, \
    Style, ToggleOption

# Create sub router for all /connection API requests
settings_router = APIRouter(
    prefix='/settings',
    tags=['Settings'],
)

def compare_update(update: dict[str, Any], value: Any, reference: Any, key: str) -> None:
    if value is not None and value != reference:
        update[key] = value
    

@settings_router.post('/update')
def update_global_settings(
        card_directory: Optional[str] = Form(default=None),
        source_directory: Optional[str] = Form(default=None),
        episode_data_source: Optional[EpisodeDataSource] = Form(default=None),
        image_source_priority: Optional[str] = Form(default=None),
        sync_specials: Optional[bool] = Form(default=None),
        default_card_type: Optional[str] = Form(default=None),
        default_watched_style: Optional[Style] = Form(default=None),
        default_unwatched_style: Optional[Style] = Form(default=None),
        validate_fonts: Optional[bool] = Form(default=None),
        card_extension: Optional[CardExtension] = Form(default=None),
        filename_format: Optional[str] = Form(default=None),
        specials_folder_format: Optional[str] = Form(default=None),
        season_folder_format: Optional[str] = Form(default=None),
        preferences = Depends(get_preferences)) -> Preferences:

    to_update = {}
    compare_update(to_update, card_directory, preferences.card_directory,
                   'card_directory')
    compare_update(to_update, source_directory, preferences.source_directory,
                   'source_directory')
    compare_update(to_update, episode_data_source,
                   preferences.episode_data_source, 'episode_data_source')
    if image_source_priority is not None:
        isp = image_source_priority.split(',')
        if isp != preferences.image_source_priority:
            to_update['image_source_priority'] = isp
    compare_update(to_update, sync_specials, preferences.sync_specials,
                   'sync_specials')
    compare_update(to_update, default_card_type, preferences.default_card_type,
                   'default_card_type')
    compare_update(to_update, default_watched_style,
                   preferences.default_watched_style, 'default_watched_style')
    compare_update(to_update, default_unwatched_style,
                   preferences.default_unwatched_style, 'default_unwatched_style')
    compare_update(to_update, validate_fonts, preferences.validate_fonts,
                   'validate_fonts')
    compare_update(to_update, card_extension, preferences.card_extension,
                   'card_extension')
    compare_update(to_update, filename_format, preferences.card_filename_format,
                   'card_filename_format')
    compare_update(to_update, specials_folder_format,
                   preferences.specials_folder_format, 'specials_folder_format')
    compare_update(to_update, season_folder_format,
                   preferences.season_folder_format, 'season_folder_format')

    preferences.update_values(**to_update)
    return preferences


@settings_router.get('/sonarr-libraries', tags=['Sonarr'])
def get_sonarr_libraries(
        preferences=Depends(get_preferences)) -> list[dict[str, str]]:

    return [
        {'name': library, 'path': path}
        for library, path in preferences.sonarr_libraries.items()
    ]


@settings_router.get('/image-source-priority',
                     response_model=list[ImageSourceToggle])
def get_image_source_priority(
        preferences=Depends(get_preferences)) -> list[EpisodeDataSourceToggle]:
    
    sources = []
    for source in preferences.image_source_priority:
        sources.append({'name': source, 'value': source, 'selected': True})
    for source in preferences.valid_image_sources:
        if source not in preferences.image_source_priority:
            sources.append({'name': source, 'value': source, 'selected': False})

    return sources