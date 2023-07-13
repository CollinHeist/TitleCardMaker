from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.database.query import (
    get_all_templates, get_episode, get_font, get_series
)
from app.database.session import Page
from app.dependencies import *
import app.models as models
from app.internal.cards import delete_cards, refresh_remote_card_types
from app.internal.episodes import set_episode_ids, refresh_episode_data
from app.schemas.base import UNSPECIFIED
from app.schemas.episode import (
    BatchUpdateEpisode, Episode, NewEpisode, UpdateEpisode
)


episodes_router = APIRouter(
    prefix='/episodes',
    tags=['Episodes'],
)


@episodes_router.post('/new', status_code=201)
def add_new_episode(
        request: Request,
        new_episode: NewEpisode = Body(...),
        db: Session = Depends(get_database),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        sonarr_interface: Optional[SonarrInterface] = Depends(get_sonarr_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
    ) -> Episode:
    """
    Add a new episode to the given series.

    - series_id: Series to add the episode to.
    - new_episode: NewEpisode to add.
    """

    # Verify Series exists
    series = get_series(db, new_episode.series_id, raise_exc=True)

    # Get dictionary of object and all associated Templates
    new_episode_dict = new_episode.dict()
    templates = get_all_templates(db, new_episode_dict)

    # Create new entry, add to database
    episode = models.episode.Episode(**new_episode_dict, templates=templates)
    db.add(episode)
    db.commit()

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=request.state.log)

    # Add background task to add episode ID's for this Episode
    set_episode_ids(
        db, series, [episode], emby_interface, jellyfin_interface,
        plex_interface, sonarr_interface, tmdb_interface, log=request.state.log,
    )

    return episode


@episodes_router.get('/{episode_id}', status_code=200)
def get_episode_by_id(
        episode_id: int,
        db: Session = Depends(get_database)
    ) -> Episode:
    """
    Get the Episode with the given ID.

    - episode_id: ID of the Episode to retrieve.
    """

    return get_episode(db, episode_id, raise_exc=True)


@episodes_router.delete('/{episode_id}', status_code=204)
def delete_episode(
        request: Request,
        episode_id: int,
        db: Session = Depends(get_database)
    ) -> None:
    """
    Delete the Episode with the ID.

    - episode_id: ID of the Episode to delete.
    """

    # Find Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Delete card files, Card objects, and Loaded objects
    delete_cards(
        db,
        db.query(models.card.Card).filter_by(episode_id=episode_id),
        db.query(models.loaded.Loaded).filter_by(episode_id=episode_id),
        log=request.state.log,
    )

    # Delete Episode itself
    db.delete(episode)
    db.commit()


@episodes_router.delete('/series/{series_id}', status_code=200, tags=['Series'])
def delete_all_series_episodes(
        request: Request,
        series_id: int,
        db: Session = Depends(get_database)
    ) -> list[int]:
    """
    Delete all Episodes for the Series with the given ID.

    - series_id: ID of the Series to delete the Episodes of.
    """

    # Get list of Episode ID's to delete
    query = db.query(models.episode.Episode).filter_by(series_id=series_id)
    deleted = [episode.id for episode in query]

    # Delete card files, Card objects, and Loaded objects
    delete_cards(
        db,
        db.query(models.card.Card).filter_by(series_id=series_id),
        db.query(models.loaded.Loaded).filter_by(series_id=series_id),
        log=request.state.log,
    )

    # Delete all associated Episodes
    query.delete()
    db.commit()

    return deleted


