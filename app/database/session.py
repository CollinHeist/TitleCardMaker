from datetime import datetime, timedelta
from logging import Logger
from os import environ
from pathlib import Path
from re import sub as re_sub
from shutil import copy as file_copy

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from fastapi_pagination import Page
from pydantic import Field
from sqlalchemy import create_engine
from sqlalchemy.event import listens_for
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.models.preferences import Preferences

from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.ImageMagickInterface import ImageMagickInterface
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface

# Whether a Docker execution or not
IS_DOCKER = environ.get('TCM_IS_DOCKER', 'false').lower() == 'true'

# Get URL of the SQL Database - based on whether in Docker or not
SQLALCHEMY_DATABASE_URL = 'sqlite:///./config/db.sqlite'
if IS_DOCKER:
    SQLALCHEMY_DATABASE_URL = 'sqlite:////config/db.sqlite'
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
)


def backup_database(*, log: Logger = log) -> Path:
    """
    Perform a backup of the SQL database.

    Args:
        log: (Keyword) Logger for all log messages.

    Returns:
        Path to the newly created backup file.
    """

    # Determine file to back up database to
    BACKUP_DT_FORMAT = '%Y.%m.%d_%H.%M.%S'
    now = datetime.now().strftime(BACKUP_DT_FORMAT)
    if IS_DOCKER:
        database = Path('/config/db.sqlite')
        backup_file = Path(f'/config/backups/db.sqlite.{now}')
    else:
        database = Path('./config/db.sqlite')
        backup_file = Path(f'./backups/db.sqlite.{now}')

    # Remove databases older than 4 weeks
    for prior_backup in backup_file.parent.glob('db.sqlite.*'):
        try:
            date = datetime.strptime(
                prior_backup.name, f'db.sqlite.{BACKUP_DT_FORMAT}'
            )
        except ValueError:
            log.warning(f'Cannot identify date of backup file "{prior_backup}"')
            continue

        if date < datetime.now() - timedelta(weeks=4):
            prior_backup.unlink(missing_ok=True)
            log.debug(f'Deleted old database backup file "{prior_backup}"')

    # Backup database
    if database.exists():
        backup_file.parent.mkdir(exist_ok=True, parents=True)
        file_copy(database, backup_file)
        log.info(f'Performed database backup')

    return backup_file


"""
Register a custom Regex replacement function that can be used on this
database.
"""
def regex_replace(pattern, replacement, string):
    """Wrapper for `re_sub()`"""
    return re_sub(pattern, replacement, string)

@listens_for(engine, 'connect')
def register_custom_functions(
        dbapi_connection,
        connection_record, # pylint: disable=unused-argument
    ) -> None:
    """When the engine is connected, register the `regex_replace` function"""
    dbapi_connection.create_function('regex_replace', 3, regex_replace)


SessionLocal = sessionmaker(
    bind=engine, expire_on_commit=False, autocommit=False, autoflush=False,
)
Base = declarative_base()

# Scheduler
Scheduler = BackgroundScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URL, engine=engine)
    }, executors={'default': ThreadPoolExecutor(20)},
    job_defaults={'coalesce': True, 'misfire_grace_time': 60 * 10},
    misfire_grace_time=600,
)

# Config file/object
preferences_file =\
    Path(__file__).parent.parent.parent / 'config' / 'config.pickle'
if IS_DOCKER:
    preferences_file = Path('/config/config.pickle')
PreferencesLocal = Preferences(preferences_file)


# Default Page arguments used for paginated returns
Page = Page.with_custom_options(size=Field(250, ge=1))


# Initialize all interfaces
ImageMagickInterfaceLocal = None
try:
    ImageMagickInterfaceLocal = ImageMagickInterface(
        **PreferencesLocal.imagemagick_arguments
    )
except Exception as e:
    pass

EmbyInterfaceLocal = None
if PreferencesLocal.use_emby:
    try:
        EmbyInterfaceLocal = EmbyInterface(**PreferencesLocal.emby_arguments)
    except Exception as e:
        pass

JellyfinInterfaceLocal = None
if PreferencesLocal.use_jellyfin:
    try:
        JellyfinInterfaceLocal = JellyfinInterface(
            **PreferencesLocal.jellyfin_arguments
        )
    except Exception as e:
        pass

PlexInterfaceLocal = None
if PreferencesLocal.use_plex:
    try:
        PlexInterfaceLocal = PlexInterface(**PreferencesLocal.plex_arguments)
    except Exception as e:
        pass

SonarrInterfaceLocal = None
if PreferencesLocal.use_sonarr:
    try:
        SonarrInterfaceLocal.REQUEST_TIMEOUT = 15
        SonarrInterfaceLocal = SonarrInterface(
            **PreferencesLocal.sonarr_arguments
        )
        SonarrInterfaceLocal.REQUEST_TIMEOUT = 600
    except Exception as e:
        pass

TMDbInterfaceLocal = None
if PreferencesLocal.use_tmdb:
    try:
        TMDbInterfaceLocal = TMDbInterface(**PreferencesLocal.tmdb_arguments)
    except Exception as e:
        pass
