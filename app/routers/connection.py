from typing import Literal

from fastapi import APIRouter, Body, Depends, Request

from app.database.query import get_connection
from app.dependencies import * # pylint: disable=W0401,W0614,W0621
from app.internal.auth import get_current_user
from app.internal.connection import (
    add_connection, update_connection, update_tmdb
)
from app import models
from app.schemas.connection import (
    EmbyConnection, JellyfinConnection, NewEmbyConnection,
    NewJellyfinConnection, NewPlexConnection, NewSonarrConnection,
    NewTautulliConnection, PlexConnection, ServerConnection, SonarrConnection,
    SonarrLibrary, TMDbConnection, UpdateEmby, UpdateJellyfin, UpdatePlex,
    UpdateSonarr, UpdateTMDb,
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
        db: Session = Depends(get_database),
        interface_group: InterfaceGroup[int, EmbyInterface] = Depends(get_emby_interfaces),
    ) -> EmbyConnection:
    """
    # TODO write
    """

    return add_connection(
        db, new_connection, interface_group, log=request.state.log,
    )


@connection_router.post('/jellyfin/new', status_code=201)
def add_jellyfin_connection(
        request: Request,
        new_connection: NewJellyfinConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: InterfaceGroup[int, EmbyInterface] = Depends(get_jellyfin_interfaces),
    ) -> EmbyConnection:
    """
    # TODO write
    """

    return add_connection(
        db, new_connection, interface_group, log=request.state.log,
    )


@connection_router.post('/plex/new', status_code=201)
def add_plex_connection(
        request: Request,
        new_connection: NewPlexConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: InterfaceGroup[int, EmbyInterface] = Depends(get_plex_interfaces),
    ) -> EmbyConnection:
    """
    # TODO write
    """

    return add_connection(
        db, new_connection, interface_group, log=request.state.log,
    )


@connection_router.post('/sonarr/new', status_code=201)
def add_sonarr_connection(
        request: Request,
        new_connection: NewSonarrConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: InterfaceGroup[int, SonarrInterface] = Depends(get_sonarr_interfaces),
    ) -> SonarrConnection:
    """
    # TODO write
    """

    return add_connection(
        db, new_connection, interface_group, log=request.state.log,
    )


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


@connection_router.put('/{connection}/{interface_id}/{status}')
def enable_or_disable_connection_by_id(
        request: Request,
        connection: Literal['emby', 'jellyfin', 'plex', 'sonarr'],
        interface_id: int,
        status: Literal['enable', 'disable'],
        db: Session = Depends(get_database),
        emby_interfaces: InterfaceGroup[int, EmbyInterface] = Depends(get_emby_interfaces),
        jellyfin_interfaces: InterfaceGroup[int, JellyfinInterface] = Depends(get_jellyfin_interfaces),
        plex_interfaces: InterfaceGroup[int, PlexInterface] = Depends(get_plex_interfaces),
        sonarr_interfaces: InterfaceGroup[int, SonarrInterface] = Depends(get_sonarr_interfaces),
    ) -> ServerConnection:
    """
    Set the enabled/disabled status of the given connection.

    - connection: Interface name whose connection is being toggled.
    - interface_id: ID of the Interface to toggle.
    - status: Whether to enable or disable the given interface.
    """

    # Get Connection with this ID
    connection = get_connection(db, interface_id, raise_exc=True)

    # Update enabled status
    connection.enabled = status == 'enable'
    db.commit()

    # If Interface was disabled, nothing else to do
    if not connection.enabled:
        emby_interfaces.disable(interface_id)
        return connection

    # Refresh interface
    if connection == 'emby':
        emby_interfaces.refresh(
            interface_id, connection.emby_kwargs, log=request.state.log,
        )
    elif connection == 'jellyfin':
        jellyfin_interfaces.refresh(
            interface_id, connection.jellyfin_kwargs, log=request.state.log,
        )
    elif connection == 'plex':
        plex_interfaces.refresh(
            interface_id, connection.plex_kwargs, log=request.state.log,
        )
    elif connection == 'sonarr':
        sonarr_interfaces.refresh(
            interface_id, connection.sonarr_kwargs, log=request.state.log,
        )

    return connection


@connection_router.get('/all', status_code=200)
def get_all_connection_details(
        db: Session = Depends(get_database),
    ) -> list[ServerConnection]:
    """
    
    """

    return db.query(models.connection.Connection).all()


@connection_router.get('/emby/all', status_code=200)
def get_all_emby_connection_details(
        db: Session = Depends(get_database),
    ) -> list[EmbyConnection]:
    """
    Get Emby connection details for all defined interfaces.
    """

    return db.query(models.connection.Connection)\
        .filter_by(interface='Emby')\
        .all()


@connection_router.get('/emby/{interface_id}', status_code=200)
def get_emby_connection_details_by_id(
        interface_id: int,
        db: Session = Depends(get_database),
    ) -> EmbyConnection:
    """
    Get the details for the Emby connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    return get_connection(db, interface_id, raise_exc=True)


@connection_router.get('/jellyfin/all', status_code=200)
def get_all_jellyfin_connection_details(
        db: Session = Depends(get_database),
    ) -> list[JellyfinConnection]:
    """
    Get Jellyfin connection details for all defined interfaces.
    """

    return db.query(models.connection.Connection)\
        .filter_by(interface='Jellyfin')\
        .all()


@connection_router.get('/jellyfin/{interface_id}', status_code=200)
def get_jellyfin_connection_details_by_id(
        interface_id: int,
        db: Session = Depends(get_database),
    ) -> JellyfinConnection:
    """
    Get the details for the Emby connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    return get_connection(db, interface_id, raise_exc=True)


