from logging import Logger
from typing import Any, Callable, Iterator, Literal, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import (
    EmbyInterfaces, ImageMagickInterfaceLocal, JellyfinInterfaces,
    PreferencesLocal, Scheduler, SessionLocal, TMDbInterfaceLocal,
    PlexInterfaces, SonarrInterfaces,
)
from app.models.preferences import Preferences

from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.ImageMagickInterface import ImageMagickInterface
from modules.InterfaceGroup import InterfaceGroup
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface


def get_database() -> Iterator[Session]:
    """
    Dependency to get a Session to the SQLite database.

    Returns:
        Iterator that yields a Session to the database then closes the
        connection.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_scheduler() -> BackgroundScheduler:
    """
    Dependency to get the global task Scheduler.

    Returns:
        Scheduler responsible for all task scheduling.
    """

    return Scheduler


def get_preferences() -> Preferences:
    """
    Dependency to get the global Preferences.

    Returns:
        Preferences object.
    """

    return PreferencesLocal


def _get_all_interfaces(
        interface_group: InterfaceGroup[int, Any],
        name: Literal['emby', 'jellyfin', 'plex', 'sonarr'],
        refresh_all_function: Callable[[int], None],
    ) -> InterfaceGroup[int, Any]:
    """
    Dependency to get all interfaces to a specific connection. This
    refreshes the connections if the connection is enabled but any
    interfaces are not initialized.

    Args:
        interface_group: `InterfaceGroup` containing interfaces to
            refresh and get.
        name: Name of the interface group.
        refresh_all_function: Function to call if a given interface is
            active but not enabled. Function should refresh the
            interface connection.

    Returns:
        Global `InterfaceGroup` of `Interface` objects.
    """

    all_interface_args = getattr(get_preferences(), f'{name}_args')
    for interface_id, interface_args in all_interface_args.items():
        if interface_args['enabled'] and not interface_group[interface_id]:
            try:
                refresh_all_function(interface_id)
            except Exception as exc:
                log.exception(f'Error connecting to {name}[{interface_id}]',exc)

    return interface_group


def _get_interface(
        interface_group: InterfaceGroup,
        interface_id: int,
        name: Literal['emby', 'jellyfin', 'plex', 'sonarr'],
        refresh_function: Callable[[int], None],
        *,
        required: bool = False,
    ) -> Optional[Any]:
    """
    Dependency to get the interface with the given ID from the given
    `InterfaceGroup`. If the interface is enabled but inactive, it is
    refreshed.

    Args:
        interface_group: InterfaceGroup containing all interfaces of
            this connection.
        interface_id: ID of the interface to return.
        name: Name of the connection this interface corresponds to.
        refresh_function: Function to call if the interface is enabled
            but inactive.
        required: Whether to raise an Exception if the
            interface cannot be returned.

    Returns:
        `Interface` object with the given ID. None is returned if
        `required` is False and the interface cannot be returned.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
        HTTPException (409): The interface with the given ID is disabled.
    """

    # Get this interface's arguments
    if (args := getattr(get_preferences(), f'{name}_args').get(interface_id)) is None:
        if required:
            raise HTTPException(
                status_code=404,
                detail=f'No {name} connection with ID {interface_id}'
            )
        return None

    # Interface is not enabled
    if not args['enabled']:
        if required:
            raise HTTPException(
                status_code=409,
                detail=f'{name}[{interface_id}] is disabled'
            )
        return None

    # Interface enabled but not active, refresh
    if not interface_group[interface_id]:
        try:
            refresh_function(interface_id)
        except Exception as exc:
            log.exception(f'Error connecting to {name}[{interface_id}]', exc)
            if required:
                raise HTTPException(
                    status_code=400,
                    detail=f'Error connecting to {name}[{interface_id}]'
                ) from exc
            return None

    return interface_group[interface_id]


# pylint: disable=global-statement
def refresh_emby_interfaces(
        interface_id: Optional[int] = None,
        *,
        log: Logger = log,
    ) -> None:
    """
    Refresh the global Emby `InterfaceGroup`. If an interface ID is
    provided, only that interface is refreshed.

    Args:
        interface_id: ID of a specific interface to refresh.
        log: Logger for all log messages.
    """

    if interface_id is None:
        EmbyInterfaces.refresh_all(
            get_preferences().emby_argument_groups, log=log
        )
    else:
        interface_args = get_preferences().emby_args[interface_id]
        EmbyInterfaces.refresh(interface_id, interface_args, log=log)


def get_all_emby_interfaces() -> InterfaceGroup[int, EmbyInterface]:
    """
    Dependency to get all interfaces to Emby.

    Returns:
        Global `InterfaceGroup` of `EmbyInterface` objects.
    """

    return _get_all_interfaces(EmbyInterfaces, 'emby', refresh_emby_interfaces)


def get_emby_interface(
        interface_id: int = Query(...),
    ) -> Optional[EmbyInterface]:
    """
    Dependency to get the `EmbyInterface` with the given ID. This adds
    `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `EmbyInterface` with the given ID as defined in the global
        `InterfaceGroup`. If the interface is disabled, undefined, or
        otherwise cannot be communicated with, then None is returned.
    """

    return _get_interface(
        EmbyInterfaces, interface_id, 'emby', refresh_emby_interfaces,
        required=False,
    )


def require_emby_interface(interface_id: int = Query(...)) -> EmbyInterface:
    """
    Dependency to get the `EmbyInterface` with the given ID. This adds
    `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `EmbyInterface` with the given ID as defined in the global
        `InterfaceGroup`.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
        HTTPException (409): The interface with the given ID is disabled.
    """

    return _get_interface(
        EmbyInterfaces, interface_id, 'emby', refresh_emby_interfaces,
        required=True,
    )


def refresh_imagemagick_interface() -> None:
    """
    Refresh the global interface to ImageMagick. This reinitializes and
    overrides the object.

    Args:
        log: Logger for all log messages.
    """

    global ImageMagickInterfaceLocal
    ImageMagickInterfaceLocal = ImageMagickInterface(
        **get_preferences().imagemagick_arguments,
    )


def get_imagemagick_interface() -> ImageMagickInterface:
    """
    Dependency to get the global interface to ImageMagick.

    Returns:
        Global ImageMagickInterface.
    """

    return ImageMagickInterfaceLocal


def refresh_jellyfin_interfaces(
        interface_id: Optional[int] = None,
        *,
        log: Logger = log,
    ) -> None:
    """
    Refresh the global Jellyfin `InterfaceGroup`. If an interface ID is
    provided, only that interface is refreshed.

    Args:
        interface_id: ID of a specific interface to refresh.
        log: Logger for all log messages.
    """

    if interface_id is None:
        JellyfinInterfaces.refresh_all(
            get_preferences().jellyfin_argument_groups, log=log
        )
    else:
        interface_args = get_preferences().jellyfin_args[interface_id]
        JellyfinInterfaces.refresh(interface_id, interface_args, log=log)


def get_all_jellyfin_interfaces() -> InterfaceGroup[int, JellyfinInterface]:
    """
    Dependency to get all interfaces to Jellyfin.

    Returns:
        Global `InterfaceGroup` of `JellyfinInterface` objects.
    """

    return _get_all_interfaces(
        JellyfinInterfaces, 'jellyfin', refresh_jellyfin_interfaces
    )


def get_jellyfin_interface(
        interface_id: int = Query(...),
    ) -> Optional[JellyfinInterface]:
    """
    Dependency to get the `JellyfinInterface` with the given ID. This
    adds `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `JellyfinInterface` with the given ID as defined in the global
        `InterfaceGroup`. If the interface is disabled, undefined, or
        otherwise cannot be communicated with, then None is returned.
    """

    return _get_interface(
        JellyfinInterfaces, interface_id, 'jellyfin', refresh_jellyfin_interfaces,
        required=False,
    )


def require_jellyfin_interface(interface_id: int = Query(...)) -> JellyfinInterface:
    """
    Dependency to get the `JellyfinInterface` with the given ID. This
    adds `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `JellyfinInterface` with the given ID as defined in the global
        `InterfaceGroup`.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
        HTTPException (409): The interface with the given ID is disabled.
    """

    return _get_interface(
        JellyfinInterfaces, interface_id, 'jellyfn', refresh_jellyfin_interfaces,
        required=True,
    )


def refresh_plex_interfaces(
        interface_id: Optional[int] = None,
        *,
        log: Logger = log,
    ) -> None:
    """
    Refresh the global Plex `InterfaceGroup`. If an interface ID is
    provided, only that interface is refreshed.

    Args:
        interface_id: ID of a specific interface to refresh.
        log: Logger for all log messages.
    """

    if interface_id is None:
        PlexInterfaces.refresh_all(
            get_preferences().plex_argument_groups, log=log
        )
    else:
        interface_args = get_preferences().plex_args[interface_id]
        PlexInterfaces.refresh(interface_id, interface_args, log=log)


def get_all_plex_interfaces() -> InterfaceGroup[int, PlexInterface]:
    """
    Dependency to get all interfaces to Plex.

    Returns:
        Global `InterfaceGroup` of `PlexInterface` objects.
    """

    return _get_all_interfaces(PlexInterfaces, 'plex', refresh_plex_interfaces)


def get_plex_interface(
        interface_id: int = Query(...),
    ) -> Optional[PlexInterface]:
    """
    Dependency to get the `PlexInterface` with the given ID. This adds
    `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `PlexInterface` with the given ID as defined in the global
        `InterfaceGroup`. If the interface is disabled, undefined, or
        otherwise cannot be communicated with, then None is returned.
    """

    return _get_interface(
        PlexInterfaces, interface_id, 'plex', refresh_plex_interfaces,
        required=False,
    )


def require_plex_interface(interface_id: int = Query(...)) -> PlexInterface:
    """
    Dependency to get the `PlexInterface` with the given ID. This adds
    `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `PlexInterface` with the given ID as defined in the global
        `InterfaceGroup`.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
        HTTPException (409): The interface with the given ID is disabled.
    """

    return _get_interface(
        PlexInterfaces, interface_id, 'Plex', refresh_plex_interfaces,
        required=True,
    )


def refresh_sonarr_interfaces(
        interface_id: Optional[int] = None,
        *,
        log: Logger = log,
    ) -> None:
    """
    Refresh the global Sonarr `InterfaceGroup`. If an interface ID is
    provided, only that interface is refreshed.

    Args:
        interface_id: ID of a specific interface to refresh.
        log: Logger for all log messages.
    """

    if interface_id is None:
        SonarrInterfaces.refresh_all(
            get_preferences().sonarr_argument_groups, log=log
        )
    else:
        interface_args = get_preferences().sonarr_args[interface_id]
        SonarrInterfaces.refresh(interface_id, interface_args, log=log)


def get_all_sonarr_interfaces() -> InterfaceGroup[int, SonarrInterface]:
    """
    Dependency to get all interfaces to Sonarr.

    Returns:
        Global `InterfaceGroup` of `SonarrInterface` objects.
    """

    for interface_id, interface_args in get_preferences().sonarr_args.items():
        if interface_args['enabled'] and not SonarrInterfaces[interface_id]:
            try:
                refresh_sonarr_interfaces(interface_id)
            except Exception as exc:
                log.exception(f'Error connecting to Sonarr[{interface_id}]',exc)

    return SonarrInterfaces


def get_sonarr_interface(
        interface_id: int = Query(...),
    ) -> Optional[SonarrInterface]:
    """
    Dependency to get the `SonarrInterface` with the given ID. This adds
    `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `SonarrInterface` with the given ID as defined in the global
        `InterfaceGroup`. If the interface is disabled, undefined, or
        otherwise cannot be communicated with, then None is returned.
    """

    return _get_interface(
        SonarrInterfaces, interface_id, 'sonarr', refresh_sonarr_interfaces,
        required=False,
    )


def require_sonarr_interface(interface_id: int = Query(...)) -> SonarrInterface:
    """
    Dependency to get the `SonarrInterface` with the given ID. This adds
    `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `SonarrInterface` with the given ID as defined in the global
        `InterfaceGroup`.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
        HTTPException (409): The interface with the given ID is disabled.
    """

    return _get_interface(
        SonarrInterfaces, interface_id, 'sonarr', refresh_sonarr_interfaces,
        required=True,
    )


def refresh_tmdb_interface(*, log: Logger = log) -> None:
    """
    Refresh the global interface to TMDb. This reinitializes and
    overrides the object.

    Args:
        log: Logger for all log messages.
    """

    global TMDbInterfaceLocal
    TMDbInterfaceLocal = TMDbInterface(
        **get_preferences().tmdb_arguments, log=log
    )


def get_tmdb_interface() -> Optional[TMDbInterface]:
    """
    Dependency to get the global interface to TMDb. This refreshes the
    connection if it is enabled but not initialized.

    Returns:
        Global TMDbInterface.
    """

    if get_preferences().use_tmdb and not TMDbInterfaceLocal:
        try:
            refresh_tmdb_interface()
        except Exception as e:
            log.exception(f'Error connecting to TMDb', e)

    return TMDbInterfaceLocal


def require_tmdb_interface() -> TMDbInterface:
    """
    Dependency to get the global `TMDbInterface`.

    Returns:
        Globally defined `TMDbInterface`.

    Raises:
        HTTPException (409): TMDb is disabled.
        HTTPException (400): TMDb cannot be communicated with.
    """

    # Interface is disabled, raise 409
    if not get_preferences().use_tmdb:
        raise HTTPException(
            status_code=409,
            detail='TMDb is disabled'
        )

    # Interface is enabled but not active, refresh
    if not TMDbInterfaceLocal:
        try:
            refresh_tmdb_interface()
        except Exception as exc:
            log.exception('Error connecting to TMDb', exc)
            raise HTTPException(
                status_code=400,
                detail='Error connecting to TMDb',
            ) from exc

    return TMDbInterfaceLocal