@episodes_router.post('/{series_id}/refresh', status_code=201)
def refresh_episode_data_(
        background_tasks: BackgroundTasks,
        request: Request,
        series_id: int,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        sonarr_interface: Optional[SonarrInterface] = Depends(get_sonarr_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
    ) -> None:
    """
    Refresh the episode data associated with the given series. This
    queries the series' episode data source for any new episodes, and
    returns all the series episodes.

    - series_id: Series whose episode data to refresh.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Refresh episode data, use BackgroundTasks for ID assignment
    refresh_episode_data(
        db, preferences,
        series,
        emby_interface, jellyfin_interface, plex_interface, sonarr_interface,
        tmdb_interface, background_tasks, log=request.state.log,
    )


@episodes_router.patch('/batch', status_code=200)
def update_multiple_episode_configs(
        request: Request,
        update_episodes: list[BatchUpdateEpisode] = Body(...),
        db: Session = Depends(get_database),
    ) -> list[Episode]:
    """
    Update all the Epiodes with the given IDs. Only provided fields are
    updated.

    - update_episodes: List of BatchUpdateEpisode containing fields to
    update.
    """

    # Get contextual logger
    log = request.state.log

    # Update each Episode in the list
    episodes, changed = [], False
    for update_obj in update_episodes:
        episode_id = update_obj.episode_id
        update_episode = update_obj.update_episode

        # Get this Episode, raise 404 if DNE
        episode = get_episode(db, update_obj.episode_id, raise_exc=True)
        update_episode_dict = update_obj.update_episode.dict()

        # If any reference ID's were indicated, verify referenced object exists
        get_font(db, getattr(update_episode, 'font_id', None), raise_exc=True)

        # Assign Templates if indicated
        if ((template_ids := update_episode_dict.get('template_ids', None))
            not in (None, UNSPECIFIED)):
            if episode.template_ids != template_ids:
                episode.templates = get_all_templates(db, update_episode_dict)
                log.debug(f'{episode.log_str}.templates = {template_ids}')
                changed = True

        # Update each attribute of the object
        for attr, value in update_episode.dict().items():
            if value != UNSPECIFIED and getattr(episode, attr) != value:
                log.debug(f'Episode[{episode_id}].{attr} = {value}')
                setattr(episode, attr, value)
                changed = True

        # Append updated Episode
        episodes.append(episode)

    # If any values were changed, commit to database
    if changed:
        db.commit()

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=log)

    return episodes


@episodes_router.patch('/{episode_id}', status_code=200)
def update_episode_config(
        request: Request,
        episode_id: int,
        update_episode: UpdateEpisode = Body(...),
        db: Session = Depends(get_database)
    ) -> Episode:
    """
    Update the Epiode with the given ID. Only provided fields are
    updated.

    - episode_id: ID of the Episode to update.
    - update_episode: UpdateEpisode containing fields to update.
    """

    # Get contextual logger
    log = request.state.log

    # Get this Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)
    update_episode_dict = update_episode.dict()

    # If any reference ID's were indicated, verify referenced object exists
    get_font(db, getattr(update_episode, 'font_id', None), raise_exc=True)

    # Assign Templates if indicated
    changed = False
    if ((template_ids := update_episode_dict.get('template_ids', None))
        not in (None, UNSPECIFIED)):
        if episode.template_ids != template_ids:
            episode.templates = get_all_templates(db, update_episode_dict)
            changed = True

    # Update each attribute of the object
    for attr, value in update_episode.dict().items():
        if value != UNSPECIFIED and getattr(episode, attr) != value:
            log.debug(f'Episode[{episode_id}].{attr} = {value}')
            setattr(episode, attr, value)
            changed = True

    # If any values were changed, commit to database
    if changed:
        db.commit()

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=log)

    return episode


@episodes_router.get('/{series_id}/all', status_code=200, tags=['Series'])
def get_all_series_episodes(
        series_id: int,
        order_by: Literal['index', 'absolute', 'id'] = 'index',
        db: Session = Depends(get_database)
    ) -> Page[Episode]:
    """
    Get all the episodes associated with the given series.

    - series_id: Series being queried.
    - order_by: How to order the returned episodes.
    """

    # Query for Episodes of this Series
    query = db.query(models.episode.Episode).filter_by(series_id=series_id)

    # Order by indicated attribute
    if order_by == 'index':
        sorted_query = query.order_by(models.episode.Episode.season_number)\
            .order_by(models.episode.Episode.episode_number)
    elif order_by == 'absolute':
        sorted_query = query.order_by(models.episode.Episode.absolute_number)
    elif order_by == 'id':
        sorted_query = query

    return paginate(sorted_query)