@connection_router.get('/plex/all', status_code=200)
def get_all_plex_connection_details(
        db: Session = Depends(get_database),
    ) -> list[PlexConnection]:
    """
    Get Plex connection details for all defined interfaces.
    """

    return db.query(models.connection.Connection)\
        .filter_by(interface='Plex')\
        .all()


@connection_router.get('/plex/{interface_id}', status_code=200)
def get_plex_connection_details_by_id(
        interface_id: int,
        db: Session = Depends(get_database),
    ) -> PlexConnection:
    """
    Get the details for the Plex connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    return get_connection(db, interface_id, raise_exc=True)


@connection_router.get('/sonarr/all', status_code=200)
def get_all_sonarr_connection_details(
        db: Session = Depends(get_database),
    ) -> list[SonarrConnection]:
    """
    Get Sonarr connection details for all defined interfaces.
    """

    return db.query(models.connection.Connection)\
        .filter_by(interface='Sonarr')\
        .all()


@connection_router.get('/sonarr/{interface_id}', status_code=200)
def get_sonarr_connection_details_by_id(
        interface_id: int,
        db: Session = Depends(get_database),
    ) -> SonarrConnection:
    """
    Get the details for the Sonarr connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    return get_connection(db, interface_id, raise_exc=True)


@connection_router.get('/tmdb', status_code=200)
def get_tmdb_connection_details(
        preferences: Preferences = Depends(get_preferences),
    ) -> TMDbConnection:
    """
    Get the connection details for TMDb.
    """

    return preferences


@connection_router.patch('/emby/{interface_id}', status_code=200)
def update_emby_connection(
        request: Request,
        interface_id: int,
        update_emby: UpdateEmby = Body(...),
        db: Session = Depends(get_database),
        emby_interfaces: InterfaceGroup[int, EmbyInterface] = Depends(get_emby_interfaces),
    ) -> EmbyConnection:
    """
    Update the Connection details for the given Emby interface.

    - update_emby: Connection details to modify.
    """

    return update_connection(
        db, interface_id, emby_interfaces, update_emby, log=request.state.log
    )


@connection_router.patch('/jellyfin/{interface_id}', status_code=200)
def update_jellyfin_connection(
        request: Request,
        interface_id: int,
        update_jellyfin: UpdateJellyfin = Body(...),
        db: Session = Depends(get_database),
        jellyfin_interfaces: InterfaceGroup[int, JellyfinInterface] = Depends(get_jellyfin_interfaces),
    ) -> JellyfinConnection:
    """
    Update the Connection details for the given Jellyfin interface.

    - update_jellyfin: Connection details to modify.
    """

    return update_connection(
        db, interface_id, jellyfin_interfaces, update_jellyfin,
        log=request.state.log
    )


@connection_router.patch('/plex/{interface_id}', status_code=200)
def update_plex_connection(
        request: Request,
        interface_id: int,
        update_plex: UpdatePlex = Body(...),
        db: Session = Depends(get_database),
        plex_interfaces: InterfaceGroup[int, PlexInterface] = Depends(get_plex_interfaces),
    ) -> PlexConnection:
    """
    Update the Connection details for the given Plex interface.

    - update_plex: Connection details to modify.
    """

    return update_connection(
        db, interface_id, plex_interfaces, update_plex, log=request.state.log
    )


@connection_router.patch('/sonarr/{interface_id}', status_code=200)
def update_sonarr_connection(
        request: Request,
        interface_id: int,
        update_sonarr: UpdateSonarr = Body(...),
        db: Session = Depends(get_database),
        sonarr_interfaces: InterfaceGroup[int, SonarrInterface] = Depends(get_sonarr_interfaces),
    ) -> SonarrConnection:
    """
    Update the Connection details for the given Sonarr interface.

    - update_sonarr: Connection details to modify.
    """

    return update_connection(
        db, interface_id, sonarr_interfaces, update_sonarr,
        log=request.state.log
    )


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


@connection_router.delete('/{interface_id}')
def delete_connection(
        interface_id: int,
        db: Session = Depends(get_database),
        emby_interfaces: InterfaceGroup[int, EmbyInterface] = Depends(get_emby_interfaces),
        jellyfin_interfaces: InterfaceGroup[int, JellyfinInterface] = Depends(get_jellyfin_interfaces),
        plex_interfaces: InterfaceGroup[int, PlexInterface] = Depends(get_plex_interfaces),
        sonarr_interfaces: InterfaceGroup[int, SonarrInterface] = Depends(get_sonarr_interfaces),
    ) -> None:
    """
    Delete the Connection with the given ID. This also disables and
    removes the Interface from the relevant InterfaceGroup.

    - interface_id: ID of the Connection to delete.
    """

    # Get Connection with this ID
    connection = get_connection(db, interface_id, raise_exc=True)

    # Remove Interface from group
    try:
        if connection.interface == 'Emby':
            emby_interfaces.disable(interface_id)
        elif connection.interface == 'Jellyfin':
            jellyfin_interfaces.disable(interface_id)
        elif connection.interface == 'Plex':
            plex_interfaces.disable(interface_id)
        elif connection.interface == 'Sonarr':
            sonarr_interfaces.disable(interface_id)
    except KeyError:
        pass

    # Delete Connection
    db.delete(connection)
    log.info(f'Deleted {connection.log_str}')
    db.commit()


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
