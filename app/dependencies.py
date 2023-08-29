from logging import Logger
from typing import Iterator, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import (
    EmbyInterfaceLocal, ImageMagickInterfaceLocal, JellyfinInterfaceLocal,
    PreferencesLocal, PlexInterfaceLocal, Scheduler, SessionLocal,
    SonarrInterfaceLocal, TMDbInterfaceLocal,
    SonarrInterfaces,
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


# pylint: disable=global-statement
def refresh_emby_interface(*, log: Logger = log) -> None:
    """
    Refresh the global interface to Emby. This reinitializes and
    overrides the object.

    Args:
        log: (Keyword) Logger for all log messages.
    """

    global EmbyInterfaceLocal
    EmbyInterfaceLocal = EmbyInterface(
        **get_preferences().emby_arguments, log=log
    )


def get_emby_interface() -> EmbyInterface:
    """
    Dependency to get the global interface to Emby. This refreshes the
    connection if it is enabled but not initialized.

    Returns:
        Global EmbyInterface.
    """

    if get_preferences().use_emby and not EmbyInterfaceLocal:
        try:
            refresh_emby_interface()
        except Exception as e:
            log.exception(f'Error connecting to Emby', e)

    return EmbyInterfaceLocal


def refresh_imagemagick_interface() -> None:
    """
    Refresh the global interface to ImageMagick. This reinitializes and
    overrides the object.

    Args:
        log: (Keyword) Logger for all log messages.
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


def refresh_jellyfin_interface(*, log: Logger = log) -> JellyfinInterface:
    """
    Refresh the global interface to Jellyfin. This reinitializes and
    overrides the object.

    Args:
        log: (Keyword) Logger for all log messages.
    """

    global JellyfinInterfaceLocal
    JellyfinInterfaceLocal = JellyfinInterface(
        **get_preferences().jellyfin_arguments, log=log
    )


def get_jellyfin_interface() -> JellyfinInterface:
    """
    Dependency to get the global interface to Jellyfin. This refreshes
    the connection if it is enabled but not initialized.

    Returns:
        Global JellyfinInterface.
    """

    if get_preferences().use_jellyfin and not JellyfinInterfaceLocal:
        try:
            refresh_jellyfin_interface()
        except Exception as e:
            log.exception(f'Error connecting to Jellyfin', e)

    return JellyfinInterfaceLocal


def refresh_plex_interface(*, log: Logger = log) -> None:
    """
    Refresh the global interface to Plex. This reinitializes and
    overrides the object.

    Args:
        log: (Keyword) Logger for all log messages.
    """

    global PlexInterfaceLocal
    PlexInterfaceLocal = PlexInterface(
        **get_preferences().plex_arguments, log=log
    )


def get_plex_interface() -> PlexInterface:
    """
    Dependency to get the global interface to Plex. This refreshes the
    connection if it is enabled but not initialized.

    Returns:
        Global PlexInterface.
    """

    if get_preferences().use_plex and not PlexInterfaceLocal:
        try:
            refresh_plex_interface()
        except Exception as e:
            log.exception(f'Error connecting to Plex', e)

    return PlexInterfaceLocal


def refresh_sonarr_interface(*, log: Logger = log) -> None:
    """
    Refresh the global interface to Sonarr. This reinitializes and
    overrides the object.

    Args:
        log: (Keyword) Logger for all log messages.
    """

    global SonarrInterfaceLocal
    SonarrInterface.REQUEST_TIMEOUT = 15
    SonarrInterfaceLocal = SonarrInterface(
        **get_preferences().sonarr_arguments, log=log
    )
    SonarrInterface.REQUEST_TIMEOUT = 600


def refresh_sonarr_interfaces(
        interface_id: Optional[int] = None,
        *,
        log: Logger = log,
    ) -> None:
    """
    Refresh the global Sonarr `InterfaceGroup`.

    Args:
        log: (Keyword) Logger for all log messages.
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
    Dependency to get all interfaces to Sonarr. This refreshes the
    connections if Sonarr is enabled but any interfaces are not
    initialized.

    Returns:
        Global InterfaceGroup for SonarrInterfaces.
    """

    for interface_id, interface_args in get_preferences().sonarr_args.items():
        if interface_args['enabled'] and not SonarrInterfaces[interface_id]:
            try:
                refresh_sonarr_interfaces(interface_id)
            except Exception as exc:
                log.exception(f'Error connecting to Sonarr[{interface_id}]',exc)

    return SonarrInterfaces


def get_sonarr_interface2(
        interface_id: int = Query(...),
    ) -> Optional[SonarrInterface]:
    """
    Dependency to get the SonarrInterface with the given ID. This adds
    the `interface_id` Query parameter for the 
    """

    if (args := get_preferences().sonarr_args.get(interface_id)) is None:
        return None

    if not args['enabled']:
        return None

    if not SonarrInterfaces[interface_id]:
        try:
            refresh_sonarr_interfaces(interface_id)
        except Exception as exc:
            log.exception(f'Error connecting to Sonarr[{interface_id}]', exc)
            return None

    return SonarrInterfaces[interface_id]


def require_sonarr_interface(interface_id: int = Query(...)) -> SonarrInterface:
    """
    Dependency to get the SonarrInterface with a given ID. This adds the
    `interface_id` Query paramater, and will raise an HTTPException if
    the interface cannot be communicated with or is disabled.
    """
    print(f'require_sonarr_interface({interface_id})')
    if (args := get_preferences().sonarr_args.get(interface_id)) is None:
        raise HTTPException(
            status_code=409,
            detail=f'No Sonarr connection with ID {interface_id}'
        )

    if not args['enabled']:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with Sonarr[{interface_id}]'
        )

    if not SonarrInterfaces[interface_id]:
        try:
            refresh_sonarr_interfaces(interface_id)
        except Exception as exc:
            log.exception(f'Error connecting to Sonarr[{interface_id}]', exc)
            raise HTTPException(
                status_code=400,
                detail=f'Error connecting to Sonarr[{interface_id}]'
            ) from exc

    return SonarrInterfaces[interface_id]


def get_sonarr_interface() -> Optional[SonarrInterface]:
    """
    Dependency to get the global interface to Sonarr. This refreshes the
    connection if it is enabled but not initialized.

    Returns:
        Global SonarrInterface.
    """

    if get_preferences().use_sonarr and not SonarrInterfaceLocal:
        try:
            refresh_sonarr_interface()
        except Exception as e:
            log.exception(f'Error connecting to Sonarr', e)

    return SonarrInterfaceLocal


def refresh_tmdb_interface(*, log: Logger = log) -> None:
    """
    Refresh the global interface to TMDb. This reinitializes and
    overrides the object.

    Args:
        log: (Keyword) Logger for all log messages.
    """

    global TMDbInterfaceLocal
    TMDbInterfaceLocal = TMDbInterface(
        **get_preferences().tmdb_arguments, log=log
    )


def get_tmdb_interface() -> TMDbInterface:
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
