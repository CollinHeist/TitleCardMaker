from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from app.dependencies import * # pylint: disable=W0401,W0614,W0621
from app.internal.auth import get_current_user
from app.internal.connection import update_connection, update_tmdb
from app.schemas.connection import (
    EmbyConnection, JellyfinConnection, NewEmbyConnection,
    NewJellyfinConnection, NewPlexConnection, NewSonarrConnection,
    NewTautulliConnection, PlexConnection, SonarrConnection, SonarrLibrary,
    TMDbConnection, UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr,
    UpdateTMDb,
)
from modules.SonarrInterface2 import SonarrInterface
from modules.TautulliInterface2 import TautulliInterface


# Create sub router for all /connection API requests
connection_router = APIRouter(
    prefix='/connection',
    tags=['Connections'],
    dependencies=[Depends(get_current_user)],
)


@connection_router.post('/emby/new', status_code=201)
def add_emby_connection(
        request: Request,
        new_connection: NewEmbyConnection = Body(...),
        preferences: Preferences = Depends(get_preferences),
        interface_group: InterfaceGroup[int, EmbyInterface] = Depends(get_all_emby_interfaces),
    ) -> EmbyConnection:
    """
    # TODO write
    """

    # Get contextual logger
    log = request.state.log

    # Create interface, get generated ID
    kwargs = new_connection.dict()
    interface_id, _ = interface_group.append_interface(log=log, **kwargs)

    # Store these interface kwargs, commit preference changes
    preferences.emby_args[interface_id] = kwargs
    preferences.commit(log=log)

    return kwargs | {'interface_id': interface_id}


@connection_router.post('/jellyfin/new', status_code=201)
def add_jellyfin_connection(
        request: Request,
        new_connection: NewJellyfinConnection = Body(...),
        preferences: Preferences = Depends(get_preferences),
        interface_group: InterfaceGroup[int, EmbyInterface] = Depends(get_all_jellyfin_interfaces),
    ) -> EmbyConnection:
    """
    # TODO write
    """

    # Get contextual logger
    log = request.state.log

    # Create interface, get generated ID
    kwargs = new_connection.dict()
    interface_id, _ = interface_group.append_interface(log=log, **kwargs)

    # Store these interface kwargs, commit preference changes
    preferences.jellyfin_args[interface_id] = kwargs
    preferences.commit(log=log)

    return kwargs | {'interface_id': interface_id}


@connection_router.post('/plex/new', status_code=201)
def add_plex_connection(
        request: Request,
        new_connection: NewPlexConnection = Body(...),
        preferences: Preferences = Depends(get_preferences),
        interface_group: InterfaceGroup[int, EmbyInterface] = Depends(get_all_plex_interfaces),
    ) -> EmbyConnection:
    """
    # TODO write
    """

    # Get contextual logger
    log = request.state.log

    # Create interface, get generated ID
    kwargs = new_connection.dict()
    interface_id, _ = interface_group.append_interface(log=log, **kwargs)

    # Store these interface kwargs, commit preference changes
    preferences.plex_args[interface_id] = kwargs
    preferences.commit(log=log)

    return kwargs | {'interface_id': interface_id}


@connection_router.post('/sonarr/new', status_code=201)
def add_sonarr_connection(
        request: Request,
        new_connection: NewSonarrConnection = Body(...),
        preferences: Preferences = Depends(get_preferences),
        interface_group: InterfaceGroup[int, SonarrInterface] = Depends(get_all_sonarr_interfaces),
    ) -> SonarrConnection:
    """
    # TODO write
    """

    # Get contextual logger
    log = request.state.log

    # Create interface, get generated ID
    kwargs = new_connection.dict()
    interface_id, _ = interface_group.append_interface(log=log, **kwargs)

    # Store these interface kwargs, commit preference changes
    preferences.sonarr_args[interface_id] = kwargs
    preferences.commit(log=log)

    return kwargs | {'interface_id': interface_id}


