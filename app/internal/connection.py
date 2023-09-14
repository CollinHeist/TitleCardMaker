from logging import Logger
from typing import Literal, Union

from fastapi import HTTPException

from app.dependencies import (
    refresh_emby_interfaces, refresh_jellyfin_interfaces, refresh_plex_interfaces,
    refresh_sonarr_interfaces, refresh_tmdb_interface,
)
from app.models.preferences import Preferences
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import (
    UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr, UpdateTMDb
)
from modules.Debug import log


UpdateConnection = Union[UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr]


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
        log: (Keyword) Logger for all log messages.

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
        preferences: Preferences,
        interface_id: int,
        update_object: UpdateConnection,
        connection: Literal['emby', 'jellyfin', 'plex', 'sonarr'],
        *,
        log: Logger = log,
    ) -> Preferences:
    """
    Update the connection details for the given connection, refreshing
    the interface if any attributes were changed.

    Args:
        preferences: Preferences to update the connection attributes of.
        interface_id: ID of the interface being updated.
        update_object: Update object with attributes to update.
        connection: Name of the connection being updated. Used as the
            prefix for the updated attributes, e.g. emby_*.
        log: (Keyword) Logger for all log messages.

    Returns:
        Modified Preferences with any updated attributes.

    Raises:
        HTTPException (404) if there is no interface with the given ID.
    """

    # Get arguments being changed
    all_interface_args = getattr(preferences, f'{connection}_args')
    if (interface_args := all_interface_args.get(interface_id)) is None:
        raise HTTPException(
            status_code=404,
            detail=f'No {connection} connection with ID {interface_id}'
        )

    # Change any attributes that are specified and different
    changed = False
    for attribute, value in update_object.dict().items():
        if (value != UNSPECIFIED
            and value != interface_args[attribute]):
            interface_args[attribute] = value
            if attribute in ('url', 'api_key'):
                log.debug(f'Preferences.{connection}[{interface_id}].{attribute} = *****')
            else:
                log.debug(f'Preferences.{connection}[{interface_id}].{attribute} = {value}')
            changed = True

    # Refresh interface if changed
    if changed and interface_args['enabled']:
        if connection == 'emby':
            refresh_emby_interfaces(interface_id, log=log)
        elif connection == 'jellyfin':
            refresh_jellyfin_interfaces(interface_id, log=log)
        elif connection == 'plex':
            refresh_plex_interfaces(interface_id, log=log)
        elif connection == 'sonarr':
            refresh_sonarr_interfaces(interface_id, log=log)

    # Commit changes
    if changed:
        preferences.commit(log=log)

    return preferences
