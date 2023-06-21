from os import environ
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from fastapi_pagination import Page
from pydantic import Field
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.models.preferences import Preferences
from modules.EmbyInterface2 import EmbyInterface
from modules.ImageMagickInterface import ImageMagickInterface
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface

# Whether a Docker execution or not
IS_DOCKER = environ.get('TCM_IS_DOCKER', 'false').lower() == 'true'

# Get URL of the SQL Database - based on whether in Docker or not
SQLALCHEMY_DATABASE_URL = 'sqlite:///./db.sqlite'
if IS_DOCKER:
    SQLALCHEMY_DATABASE_URL = 'sqlite:////config/source/db.sqlite'
else:
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
    job_defaults={'coalesce': True, 'misfire_grace_time': 600},
    misfire_grace_time=600,
)

# Preference file/object
if IS_DOCKER:
    preferences_file = Path('/config/.objects/prefs.json')
else:
    preferences_file = Path(__file__).parent.parent.parent / 'modules' / '.objects' / 'prefs.json'
PreferencesLocal = Preferences(preferences_file)

# Page used for all paginated returns
Page = Page.with_custom_options(
    size=Field(250, ge=1),
)

# Initialize all interfaces
ImageMagickInterfaceLocal = None
try:
    ImageMagickInterfaceLocal = ImageMagickInterface(
        **PreferencesLocal.imagemagick_arguments
    )
except Exception as e:
    ...

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
        SonarrInterfaceLocal.REQUEST_TIMEOUT = 15
        SonarrInterfaceLocal = SonarrInterface(
            **PreferencesLocal.sonarr_arguments
        )
        SonarrInterfaceLocal.REQUEST_TIMEOUT = 600
    except Exception as e:
        ...

TMDbInterfaceLocal = None
if PreferencesLocal.use_tmdb:
    try:
        TMDbInterfaceLocal = TMDbInterface(**PreferencesLocal.tmdb_arguments)
    except Exception as e:
        ...