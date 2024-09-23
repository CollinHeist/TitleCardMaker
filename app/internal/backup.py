from datetime import datetime, timedelta
from os import environ
from pathlib import Path
from shutil import copy as file_copy
from sqlite3 import connect, OperationalError
from typing import NamedTuple, Optional, Union

from fastapi import HTTPException

from app.schemas.preferences import DatabaseBackup, SettingsBackup, SystemBackup
from modules.Debug import Logger, log
from modules.Version import Version


"""Naming scheme for backup subfolders"""
BACKUP_DT_FORMAT = '%Y-%m-%d_%H-%M-%S'

"""How long to keep old backups"""
BACKUP_RETENTION = timedelta(days=int(environ.get('TCM_BACKUP_RETENTION', 21)))

"""Whether executing in Docker mode"""
IS_DOCKER = environ.get('TCM_IS_DOCKER', 'false').lower() == 'true'

"""Directory for all backups"""
BACKUP_DIRECTORY = Path('/config/backups' if IS_DOCKER else './config/backups')
BACKUP_DIRECTORY.mkdir(parents=True, exist_ok=True)


class DataBackup(NamedTuple): # pylint: disable=missing-class-docstring
    config: Path
    database: Path


def delete_old_backups(*, log: Logger = log) -> None:
    """
    Delete all backups older than `BACKUP_RETENTION`.

    Args:
        log: Logger for all log messages.
    """

    delete_before = datetime.now() - BACKUP_RETENTION

    for backup in BACKUP_DIRECTORY.iterdir():
        # Backup subdirectories
        if backup.is_dir():
            try:
                date = datetime.strptime(backup.name, BACKUP_DT_FORMAT)
            except ValueError:
                log.warning(f'Cannot identify date of backup file "{backup}"')
                continue

            if date < delete_before:
                for file in backup.iterdir():
                    file.unlink(missing_ok=True)
                    log.debug(f'Deleted old backup "{backup.name}/{file.name}"')
                backup.rmdir()
        # Old-style files not stored in a subdirectory
        else:
            try:
                date = datetime.strptime(
                    backup.name.rsplit('.')[-1],
                    BACKUP_DT_FORMAT
                )
            except ValueError:
                log.debug(f'Cannot identify date of backup file "{backup}"')
                continue

            if date < delete_before:
                backup.unlink(missing_ok=True)
                log.debug(f'Deleted old backup "{backup}"')


def delete_backup(folder_name: Union[str, Path], *, log: Logger = log) -> None:
    """
    Delete the given backup folder.

    Args:
        folder_name: Name of the directory to delete.
        log: Logger for all log messages.
    """

    if not (folder := Path(BACKUP_DIRECTORY / folder_name)).exists():
        log.debug(f'Specified backup folder ({folder}) does not exist')
        return None

    # Delete subcontents and folder
    for file in folder.iterdir():
        file.unlink(missing_ok=True)
        log.debug(f'Deleted backup file "{folder.name}/{file.name}"')
    folder.rmdir()

    return None


def backup_data(
        version: Union[str, Version],
        *,
        log: Logger = log,
    ) -> DataBackup:
    """
    Perform a backup of the SQL database and global preferences. This
    also deletes any "old" backups.

    Args:
        version: Current version of TCM.
        log: Logger for all log messages.

    Returns:
        Tuple of Paths to created preferences and database backup files.
    """

    # Store backups in a dated subfolder
    backup_folder = BACKUP_DIRECTORY / datetime.now().strftime(BACKUP_DT_FORMAT)
    backup_folder.mkdir(exist_ok=True, parents=True)

    # Identify source and destination files
    pre = '' if IS_DOCKER else '.'
    config = Path(f'{pre}/config/config.pickle')
    config_backup = backup_folder / f'config.pickle.{version}'
    database = Path(f'{pre}/config/db.sqlite')
    database_backup = backup_folder / f'db.sqlite.{version}'

    delete_old_backups(log=log)

    # Backup config
    if config.exists():
        file_copy(config, config_backup)
        log.info(f'Performed settings backup ({config_backup})')

    # Backup database
    if database.exists():
        file_copy(database, database_backup)
        log.info(f'Performed database backup ({database_backup})')

    return DataBackup(config=config_backup, database=database_backup)


def restore_backup(backup: Union[DataBackup, str], /, *, log: Logger = log):
    """
    Restore the config and database from the given data backup.

    Args:
        backup: Tuple of backup data (as returned by `backup_data()`)
            to restore from; or the name of the folder containing data.
        log: Logger for all log messages.
    """

    # If a folder name was provided, search for the config/db files
    if isinstance(backup, str):
        folder = BACKUP_DIRECTORY / backup
        try:
            config = next(folder.glob('config.pickle*'))
            database = next(folder.glob('db.sqlite*'))
        except StopIteration as exc:
            log.exception(f'Unable to identify backup data from folder')
            raise HTTPException(
                status_code=400,
                detail='Invalid backup folder'
            ) from exc
    else:
        config, database = backup

    # Restore config
    if config and config.exists():
        if IS_DOCKER:
            file_copy(config, Path('/config/config.pickle'))
        else:
            file_copy(config, Path('./config/config.pickle'))
        log.debug(f'Restored backup from "{config}"')
    else:
        log.warning(f'Cannot restore backup from "{config}"')

    # Restore database
    if database.exists():
        if IS_DOCKER:
            file_copy(database, Path('/config/db.sqlite'))
        else:
            file_copy(database, Path('./config/db.sqlite'))
        log.debug(f'Restored backup from "{database}"')
    else:
        log.warning(f'Cannot restore backup from "{database}"')


def list_available_backups(*, log: Logger = log) -> list[SystemBackup]:
    """
    Get a list detailing all the available system backups.

    Args:
        log: Logger for all log messages.

    Returns:
        List of system backup information.
    """

    def _parse_version_number(file: Path) -> str:
        """Parse the version number from the given file."""
        return file.name[len('config.pickle') + 1:]

    def _parse_schema_version(file: Path) -> Optional[str]:
        """Parse the alembic schema version from the given file."""
        connection = connect(file)
        try:
            return connection.cursor()\
                .execute('SELECT * FROM alembic_version LIMIT 1')\
                .fetchone()[0]
        except OperationalError:
            log.debug(f'Unable to detect schema from {file}')
            return None
        finally:
            connection.close()

    backups: list[SystemBackup] = []
    for subfolder in BACKUP_DIRECTORY.glob('2*'):
        # Find setting and database files
        try:
            settings = next(subfolder.glob('config.pickle*'))
            database = next(subfolder.glob('db.sqlite*'))
        except StopIteration:
            log.debug(f'Missing backup file(s) from "{subfolder}"')
            continue

        # Skip if there's no version or schema
        if (not (schema := _parse_schema_version(database))
            or not (version := _parse_version_number(settings))):
            log.debug(f'Unable to identify database schema or version from '
                      f'"{subfolder}')
            continue

        backups.append(SystemBackup(
            database=DatabaseBackup(
                filename=database.name,
                filesize=database.stat().st_size,
                schema_version=schema,
            ),
            settings=SettingsBackup(
                filename=settings.name,
                filesize=settings.stat().st_size,
            ),
            timestamp=datetime.strptime(settings.parent.name, BACKUP_DT_FORMAT),
            version=version,
            folder_name=subfolder.name,
        ))

    return sorted(backups, key=lambda b: b.timestamp)
