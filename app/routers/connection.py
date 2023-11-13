from typing import Literal, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from app.dependencies import * # pylint: disable=W0401,W0614,W0621
from app.internal.auth import get_current_user
from app.internal.connection import update_connection
from app.schemas.preferences import (
    EmbyConnection, JellyfinConnection, PlexConnection, SonarrConnection,
    SonarrLibrary, TautulliConnection, TMDbConnection, UpdateEmby,
    UpdateJellyfin, UpdatePlex, UpdateSonarr, UpdateTMDb,
)
from modules.SonarrInterface2 import SonarrInterface
from modules.TautulliInterface2 import TautulliInterface


# Create sub router for all /connection API requests
connection_router = APIRouter(
    prefix='/connection',
    tags=['Connections'],
    dependencies=[Depends(get_current_user)],
)


@connection_router.put('/{connection}/{status}', status_code=204)
def enable_or_disable_connection(
        request: Request,
        connection: Literal['emby', 'jellyfin', 'plex', 'sonarr', 'tmdb'],
        status: Literal['enable', 'disable'],
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Set the enabled/disabled status of the given connection.

    - connection: Interface name whose connection is being toggled.
    - status: Whether to enable or disable the given connection.
    """

    # Get contextual logger
    log = request.state.log

    if connection == 'emby':
        preferences.use_emby = status == 'enable'
        if preferences.use_emby:
            refresh_emby_interface(log=log)
    elif connection == 'jellyfin':
        preferences.use_jellyfin = status == 'enable'
        if preferences.use_jellyfin:
            refresh_jellyfin_interface(log=log)
    elif connection == 'plex':
        preferences.use_plex = status == 'enable'
        if preferences.use_plex:
            refresh_plex_interface(log=log)
    elif connection == 'sonarr':
        preferences.use_sonarr = status == 'enable'
        if preferences.use_sonarr:
            refresh_sonarr_interface(log=log)
    elif connection == 'tmdb':
        preferences.use_tmdb = status == 'enable'
        if preferences.use_tmdb:
            refresh_tmdb_interface(log=log)

    preferences.commit()


@connection_router.get('/emby', status_code=200)
def get_emby_connection_details(
        preferences: Preferences = Depends(get_preferences),
    ) -> EmbyConnection:
    """
    Get the connection details for Emby.
    """

    return preferences


@connection_router.get('/jellyfin', status_code=200)
def get_jellyfin_connection_details(
        preferences: Preferences = Depends(get_preferences),
    ) -> JellyfinConnection:
    """
    Get the connection details for Jellyfin.
    """

    return preferences


@connection_router.get('/plex', status_code=200)
def get_plex_connection_details(
        preferences: Preferences = Depends(get_preferences),
    ) -> PlexConnection:
    """
    Get the connection details for Plex.
    """

    return preferences


@connection_router.get('/sonarr', status_code=200)
def get_sonarr_connection_details(
        preferences: Preferences = Depends(get_preferences),
    ) -> SonarrConnection:
    """
    Get the connection details for Sonarr.
    """

    return preferences


@connection_router.get('/tmdb', status_code=200)
def get_tmdb_connection_details(
        preferences: Preferences = Depends(get_preferences),
    ) -> TMDbConnection:
    """
    Get the connection details for TMDb.
    """

    return preferences


@connection_router.patch('/emby', status_code=200)
def update_emby_connection(
        request: Request,
        update_emby: UpdateEmby = Body(...),
        preferences: Preferences = Depends(get_preferences),
    ) -> EmbyConnection:
    """
    Update the connection details for Emby.

    - update_emby: Emby connection details to modify.
    """

    return update_connection(
        preferences, update_emby, 'emby', log=request.state.log,
    )


@connection_router.patch('/jellyfin', status_code=200)
def update_jellyfin_connection(
        request: Request,
        update_jellyfin: UpdateJellyfin = Body(...),
        preferences: Preferences = Depends(get_preferences),
    ) -> JellyfinConnection:
    """
    Update the connection details for Jellyfin.

    - update_jellyfin: Jellyfin connection details to modify.
    """

    return update_connection(
        preferences, update_jellyfin, 'jellyfin', log=request.state.log,
    )


@connection_router.patch('/plex', status_code=200)
def update_plex_connection(
        request: Request,
        update_plex: UpdatePlex = Body(...),
        preferences: Preferences = Depends(get_preferences),
    ) -> PlexConnection:
    """
    Update the connection details for Plex.

    - update_plex: Plex connection details to modify.
    """

    return update_connection(
        preferences, update_plex, 'plex', log=request.state.log,
    )


@connection_router.patch('/sonarr', status_code=200)
def update_sonarr_connection(
        request: Request,
        update_sonarr: UpdateSonarr = Body(...),
        preferences: Preferences = Depends(get_preferences),
    ) -> SonarrConnection:
    """
    Update the connection details for Sonarr.

    - update_sonarr: Sonarr connection details to modify.
    """

    return update_connection(
        preferences, update_sonarr, 'sonarr', log=request.state.log
    )


@connection_router.patch('/tmdb', status_code=200)
def update_tmdb_connection(
        request: Request,
        update_tmdb: UpdateTMDb = Body(...),
        preferences: Preferences = Depends(get_preferences),
    ) -> TMDbConnection:
    """
    Update the connection details for TMDb.

    - update_tmdb: TMDb connection details to modify.
    """

    return update_connection(
        preferences, update_tmdb, 'tmdb', log=request.state.log
    )


@connection_router.get('/sonarr/libraries', status_code=200, tags=['Sonarr'])
def get_potential_sonarr_libraries(
        sonarr_interface: Optional[SonarrInterface] = Depends(get_sonarr_interface),
    ) -> list[SonarrLibrary]:
    """
    Get the potential library names and paths from Sonarr.
    """

    # If Sonarr is disabled, raise 409
    if sonarr_interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with Sonarr'
        )

    # Function to parse a library name from a folder name
    def _guess_library_name(folder_name: str) -> str:
        return folder_name.replace('-', ' ').replace('_', ' ')

    # Attempt to interpret library names from root folders
    return [
        SonarrLibrary(name=_guess_library_name(folder.name), path=str(folder))
        for folder in sonarr_interface.get_root_folders()
    ]


@connection_router.post('/tautulli/check', status_code=200, tags=['Tautulli'])
def check_tautulli_integration(
        request: Request,
        tautulli_connection: TautulliConnection = Body(...),
    ) -> bool:
    """
    Check whether Tautulli is integrated with TCM.

    - tautulli_connection: Details of the connection to Tautull, and the
    Notification Agent to search for integration of.
    """

    interface = TautulliInterface(
        tcm_url=str(request.url).split('/tautulli/check', maxsplit=1)[0],
        tautulli_url=tautulli_connection.tautulli_url,
        api_key=tautulli_connection.tautulli_api_key.get_secret_value(),
        use_ssl=tautulli_connection.tautulli_use_ssl,
        agent_name=tautulli_connection.tautulli_agent_name,
        log=request.state.log,
    )

    return interface.is_integrated()


@connection_router.post('/tautulli/integrate', status_code=201, tags=['Tautulli'])
def add_tautulli_integration(
        request: Request,
        tautulli_connection: TautulliConnection = Body(...),
    ) -> None:
    """
    Integrate Tautulli with TitleCardMaker by creating a Notification
    Agent that triggers the /cards/key API route to quickly create
    title cards.

    - tautulli_connection: Details of the connection to Tautulli and the
    Notification Agent to search for or create.
    """

    request_url = str(request.url)
    url = request_url.split('/api/connection/tautulli/integrate', maxsplit=1)[0]

    interface = TautulliInterface(
        tcm_url=url,
        tautulli_url=tautulli_connection.tautulli_url,
        api_key=tautulli_connection.tautulli_api_key.get_secret_value(),
        use_ssl=tautulli_connection.tautulli_use_ssl,
        agent_name=tautulli_connection.tautulli_agent_name,
        log=request.state.log,
    )

    interface.integrate(log=request.state.log)
