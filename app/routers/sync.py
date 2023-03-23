from typing import Literal, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Form, HTTPException, Query
from sqlalchemy import and_, or_

from modules.Debug import log
from app.dependencies import get_database, get_preferences, get_emby_interface,\
    get_jellyfin_interface, get_plex_interface, get_sonarr_interface, \
    get_tmdb_interface
from app.routers.series import set_series_database_ids, download_series_poster
from app.schemas.sync import (
    EmbySync, JellyfinSync, PlexSync, SonarrSeriesType, SonarrSync, Sync, Interface,
    NewEmbySync, NewJellyfinSync, NewPlexSync, NewSonarrSync, UpdateSync,
)
from app.schemas.series import Series
import app.models as models

# Create sub router for all /sync API requests
sync_router = APIRouter(
    prefix='/sync',
    tags=['Sync']
)

def verify_template_exists(db, template_id: int) -> None:
    """
    Verify the template with the given ID exists.

    Args:
        db: SQLAlchemy database to query.
        template_id: ID of the template to search for.

    Raises:
        HTTPException (404) if the specified template does not exist.
    """
    if template_id is None:
        return None
    
    template = db.query(models.template.Template)\
        .filter_by(id=template_id)\
        .first()
    if template is None:
        raise HTTPException(
            status_code=404,
            detail=f'Template {template_id} not found',
        )

    return None


def add_sync(db, new_sync) -> Sync:
    """
    Add the given sync to the database.

    Args:
        db: SQLAlchemy database to query.
        new_sync: NewSync object to add to the database.
    """

    # Verify template exists (if specified), raise 404 if DNE
    verify_template_exists(db, new_sync.template_id)

    # Create DB entry from Pydantic model, add to database
    sync = models.sync.Sync(**new_sync.dict())
    db.add(sync)
    db.commit()

    return sync


@sync_router.post('/emby/new', tags=['Emby'], status_code=201)
def create_new_emby_sync(
        new_sync: NewEmbySync = Body(...),
        db = Depends(get_database)) -> EmbySync:
    """
    Create a new Sync that interfaces with Emby.

    - new_sync: Sync definition to create.
    """

    return add_sync(db, new_sync)


@sync_router.post('/jellyfin/new', tags=['Jellyfin'], status_code=201)
def create_new_jellyfin_sync(
        new_sync: NewJellyfinSync = Body(...),
        db = Depends(get_database)) -> JellyfinSync:
    """
    Create a new Sync that interfaces with Jellyfin.

    - new_sync: Sync definition to create.
    """

    return add_sync(db, new_sync)


@sync_router.post('/plex/new', tags=['Plex'], status_code=201)
def create_new_plex_sync(
        new_sync: NewPlexSync = Body(...),
        db = Depends(get_database)) -> PlexSync:
    """
    Create a new Sync that interfaces with Plex.

    - new_sync: Sync definition to create.
    """
    
    return add_sync(db, new_sync)


@sync_router.post('/sonarr/new', tags=['Sonarr'], status_code=201)
def create_new_sonarr_sync(
        new_sync: NewSonarrSync = Body(...),
        db = Depends(get_database)) -> SonarrSync:
    """
    Create a new Sync that interfaces with Sonarr.

    - new_sync: Sync definition to create.
    """

    return add_sync(db, new_sync)


@sync_router.patch('/edit/{sync_id}', status_code=200)
def edit_sync(
        sync_id: int,
        update_sync: UpdateSync = Body(...),
        db = Depends(get_database)) -> Sync:
    """
    Update the Sync with the given ID. Only provided fields are updated.

    - sync_id: ID of the Sync to update.
    - update_sync: UpdateSync containing fields to update.
    """

    # Get existing sync
    sync = db.query(models.sync.Sync).filter_by(id=sync_id).first()
    if sync is None:
        raise HTTPException(
            status_code=404,
            detail=f'Sync {sync_id} not found',
        )

    # Verify template exists (if specified), raise 404 if DNE
    verify_template_exists(update_sync.template_id)

    # Update object
    changed = False
    for attribute, value in update_sync.dict().items():
        if value is not None and getattr(sync, attribute) != value:
            setattr(sync, attribute, value)
            changed = True

    # If object was changed, update DB
    if changed:
        db.commit()

    return sync


