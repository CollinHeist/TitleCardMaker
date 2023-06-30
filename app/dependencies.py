from typing import Iterator

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.database.session import (
    EmbyInterfaceLocal, ImageMagickInterfaceLocal, JellyfinInterfaceLocal,
    PreferencesLocal, PlexInterfaceLocal, Scheduler, SessionLocal,
    SonarrInterfaceLocal, TMDbInterfaceLocal
)
from app.models.preferences import Preferences

from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.ImageMagickInterface import ImageMagickInterface
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface

"""
Miscellaneous global dependencies
"""
def get_database() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_scheduler() -> BackgroundScheduler:
    return Scheduler

def get_preferences() -> Preferences:
    return PreferencesLocal

"""
Emby interface
"""
def refresh_emby_interface() -> None:
    preferences = get_preferences()
    global EmbyInterfaceLocal
    EmbyInterfaceLocal = EmbyInterface(**preferences.emby_arguments)

def get_emby_interface() -> EmbyInterface:
    preferences = get_preferences()
    if preferences.use_emby and not EmbyInterfaceLocal:
        try:
            refresh_emby_interface()
        except Exception as e:
            log.exception(f'Error connecting to Emby', e)

    return EmbyInterfaceLocal

"""
ImageMagick interface
"""
def refresh_imagemagick_interface() -> None:
    preferences = get_preferences()
    global ImageMagickInterfaceLocal
    ImageMagickInterfaceLocal = ImageMagickInterface(
        **preferences.imagemagick_arguments
    )

def get_imagemagick_interface() -> ImageMagickInterface:
    return ImageMagickInterfaceLocal

"""
JellyFin interface
"""

def refresh_jellyfin_interface() -> JellyfinInterface:
    preferences = get_preferences()
    global JellyfinInterfaceLocal
    JellyfinInterfaceLocal = JellyfinInterface(**preferences.jellyfin_arguments)

def get_jellyfin_interface() -> JellyfinInterface:
    preferences = get_preferences()
    if preferences.use_jellyfin and not JellyfinInterfaceLocal:
        try:
            refresh_jellyfin_interface()
        except Exception as e:
            log.exception(f'Error connecting to Jellyfin', e)

    return JellyfinInterfaceLocal

"""
Plex interface
"""

def refresh_plex_interface() -> None:
    preferences = get_preferences()
    global PlexInterfaceLocal
    PlexInterfaceLocal = PlexInterface(**preferences.plex_arguments)

def get_plex_interface() -> PlexInterface:
    preferences = get_preferences()
    if preferences.use_plex and not PlexInterfaceLocal:
        try:
            refresh_plex_interface()
        except Exception as e:
            log.exception(f'Error connecting to Plex', e)

    return PlexInterfaceLocal

"""
Sonarr interface
"""

def refresh_sonarr_interface() -> None:
    preferences = get_preferences()
    global SonarrInterfaceLocal
    SonarrInterface.REQUEST_TIMEOUT = 15
    SonarrInterfaceLocal = SonarrInterface(**preferences.sonarr_arguments)
    SonarrInterface.REQUEST_TIMEOUT = 600

def get_sonarr_interface() -> SonarrInterface:
    preferences = get_preferences()
    if preferences.use_sonarr and not SonarrInterfaceLocal:
        try:
            refresh_sonarr_interface()
        except Exception as e:
            log.exception(f'Error connecting to Sonarr', e)

    return SonarrInterfaceLocal

"""
TMDb interface
"""

def refresh_tmdb_interface() -> None:
    preferences = get_preferences()
    global TMDbInterfaceLocal
    TMDbInterfaceLocal = TMDbInterface(**preferences.tmdb_arguments)

def get_tmdb_interface() -> TMDbInterface:
    preferences = get_preferences()
    if preferences.use_tmdb and not TMDbInterfaceLocal:
        try:
            refresh_tmdb_interface()
        except Exception as e:
            log.exception(f'Error connecting to TMDb', e)

    return TMDbInterfaceLocal