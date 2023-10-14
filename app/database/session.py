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
from thefuzz.fuzz import partial_ratio

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

# URL of the SQL Database - based on whether in Docker or not
SQLALCHEMY_DATABASE_URL = 'sqlite:///./config/db.sqlite'
if IS_DOCKER:
    SQLALCHEMY_DATABASE_URL = 'sqlite:////config/db.sqlite'
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False},
)

# URL to the Blueprints SQL database
BLUEPRINT_SQL_DATABASE_URL = 'sqlite:///./modules/.objects/blueprints.db'
if IS_DOCKER:
    BLUEPRINT_SQL_DATABASE_URL = 'sqlite:////maker/modules/.objects/blueprints.db'
blueprint_engine = create_engine(
    BLUEPRINT_SQL_DATABASE_URL, connect_args={'check_same_thread': False},
)


def backup_data(*, log: Logger = log) -> tuple[Path, Path]:
    """
    Perform a backup of the SQL database and global preferences.

    Args:
        log: Logger for all log messages.

    Returns:
        Tuple of Paths to created preferences and database backup files.
    """

    # Determine file to back up database to
    BACKUP_DT_FORMAT = '%Y.%m.%d_%H.%M.%S'
    now = datetime.now().strftime(BACKUP_DT_FORMAT)
    if IS_DOCKER:
        config = Path('/config/config.pickle')
        config_backup = Path(f'/config/backups/config.pickle.{now}')
        database = Path('/config/db.sqlite')
        database_backup = Path(f'/config/backups/db.sqlite.{now}')
    else:
        config = Path('./config/config.pickle')
        config_backup = Path(f'./config/backups/config.pickle.{now}')
        database = Path('./config/db.sqlite')
        database_backup = Path(f'./config/backups/db.sqlite.{now}')

    # Remove backups older than 3 weeks
    def delete_old_backup(backup_file: Path, base_filename: str) -> None:
        for prior in backup_file.parent.glob(f'{base_filename}.*'):
            try:
                date = datetime.strptime(
                    prior.name, f'{base_filename}.{BACKUP_DT_FORMAT}'
                )
            except ValueError:
                log.warning(f'Cannot identify date of backup file "{prior}"')
                continue

            if date < datetime.now() - timedelta(weeks=3):
                prior.unlink(missing_ok=True)
                log.debug(f'Deleted old backup "{prior}"')

    delete_old_backup(config_backup, 'config.pickle')
    delete_old_backup(database_backup, 'db.sqlite')

    # Backup config
    if config.exists():
        config_backup.parent.mkdir(exist_ok=True, parents=True)
        file_copy(config, config_backup)
        log.info(f'Performed settings backup')

    # Backup database
    if database.exists():
        database_backup.parent.mkdir(exist_ok=True, parents=True)
        file_copy(database, database_backup)
        log.info(f'Performed database backup')

    return config_backup, database_backup


"""
Register a custom Regex replacement function that can be used on this
database.
"""

@listens_for(engine, 'connect')
def register_custom_functions(
        dbapi_connection,
        connection_record, # pylint: disable=unused-argument
    ) -> None:
    """
    When the engine is connected, register the regex replacement
    function (`re_sub`) as `regex_replace`, as well as the
    `partial_ratio` fuzzy-string match function.
    """
    dbapi_connection.create_function('regex_replace', 3, re_sub)
    dbapi_connection.create_function('partial_ratio', 2, partial_ratio)
@listens_for(blueprint_engine, 'connect')
def register_custom_functions_blueprints(
        dbapi_connection,
        connection_record, # pylint: disable=unused-argument
    ) -> None:
    """When the engine is connected, register the `regex_replace` function"""
    dbapi_connection.create_function('regex_replace', 3, re_sub)


# Session maker for connecting to each database
SessionLocal = sessionmaker(
    bind=engine, expire_on_commit=False, autocommit=False, autoflush=False,
)
Base = declarative_base()
BlueprintSessionMaker = sessionmaker(bind=blueprint_engine)
BlueprintBase = declarative_base()

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
