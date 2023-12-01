from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request
from sqlalchemy.orm import Session

from app.database.query import get_all_templates, get_sync
from app.dependencies import get_database
from app.internal.auth import get_current_user
from app.internal.sync import add_sync, run_sync
from app import models
from app.schemas.sync import (
    EmbySync, JellyfinSync, PlexSync, SonarrSync, Sync, NewEmbySync,
    NewJellyfinSync, NewPlexSync, NewSonarrSync, UpdateSync,
)
from app.schemas.series import Series


# Create sub router for all /sync API requests
sync_router = APIRouter(
    prefix='/sync',
    tags=['Sync'],
    dependencies=[Depends(get_current_user)],
)


@sync_router.post('/emby/new', tags=['Emby'], status_code=201)
def create_new_emby_sync(
        request: Request,
        new_sync: NewEmbySync = Body(...),
        db: Session = Depends(get_database),
    ) -> EmbySync:
    """
    Create a new Sync that interfaces with Emby.

    - new_sync: Sync definition to create.
    """

    return add_sync(db, new_sync, log=request.state.log)


@sync_router.post('/jellyfin/new', tags=['Jellyfin'], status_code=201)
def create_new_jellyfin_sync(
        request: Request,
        new_sync: NewJellyfinSync = Body(...),
        db: Session = Depends(get_database),
    ) -> JellyfinSync:
    """
    Create a new Sync that interfaces with Jellyfin.

    - new_sync: Sync definition to create.
    """

    return add_sync(db, new_sync, log=request.state.log)


@sync_router.post('/plex/new', tags=['Plex'], status_code=201)
def create_new_plex_sync(
        request: Request,
        new_sync: NewPlexSync = Body(...),
        db: Session = Depends(get_database),
    ) -> PlexSync:
    """
    Create a new Sync that interfaces with Plex.

    - new_sync: Sync definition to create.
    """

    return add_sync(db, new_sync, log=request.state.log)


@sync_router.post('/sonarr/new', tags=['Sonarr'], status_code=201)
def create_new_sonarr_sync(
        request: Request,
        new_sync: NewSonarrSync = Body(...),
        db: Session = Depends(get_database),
    ) -> SonarrSync:
    """
    Create a new Sync that interfaces with Sonarr.

    - new_sync: Sync definition to create.
    """

    return add_sync(db, new_sync, log=request.state.log)


@sync_router.patch('/{sync_id}', status_code=201)
def edit_sync(
        request: Request,
        sync_id: int,
        update_sync: UpdateSync = Body(...),
        db: Session = Depends(get_database),
    ) -> Sync:
    """
    Update the Sync with the given ID. Only provided fields are updated.

    - sync_id: ID of the Sync to update.
    - update_sync: UpdateSync containing fields to update.
    """

    # Get contextual logger
    log = request.state.log

    # Get existing Sync, raise 404 if DNE
    sync = get_sync(db, sync_id, raise_exc=True)
    update_sync_dict = update_sync.dict()

    # Verify any indicated Templates exist and update Sync
    changed = False
    if (template_ids := getattr(update_sync, 'template_ids', None)) is not None:
        if template_ids != sync.template_ids:
            templates = get_all_templates(db, update_sync_dict)
            sync.assign_templates(templates, log=log)
            changed = True

    # Update Sync itself
    for attribute, value in update_sync_dict.items():
        if value is not None and getattr(sync, attribute) != value:
            setattr(sync, attribute, value)
            log.debug(f'Sync[{sync.id}].{attribute} = {value}')
            changed = True

    # If Sync was changed, update database
    if changed:
        db.commit()

    return sync


@sync_router.delete('/delete/{sync_id}', status_code=204)
def delete_sync(
        request: Request,
        sync_id: int,
        delete_series: bool = False,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Delete the Sync with the given ID.

    - sync_id: ID of the Sync to delete.
    - delete_series: Whether to delete Series that were added by this
    Sync.
    """

    # Get associated Sync, raise 404 if DNE
    sync = get_sync(db, sync_id, raise_exc=True)

    # If deleting Series, iterate and delete Series and all Episodes
    if delete_series:
        for series in sync.series:
            delete_series(
                db, series, commit_changes=False, log=request.state.log
            )

    db.delete(sync)
    db.commit()


@sync_router.get('/all', status_code=200)
def get_all_syncs(
        db: Session = Depends(get_database),
    ) -> list[Sync]:
    """
    Get all defined Syncs.
    """

    return db.query(models.sync.Sync).all()


@sync_router.get('/emby/all', tags=['Emby'], status_code=200)
def get_all_emby_syncs(
        db: Session = Depends(get_database),
    ) -> list[EmbySync]:
    """
    Get all defined Syncs that interface with Emby.
    """

    return db.query(models.sync.Sync).filter_by(interface='Emby').all()


@sync_router.get('/jellyfin/all', tags=['Jellyfin'], status_code=200)
def get_all_jellyfin_syncs(
        db: Session = Depends(get_database),
    ) -> list[JellyfinSync]:
    """
    Get all defined Syncs that interface with Jellyfin.
    """

    return db.query(models.sync.Sync).filter_by(interface='Jellyfin').all()


@sync_router.get('/plex/all', tags=['Plex'], status_code=200)
def get_all_plex_syncs(
        db: Session = Depends(get_database),
    ) -> list[PlexSync]:
    """
    Get all defined Syncs that interface with Plex.
    """

    return db.query(models.sync.Sync).filter_by(interface='Plex').all()


@sync_router.get('/sonarr/all', tags=['Sonarr'], status_code=200)
def get_all_sonarr_syncs(
        db: Session = Depends(get_database),
    ) -> list[SonarrSync]:
    """
    Get all defined Syncs that interface with Sonarr.
    """

    return db.query(models.sync.Sync).filter_by(interface='Sonarr').all()


@sync_router.get('/{sync_id}', status_code=200)
def get_sync_by_id(
        sync_id: int,
        db: Session = Depends(get_database),
    ) -> Sync:
    """
    Get the Sync with the given ID.

    - sync_id: ID of the Sync to retrieve.
    """

    return get_sync(db, sync_id, raise_exc=True)


@sync_router.post('/{sync_id}', status_code=201)
def run_sync_(
        background_tasks: BackgroundTasks,
        request: Request,
        sync_id: int,
        db: Session = Depends(get_database),
    ) -> list[Series]:
    """
    Run the given Sync by querying the assigned interface, adding any
    new series to the database. Return a list of any new Series.

    - sync_id: ID of the Sync to run.
    """

    # Get existing Sync, raise 404 if DNE
    sync = get_sync(db, sync_id, raise_exc=True)

    return run_sync(db, sync, background_tasks, log=request.state.log)
