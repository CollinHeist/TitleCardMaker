from logging import Logger
from time import sleep
from typing import Optional, Union

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database.query import get_all_templates
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.series import add_series
from app import models
from app.models.sync import Sync
from app.schemas.sync import (
    NewEmbySync, NewJellyfinSync, NewPlexSync, NewSonarrSync,
)
from app.schemas.series import NewSeries, Series
from app.schemas.preferences import Preferences


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
            for sync in db.query(Sync).all():
                try:
                    run_sync(
                        db, get_preferences(), sync, get_emby_interface(),
                        get_imagemagick_interface(), get_jellyfin_interface(),
                        get_plex_interface(), get_sonarr_interface(),
                        get_tmdb_interface(), log=log,
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
    sync = models.sync.Sync(**new_sync_dict, templates=templates)
    db.add(sync)
    db.commit()

    return sync


def run_sync(
        db: Session,
        preferences: Preferences,
        sync: Sync,
        emby_interface: Optional[EmbyInterface],
        imagemagick_interface: Optional[ImageMagickInterface],
        jellyfin_interface: Optional[JellyfinInterface],
        plex_interface: Optional[PlexInterface],
        sonarr_interface: Optional[SonarrInterface],
        tmdb_interface: Optional[TMDbInterface],
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
        'Emby': emby_interface,
        'Jellyfin': jellyfin_interface,
        'Plex': plex_interface,
        'Sonarr': sonarr_interface,
    }.get(sync.interface, None)
    if interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with {sync.interface}',
        )

    # Sync depending on the associated interface
    added: list[NewSeries] = []

    # Sync from Emby
    log.debug(f'{sync.log_str} starting to query {sync.interface}')
    if sync.interface == 'Emby':
        all_series = emby_interface.get_all_series(
            required_libraries=sync.required_libraries,
            excluded_libraries=sync.excluded_libraries,
            required_tags=sync.required_tags,
            excluded_tags=sync.excluded_tags,
            log=log,
        )
        for series_info, library in all_series:
            # Look for existing series, add if DNE
            existing = db.query(models.series.Series)\
                .filter(series_info.filter_conditions(models.series.Series))\
                .first()
            if existing is None:
                added.append(NewSeries(
                    name=series_info.name,
                    year=series_info.year,
                    sync_id=sync.id,
                    template_ids=sync.template_ids,
                    emby_library_name=library,
                    **series_info.ids,
                ))
    # Sync from Jellyfin
    elif sync.interface == 'Jellyfin':
        all_series = jellyfin_interface.get_all_series(
            required_libraries=sync.required_libraries,
            excluded_libraries=sync.excluded_libraries,
            required_tags=sync.required_tags,
            excluded_tags=sync.excluded_tags,
            log=log,
        )
        for series_info, library in all_series:
            # Look for existing series, add if DNE
            existing = db.query(models.series.Series)\
                .filter(series_info.filter_conditions(models.series.Series))\
                .first()
            if existing is None:
                added.append(NewSeries(
                    name=series_info.name,
                    year=series_info.year,
                    sync_id=sync.id,
                    template_ids=sync.template_ids,
                    jellyfin_library_name=library,
                    **series_info.ids,
                ))
    # Sync from Plex
    elif sync.interface == 'Plex':
        all_series = plex_interface.get_all_series(
            required_libraries=sync.required_libraries,
            excluded_libraries=sync.excluded_libraries,
            required_tags=sync.required_tags,
            excluded_tags=sync.excluded_tags,
            log=log,
        )

        for series_info, library in all_series:
            # Look for existing series, add if DNE
            existing = db.query(models.series.Series)\
                .filter(series_info.filter_conditions(models.series.Series))\
                .first()
            if existing is None:
                added.append(NewSeries(
                    name=series_info.name,
                    year=series_info.year,
                    sync_id=sync.id,
                    template_ids=sync.template_ids,
                    plex_library_name=library,
                    **series_info.ids,
                ))
    # Sync from Sonarr
    elif sync.interface == 'Sonarr':
        all_series = sonarr_interface.get_all_series(
            required_tags=sync.required_tags,
            excluded_tags=sync.excluded_tags,
            monitored_only=sync.monitored_only,
            downloaded_only=sync.downloaded_only,
            required_series_type=sync.required_series_type,
            excluded_series_type=sync.excluded_series_type,
            log=log,
        )
        for series_info, directory in all_series:
            # Look for existing series, add if DNE
            existing = db.query(models.series.Series)\
                .filter(series_info.filter_conditions(models.series.Series))\
                .first()
            if existing is None:
                library = preferences.determine_sonarr_library(directory)
                added.append(NewSeries(
                    name=series_info.name,
                    year=series_info.year,
                    sync_id=sync.id,
                    template_ids=sync.template_ids,
                    plex_library_name=library,
                    **series_info.ids,
                ))

    # If anything was added, commit updates to database
    if added:
        db.commit()
    else:
        log.debug(f'{sync.log_str} No new Series synced')

    # Process each newly added Series
    return [
        add_series(
            new_series, background_tasks, db, emby_interface,
            imagemagick_interface, jellyfin_interface, plex_interface,
            sonarr_interface, tmdb_interface, log=log,
        ) for new_series in added
    ]
