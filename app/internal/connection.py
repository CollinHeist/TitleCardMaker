from logging import Logger
from typing import Literal, Union

from app.dependencies import (
    refresh_emby_interface, refresh_jellyfin_interface, refresh_plex_interface,
    refresh_sonarr_interface, refresh_tmdb_interface,
)
from app.models.preferences import Preferences
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import (
    UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr, UpdateTMDb
)
from modules.Debug import log


UpdateConnection = Union[
    UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr, UpdateTMDb
]


def update_connection(
        preferences: Preferences,
        update_object: UpdateConnection,
        connection: Literal['emby', 'jellyfin', 'plex', 'sonarr', 'tmdb'],
        *,
        log: Logger = log,
    ) -> Preferences:
    """
    Update the connection details for the given connection, refreshing
    the interface if any attributes were changed.

    Args:
        preferences: Preferences to update the connection attributes of.
        update_object: Update object with attributes to update.
        connection: Name of the connection being updated. Used as the
            prefix for the updated attributes, e.g. emby_*.
        log: (Keyword) Logger for all log messages.

    Returns:
        Modified Preferences with any updated attributes.
    """

    # Change any attributes that are specified and different
    changed = False
    for attribute, value in update_object.dict().items():
        if (value != UNSPECIFIED
            and value != getattr(preferences, f'{connection}_{attribute}')):
            setattr(preferences, f'{connection}_{attribute}', value)
            if f'{connection}_{attribute}' in preferences.PRIVATE_ATTRIBUTES:
                log.debug(f'Preferences.{connection}_{attribute} = *****')
            else:
                log.debug(f'Preferences.{connection}_{attribute} = {value}')
            changed = True

    # Refresh interface if changed
    if changed and getattr(preferences, f'use_{connection}'):
        if connection == 'emby':
            refresh_emby_interface(log=log)
        elif connection == 'jellyfin':
            refresh_jellyfin_interface(log=log)
        elif connection == 'plex':
            refresh_plex_interface(log=log)
        elif connection == 'sonarr':
            refresh_sonarr_interface(log=log)
        elif connection == 'tmdb':
            refresh_tmdb_interface(log=log)

    # Commit changes
    if changed:
        preferences.commit()

    return preferences
