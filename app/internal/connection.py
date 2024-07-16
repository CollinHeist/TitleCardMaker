from logging import Logger
from typing import Union

from sqlalchemy.orm import Session

from app.database.query import get_connection
from app.dependencies import (
    get_emby_interfaces, get_jellyfin_interfaces, get_plex_interfaces,
    get_preferences, get_sonarr_interfaces, get_tmdb_interfaces,
    get_tvdb_interfaces,
)
from app.internal.auth import encrypt
from app.models.connection import Connection
from app.models.preferences import Preferences
from app.schemas.base import UNSPECIFIED
from app.schemas.connection import (
    NewEmbyConnection, NewJellyfinConnection, NewPlexConnection,
    NewSonarrConnection, NewTMDbConnection, NewTVDbConnection,
    UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr, UpdateTMDb, UpdateTVDb
)
from modules.Debug import log
from modules.Debug2 import SECRETS
from modules.InterfaceGroup import InterfaceGroup


_NewConnection = Union[
    NewEmbyConnection, NewJellyfinConnection, NewPlexConnection,
    NewSonarrConnection, NewTMDbConnection, NewTVDbConnection,
]
_UpdateConnection = Union[
    UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr, UpdateTMDb, UpdateTVDb
]


def initialize_connections(
        db: Session,
        preferences: Preferences,
        *,
        log: Logger = log,
    ) -> None:
    """
    Initialize all Interfaces (and add them to their respective
    InterfaceGroup). This also adds their secrets to the set of secrets
    for logging.

    Args:
        db: Database with Connection definitions to query.
        preferences: Preferences whose `use_*` toggles to set.
        log: Logger for all log messages.
    """

    # Initialize each type of Interface
    for interface_group, interface_type in (
            (get_emby_interfaces(), 'Emby'),
            (get_jellyfin_interfaces(), 'Jellyfin'),
            (get_plex_interfaces(), 'Plex'),
            (get_sonarr_interfaces(), 'Sonarr'),
            (get_tmdb_interfaces(), 'TMDb'),
            (get_tvdb_interfaces(), 'TVDb'),
        ):
        # Get all Connections of this interface type
        connections: list[Connection] = db.query(Connection)\
            .filter_by(interface_type=interface_type)\
            .all()

        # Set use_ toggle
        use_connection = any(connection.enabled for connection in connections)
        setattr(preferences, f'use_{interface_type.lower()}', use_connection)

        # Initialize an Interface for each Connection (if enabled)
        for connection in connections:
            # Add to set of secrets
            connection.add_secrets(SECRETS)

            # Skip if disabled
            if not connection.enabled:
                log.debug(f'Not initializing {connection} (disabled)')
                continue

            try:
                interface_group.initialize_interface(
                    connection.id, connection.interface_kwargs, log=log,
                )
            except Exception:
                preferences.invalid_connections.append(connection.id)
                log.exception(f'Error initializing {connection}')

    # Log any invalid Connections
    if preferences.invalid_connections:
        log.info(f'Disabled Connection(s) {preferences.invalid_connections}')


def add_connection(
        db: Session,
        new_connection: _NewConnection,
        interface_group: InterfaceGroup,
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
        log: Logger for all log messages.

    Returns:
        Newly created Connection.
    """

    # Add to database
    connection = Connection(**new_connection.dict())
    connection.encrypt()
    db.add(connection)
    db.commit()

    # Add API key to set of secrets
    connection.add_secrets(SECRETS)
    log.info(f'Created {connection}')

    # Update global use_ attribute
    preferences = get_preferences()
    setattr(preferences, f'use_{connection.interface_type.lower()}', True)

    # Assign global EDS if unset
    if preferences.episode_data_source is None:
        preferences.episode_data_source = connection.id
        log.info(f'Set global Episode Data Source to {connection}')
        preferences.commit()

    # Update InterfaceGroup
    if connection.enabled:
        try:
            interface_group.initialize_interface(
                connection.id, connection.interface_kwargs, log=log
            )
        except Exception as exc:
            preferences.invalid_connections.append(connection.id)
            raise exc

    return connection


def update_connection(
        db: Session,
        interface_id: int,
        interface_group: InterfaceGroup,
        update_object: _UpdateConnection,
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
    connection = get_connection(db, interface_id, raise_exc=True)

    # Update each attribute of the object
    changed = False
    for attr, value in update_object.dict(exclude_defaults=True).items():
        if value != UNSPECIFIED and getattr(connection, attr) != value:
            # Update Connection
            if attr in ('api_key', 'url'):
                setattr(connection, attr, encrypt(value))
            else:
                setattr(connection, attr, value)
            changed = True

            # Update secrets, log change
            connection.add_secrets(SECRETS)
            log.debug(f'Connection[{interface_id}].{attr} = {value}')

    # If any values were changed, commit to database
    if changed:
        db.commit()
        preferences = get_preferences()
        if connection.enabled:
            # Attempt to re-initialize Interface with new details
            try:
                interface_group.refresh(
                    interface_id, connection.interface_kwargs, log=log
                )
                if interface_id in preferences.invalid_connections:
                    preferences.invalid_connections.remove(interface_id)
            except Exception as exc:
                if interface_id not in preferences.invalid_connections:
                    preferences.invalid_connections.append(interface_id)
                raise exc
        # Connection is disabled, remove from group
        else:
            interface_group.disable(interface_id)
            if interface_id in preferences.invalid_connections:
                preferences.invalid_connections.remove(interface_id)

    return connection
