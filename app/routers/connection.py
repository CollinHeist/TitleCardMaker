from typing import Literal, Optional, Union
from urllib.parse import unquote

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Query, Request
from requests import get
from sqlalchemy.orm import Session

from app.dependencies import (
    get_database, get_preferences, get_emby_interface, get_jellyfin_interface,
    get_plex_interface, get_sonarr_interface, get_tmdb_interface,
    refresh_emby_interface, refresh_jellyfin_interface, refresh_plex_interface,
    refresh_sonarr_interface, refresh_tmdb_interface,
)
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import (
    EmbyConnection, JellyfinConnection, PlexConnection, Preferences,
    SonarrConnection, TautulliConnection, TMDbConnection, UpdateEmby,
    UpdateJellyfin, UpdatePlex, UpdateSonarr, UpdateTMDb
)
from modules.Debug import log
from modules.TautulliInterface2 import TautulliInterface

# Create sub router for all /connection API requests
connection_router = APIRouter(
    prefix='/connection',
    tags=['Connections'],
)

SupportedConnection = Literal['emby', 'jellyfin', 'plex', 'sonarr', 'tmdb']

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
        if preferences.use_emby: refresh_emby_interface()
    elif connection == 'jellyfin':
        preferences.use_jellyfin = (status == 'enable')
        if preferences.use_emby: refresh_jellyfin_interface()
    elif connection == 'plex':
        preferences.use_plex = (status == 'enable')
        if preferences.use_emby: refresh_plex_interface()
    elif connection == 'sonarr':
        preferences.use_sonarr = (status == 'enable')
        if preferences.use_emby: refresh_sonarr_interface()
    elif connection == 'tmdb':
        preferences.use_tmdb = (status == 'enable')
        if preferences.use_emby: refresh_tmdb_interface()


@connection_router.get('/emby', status_code=200)
def get_emby_connection_details(
        preferences = Depends(get_preferences)) -> EmbyConnection:

    return preferences


@connection_router.get('/jellyfin', status_code=200)
def get_jellyfin_connection_details(
        preferences = Depends(get_preferences)) -> JellyfinConnection:

    return preferences


@connection_router.get('/plex', status_code=200)
def get_plex_connection_details(
        preferences = Depends(get_preferences)) -> PlexConnection:

    return preferences


@connection_router.get('/sonarr', status_code=200)
def get_sonarr_connection_details(
        preferences = Depends(get_preferences)) -> SonarrConnection:

    return preferences


@connection_router.get('/tmdb', status_code=200)
def get_tmdb_connection_details(
        preferences = Depends(get_preferences)) -> TMDbConnection:

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
        refresh_emby_interface()

    return preferences


@connection_router.patch('/jellyfin', status_code=200)
def update_jellyfin_connection(
        update_jellyfin: UpdateJellyfin = Body(...),
        preferences = Depends(get_preferences),
        jellyfin_interface = Depends(get_jellyfin_interface)) -> JellyfinConnection:
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
        refresh_jellyfin_interface()

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
        refresh_plex_interface()

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

    # Update attributes
    changed = False
    for attribute, value in update_sonarr.dict().items():
        if (value != UNSPECIFIED
            and value != getattr(preferences, f'sonarr_{attribute}')):
            setattr(preferences, f'sonarr_{attribute}', value)
            changed = True

    # Remake SonarrInterface if changed
    if preferences.use_sonarr and changed:
        refresh_sonarr_interface()

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
        refresh_tmdb_interface()

    return preferences


@connection_router.post('/tautulli/check', status_code=200)
def check_tautulli_integration(
        request: Request,
        tautulli_connection: TautulliConnection = Body(...)) -> bool:
    """
    Check whether Tautulli is integrated with TCM.

    - tautulli_connection: Details of the connection to Tautull, and the
    Notification Agent to search for integration of.
    """

    tcm_url = str(request.url).split('/tautulli/check')[0]

    interface = TautulliInterface(
        tcm_url=tcm_url,
        tautulli_url=tautulli_connection.tautulli_url,
        api_key=tautulli_connection.tautulli_api_key,
        verify_ssl=tautulli_connection.tautulli_verify_ssl,
        agent_name=tautulli_connection.tautulli_agent_name,
    )

    return interface.is_integrated()


@connection_router.post('/tautulli/integrate', status_code=201)
def add_tautulli_integration(
        request: Request,
        tautulli_connection: TautulliConnection = Body(...)) -> None:
    """
    Integrate Tautulli with TitleCardMaker by creating a Notification
    Agent that triggers the /cards/key API route to quickly create
    title cards.

    - tautulli_connection: Details of the connection to Tautulli and the
    Notification Agent to search for or create.
    """

    tcm_url = str(request.url).split('/api/connection/tautulli/integrate')[0]

    interface = TautulliInterface(
        tcm_url=tcm_url,
        tautulli_url=tautulli_connection.tautulli_url,
        api_key=tautulli_connection.tautulli_api_key,
        verify_ssl=tautulli_connection.tautulli_verify_ssl,
        agent_name=tautulli_connection.tautulli_agent_name,
    )

    interface.integrate()