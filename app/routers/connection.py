from typing import Literal

from fastapi import APIRouter, Body, Depends, Request

from app.database.query import get_connection
from app.dependencies import * # pylint: disable=W0401,W0614,W0621
from app.internal.auth import get_current_user
from app.internal.connection import (
    add_connection, update_connection, update_tmdb
)
from app.models.series import Series
from app.models.sync import Sync
from app.models.template import Template
from app import models
from app.schemas.connection import (
    EmbyConnection, JellyfinConnection, NewEmbyConnection,
    NewJellyfinConnection, NewPlexConnection, NewSonarrConnection,
    NewTautulliConnection, PlexConnection, PotentialSonarrLibrary,
    ServerConnection, SonarrConnection, TMDbConnection, UpdateEmby,
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


@connection_router.post('/emby/new', status_code=201)
def add_emby_connection(
        request: Request,
        new_connection: NewEmbyConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: InterfaceGroup[int, EmbyInterface] = Depends(get_emby_interfaces),
        preferences: Preferences = Depends(get_preferences),
    ) -> EmbyConnection:
    """
    Create a new Connection to Emby; adding it to the Database and
    adding an initialized Interface to the InterFaceGroup.

    - new_connection: Details of the new Connection to add and create.
    """

    return add_connection(
        db, new_connection, interface_group, preferences, log=request.state.log,
    )


@connection_router.post('/jellyfin/new', status_code=201)
def add_jellyfin_connection(
        request: Request,
        new_connection: NewJellyfinConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: InterfaceGroup[int, EmbyInterface] = Depends(get_jellyfin_interfaces),
        preferences: Preferences = Depends(get_preferences),
    ) -> JellyfinConnection:
    """
    Create a new Connection to Jellyfin; adding it to the Database and
    adding an initialized Interface to the InterFaceGroup.

    - new_connection: Details of the new Connection to add and create.
    """

    return add_connection(
        db, new_connection, interface_group, preferences, log=request.state.log,
    )


@connection_router.post('/plex/new', status_code=201)
def add_plex_connection(
        request: Request,
        new_connection: NewPlexConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: InterfaceGroup[int, EmbyInterface] = Depends(get_plex_interfaces),
        preferences: Preferences = Depends(get_preferences),
    ) -> PlexConnection:
    """
    Create a new Connection to Sonarr; adding it to the Database and
    adding an initialized Interface to the InterFaceGroup.

    - new_connection: Details of the new Connection to add and create.
    """

    return add_connection(
        db, new_connection, interface_group, preferences, log=request.state.log,
    )


@connection_router.post('/sonarr/new', status_code=201)
def add_sonarr_connection(
        request: Request,
        new_connection: NewSonarrConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: InterfaceGroup[int, SonarrInterface] = Depends(get_sonarr_interfaces),
        preferences: Preferences = Depends(get_preferences),
    ) -> SonarrConnection:
    """
    Create a new Connection to sonarr; adding it to the Database and
    adding an initialized Interface to the InterFaceGroup.

    - new_connection: Details of the new Connection to add and create.
    """

    return add_connection(
        db, new_connection, interface_group, preferences, log=request.state.log,
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
    Get details for all defined Connections (of all types).
    """

    return db.query(models.connection.Connection).all()


@connection_router.get('/emby/all', status_code=200)
def get_all_emby_connection_details(
        db: Session = Depends(get_database),
    ) -> list[EmbyConnection]:
    """
    Get details for all defined Emby Connections.
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
    Get details for all defined Jellyfin Connections.
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
    Get details for all defined Plex Connections.
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
    Get details for all defined Sonarr Connections.
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
        request: Request,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        emby_interfaces: InterfaceGroup[int, EmbyInterface] = Depends(get_emby_interfaces),
        jellyfin_interfaces: InterfaceGroup[int, JellyfinInterface] = Depends(get_jellyfin_interfaces),
        plex_interfaces: InterfaceGroup[int, PlexInterface] = Depends(get_plex_interfaces),
        sonarr_interfaces: InterfaceGroup[int, SonarrInterface] = Depends(get_sonarr_interfaces),
    ) -> None:
    """
    Delete the Connection with the given ID. This also disables and
    removes the Interface from the relevant InterfaceGroup, deletes any
    linked Syncs, removes this Connection[s libraries from any Series,
    any Episode Data Sources from Series and templates, and deletes the
    Connection from the global image source priority and episode data
    source.

    - interface_id: ID of the Connection to delete.
    """

    # Get contextual logger
    log: Logger = request.state.log

    # Get Connection with this ID
    connection = get_connection(db, interface_id, raise_exc=True)

    # Remove Interface from group
    try:
        if connection.interface_type == 'Emby':
            emby_interfaces.disable(interface_id)
        elif connection.interface_type == 'Jellyfin':
            jellyfin_interfaces.disable(interface_id)
        elif connection.interface_type == 'Plex':
            plex_interfaces.disable(interface_id)
        elif connection.interface_type == 'Sonarr':
            sonarr_interfaces.disable(interface_id)
    except KeyError:
        pass

    # Delete any linked Syncs
    for sync in db.query(Sync).filter_by(interface_id=interface_id).all():
        log.info(f'Deleting {sync.log_str}')
        db.delete(sync)

    # Remove from any linked Series libraries or data sources
    for series in db.query(Series).all():
        if any(library['interface_id'] == interface_id
               for library in series.libraries):
            log.warning(f'Removing {connection.log_str} libraries from {series.log_str}')
            series.libraries = [
                library for library in series.libraries
                if library['interface_id'] != interface_id
            ]

        if series.data_source_id == interface_id:
            log.warning(f'Removing Episode Data Source from {series.log_str}')
            series.data_source_id = None

    # Remove linked data source from Templates
    for template in db.query(Template).filter_by(data_source_id=interface_id).all():
        log.warning(f'Removing Episode Data Source from {template.log_str}')
        template.data_source_id = None

    # Delete from ISP if present
    preferences.image_source_priority = [
        source for source in preferences.image_source_priority
        if source['interface_id'] != interface_id
    ]

    # Reset EDS if set
    if preferences.episode_data_source['interface_id'] == interface_id:
        preferences.episode_data_source =preferences.DEFAULT_EPISODE_DATA_SOURCE
        log.warning(f'Reset global Episode data source')

    # Delete Connection
    db.delete(connection)
    log.info(f'Deleting {connection.log_str}')

    # Commit changes to global options and Database
    preferences.commit()
    db.commit()


@connection_router.get('/sonarr/{interface_id}/libraries', status_code=200, tags=['Sonarr'])
def get_potential_sonarr_libraries(
        interface_id: int,
        sonarr_interfaces: InterfaceGroup[int, SonarrInterface] = Depends(get_sonarr_interfaces),
    ) -> list[PotentialSonarrLibrary]:
    """
    Get the potential library names and paths from Sonarr.
    """

    if not (sonarr_interface := sonarr_interfaces[interface_id]):
        raise HTTPException(
            status_code=409,
            detail=f'No valid Sonarr Connection with ID {interface_id}',
        )

    # Attempt to interpret library names from root folders
    return [
        {
            'name': folder.name.replace('-', ' ').replace('_', ' '),
            'path': str(folder)
        } for folder in sonarr_interface.get_root_folders()
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
