from typing import Literal, Optional
from urllib.parse import unquote

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_preferences, get_emby_interface, get_jellyfin_interface, get_plex_interface, get_sonarr_interface, get_tmdb_interface
from app.routers.fonts import join_lists
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import EmbyConnection, FilesizeUnit, PlexConnection, Preferences, SonarrConnection, Style, TMDbConnection, UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr, UpdateTMDb
from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.JellyfinInterface import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface

SupportedConnection = Literal['emby', 'jellyfin', 'plex', 'sonarr', 'tmdb']

# Create sub router for all /connection API requests
connection_router = APIRouter(
    prefix='/connection',
)

@connection_router.get('/{connection}')
def get_connection_details(
        connection: SupportedConnection,
        db = Depends(get_database),
        preferences = Depends(get_preferences)) -> Preferences:

    return Preferences


@connection_router.put('/{connection}/{status}', status_code=204)
def enable_or_disable_connection(
        connection: SupportedConnection,
        status: Literal['enable', 'disable'],
        preferences=Depends(get_preferences)) -> None:
    """
    Set the enabled/disabled status of the given connection.

    - connection: Interface name whose connection is being toggled.
    - status: Whether to enable or disable the given connection.
    """

    if connection == 'emby':
        preferences.use_emby = (status == 'enable')
    elif connection == 'jellyfin':
        preferences.use_jellyfin = (status == 'enable')
    elif connection == 'plex':
        preferences.use_plex = (status == 'enable')
    elif connection == 'sonarr':
        preferences.use_sonarr = (status == 'enable')
    elif connection == 'tmdb':
        preferences.use_tmdb = (status == 'enable')


@connection_router.get('/emby', status_code=200, response_model=EmbyConnection)
def get_emby_connection_details(
        preferences = Depends(get_preferences)) -> EmbyConnection:

    return preferences


@connection_router.patch('/emby', status_code=200)
def update_emby_connection(
        update_emby: UpdateEmby = Body(...),
        preferences = Depends(get_preferences),
        emby_interface = Depends(get_emby_interface)) -> EmbyConnection:
    """
    Update the connection details for Emby.

    - update_emby: Emby connection details to modify.
    """

    # Validate arguments
    if ((update_emby.filesize_limit_number not in (None, UNSPECIFIED))
        and (update_emby.filesize_limit_unit in (None, UNSPECIFIED))):
        raise HTTPException(
            status_code=400,
            detail='Provide both filesize limit number and unit'
        )

    # Update attributes
    changed = False
    for attribute, value in update_emby.dict().items():
        if (value != UNSPECIFIED
            and value != getattr(preferences, f'emby_{attribute}')):
            setattr(preferences, f'emby_{attribute}', value)
            changed = True

    # Remake EmbyInterface if changed
    if preferences.use_emby and changed:
        emby_interface = EmbyInterface(**preferences.emby_arguments)

    return preferences


@connection_router.patch('/jellyfin', status_code=200)
def update_jellyfin_connection(
        update_jellyfin: UpdateJellyfin = Body(...),
        preferences = Depends(get_preferences),
        jellyfin_interface = Depends(get_jellyfin_interface)) -> EmbyConnection:
    """
    Update the connection details for Jellyfin.

    - update_jellyfin: Jellyfin connection details to modify.
    """
    log.critical(f'{update_jellyfin.dict()=}')
    # Validate arguments
    if ((update_jellyfin.filesize_limit_number not in (None, UNSPECIFIED))
        and (update_jellyfin.filesize_limit_unit in (None, UNSPECIFIED))):
        raise HTTPException(
            status_code=400,
            detail='Provide both filesize limit number and unit'
        )

    # Update attributes
    changed = False
    for attribute, value in update_jellyfin.dict().items():
        if (value != UNSPECIFIED
            and value != getattr(preferences, f'jellyfin_{attribute}')):
            setattr(preferences, f'jellyfin_{attribute}', value)
            changed = True

    # Remake JellyfinInterface if changed
    if preferences.use_jellyfin and changed:
        jellyfin_interface = JellyfinInterface(**preferences.jellyfin_arguments)

    return preferences


@connection_router.patch('/plex', status_code=200)
def update_plex_connection(
        update_plex: UpdatePlex = Body(...),
        preferences=Depends(get_preferences),
        plex_interface = Depends(get_plex_interface)) -> PlexConnection:
    """
    Update the connection details for Plex.

    - update_plex: Plex connection details to modify.
    """

    # Validate arguments
    if ((update_plex.filesize_limit_number not in (None, UNSPECIFIED))
        and (update_plex.filesize_limit_unit in (None, UNSPECIFIED))):
        raise HTTPException(
            status_code=400,
            detail='Provide both filesize limit number and unit'
        )

    # Update attributes
    changed = False
    for attribute, value in update_plex.dict().items():
        if (value != UNSPECIFIED
            and value != getattr(preferences, f'plex_{attribute}')):
            setattr(preferences, f'plex_{attribute}', value)
            changed = True

    # Remake PlexInterface if changed
    if preferences.use_plex and changed:
        plex_interface = PlexInterface(**preferences.plex_arguments)

    return preferences


@connection_router.patch('/sonarr', status_code=200)
def update_sonarr_connection(
        update_sonarr: UpdateSonarr = Body(...), 
        preferences = Depends(get_preferences),
        sonarr_interface = Depends(get_sonarr_interface)) -> SonarrConnection:
    """
    Update the connection details for Sonarr.

    - update_sonarr: Sonarr connection details to modify.
    """

    # Validate and join library names/paths
    sonarr_libraries = join_lists(
        update_sonarr.library_names, update_sonarr.library_paths,
        'library names and paths', default=UNSPECIFIED,
    )

    # Update attributes
    changed = False
    for attribute, value in update_sonarr.dict().items():
        # Exclude library names/paths
        if attribute in ('library_names', 'library_paths'): continue
        if (value != UNSPECIFIED
            and value != getattr(preferences, f'sonarr_{attribute}')):
            setattr(preferences, f'sonarr_{attribute}', value)
            changed = True

    # Update libraries if indicated
    if (sonarr_libraries != UNSPECIFIED
        and preferences.sonarr_libraries != sonarr_libraries):
        preferences.sonarr_libraries = sonarr_libraries

    # Remake SonarrInterface if changed
    if preferences.use_sonarr and changed:
        sonarr_interface = SonarrInterface(**preferences.sonarr_arguments)

    return preferences


@connection_router.patch('/tmdb', status_code=200)
def update_tmdb_connection(
        update_tmdb: UpdateTMDb = Body(...),
        preferences = Depends(get_preferences),
        tmdb_interface = Depends(get_tmdb_interface)) -> TMDbConnection:
    """
    Update the connection details for TMDb.

    - update_tmdb: TMDb connection details to modify.
    """

    # Update attributes
    changed = False
    for attribute, value in update_tmdb.dict().items():
        if (value != UNSPECIFIED
            and value != getattr(preferences, f'tmdb_{attribute}')):
            setattr(preferences, f'tmdb_{attribute}', value)
            changed = True

    # Remake TMDbInterface if changed
    if preferences.use_tmdb and changed:
        tmdb_interface = TMDbInterface(**preferences.tmdb_arguments)

    return preferences