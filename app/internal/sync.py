from logging import Logger
from time import sleep
from typing import Optional, Union

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database.query import get_all_templates, get_interface
from app.dependencies import get_database, get_preferences
from app.internal.series import add_series
from app.models.connection import Connection
from app.models.series import Series
from app.models.sync import Sync
from app.schemas.series import NewSeries
from app.schemas.sync import (
    NewEmbySync, NewJellyfinSync, NewPlexSync, NewSonarrSync
)
from modules.Debug import log
from modules.NotificationGroup import SyncNotification


def sync_all(*, log: Logger = log) -> None:
    """
    Schedule-able function to run all defined Syncs in the Database.
    """

    notifications = SyncNotification(log)

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get and run all Syncs
            for sync in db.query(Sync).all():
                try:
                    run_sync(db, sync, log=notifications)
                except HTTPException as e:
                    log.exception(f'{sync} Error Syncing - {e.detail}', e)
                except OperationalError:
                    log.debug(f'Database is busy, sleeping..')
                    sleep(30)
    except Exception as e:
        log.exception(f'Failed to run all Syncs', e)
        notifications.mark_failure()

    get_preferences().currently_running_sync = None
    notifications.notify()


def add_sync(
        db: Session,
        new_sync: Union[NewEmbySync, NewJellyfinSync, NewPlexSync,NewSonarrSync],
        *,
        log: Logger = log,
    ) -> Sync:
    """
    Add the given Sync to the database.

    Args:
        db: Database to query for Templates and add the Sync to.
        new_sync: New Sync definition to add to the database.
        log: Logger for all log messages.

    Returns:
        Newly created Sync object.
    """

    # Verify all Templates exists, raise 404 if DNE
    new_sync_dict = new_sync.dict()
    templates = get_all_templates(db, new_sync_dict)

    # Create DB entry from Pydantic model, add to database
    sync = Sync(**new_sync_dict)
    db.add(sync)
    db.commit()

    # Add Templates
    sync.assign_templates(templates, log=log)
    db.commit()

    return sync


def run_sync(
        db: Session,
        sync: Sync,
        background_tasks: Optional[BackgroundTasks] = None,
        *,
        log: SyncNotification = log,
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

    # Mark Sync as running
    preferences = get_preferences()
    preferences.currently_running_sync = sync.id

    # Get specified Interface
    interface = get_interface(sync.interface_id, raise_exc=True)

    # Get this Interface's Connection
    if (connection := sync.connection) is None:
        log.error(f'Unable to communicate with {sync.interface}')
        preferences.currently_running_sync = None
        raise HTTPException(
            status_code=404,
            detail=f'Unable to communicate with {sync.interface}',
        )

    # Query interface for the indicated subset of Series
    log.debug(f'{sync} starting to query {sync.interface}[{sync.interface_id}]')
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
            # Determine libraries using this Connection
            library_data = connection.determine_libraries(lib_or_dir)
            for interface_id, library in library_data:
                # Get Connection of this library
                library_connection = db.query(Connection)\
                    .filter_by(id=interface_id)\
                    .first()
                if library_connection is None:
                    log.increment_count('Failed Library Assignments')
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
            for new in libraries:
                exists = any(
                    new['interface_id'] == existing_library['interface_id']
                    and new['name'] == existing_library['name']
                    for existing_library in existing.libraries
                )
                if not exists:
                    existing.libraries.append(new)
                    log.debug(f'Added Library "{new["name"]}" to {existing}')
                    log.increment_count('Libraries Updated')

            # Update IDs
            existing.update_from_series_info(series_info)
            db.commit()
            continue

        # Create NewSeries for this entry
        log.add_to_list('Series Added', series_info.full_name)
        added.append(NewSeries(
            name=series_info.name, year=series_info.year, libraries=libraries,
            **series_info.ids, sync_id=sync.id, template_ids=sync.template_ids,
        ))

    # Nothing added, log
    if not added:
        log.debug(f'{sync} No new Series synced')

    # Process each newly added Series
    preferences.currently_running_sync = None
    return [
        add_series(new_series, background_tasks, db, log=log)
        for new_series in added
    ]
