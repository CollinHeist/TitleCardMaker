from pathlib import Path

from fastapi import APIRouter, Body, Depends

from app.dependencies import get_preferences, refresh_imagemagick_interface
from app.schemas.preferences import EpisodeDataSourceToggle, LanguageToggle, Preferences, UpdatePreferences

from modules.Debug import log
from modules.TMDbInterface2 import TMDbInterface


# Create sub router for all /settings API requests
settings_router = APIRouter(
    prefix='/settings',
    tags=['Settings'],
)


@settings_router.get('/version', status_code=200)
def get_current_version(preferences = Depends(get_preferences)) -> str:
    """
    Get the current version of TitleCardMaker.
    """

    return preferences.version


@settings_router.patch('/update', status_code=200)
def update_global_settings(
        update_preferences: UpdatePreferences = Body(...),
        preferences = Depends(get_preferences)) -> Preferences:
    """
    Update all global settings.

    - update_preferences: UpdatePreferences containing fields to update.
    """

    preferences.update_values(**update_preferences.dict())
    refresh_imagemagick_interface()
    preferences.determine_imagemagick_prefix()

    return preferences


@settings_router.get('/sonarr-libraries', tags=['Sonarr'])
def get_sonarr_libraries(
        preferences=Depends(get_preferences)) -> list[dict[str, str]]:

    return [
        {'name': library, 'path': path}
        for library, path in preferences.sonarr_libraries.items()
    ]


@settings_router.get('/image-source-priority')
def get_image_source_priority(
        preferences=Depends(get_preferences)) -> list[EpisodeDataSourceToggle]:
    
    sources = []
    for source in preferences.image_source_priority:
        sources.append({'name': source, 'value': source, 'selected': True})
    for source in preferences.valid_image_sources:
        if source not in preferences.image_source_priority:
            sources.append({'name': source, 'value': source, 'selected': False})

    return sources


@settings_router.get('/logo-language-priority')
def get_tmdb_logo_language_priority(
        preferences=Depends(get_preferences)) -> list[LanguageToggle]:

    languages = []
    for code in preferences.tmdb_logo_language_priority:
        languages.append({
            'name': TMDbInterface.LANGUAGES[code],
            'value': code,
            'selected': True
        })
    for code, language in sorted(TMDbInterface.LANGUAGES.items(),
                                 key=lambda kv: kv[1]):
        if code not in preferences.tmdb_logo_language_priority:
            languages.append({
                'name': language,
                'value': code,
                'selected': False,
            })

    return languages