from datetime import datetime, timedelta
from logging import Logger
from os import environ
from pathlib import Path
from re import IGNORECASE, sub as re_sub, match as _regex_match
from shutil import copy as file_copy
from typing import NamedTuple

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from fastapi_pagination import Page
from pydantic import Field
from sqlalchemy import create_engine
from sqlalchemy.event import listens_for
from sqlalchemy.orm import declarative_base, sessionmaker
from thefuzz.fuzz import partial_token_sort_ratio as partial_ratio # partial_ratio

from app.models.preferences import Preferences

from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.ImageMagickInterface import ImageMagickInterface
from modules.InterfaceGroup import InterfaceGroup
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
    SQLALCHEMY_DATABASE_URL,
    # https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic
    pool_pre_ping=True,
    # https://docs.sqlalchemy.org/en/20/core/pooling.html#pool-disconnects
    connect_args={'check_same_thread': False, 'timeout': 30},
)

# URL to the Blueprints SQL database
BLUEPRINT_SQL_DATABASE_URL = 'sqlite:///./modules/.objects/blueprints.db'
if IS_DOCKER:
    BLUEPRINT_SQL_DATABASE_URL = 'sqlite:////maker/modules/.objects/blueprints.db'
blueprint_engine = create_engine(
    BLUEPRINT_SQL_DATABASE_URL, connect_args={'check_same_thread': False},
)

class DataBackup(NamedTuple): # pylint: disable=missing-class-docstring
    config: Path
    database: Path

def backup_data(*, log: Logger = log) -> DataBackup:
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

    return DataBackup(config=config_backup, database=database_backup)


def restore_backup(backup: DataBackup, /, *, log: Logger = log):
    """
    Restore the config and database from the given data backup.

    Args:
        backup: Tuple of backup data (as returned by `backup_data()`)
            to restore from.
        log: Logger for all log messages.
    """

    # Restore config
    if backup.config.exists():
        if IS_DOCKER:
            file_copy(backup.config, Path('/config/config.pickle'))
        else:
            file_copy(backup.config, Path('./config/config.pickle'))
        log.debug(f'Restored backup from "{backup.config}"')
    else:
        log.warning(f'Cannot restore backup from "{backup.config}"')

    # Restore database
    if backup.database.exists():
        if IS_DOCKER:
            file_copy(backup.database, Path('/config/db.sqlite'))
        else:
            file_copy(backup.database, Path('./config/db.sqlite'))
        log.debug(f'Restored backup from "{backup.database}"')
    else:
        log.warning(f'Cannot restore backup from "{backup.database}"')


"""
Register a custom Regex replacement function that can be used on this
database.
"""
def regex_replace(pattern: str, repl: str, string: str) -> str:
    """Regex replacement function for DB registration"""

    return re_sub(pattern, repl, string, flags=IGNORECASE)

def regex_match(pattern: str, string: str) -> bool:
    """Regex match function for DB registration"""

    return bool(_regex_match(pattern, string, flags=IGNORECASE))

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
    dbapi_connection.create_function('regex_replace', 3, regex_replace)
    dbapi_connection.create_function('regex_match', 2, regex_match)
    dbapi_connection.create_function('partial_ratio', 2, partial_ratio)

@listens_for(blueprint_engine, 'connect')
def register_custom_functions_blueprints(
        dbapi_connection,
        connection_record, # pylint: disable=unused-argument
    ) -> None:
    """When the engine is connected, register the `regex_replace` function"""
    dbapi_connection.create_function('regex_replace', 3, regex_replace)


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
    },
    executors={'default': ThreadPoolExecutor(20)},
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
Page = Page.with_custom_options(size=Field(100, ge=1))


# Initialize all interfaces
ImageMagickInterfaceLocal = None
try:
    ImageMagickInterfaceLocal = ImageMagickInterface(
        **PreferencesLocal.imagemagick_arguments
    )
except Exception:
    pass

EmbyInterfaces: InterfaceGroup[int, EmbyInterface] = InterfaceGroup(EmbyInterface)
JellyfinInterfaces: InterfaceGroup[int, JellyfinInterface] = InterfaceGroup(JellyfinInterface)
PlexInterfaces: InterfaceGroup[int, PlexInterface] = InterfaceGroup(PlexInterface)
SonarrInterfaces: InterfaceGroup[int, SonarrInterface] = InterfaceGroup(SonarrInterface)
TMDbInterfaces: InterfaceGroup[int, TMDbInterface] = InterfaceGroup(TMDbInterface)
