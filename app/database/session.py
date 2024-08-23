from os import environ
from pathlib import Path
from re import IGNORECASE, sub as re_sub, match as _regex_match
from typing import Any, Generator

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from fastapi_pagination import Page
from fastapi_pagination.customization import (
    CustomizedPage,
    UseName,
    UseParamsFields
)
from pydantic import Field
from sqlalchemy import create_engine
from sqlalchemy.event import listens_for
from sqlalchemy.orm import declarative_base, sessionmaker
from thefuzz.fuzz import partial_token_sort_ratio as partial_ratio
from unidecode import unidecode

from app.models.preferences import Preferences
from modules.EmbyInterface2 import EmbyInterface
from modules.ImageMagickInterface import ImageMagickInterface
from modules.InterfaceGroup import InterfaceGroup
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface
from modules.TVDbInterface import TVDbInterface


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
    # echo=True,
)

# URL to the Blueprints SQL database
BLUEPRINT_SQL_DATABASE_URL = 'sqlite:///./modules/.objects/blueprints.db'
if IS_DOCKER:
    BLUEPRINT_SQL_DATABASE_URL = 'sqlite:////maker/modules/.objects/blueprints.db'
blueprint_engine = create_engine(
    BLUEPRINT_SQL_DATABASE_URL, connect_args={'check_same_thread': False},
)

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
    dbapi_connection.create_function(
        'unidecode', 1, lambda s: unidecode(s, errors='preserve')
    )

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

# Create a default __rich_repr__ which all tables subclassing this base
# class can utilize for rich output in Tracebacks
# See https://rich.readthedocs.io/en/stable/pretty.html#rich-repr-protocol
def default_rich_repr(self) -> Generator[tuple[str, Any], None, None]:
    """
    Print key/value pairs of all non-private, non-None items in this
    class.
    """

    for k, v in sorted(self.__dict__.items()):
        if not k.startswith('_'): # Skip private attributes
            yield k, v, None # Assume all defaults are None
Base.__rich_repr__ = default_rich_repr


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
preferences_file = \
    Path(__file__).parent.parent.parent / 'config' / 'config.pickle'
if IS_DOCKER:
    preferences_file = Path('/config/config.pickle')
PreferencesLocal = Preferences(preferences_file)


# Default Page arguments used for paginated returns
Page = CustomizedPage[
    Page,
    UseName('Page'),
    UseParamsFields(size=100),
]


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
TVDbInterfaces: InterfaceGroup[int, TVDbInterface] = InterfaceGroup(TVDbInterface)
