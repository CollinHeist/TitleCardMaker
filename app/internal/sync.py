from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import and_, or_

from app.database.query import get_template
from app.dependencies import (
    get_database, get_preferences, get_emby_interface, get_imagemagick_interface,
    get_jellyfin_interface, get_plex_interface, get_sonarr_interface,
    get_tmdb_interface
)
from app.internal.series import download_series_poster, set_series_database_ids
from app.internal.sources import download_series_logo
from app.schemas.sync import Sync
from app.schemas.series import Series
import app.models as models

from modules.Debug import log


def sync_all() -> None:
    """
    Schedule-able function to run all defined Syncs in the Database.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get and run all Syncs
            all_syncs = db.query(models.sync.Sync).all()
            for sync in all_syncs:
                run_sync(
                    db, get_preferences(), sync, get_imagemagick_interface(),
                    get_emby_interface(), get_jellyfin_interface(),
                    get_plex_interface(), get_sonarr_interface(),
                    get_tmdb_interface(),
                )
    except Exception as e:
        log.exception(f'Failed to run all Syncs', e)


def add_sync(db, new_sync: 'NewSync') -> Sync:
    """
    Add the given sync to the database.

    Args:
        db: SQLAlchemy database to query.
        new_sync: New Sync object to add to the database.
    """

    # Verify template exists (if specified), raise 404 if DNE
    get_template(db, new_sync.template_id, raise_exc=True)

    # Create DB entry from Pydantic model, add to database
    sync = models.sync.Sync(**new_sync.dict())
    db.add(sync)
    db.commit()

    return sync


def run_sync(
        db: 'Database',
        preferences: 'Preferences',
        sync: Sync,
        emby_interface: Optional['EmbyInterface'],
        imagemagick_interface: Optional['ImageMagickInterface'],
        jellyfin_interface: Optional['JellyfinInterface'],
        plex_interface: Optional['PlexInterface'],
        sonarr_interface: Optional['SonarrInterface'],
        tmdb_interface: Optional['TMDbInterface'],
        background_tasks: Optional[BackgroundTasks] = None) -> list[Series]:
    """
    Run the given Sync. This adds any missing Series from the given Sync
    to the Database. Any newly added Series have their database ID's
    set, and a poster and logo are downloaded.
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
    added = []
    log.debug(f'Starting to Sync[{sync.id}] from {sync.interface}')
    # Sync from Emby
    if sync.interface == 'Emby':
        # Get filtered list of series from Sonarr
        all_series = emby_interface.get_all_series(
            required_libraries=sync.required_libraries,
            excluded_libraries=sync.excluded_libraries,
            required_tags=sync.required_tags,
            excluded_tags=sync.excluded_tags,
        )
        for series_info, library in all_series:
            # Look for an existing series with this name+year or Emby ID
            # TODO maybe query by other database ID's?
            existing = db.query(models.series.Series)\
                .filter(or_(
                    and_(
                        models.series.Series.name==series_info.name,
                        models.series.Series.year==series_info.year
                    ), models.series.Series.emby_id==series_info.emby_id,
                )).first()
            if existing is None:
                series = models.series.Series(
                    name=series_info.name,
                    year=series_info.year,
                    sync_id=sync.id,
                    template_id=sync.template_id,
                    emby_library_name=library,
                    **series_info.ids,
                )
                db.add(series)
                added.append(series)
    # Sync from Jellyfin
    elif sync.interface == 'Jellyfin':
        # Get filtered list of series from Jellyfin
        all_series = jellyfin_interface.get_all_series(
            required_libraries=sync.required_libraries,
            excluded_libraries=sync.excluded_libraries,
            required_tags=sync.required_tags,
            excluded_tags=sync.excluded_tags,
        )
        for series_info, library in all_series:
            # Look for an existing series with this name+year or Jellyfin ID
            # TODO maybe query by other database ID's?
            existing = db.query(models.series.Series)\
                .filter(or_(
                    and_(
                        models.series.Series.name==series_info.name,
                        models.series.Series.year==series_info.year
                    ), models.series.Series.jellyfin_id==series_info.jellyfin_id
                )).first()
            if existing is None:
                series = models.series.Series(
                    name=series_info.name,
                    year=series_info.year,
                    sync_id=sync.id,
                    template_id=sync.template_id,
                    jellyfin_library_name=library,
                    **series_info.ids,
                )
                db.add(series)
                added.append(series)
    # Sync from Plex
    elif sync.interface == 'Plex':
        # Get filtered list of series from Plex
        all_series = plex_interface.get_all_series(
            required_libraries=sync.required_libraries,
            excluded_libraries=sync.excluded_libraries,
            required_tags=sync.required_tags,
            excluded_tags=sync.excluded_tags,
        )

        for series_info, library in all_series:
            # Look for existing series, add if DNE
            existing = db.query(models.series.Series)\
                .filter(
                    # TODO filter by other ID's
                    models.series.Series.name==series_info.name,
                    models.series.Series.year==series_info.year,
                ).first() 

            if existing is None:
                series = models.series.Series(
                    name=series_info.name,
                    year=series_info.year,
                    sync_id=sync.id,
                    template_id=sync.template_id,
                    plex_library_name=library,
                    **series_info.ids,
                )
                db.add(series)
                added.append(series)
    # Sync from Sonarr
    elif sync.interface == 'Sonarr':
        # Get filtered list of series from Sonarr
        all_series = sonarr_interface.get_all_series(
            required_tags=sync.required_tags,
            excluded_tags=sync.excluded_tags,
            monitored_only=sync.monitored_only,
            downloaded_only=sync.downloaded_only,
            required_series_type=sync.required_series_type,
            excluded_series_type=sync.excluded_series_type,
        )
        for series_info, directory in all_series:
            # Look for an existing series with this name+year or Sonarr ID
            existing = db.query(models.series.Series)\
                .filter(or_(
                    and_(
                        models.series.Series.name==series_info.name,
                        models.series.Series.year==series_info.year
                    ), models.series.Series.sonarr_id==series_info.sonarr_id,
                )).first()
            if existing is None:
                library = preferences.determine_sonarr_library(directory)
                series = models.series.Series(
                    name=series_info.name,
                    year=series_info.year,
                    sync_id=sync.id,
                    template_id=sync.template_id,
                    plex_library_name=library,
                    **series_info.ids,
                )
                db.add(series)
                added.append(series)

    # If anything was added, update DB and return list
    if added:
        db.commit()

    # Process each newly added series
    for series in added:
        log.info(f'Sync[{sync.id}] Added {series.name} ({series.year})')
        Path(series.source_directory).mkdir(parents=True, exist_ok=True)
        # Set Series ID's, download poster and logo
        if background_tasks is None:
            set_series_database_ids(
                series, db, emby_interface, jellyfin_interface, plex_interface,
                sonarr_interface, tmdb_interface,
            )
            download_series_poster(db, preferences, series, tmdb_interface)
            download_series_logo(
                db, preferences, emby_interface, imagemagick_interface,
                jellyfin_interface, tmdb_interface, series,
            )
        else:
            background_tasks.add_task(
                # Function
                set_series_database_ids,
                # Arguments
                series, db, emby_interface, jellyfin_interface, plex_interface,
                sonarr_interface, tmdb_interface,
            )
            background_tasks.add_task(
                # Function
                download_series_poster,
                # Arguments
                db, preferences, series, tmdb_interface,
            )
            background_tasks.add_task(
                # Function
                download_series_logo, 
                # Arguments
                db, preferences, emby_interface, imagemagick_interface,
                jellyfin_interface, tmdb_interface, series,
            )

    if not added:
        log.info(f'Sync[{sync.id}] No series synced')

    return added