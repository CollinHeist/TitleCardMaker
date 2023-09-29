from fastapi import APIRouter, Body, Depends, Request
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_preferences
from app.internal.auth import get_current_user
from app.models.connection import Connection
from app.models.preferences import Preferences as PreferencesModel
from app.schemas.preferences import (
    ImageSourceToggle, LanguageToggle, Preferences, UpdatePreferences
)

from modules.TMDbInterface2 import TMDbInterface


# Create sub router for all /settings API requests
settings_router = APIRouter(
    prefix='/settings',
    tags=['Settings'],
    dependencies=[Depends(get_current_user)],
)


@settings_router.get('/version', status_code=200)
def get_current_version(
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> str:
    """
    Get the current version of TitleCardMaker.
    """

    return preferences.version


@settings_router.patch('/update', status_code=200)
def update_global_settings(
        request: Request,
        update_preferences: UpdatePreferences = Body(...),
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> Preferences:
    """
    Update all global settings.

    - update_preferences: UpdatePreferences containing fields to update.
    """

    preferences.update_values(**update_preferences.dict(), log=request.state.log)

    return preferences


@settings_router.get('/episode-data-source')
def get_global_episode_data_source(
        db: Session = Depends(get_database),
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> list[ImageSourceToggle]:
    """
    Get the list of Episode data sources.
    """

    # Add default EDS
    sources = [preferences.episode_data_source | {'selected': True}]

    # Add remaining Connections
    for connection in db.query(Connection).all():
        if connection.id != preferences.episode_data_source['interface_id']:
            sources.append({
                'interface': connection.interface,
                'interface_id': connection.id,
                'selected': False,
            })

    return sources


@settings_router.get('/image-source-priority')
def get_image_source_priority(
        db: Session = Depends(get_database),
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> list[ImageSourceToggle]:
    """
    Get the global image source priority.
    """

    # Add all selected Connections
    sources, source_ids = [], []
    for connection in preferences.image_source_priority:
        sources.append(connection | {'selected': True})
        source_ids.append(connection['interface_id'])

    # Add remaining non-Sonarr Connections
    connections = db.query(Connection)\
        .filter(Connection.interface != 'Sonarr')\
        .all()
    for connection in connections:
        if connection.id not in source_ids:
            sources.append({
                'interface': connection.interface,
                'interface_id': connection.id,
                'selected': False,
            })

    return sources


@settings_router.get('/logo-language-priority')
def get_tmdb_logo_language_priority(
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> list[LanguageToggle]:
    """
    Get the global TMDb logo language priority setting.
    """

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
