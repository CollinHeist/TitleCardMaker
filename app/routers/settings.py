from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, Body, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_preferences
from app.schemas.preferences import EpisodeDataSourceToggle, Preferences, UpdatePreferences
from modules.Debug import log

# Create sub router for all /connection API requests
settings_router = APIRouter(
    prefix='/settings',
    tags=['Settings'],
)


@settings_router.patch('/update', status_code=200)
def update_global_settings(
        update_preferences: UpdatePreferences = Body(...),
        preferences = Depends(get_preferences)) -> Preferences:
    """
    Update all global settings.

    - update_preferences: UpdatePreferences containing fields to update.
    """
    preferences.update_values(**update_preferences.dict())

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