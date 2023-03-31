from typing import Generator

from app.database.session import (
    EmbyInterfaceLocal, JellyfinInterfaceLocal, PreferencesLocal,
    PlexInterfaceLocal, Scheduler, SessionLocal, SonarrInterfaceLocal,
    TMDbInterfaceLocal
)

def get_database() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_preferences() -> 'Preferences':
    return PreferencesLocal

def get_emby_interface() -> 'EmbyInterface':
    return EmbyInterfaceLocal

def get_jellyfin_interface() -> 'JellyfinInterface':
    return JellyfinInterfaceLocal

def get_plex_interface() -> 'PlexInterface':
    return PlexInterfaceLocal

def get_sonarr_interface() -> 'SonarrInterface':
    return SonarrInterfaceLocal

def get_tmdb_interface() -> 'TMDbInterface':
    return TMDbInterfaceLocal

def get_scheduler() -> 'BackgroundScheduler':
    return Scheduler