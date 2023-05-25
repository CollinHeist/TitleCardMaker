from typing import Generator

from app.database.session import (
    EmbyInterfaceLocal, ImageMagickInterfaceLocal, JellyfinInterfaceLocal,
    PreferencesLocal, PlexInterfaceLocal, Scheduler, SessionLocal,
    SonarrInterfaceLocal, TMDbInterfaceLocal
)
from modules.EmbyInterface2 import EmbyInterface
from modules.ImageMagickInterface import ImageMagickInterface
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface

def get_database() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_scheduler() -> 'BackgroundScheduler':
    return Scheduler

def get_preferences() -> 'Preferences':
    return PreferencesLocal

def get_emby_interface() -> EmbyInterface:
    return EmbyInterfaceLocal

def refresh_emby_interface() -> None:
    preferences = get_preferences()
    global EmbyInterfaceLocal
    EmbyInterfaceLocal = EmbyInterface(**preferences.emby_arguments)

def get_imagemagick_interface() -> ImageMagickInterface:
    return ImageMagickInterfaceLocal

def refresh_imagemagick_interface() -> None:
    preferences = get_preferences()
    global ImageMagickInterfaceLocal
    ImageMagickInterfaceLocal = ImageMagickInterface(
        **preferences.imagemagick_arguments
    )

def get_jellyfin_interface() -> JellyfinInterface:
    return JellyfinInterfaceLocal

def refresh_jellyfin_interface() -> JellyfinInterface:
    preferences = get_preferences()
    global JellyfinInterfaceLocal
    JellyfinInterfaceLocal = JellyfinInterface(**preferences.jellyfin_arguments)

def get_plex_interface() -> PlexInterface:
    return PlexInterfaceLocal

def refresh_plex_interface() -> None:
    preferences = get_preferences()
    global PlexInterfaceLocal
    PlexInterfaceLocal = PlexInterface(**preferences.plex_arguments)

def get_sonarr_interface() -> SonarrInterface:
    return SonarrInterfaceLocal

def refresh_sonarr_interface() -> None:
    preferences = get_preferences()
    global SonarrInterfaceLocal
    SonarrInterfaceLocal = SonarrInterface(**preferences.sonarr_arguments)

def get_tmdb_interface() -> TMDbInterface:
    return TMDbInterfaceLocal

def refresh_tmdb_interface() -> None:
    preferences = get_preferences()
    global TMDbInterfaceLocal
    TMDbInterfaceLocal = TMDbInterface(**preferences.tmdb_arguments)