from logging import Logger
from pathlib import Path
from time import sleep
from typing import Optional, Union

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database.query import get_all_templates
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.episodes import refresh_episode_data
from app.internal.series import download_series_poster, set_series_database_ids
from app.internal.sources import download_series_logo
from app import models
from app.models.preferences import Preferences
from app.models.series import Series
from app.schemas.sync import (
    NewEmbySync, NewJellyfinSync, NewPlexSync, NewSonarrSync, Sync
)

from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.ImageMagickInterface import ImageMagickInterface
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface


def sync_all(*, log: Logger = log) -> None:
    """
    Schedule-able function to run all defined Syncs in the Database.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get and run all Syncs
            for sync in db.query(models.sync.Sync).all():
                try:
                    run_sync(
                        db, get_preferences(), sync,
                        get_emby_interfaces(),
                        get_imagemagick_interface(),
                        get_jellyfin_interfaces(),
                        get_plex_interfaces(),
                        get_sonarr_interfaces(),
                        get_tmdb_interface(),
                        log=log,
                    )
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
    sync = models.sync.Sync(**new_sync_dict, templates=templates)
    db.add(sync)
    db.commit()

    return sync


def run_sync(
        db: Session,
        preferences: Preferences,
        sync: Sync,
        emby_interfaces: InterfaceGroup[int, EmbyInterface],
        imagemagick_interface: ImageMagickInterface,
        jellyfin_interfaces: InterfaceGroup[int, JellyfinInterface],
        plex_interfaces: InterfaceGroup[int, PlexInterface],
        sonarr_interfaces: InterfaceGroup[int, SonarrInterface],
        tmdb_interface: InterfaceGroup[int, TMDbInterface],
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
        preferences: Preferences to use for global settings.
        sync: Sync to run.
        *_interface: Interfaces to query.
        background_tasks: BackgroundTasks to add tasks to for any newly
            added Series.
        log: Logger for all log messages.
    """

    # If specified interface is disabled, raise 409
    interface = {
        'Emby': emby_interfaces,
        'Jellyfin': jellyfin_interfaces,
        'Plex': plex_interfaces,
        'Sonarr': sonarr_interfaces,
    }[sync.interface][sync.interface_id]
    if interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with {sync.interface}',
        )

    # Sync depending on the associated interface
    added: list[Series] = []
    log.debug(f'{sync.log_str} starting to query {sync.interface}[{sync.interface_id}]')
    # Sync from Emby
    if sync.interface == 'Emby':
        # Get filtered list of series from Sonarr
        interface: EmbyInterface = interface
        all_series = interface.get_all_series(
            required_libraries=sync.required_libraries,
            excluded_libraries=sync.excluded_libraries,
            required_tags=sync.required_tags,
            excluded_tags=sync.excluded_tags,
            log=log,
        )
    # Sync from Jellyfin
    elif sync.interface == 'Jellyfin':
        # Get filtered list of series from Jellyfin
        interface: JellyfinInterface = interface
        all_series = interface.get_all_series(
            required_libraries=sync.required_libraries,
            excluded_libraries=sync.excluded_libraries,
            required_tags=sync.required_tags,
            excluded_tags=sync.excluded_tags,
            log=log,
        )
    # Sync from Plex
    elif sync.interface == 'Plex':
        # Get filtered list of series from Plex
        interface: PlexInterface = interface
        all_series = interface.get_all_series(
            required_libraries=sync.required_libraries,
            excluded_libraries=sync.excluded_libraries,
            required_tags=sync.required_tags,
            excluded_tags=sync.excluded_tags,
            log=log,
        )
    # Sync from Sonarr
    elif sync.interface == 'Sonarr':
        # Get filtered list of series from Sonarr
        interface: SonarrInterface = interface
        all_series = interface.get_all_series(
            required_tags=sync.required_tags,
            excluded_tags=sync.excluded_tags,
            monitored_only=sync.monitored_only,
            downloaded_only=sync.downloaded_only,
            required_series_type=sync.required_series_type,
            excluded_series_type=sync.excluded_series_type,
            log=log,
        )

    # Process all Series returned by Sync
    for series_info, lib_or_dir in all_series:
        # Look for existing Series, skip if already exists
        existing = db.query(Series)\
            .filter(series_info.filter_conditions(Series))\
            .first()
        if existing:
            continue

        # Determine this Series' libraries
        libraries = []
        if sync.interface in ('Emby', 'Jellyfin', 'Plex'):
            libraries.append({
                'media_server': sync.interface,
                'interface_id': sync.interface_id,
                'name': lib_or_dir
            })
        else:
            library_data = preferences.determine_sonarr_library(
                lib_or_dir, sync.interface_id,
            )
            for media_server, interface_id, library in library_data:
                libraries.append({
                    'media_server': media_server,
                    'interface_id': interface_id,
                    'name': library,
                })

        series = Series(
            name=series_info.name,
            year=series_info.year,
            sync=sync,
            templates=sync.templates,
            libraries=libraries
            **series_info.ids,
        )
        db.add(series)
        added.append(series)

    # If anything was added, commit updates to database
    if added:
        db.commit()
    else:
        log.debug(f'{sync.log_str} No new Series synced')

    # Process each newly added series
    for series in added:
        log.info(f'{sync.log_str} Added {series.name} ({series.year})')
        Path(series.source_directory).mkdir(parents=True, exist_ok=True)
        # Set Series ID's, download poster and logo
        if background_tasks is None:
            set_series_database_ids(
                series, db, emby_interfaces, jellyfin_interfaces,
                plex_interfaces, sonarr_interfaces, tmdb_interface, log=log,
            )
            download_series_poster(
                db, preferences, series, emby_interfaces, imagemagick_interface,
                jellyfin_interfaces, plex_interfaces, tmdb_interface, log=log,
            )
            download_series_logo(
                preferences, emby_interfaces, imagemagick_interface,
                jellyfin_interfaces, tmdb_interface, series, log=log,
            )
            refresh_episode_data(
                db, preferences, series, emby_interfaces, jellyfin_interfaces,
                plex_interfaces, sonarr_interfaces, tmdb_interface, log=log
            )
        else:
            background_tasks.add_task(
                # Function
                set_series_database_ids,
                # Arguments
                series, db, emby_interfaces, jellyfin_interfaces,
                plex_interfaces, sonarr_interfaces, tmdb_interface, log=log,
            )
            background_tasks.add_task(
                # Function
                download_series_poster,
                # Arguments
                db, preferences, series, emby_interfaces, imagemagick_interface,
                jellyfin_interfaces, plex_interfaces, tmdb_interface, log=log,
            )
            background_tasks.add_task(
                # Function
                download_series_logo,
                # Arguments
                preferences, emby_interfaces, imagemagick_interface,
                jellyfin_interfaces, tmdb_interface, series, log=log,
            )
            background_tasks.add_task(
                # Function
                refresh_episode_data,
                # Arguments
                db, preferences, series, emby_interfaces, jellyfin_interfaces,
                plex_interfaces, sonarr_interfaces, tmdb_interface, log=log
            )

    return added
