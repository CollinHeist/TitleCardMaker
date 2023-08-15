from logging import Logger
from typing import Iterator, Optional

from apscheduler.schedulers.background import BackgroundScheduler
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

    preferences = get_preferences()
    global EmbyInterfaceLocal
    EmbyInterfaceLocal = EmbyInterface(**preferences.emby_arguments, log=log)


def get_emby_interface() -> EmbyInterface:
    """
    Dependency to get the global interface to Emby. This refreshes the
    connection if it is enabled but not initialized.

    Returns:
        Global EmbyInterface.
    """

    preferences = get_preferences()
    if preferences.use_emby and not EmbyInterfaceLocal:
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

    preferences = get_preferences()
    global ImageMagickInterfaceLocal
    ImageMagickInterfaceLocal = ImageMagickInterface(
        **preferences.imagemagick_arguments,
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

    preferences = get_preferences()
    global JellyfinInterfaceLocal
    JellyfinInterfaceLocal = JellyfinInterface(
        **preferences.jellyfin_arguments, log=log
    )


def get_jellyfin_interface() -> JellyfinInterface:
    """
    Dependency to get the global interface to Jellyfin. This refreshes
    the connection if it is enabled but not initialized.

    Returns:
        Global JellyfinInterface.
    """

    preferences = get_preferences()
    if preferences.use_jellyfin and not JellyfinInterfaceLocal:
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

    preferences = get_preferences()
    global PlexInterfaceLocal
    PlexInterfaceLocal = PlexInterface(**preferences.plex_arguments, log=log)


def get_plex_interface() -> PlexInterface:
    """
    Dependency to get the global interface to Plex. This refreshes the
    connection if it is enabled but not initialized.

    Returns:
        Global PlexInterface.
    """

    preferences = get_preferences()
    if preferences.use_plex and not PlexInterfaceLocal:
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
        SonarrInterfaces.refresh_all(get_preferences().sonarr_args, log=log)
    else:
        interface_args = get_preferences().sonarr_args[interface_id]
        SonarrInterfaces.refresh(interface_id, interface_args, log=log)


def get_sonarr_interfaces() -> InterfaceGroup[int, SonarrInterface]:
    """
    Dependency to get all interfaces to Sonarr. This refreshes the
    connections if Sonarr is enabled but any interfaces are not
    initialized.

    Returns:
        Global InterfaceGroup for SonarrInterfaces.
    """

    preferences = get_preferences()
    if preferences.use_sonarr and not SonarrInterfaces:
        try:
            refresh_sonarr_interfaces()
        except Exception as exc:
            log.exception(f'Error connecting to Sonarr', exc)

    return SonarrInterfaces


def get_sonarr_interface() -> SonarrInterface:
    """
    Dependency to get the global interface to Sonarr. This refreshes the
    connection if it is enabled but not initialized.

    Returns:
        Global SonarrInterface.
    """

    preferences = get_preferences()
    if preferences.use_sonarr and not SonarrInterfaceLocal:
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

    preferences = get_preferences()
    global TMDbInterfaceLocal
    TMDbInterfaceLocal = TMDbInterface(**preferences.tmdb_arguments, log=log)


def get_tmdb_interface() -> TMDbInterface:
    """
    Dependency to get the global interface to TMDb. This refreshes the
    connection if it is enabled but not initialized.

    Returns:
        Global TMDbInterface.
    """

    preferences = get_preferences()
    if preferences.use_tmdb and not TMDbInterfaceLocal:
        try:
            refresh_tmdb_interface()
        except Exception as e:
            log.exception(f'Error connecting to TMDb', e)

    return TMDbInterfaceLocal
