# pylint: skip-file
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

"""
Auto-detect db changes:
>>> alembic revision --autogenerate -m "..."
Manually perform DB migrations (to latest revision)
>>> alembic upgrade head
Manually downgrade DB to specific version
>>> alembic downgrade <target-revision>

Schema Version History (oldest to newest):
- 693dd5aa47cd | Initialize tables
- 65fd10d8732e | Add User table
- 0233f2608d72 | Add interword spacing
- 5861246a49f3 | Change default of Font.interword_spacing
- 4d7cb48238be | Replace Font.file with Font.file_name
- 25490125daaf | Add explicit ordering to Templates
- caec4f618689 | Turn Card attributes into Card.model_json
- a61f373185d4 | Add support for multiple Connections
- 5318f59eadbf | Utilize ORM Mappings and finalize Column nullability
- 48872195483e | Add Snapshot table
- 32ef3d4633ce | Add Card.source_file column
- b99ce3bfdfbd | Add Sync.required_root_folder column
- 3122c0553b1e | Separate Font replacements, migrate cardinal and ordinal formatting
- f1692007cf8a | Add Series level title split toggle
- 1be1951acc40 | Add Font.line_split_modifier column
"""

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.models.card import Card
from app.models.connection import Connection
from app.models.episode import Episode
from app.models.font import Font
from app.models.loaded import Loaded
from app.models.preferences import Preferences
from app.models.series import Series
from app.models.snapshot import Snapshot
from app.models.sync import Sync
from app.models.template import Template
from app.models.user import User
from app.database.session import Base
target_metadata = Base.metadata

from os import environ
IS_DOCKER = environ.get('TCM_IS_DOCKER', 'false').lower() == 'true'


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """

    url = config.get_main_option("sqlalchemy.url")
    if IS_DOCKER:
        url = '/config/db.sqlite'

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_server_default=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    url = config.get_main_option("sqlalchemy.url")
    if IS_DOCKER:
        url = '/config/db.sqlite'

    with connectable.connect() as connection:
        context.configure(
            url=url,
            connection=connection,
            target_metadata=target_metadata,
            compare_server_default=True,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
