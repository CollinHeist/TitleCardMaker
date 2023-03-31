from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.models.preferences import Preferences
from modules.EmbyInterface2 import EmbyInterface
from modules.JellyfinInterface import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface

# SQL Database
SQLALCHEMY_DATABASE_URL = 'sqlite:///./db.sqlite'
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Scheduler
Scheduler = BackgroundScheduler(
    jobstores={'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URL)},
    executors={'default': ThreadPoolExecutor(20)},
    job_defaults={'coalesce': True},
)
Scheduler.start()

# Preference file/object

if (file := Path('/mnt/user/Media/TitleCardMaker/app/prefs.json')).exists():
    from pickle import load 
    with file.open('rb') as fh:
        PreferencesLocal = load(fh)
else:
    PreferencesLocal = Preferences()

# Interfaces

EmbyInterfaceLocal = None
if PreferencesLocal.use_emby:
    try:
        EmbyInterfaceLocal = EmbyInterface(**PreferencesLocal.emby_arguments)
    except Exception as e:
        ...

JellyfinInterfaceLocal = None
if PreferencesLocal.use_jellyfin:
    try:
        JellyfinInterfaceLocal = JellyfinInterface(
            **PreferencesLocal.jellyfin_arguments
        )
    except Exception as e:
        ...

PlexInterfaceLocal = None
if PreferencesLocal.use_plex:
    try:
        PlexInterfaceLocal = PlexInterface(**PreferencesLocal.plex_arguments)
    except Exception as e:
        ...

SonarrInterfaceLocal = None
if PreferencesLocal.use_sonarr:
    try:
        SonarrInterfaceLocal = SonarrInterface(
            **PreferencesLocal.sonarr_arguments
        )
    except Exception as e:
        ...

TMDbInterfaceLocal = None
if PreferencesLocal.use_tmdb:
    try:
        TMDbInterfaceLocal = TMDbInterface(**PreferencesLocal.tmdb_arguments)
    except Exception as e:
        ...