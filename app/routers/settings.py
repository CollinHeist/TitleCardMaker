from typing import Optional
from fastapi import APIRouter, Body, Depends, Request
from sqlalchemy.orm import Session

from app.database.query import get_template
from app.dependencies import get_database, get_preferences
from app.internal.auth import get_current_user
from app.internal.backup import list_available_backups
from app.internal.settings import get_episode_data_sources
from app.models.connection import Connection
from app.models.preferences import Preferences as PreferencesModel
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import (
    EpisodeDataSourceToggle,
    ImageSourceToggle,
    Preferences,
    SystemBackup,
    UpdatePreferences,
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
    """Get the global settings"""

    return preferences


@settings_router.get('/version')
def get_current_version(
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> str:
    """Get the currently running version of TitleCardMaker."""

    return preferences.current_version


@settings_router.patch('/update')
def update_global_settings(
        request: Request,
        update_preferences: UpdatePreferences = Body(...),
        db: Session = Depends(get_database),
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> Preferences:
    """
    Update all global settings.

    - update_preferences: UpdatePreferences containing fields to update.
    """

    # Verify all specified Templates exist
    if (hasattr(update_preferences, 'default_templates')
        and update_preferences.default_templates != UNSPECIFIED):
        for template_id in update_preferences.default_templates:
            get_template(db, template_id, raise_exc=True)

    preferences.update_values(**update_preferences.dict(), log=request.state.log)
    preferences.determine_imagemagick_prefix(log=request.state.log)

    return preferences


@settings_router.get('/episode-data-source')
def get_global_episode_data_source(
        db: Session = Depends(get_database),
    ) -> list[EpisodeDataSourceToggle]:
    """Get the list of Episode data sources."""

    return get_episode_data_sources(db)


@settings_router.get('/image-source-priority')
def get_image_source_priority(
        request: Request,
        db: Session = Depends(get_database),
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> list[ImageSourceToggle]:
    """Get the global image source priority."""

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


@settings_router.get('/backups')
def get_available_system_backups() -> list[SystemBackup]:
    """Get a list detailing all the available system backups."""

    return list_available_backups()


@settings_router.get('/background-tasks')
def get_pending_background_tasks() -> list[tuple[str, Optional[str]]]:
    from modules.BackgroundTasks import task_queue

    return [
        (
            task[1].__name__,
            task[1].__doc__,
        )
        for task in task_queue
    ]
