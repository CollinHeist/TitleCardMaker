from logging import Logger
from pathlib import Path
from time import sleep
from typing import Optional, Union

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database.query import get_all_templates, get_interface
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.episodes import refresh_episode_data
from app.internal.series import download_series_poster, set_series_database_ids
from app.internal.sources import download_series_logo
from app.models.connection import Connection
from app.models.series import Series
from app.models.sync import Sync
from app.schemas.sync import (
    NewEmbySync, NewJellyfinSync, NewPlexSync, NewSonarrSync
)

from modules.Debug import log


def sync_all(*, log: Logger = log) -> None:
    """
    Schedule-able function to run all defined Syncs in the Database.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get and run all Syncs
            for sync in db.query(Sync).all():
                try:
                    run_sync(db, sync, log=log)
                except HTTPException as e:
                    log.exception(f'{sync.log_str} Error Syncing - {e.detail}', e)
                except OperationalError:
                    log.debug(f'Database is busy, sleeping..')
                    sleep(30)
    except Exception as e:
        log.exception(f'Failed to run all Syncs', e)


def add_sync(
        db: Session,
        new_sync: Union[NewEmbySync, NewJellyfinSync, NewPlexSync,NewSonarrSync]
    ) -> Sync:
    """
    Add the given sync to the database.

    Args:
        db: SQLAlchemy database to query.
        new_sync: New Sync object to add to the database.
    """

    # Verify all Templates exists, raise 404 if DNE
    new_sync_dict = new_sync.dict()
    templates = get_all_templates(db, new_sync_dict)

    # Create DB entry from Pydantic model, add to database
    sync = Sync(**new_sync_dict, templates=templates)
    db.add(sync)
    db.commit()

    return sync


def run_sync(
        db: Session,
        sync: Sync,
        background_tasks: Optional[BackgroundTasks] = None,
        *,
        log: Logger = log,
    ) -> list[Series]:
    """
    Run the given Sync. This adds any missing Series from the given Sync
    to the Database. Any newly added Series have their database ID's
    set, and a poster and logo are downloaded.

    Args:
        db: Database to query for existing Series.
        sync: Sync to run.
        background_tasks: BackgroundTasks to add tasks to for any newly
            added Series.
        log: Logger for all log messages.
    """

    # Get specified Interface
    interface = get_interface(sync.interface_id, raise_exc=True)

    # Query interface for the indicated subset of Series
    log.debug(f'{sync.log_str} starting to query {sync.interface}[{sync.interface_id}]')
    all_series = interface.get_all_series(**sync.sync_kwargs, log=log)

    # Process all Series returned by Sync
    added: list[Series] = []
    for series_info, lib_or_dir in all_series:
        # Look for existing Series
        existing = db.query(Series)\
            .filter(series_info.filter_conditions(Series))\
            .first()

        # Determine this Series' libraries
        libraries = []
        if sync.interface == 'Sonarr':
            # Get the Connection associated with this Sync
            if (connection := sync.connection) is None:
                raise HTTPException(
                    status_code=409,
                    detail=f'Unable to communicate with {sync.interface}',
                )

            # Determine libraries using this Connection
            library_data = connection.determine_libraries(lib_or_dir)
            for interface_id, library in library_data:
                # Get Connection of this library
                library_connection = db.query(Connection)\
                    .filter_by(id=interface_id)\
                    .first()
                if library_connection is None:
                    log.error(f'No Connection of ID {interface_id} - cannot '
                              f'assign library')
                    continue

                libraries.append({
                    'interface': library_connection.interface_type,
                    'interface_id': interface_id,
                    'name': library,
                })
        else:
            libraries.append({
                'interface': sync.interface,
                'interface_id': sync.interface_id,
                'name': lib_or_dir
            })

        # If already exists in Database, update IDs and libraries then skip
        if existing:
            # Add any new libraries
            existing.libraries += [
                library for library in libraries
                if library not in existing.libraries
            ]
            # Update IDs
            existing.update_from_series_info(series_info)
            db.commit()
            continue

        # Create Series, add to database and immediately commit so any
        # subsequent same-Series can be matched
        series = Series(
            name=series_info.name,
            year=series_info.year,
            sync=sync,
            templates=sync.templates,
            libraries=libraries,
            **series_info.ids,
        )
        db.add(series)
        db.commit()
        added.append(series)

    # Nothing added, log
    if not added:
        log.debug(f'{sync.log_str} No new Series synced')

    # Process each newly added series
    for series in added:
        log.info(f'{sync.log_str} Added {series.name} ({series.year})')
        Path(series.source_directory).mkdir(parents=True, exist_ok=True)
        # Set Series ID's, download poster and logo
        if background_tasks is None:
            set_series_database_ids(series, db, log=log)
            download_series_poster(db, series, log=log)
            download_series_logo(series, log=log)
            refresh_episode_data(db, series, log=log)
        else:
            background_tasks.add_task(
                # Function
                set_series_database_ids,
                # Arguments
                series, db, log=log,
            )
            background_tasks.add_task(
                # Function
                download_series_poster,
                # Arguments
                db, series, log=log,
            )
            background_tasks.add_task(
                # Function
                download_series_logo,
                # Arguments
                series, log=log,
            )
            background_tasks.add_task(
                # Function
                refresh_episode_data,
                # Arguments
                db, series, log=log
            )

    return added
