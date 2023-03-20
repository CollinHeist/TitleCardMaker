from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.models.preferences import Preferences
from modules.EmbyInterface import EmbyInterface
from modules.JellyfinInterface import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface

SQLALCHEMY_DATABASE_URL = 'sqlite:///./db.sqlite'
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

if (file := Path('/mnt/user/Media/TitleCardMaker/app/prefs.json')).exists():
    from pickle import load 
    with file.open('rb') as fh:
        PreferencesLocal = load(fh)
else:
    PreferencesLocal = Preferences()

EmbyInterfaceLocal = None
if PreferencesLocal.use_emby:
    try:
        EmbyInterfaceLocal = EmbyInterface(
            PreferencesLocal.emby_url,
            PreferencesLocal.emby_api_key,
            PreferencesLocal.emby_username,
            PreferencesLocal.emby_use_ssl,
            PreferencesLocal.emby_filesize_limit,
        )
    except Exception as e:
        ...

JellyfinInterfaceLocal = None
if PreferencesLocal.use_jellyfin:
    try:
        JellyfinInterfaceLocal = JellyfinInterface(
            PreferencesLocal.jellyfin_url,
            PreferencesLocal.jellyfin_api_key,
            PreferencesLocal.jellyfin_username,
            PreferencesLocal.jellyfin_use_ssl,
            PreferencesLocal.jellyfin_filesize_limit,
        )
    except Exception as e:
        ...

PlexInterfaceLocal = None
if PreferencesLocal.use_plex:
    try:
        PlexInterfaceLocal = PlexInterface(
            PreferencesLocal.plex_url,
            PreferencesLocal.plex_token,
            PreferencesLocal.plex_use_ssl, 
            PreferencesLocal.plex_integrate_with_pmm,
            PreferencesLocal.plex_filesize_limit,
        )
    except Exception:
        ...

SonarrInterfaceLocal = None
if PreferencesLocal.use_sonarr:
    SonarrInterfaceLocal = SonarrInterface(
        PreferencesLocal.sonarr_url,
        PreferencesLocal.sonarr_api_key,
        PreferencesLocal.plex_use_ssl,
    )

TMDbInterfaceLocal = None
if PreferencesLocal.use_tmdb:
    TMDbInterfaceLocal = TMDbInterface(
        PreferencesLocal.tmdb_api_key,
    )