from fastapi import APIRouter, Body, Depends, Request
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_preferences
from app.internal.auth import get_current_user
from app.models.connection import Connection
from app.models.preferences import Preferences as PreferencesModel
from app.schemas.preferences import (
    EpisodeDataSourceToggle, ImageSourceToggle, Preferences, ToggleOption,
    UpdatePreferences
)


# Create sub router for all /settings API requests
settings_router = APIRouter(
    prefix='/settings',
    tags=['Settings'],
    dependencies=[Depends(get_current_user)],
)


@settings_router.get('/settings')
def get_global_settings(
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> Preferences:

    return preferences


@settings_router.get('/version', status_code=200)
def get_current_version(
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> str:
    """Get the current version of TitleCardMaker."""

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
    ) -> list[EpisodeDataSourceToggle]:
    """
    Get the list of Episode data sources.
    """

    return [{
        'interface': connection.interface_type,
        'interface_id': connection.id,
        'name': connection.name,
        'selected': preferences.episode_data_source == connection.id,
    } for connection in db.query(Connection).all()]


@settings_router.get('/image-source-priority')
def get_image_source_priority(
        request: Request,
        db: Session = Depends(get_database),
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> list[ImageSourceToggle]:
    """
    Get the global image source priority.
    """

    # Add all selected Connections
    sources, source_ids = [], []
    for interface_id in preferences.image_source_priority:
        isp_connection = db.query(Connection).filter_by(id=interface_id).first()
        if isp_connection is None:
            request.state.log.warning(f'No Connection with ID {interface_id}')
            continue

        source_ids.append(interface_id)
        sources.append({
            'interface': isp_connection.interface_type,
            'interface_id': interface_id,
            'name': isp_connection.name,
            'selected': True,
        })

    # Add remaining non-Sonarr Connections
    connections = db.query(Connection)\
        .filter(Connection.interface_type != 'Sonarr')\
        .all()
    for connection in connections:
        if connection.id not in source_ids:
            sources.append({
                'interface': connection.interface_type,
                'interface_id': connection.id,
                'name': connection.name,
                'selected': False,
            })
    return sources
