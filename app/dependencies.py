from datetime import datetime, timedelta
from logging import Logger
from typing import Any, Iterator, Optional, Union

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import HTTPException, Query, Request
from requests import get
from sqlalchemy.orm import Session

from app.database.session import (
    BlueprintSessionMaker, EmbyInterfaces, ImageMagickInterfaceLocal,
    JellyfinInterfaces, PreferencesLocal, Scheduler, SessionLocal,
    TMDbInterfaces, PlexInterfaces, SonarrInterfaces
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


__all__ = [
    'Preferences', 'Session', 'EmbyInterface', 'ImageMagickInterface',
    'InterfaceGroup',  'JellyfinInterface', 'PlexInterface', 'SonarrInterface',
    'TMDbInterface', 'get_database', 'get_blueprint_database', 'get_scheduler',
    'get_preferences', 'get_emby_interfaces', 'require_emby_interface',
    'refresh_imagemagick_interface', 'get_imagemagick_interface',
    'get_jellyfin_interfaces', 'require_jellyfin_interface',
    'get_plex_interfaces', 'require_plex_interface', 'get_sonarr_interfaces',
    'require_sonarr_interface', 'get_tmdb_interfaces', 'require_tmdb_interface',
    'require_interface',
]


"""Type for any generic interface"""
AnyInterface = Union[
    EmbyInterface, JellyfinInterface, PlexInterface, SonarrInterface,
    TMDbInterface
]

"""Where to download the Blueprint SQL Database from"""
BLUEPRINT_DATABASE_URL =\
    'https://github.com/CollinHeist/TCM-Blueprints-v2/raw/master/blueprints.db'
"""Where to read/write the Blueprint SQL database file"""
BLUEPRINT_DATABASE_FILE = Preferences.TEMPORARY_DIRECTORY / 'blueprints.db'


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


def download_blueprint_database(*, log: Logger = log) -> None:
    """
    Download the Blueprint SQL database from the GitHub repository.

    Args:
        log: Logger for all log messages.
    """

    response = get(BLUEPRINT_DATABASE_URL, timeout=30)

    # If no file was found, raise
    if response.status_code == 404:
        log.error(f'No blueprint database file found at "{BLUEPRINT_DATABASE_URL}"')
        raise HTTPException(
            status_code=404,
            detail=f'No Blueprint database file found',
        )

    # Non-404 error, raise
    if not response.ok:
        raise HTTPException(
            status_code=response.status_code,
            detail=f'Error downloading Blueprint database',
        )

    # Write database to file
    BLUEPRINT_DATABASE_FILE.parent.mkdir(exist_ok=True, parents=True)
    BLUEPRINT_DATABASE_FILE.write_bytes(response.content)


_db_expiration = datetime.now()
def get_blueprint_database(
        request: Request,
        refresh_database: bool = Query(default=False),
    ) -> Iterator[Session]:
    """
    Dependency to get a Session to the Blueprint SQLite database.

    Args:
        refresh_database: Query parameter on whether to force a refresh
            of the database.
    
    Yields:
        A Session to the database which is closed afterwards.
    """

    # Get contextual logger
    log = request.state.log

    # If refreshing db, database DNE, or file has expired, re-download
    global _db_expiration # pylint: disable=global-statement
    if (refresh_database
        or not BLUEPRINT_DATABASE_FILE.exists()
        or _db_expiration <= datetime.now()):
        download_blueprint_database()
        log.debug(f'Downloaded Blueprint database')
        _db_expiration = datetime.now() + timedelta(hours=2)

    db = BlueprintSessionMaker()
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


def _require_interface(
        interface_group: InterfaceGroup,
        interface_id: int,
        name: str,
    ) -> Any:
    """
    Dependency to get the interface with the given ID from the given
    `InterfaceGroup`.

    Args:
        interface_group: InterfaceGroup containing all interfaces of
            this connection.
        interface_id: ID of the interface to return.
        name: Name of the connection this interface corresponds to.

    Returns:
        `Interface` object with the given ID.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
    """

    # Get this interface's arguments
    if interface_id not in interface_group:
        raise HTTPException(
            status_code=404,
            detail=f'No {name} Connection with ID {interface_id}'
        )

    # Interface enabled but not active, refresh
    if not interface_group[interface_id]:
        raise HTTPException(
            status_code=400,
            detail=f'Error connecting to {name}[{interface_id}]'
        )

    return interface_group[interface_id]


# pylint: disable=global-statement
def get_emby_interfaces() -> InterfaceGroup[int, EmbyInterface]:
    """
    Dependency to get all interfaces to Emby.

    Returns:
        Global `InterfaceGroup` of `EmbyInterface` objects.
    """

    return EmbyInterfaces


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
    """

    return _require_interface(EmbyInterfaces, interface_id, 'Emby')


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


def get_jellyfin_interfaces() -> InterfaceGroup[int, JellyfinInterface]:
    """
    Dependency to get all interfaces to Jellyfin.

    Returns:
        Global `InterfaceGroup` of `JellyfinInterface` objects.
    """

    return JellyfinInterfaces


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
    """

    return _require_interface(JellyfinInterfaces, interface_id, 'Jellyfn')


def get_plex_interfaces() -> InterfaceGroup[int, PlexInterface]:
    """
    Dependency to get all interfaces to Plex.

    Returns:
        Global `InterfaceGroup` of `PlexInterface` objects.
    """

    return PlexInterfaces


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
    """

    return _require_interface(PlexInterfaces, interface_id, 'Plex')


def get_sonarr_interfaces() -> InterfaceGroup[int, SonarrInterface]:
    """
    Dependency to get all interfaces to Sonarr.

    Returns:
        Global `InterfaceGroup` of `SonarrInterface` objects.
    """

    return SonarrInterfaces


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
    """

    return _require_interface(SonarrInterfaces, interface_id, 'sonarr')


def get_tmdb_interfaces() -> InterfaceGroup[int, TMDbInterface]:
    """
    Dependency to get all interfaces to TMDb.

    Returns:
        Global `InterfaceGroup` of `TMDbInterface` objects.
    """

    return TMDbInterfaces


def require_tmdb_interface(
        interface_id: Optional[int] = Query(default=None)
    ) -> TMDbInterface:
    """
    Dependency to get the `TMDbInterface` with the given ID. This adds
    `interface_id` as a Query parameter. If the parameter is omitted,
    then the first TMDbInterface is used.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `TMDbInterface` with the given ID (or the first one if
        `interface_id` is None) as defined in the global
        `InterfaceGroup`.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
    """

    # If no ID was provided, get the first available TMDb interface
    if interface_id is None:
        for _, interface in TMDbInterfaces:
            return interface

    return _require_interface(TMDbInterfaces, interface_id, 'tmdb')


def require_interface(interface_id: int = Query(...)) -> AnyInterface:
    """
    Dependency to get the interface with the given ID. This adds
    `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        Interface with the given ID as defined in the global
        `InterfaceGroup` for the corresponding type.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
    """

    groups = (
        (EmbyInterfaces, 'Emby'), (JellyfinInterfaces, 'Jellyfin'),
        (PlexInterfaces, 'Plex'), (SonarrInterfaces, 'Sonarr'),
        (TMDbInterfaces, 'TMDb'),
    )

    for interface_group, name in groups:
        try:
            return _require_interface(interface_group, interface_id, name)
        except HTTPException as exc:
            if exc.status_code != 404:
                raise exc

    raise HTTPException(
        status_code=404,
        detail=f'No Connection with ID {interface_id}'
    )
