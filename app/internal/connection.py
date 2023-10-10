from logging import Logger
from typing import Union

from sqlalchemy.orm import Session
from app.database.query import get_connection

from app.dependencies import (
    get_emby_interfaces, get_jellyfin_interfaces,
    get_plex_interfaces, get_sonarr_interfaces, refresh_tmdb_interface
)
from app.models.connection import Connection
from app.models.preferences import Preferences
from app.schemas.base import UNSPECIFIED
from app.schemas.connection import (
    NewEmbyConnection, NewJellyfinConnection, NewPlexConnection,
    NewSonarrConnection,
    UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr, UpdateTMDb
)
from modules.Debug import log
from modules.InterfaceGroup import InterfaceGroup


NewConnection = Union[
    NewEmbyConnection, NewJellyfinConnection, NewPlexConnection,
    NewSonarrConnection
]
UpdateConnection = Union[UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr]


def initialize_connections(
        db: Session,
        preferences: Preferences,
        *,
        log: Logger = log,
    ) -> None:
    """
    Initialize all Interfaces (and add them to their respective
    InterfaceGroup).

    Args:
        db: Database with Connection definitions to query.
        preferences: Preferences whose `use_*` toggles to set.
        log: Logger for all log messages.
    """

    # Initialize each type of Interface
    for interface_group, interface_name in (
            (get_emby_interfaces(), 'Emby'),
            (get_jellyfin_interfaces(), 'Jellyfin'),
            (get_plex_interfaces(), 'Plex'),
            (get_sonarr_interfaces(), 'Sonarr')):

        # Get all Connections of this interface type
        connections: list[Connection] = db.query(Connection)\
            .filter_by(interface=interface_name)\
            .all()

        # Set use_ toggle
        setattr(preferences, f'use_{interface_name.lower()}', bool(connections))
        log.debug(f'Preferences.use_{interface_name.lower()} = {getattr(preferences, f"use_{interface_name.lower()}")}')

        # Initialize an Interface for each Connection (if enabled)
        for connection in connections:
            if not connection.enabled:
                continue

            try:
                interface_group.initialize_interface(
                    connection.id, connection.interface_kwargs
                )
                log.debug(f'Initialized Connection to {connection.log_str}')
            except Exception as exc:
                log.exception(f'Error initializing {connection.log_str} - {exc}', exc)


def add_connection(
        db: Session,
        new_connection: NewConnection,
        interface_group: InterfaceGroup,
        preferences: Preferences,
        *,
        log: Logger = log,
    ) -> Connection:
    """
    Create a new Connecton and add it to the Database. If enabled, an
    Interface with the defined details is then initialized and added
    to the InterfaceGroup.

    Args:
        db: Database to add the new Connection to.
        new_connection: Details of the new Connection to add.
        interface_group: InterfaceGroup to add the initialized Interface
            to (if enabled).
        preferences: Global preferences whose interface-enable attribute
            should be toggled.
        log: Logger for all log messages.

    Returns:
        Newly created Connection.
    """

    # Add to database
    connection = Connection(**new_connection.dict())
    db.add(connection)
    db.commit()
    log.info(f'Created {connection.log_str}')

    # Update global use_ attribute
    setattr(preferences, f'use_{connection.interface.lower()}', True)

    # Update InterfaceGroup
    if connection.enabled:
        interface_group.initialize_interface(
            connection.id, connection.interface_kwargs, log=log
        )

    return connection


def update_tmdb(
        preferences: Preferences,
        update_object: UpdateTMDb,
        *,
        log: Logger = log,
    ) -> Preferences:
    """
    Update the connection details for TMDb, refreshing the interface if
    any attributes were changed.

    Args:
        preferences: Preferences to update the connection attributes of.
        update_object: Update object with attributes to update.
        log: Logger for all log messages.

    Returns:
        Modified Preferences with any updated attributes.
    """

    # Change any attributes that are specified and different
    changed = False
    for attribute, value in update_object.dict().items():
        if (value != UNSPECIFIED
            and value != getattr(preferences, f'tmdb_{attribute}')):
            setattr(preferences, f'tmdb_{attribute}', value)
            if attribute.endswith(('_key', '_url')):
                log.debug(f'Preferences.tmdb_{attribute} = *****')
            else:
                log.debug(f'Preferences.tmdb_{attribute} = {value}')
            changed = True

    # Refresh interface (if enabled), and write changes
    if changed:
        if preferences.use_tmdb:
            refresh_tmdb_interface(log=log)
        preferences.commit(log=log)

    return preferences


def update_connection(
        db: Session,
        interface_id: int,
        interface_group: InterfaceGroup,
        update_object: UpdateConnection,
        *,
        log: Logger = log,
    ) -> Preferences:
    """
    Update the given Connection, refreshing the interface if any
    attributes were changed.

    Args:
        db: Database to query for the given Connection.
        interface_id: ID of the interface being updated.
        update_object: Update object with attributes to update.
        log: Logger for all log messages.

    Returns:
        Modified Preferences with any updated attributes.

    Raises:
        HTTPException (404): There is no Connection with the given ID.
    """

    # Get existing Connection
    connection: Connection = get_connection(db, interface_id, raise_exc=True)

    # Update each attribute of the object
    changed = False
    for attr, value in update_object.dict().items():
        if value != UNSPECIFIED and getattr(connection, attr) != value:
            log.debug(f'Connection[{interface_id}].{attr} = {value}')
            setattr(connection, attr, value)
            changed = True

    # If any values were changed, commit to database
    if changed:
        db.commit()
        if connection.enabled:
            interface_group.refresh(
                interface_id, connection.interface_kwargs, log=log
            )

    return connection