@connection_router.put('/tmdb/{status}', status_code=204)
def enable_or_disable_tmdb(
        request: Request,
        status: Literal['enable', 'disable'],
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Set the enabled/disabled status of TMDb.

    - status: Whether to enable or disable TMDb.
    """

    # Get contextual logger
    log = request.state.log

    preferences.use_tmdb = status == 'enable'
    if preferences.use_tmdb:
        refresh_tmdb_interface(log=log)

    preferences.commit(log=log)


@connection_router.put('/{connection}/{interface_id}/{status}', status_code=204)
def enable_or_disable_connection_by_id(
        request: Request,
        connection: Literal['emby', 'jellyfin', 'plex', 'sonarr'],
        interface_id: int,
        status: Literal['enable', 'disable'],
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Set the enabled/disabled status of the given connection.

    - connection: Interface name whose connection is being toggled.
    - interface_id: ID of the Interface to toggle.
    - status: Whether to enable or disable the given interface.
    """

    # Get contextual logger
    log = request.state.log

    if connection == 'emby':
        if interface_id not in preferences.emby_args:
            raise HTTPException(
                status_code=409,
                detail=f'No Emby connection with ID {interface_id}',
            )
        preferences.emby_args[interface_id]['enabled'] = status == 'enable'
        if status == 'enable':
            refresh_emby_interfaces(interface_id, log=log)
    elif connection == 'jellyfin':
        if interface_id not in preferences.jellyfin_args:
            raise HTTPException(
                status_code=409,
                detail=f'No Jellyfin connection with ID {interface_id}',
            )
        preferences.jellyfin_args[interface_id]['enabled'] = status == 'enable'
        if status == 'enable':
            refresh_jellyfin_interfaces(interface_id, log=log)
    elif connection == 'plex':
        if interface_id not in preferences.plex_args:
            raise HTTPException(
                status_code=409,
                detail=f'No Plex connection with ID {interface_id}',
            )
        preferences.plex_args[interface_id]['enabled'] = status == 'enable'
        if status == 'enable':
            refresh_plex_interfaces(interface_id, log=log)
    elif connection == 'sonarr':
        if interface_id not in preferences.sonarr_args:
            raise HTTPException(
                status_code=409,
                detail=f'No Sonarr connection with ID {interface_id}',
            )
        preferences.sonarr_args[interface_id]['enabled'] = status == 'enable'
        if status == 'enable':
            refresh_sonarr_interfaces(interface_id, log=log)

    preferences.commit(log=log)


@connection_router.get('/emby/all', status_code=200)
def get_all_emby_connection_details(
        preferences: Preferences = Depends(get_preferences),
    ) -> list[EmbyConnection]:
    """
    Get Emby connection details for all defined interfaces.
    """

    return preferences.all_emby_argument_groups


@connection_router.get('/emby/{interface_id}', status_code=200)
def get_emby_connection_details_by_id(
        interface_id: int,
        preferences: Preferences = Depends(get_preferences),
    ) -> EmbyConnection:
    """
    Get the details for the Emby connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    if interface_id in preferences.emby_args:
        return preferences.emby_args[interface_id]

    raise HTTPException(
        status_code=404,
        detail=f'No Emby connection with ID {interface_id}',
    )


@connection_router.get('/jellyfin/all', status_code=200)
def get_all_jellyfin_connection_details(
        preferences: Preferences = Depends(get_preferences),
    ) -> list[JellyfinConnection]:
    """
    Get Jellyfin connection details for all defined interfaces.
    """

    return preferences.all_emby_argument_groups


@connection_router.get('/jellyfin/{interface_id}', status_code=200)
def get_jellyfin_connection_details_by_id(
        interface_id: int,
        preferences: Preferences = Depends(get_preferences),
    ) -> JellyfinConnection:
    """
    Get the details for the Emby connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    if interface_id in preferences.jellyfin_args:
        return preferences.jellyfin_args[interface_id]

    raise HTTPException(
        status_code=404,
        detail=f'No Jellyfin connection with ID {interface_id}',
    )


@connection_router.get('/plex/all', status_code=200)
def get_all_plex_connection_details(
        preferences: Preferences = Depends(get_preferences),
    ) -> list[PlexConnection]:
    """
    Get Plex connection details for all defined interfaces.
    """

    return preferences.all_plex_argument_groups


@connection_router.get('/plex/{interface_id}', status_code=200)
def get_plex_connection_details_by_id(
        interface_id: int,
        preferences: Preferences = Depends(get_preferences),
    ) -> PlexConnection:
    """
    Get the details for the Plex connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    if interface_id in preferences.plex_args:
        return preferences.plex_args[interface_id]

    raise HTTPException(
        status_code=404,
        detail=f'No Plex connection with ID {interface_id}',
    )


@connection_router.get('/sonarr/all', status_code=200)
def get_all_sonarr_connection_details(
        preferences: Preferences = Depends(get_preferences),
    ) -> list[SonarrConnection]:
    """
    Get Sonarr connection details for all defined interfaces.
    """

    return preferences.all_sonarr_argument_groups


@connection_router.get('/sonarr/{interface_id}', status_code=200)
def get_sonarr_connection_details_by_id(
        interface_id: int,
        preferences: Preferences = Depends(get_preferences),
    ) -> SonarrConnection:
    """
    Get the details for the Sonarr connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    if interface_id in preferences.sonarr_args:
        return preferences.sonarr_args[interface_id]

    raise HTTPException(
        status_code=404,
        detail=f'No Sonarr connection with ID {interface_id}',
    )


@connection_router.get('/tmdb', status_code=200)
def get_tmdb_connection_details(
        preferences: Preferences = Depends(get_preferences),
    ) -> TMDbConnection:
    """
    Get the connection details for TMDb.
    """

    return preferences


@connection_router.patch('/emby/{interface_id}', status_code=200)
def update_emby_connection_by_id(
        request: Request,
        interface_id: int,
        update_emby: UpdateEmby = Body(...),
        preferences: Preferences = Depends(get_preferences),
    ) -> EmbyConnection:
    """
    Update the connection details for Emby.

    - update_sonarr: New Emby connection details.
    """

    return update_connection(
        preferences, interface_id, update_emby, 'emby',
        log=request.state.log
    ).emby_args[interface_id]


@connection_router.patch('/jellyfin/{interface_id}', status_code=200)
def update_jellyfin_connection_by_id(
        request: Request,
        interface_id: int,
        update_jellyfin: UpdateJellyfin = Body(...),
        preferences: Preferences = Depends(get_preferences),
    ) -> JellyfinConnection:
    """
    Update the connection details for Jellyfin.

    - update_sonarr: New Jellyfin connection details.
    """

    return update_connection(
        preferences, interface_id, update_jellyfin, 'pjellyfinlex',
        log=request.state.log
    ).jellyfin_args[interface_id]


@connection_router.patch('/plex/{interface_id}', status_code=200)
def update_plex_connection_by_id(
        request: Request,
        interface_id: int,
        update_plex: UpdatePlex = Body(...),
        preferences: Preferences = Depends(get_preferences),
    ) -> PlexConnection:
    """
    Update the connection details for Plex.

    - update_sonarr: New Plex connection details.
    """

    return update_connection(
        preferences, interface_id, update_plex, 'plex',
        log=request.state.log
    ).plex_args[interface_id]


@connection_router.patch('/sonarr/{interface_id}', status_code=200)
def update_sonarr_connection_by_id(
        request: Request,
        interface_id: int,
        update_sonarr: UpdateSonarr = Body(...),
        preferences: Preferences = Depends(get_preferences),
    ) -> SonarrConnection:
    """
    Update the connection details for Sonarr.

    - update_sonarr: New Sonarr connection details.
    """

    return update_connection(
        preferences, interface_id, update_sonarr, 'sonarr',
        log=request.state.log
    ).sonarr_args[interface_id]


@connection_router.patch('/tmdb', status_code=200)
def update_tmdb_connection(
        request: Request,
        update_object: UpdateTMDb = Body(...),
        preferences: Preferences = Depends(get_preferences),
    ) -> TMDbConnection:
    """
    Update the connection details for TMDb.

    - update_tmdb: TMDb connection details to modify.
    """

    return update_tmdb(preferences, update_object, log=request.state.log)


@connection_router.get('/sonarr/libraries', status_code=200, tags=['Sonarr'])
def get_potential_sonarr_libraries(
        sonarr_interface: SonarrInterface = Depends(require_sonarr_interface),
    ) -> list[SonarrLibrary]:
    """
    Get the potential library names and paths from Sonarr.
    """

    # Function to parse a library name from a folder name
    def _guess_library_name(folder_name: str) -> str:
        return folder_name.replace('-', ' ').replace('_', ' ')

    # Attempt to interpret library names from root folders
    return [
        {'name': _guess_library_name(folder.name), 'path': str(folder)}
        for folder in sonarr_interface.get_root_folders()
    ]


@connection_router.post('/tautulli/check', status_code=200, tags=['Tautulli'])
def check_tautulli_integration(
        request: Request,
        tautulli_connection: NewTautulliConnection = Body(...),
    ) -> bool:
    """
    Check whether Tautulli is integrated with TCM.

    - tautulli_connection: Details of the connection to Tautull, and the
    Notification Agent to search for integration of.
    """

    interface = TautulliInterface(
        tcm_url=str(request.url).split('/tautulli/check', maxsplit=1)[0],
        tautulli_url=tautulli_connection.url,
        api_key=tautulli_connection.api_key.get_secret_value(),
        use_ssl=tautulli_connection.use_ssl,
        agent_name=tautulli_connection.agent_name,
        log=request.state.log,
    )

    return interface.is_integrated()


@connection_router.post('/tautulli/integrate', status_code=201, tags=['Tautulli'])
def add_tautulli_integration(
        request: Request,
        tautulli_connection: NewTautulliConnection = Body(...),
    ) -> None:
    """
    Integrate Tautulli with TitleCardMaker by creating a Notification
    Agent that triggers the /cards/key API route to quickly create
    title cards.

    - tautulli_connection: Details of the connection to Tautulli and the
    Notification Agent to search for/create.
    """

    request_url = str(request.url)
    url = request_url.split('/api/connection/tautulli/integrate', maxsplit=1)[0]

    interface = TautulliInterface(
        tcm_url=url,
        tautulli_url=tautulli_connection.url,
        api_key=tautulli_connection.api_key.get_secret_value(),
        use_ssl=tautulli_connection.use_ssl,
        agent_name=tautulli_connection.agent_name,
        log=request.state.log,
    )

    interface.integrate(log=request.state.log)