@sync_router.delete('/delete/{sync_id}', status_code=204)
def delete_sync(
        sync_id: int,
        db = Depends(get_database)) -> None:
    """
    Delete the Sync with the given ID.

    - sync_id: ID of the Sync to delete
    """

    query = db.query(models.sync.Sync).filter_by(id=sync_id)
    if query.first() is None:
        raise HTTPException(
            status_code=404,
            detail=f'Sync {sync_id} not found',
        )
    query.delete()
    db.commit()

    return None


@sync_router.get('/all', status_code=200)
def get_all_syncs(
        db = Depends(get_database)) -> list[Sync]:
    """
    Get all defined Syncs.
    """

    return db.query(models.sync.Sync).all()


@sync_router.get('/emby/all', tags=['Emby'], status_code=200)
def get_all_emby_syncs(
        db = Depends(get_database)) -> list[EmbySync]:
    """
    Get all defined Syncs that interface with Emby.
    """

    return db.query(models.sync.Sync).filter_by(interface='Emby').all()


@sync_router.get('/jellyfin/all', tags=['Jellyfin'], status_code=200)
def get_all_jellyfin_syncs(
        db = Depends(get_database)) -> list[JellyfinSync]:
    """
    Get all defined Syncs that interface with Jellyfin.
    """

    return db.query(models.sync.Sync).filter_by(interface='Jellyfin').all()


@sync_router.get('/plex/all', tags=['Plex'], status_code=200)
def get_all_plex_syncs(
        db = Depends(get_database)) -> list[PlexSync]:
    """
    Get all defined Syncs that interface with Plex.
    """

    return db.query(models.sync.Sync).filter_by(interface='Plex').all()


@sync_router.get('/sonarr/all', tags=['Sonarr'], status_code=200)
def get_all_sonarr_syncs(
        db = Depends(get_database)) -> list[SonarrSync]:
    """
    Get all defined Syncs that interface with Sonarr.
    """

    return db.query(models.sync.Sync).filter_by(interface='Sonarr').all()


@sync_router.get('/{sync_id}', status_code=200)
def get_sync_by_id(
        sync_id: int,
        db = Depends(get_database)) -> Sync:
    """
    Get the Sync with the given ID.

    - sync_id: ID of the Sync to retrieve.
    """

    sync = db.query(models.sync.Sync).filter_by(id=sync_id).first()
    if sync is None:
        raise HTTPException(status_code=404, detail=f'Sync {sync_id} not found')

    return sync


@sync_router.post('/{sync_id}', status_code=201)
def sync(
        sync_id: int,
        background_tasks: BackgroundTasks,
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface),
        sonarr_interface = Depends(get_sonarr_interface),
        tmdb_interface = Depends(get_tmdb_interface),
        ) -> list[Series]:
    """
    Run the given Sync by querying the assigned interface, adding any
    new series to the database. Return a list of any new Series.

    - sync_id: ID of the sync to run.
    """

    # Get the sync with this ID, raise 404 if DNE
    sync = db.query(models.sync.Sync).filter_by(id=sync_id).first()
    if sync is None:
        raise HTTPException(
            status_code=404,
            detail=f'Sync {sync_id} not found',
        )

    # If specified interface is disabled, raise 409
    interface = {
        'Emby': emby_interface,
        'Jellyfin': jellyfin_interface,
        'Plex': plex_interface,
        'Sonarr': sonarr_interface,
    }[sync.interface]
    if interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with {sync.interface}',
        )

    # Sync depending on the associated interface
    added = []
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
                    template_id=sync.template_id,
                    emby_library_name=library,
                    **series_info.ids,
                )
                db.add(series)
                added.append(series)
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
                    models.series.Series.name==series_info.name,
                    models.series.Series.year==series_info.year,
                ).first() 

            if existing is None:
                series = models.series.Series(
                    name=series_info.name,
                    year=series_info.year,
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
# TODO maybe query by other database ID's?
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
                    template_id=sync.template_id,
# TODO Determine which media server to assign this library to
                    plex_library_name=library,
                    **series_info.ids,
                )
                db.add(series)
                added.append(series)

    # If anything was added, update DB and return list
    if added:
        db.commit()

    # Add background tasks to set ID's and download a poster for each series
    for series in added:
        background_tasks.add_task(
            set_series_database_ids,
            series, db, series.emby_library_name, series.jellyfin_library_name,
            series.plex_library_name, emby_interface, jellyfin_interface,
            plex_interface, sonarr_interface, tmdb_interface,
        )
        background_tasks.add_task(
            download_series_poster, series, db, preferences, tmdb_interface
        )

    return added