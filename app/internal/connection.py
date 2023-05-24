from typing import Literal, Union

from app.dependencies import (
    refresh_emby_interface, refresh_jellyfin_interface, refresh_plex_interface,
    refresh_sonarr_interface, refresh_tmdb_interface,
)
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import (
    Preferences, UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr, UpdateTMDb
)

UpdateConnection = Union[
    UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr, UpdateTMDb
]

def update_connection(
        preferences: Preferences,
        update_connection: UpdateConnection,
        connection: Literal['emby', 'jellyfin', 'plex', 'sonarr', 'tmdb']
    ) -> Preferences:
    """
    Update the connection details for the given connection, refreshing
    the interface if any attributes were changed.

    Args:
        preferences: Preferences to update the connection attributes of.
        update_connection: Update object with attributes to update.
        connection: Name of the connection being updated. Used as the
            prefix for the updated attributes, e.g. emby_*.
        refresh_interface_function: Function to call to refresh the
            interface if any attributes were changed.

    Returns:
        Modified Preferences with any updated attributes.
    """

    # Change any attributes that are specified and different
    changed = False
    for attribute, value in update_connection.dict().items():
        if (value != UNSPECIFIED
            and value != getattr(preferences, f'{connection}_{attribute}')):
            setattr(preferences, f'{connection}_{attribute}', value)
            changed = True
    preferences.commit()

    # Refresh interface if changed
    if changed and getattr(preferences, f'use_{connection}'):
        if   connection == 'emby':     refresh_emby_interface()
        elif connection == 'jellyfin': refresh_jellyfin_interface()
        elif connection == 'plex':     refresh_plex_interface()
        elif connection == 'sonarr':   refresh_sonarr_interface()
        elif connection == 'tmdb':     refresh_tmdb_interface()

    return preferences