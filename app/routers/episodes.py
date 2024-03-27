from logging import Logger
from typing import Literal

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.database.query import get_all_templates, get_episode, get_series
from app.database.session import Page
from app.dependencies import get_database
from app.internal.auth import get_current_user
from app.internal.cards import delete_cards, refresh_remote_card_types
from app.internal.episodes import (
    set_episode_ids, refresh_episode_data, update_episode_config
)
from app.models.card import Card
from app.models.episode import Episode as EpisodeModel
from app.models.loaded import Loaded
from app.models.series import Series
from app.schemas.episode import (
    BatchUpdateEpisode, Episode, EpisodeOverview, NewEpisode, UpdateEpisode
)


episodes_router = APIRouter(
    prefix='/episodes',
    tags=['Episodes'],
    dependencies=[Depends(get_current_user)],
)


@episodes_router.post('/new', status_code=201)
def add_new_episode(
        request: Request,
        new_episode: NewEpisode = Body(...),
        db: Session = Depends(get_database),
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
    episode = EpisodeModel(**new_episode_dict)
    db.add(episode)
    db.commit()

    # Assign Templates
    episode.assign_templates(templates, log=request.state.log)
    db.commit()

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=request.state.log)

    # Add ID's for this Episode
    set_episode_ids(db, series, [episode], log=request.state.log)

    return episode


@episodes_router.get('/episode/{episode_id}')
def get_episode_by_id(
        episode_id: int,
        db: Session = Depends(get_database),
    ) -> Episode:
    """
    Get the Episode with the given ID.

    - episode_id: ID of the Episode to retrieve.
    """

    return get_episode(db, episode_id, raise_exc=True)


@episodes_router.delete('/episode/{episode_id}', status_code=204)
def delete_episode(
        request: Request,
        episode_id: int,
        db: Session = Depends(get_database),
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
        db.query(Card).filter_by(episode_id=episode_id),
        db.query(Loaded).filter_by(episode_id=episode_id),
        log=request.state.log,
    )

    # Delete Episode itself
    db.delete(episode)
    db.commit()


@episodes_router.delete('/series/{series_id}', tags=['Series'])
def delete_all_series_episodes(
        request: Request,
        series_id: int,
        db: Session = Depends(get_database),
    ) -> list[int]:
    """
    Delete all Episodes for the Series with the given ID.

    - series_id: ID of the Series to delete the Episodes of.
    """

    # Get list of Episode ID's to delete
    query = db.query(EpisodeModel).filter_by(series_id=series_id)
    deleted = [episode.id for episode in query]

    # Delete card files, Card objects, and Loaded objects
    delete_cards(
        db,
        db.query(Card).filter_by(series_id=series_id),
        db.query(Loaded).filter_by(series_id=series_id),
        log=request.state.log,
    )

    # Delete all associated Episodes
    query.delete()
    db.commit()

    return deleted


@episodes_router.post('/series/{series_id}/refresh', status_code=201)
def refresh_episode_data_(
        request: Request,
        series_id: int,
        db: Session = Depends(get_database),
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
    refresh_episode_data(db, series, None, log=request.state.log)


@episodes_router.patch('/batch')
def update_multiple_episode_configs(
        request: Request,
        update_episodes: list[BatchUpdateEpisode] = Body(...),
        db: Session = Depends(get_database),
    ) -> list[Episode]:
    """
    Update all the Epiodes at once. Only provided fields are updated.

    - update_episodes: List of BatchUpdateEpisode containing fields to
    update.
    """

    # Get contextual logger
    log = request.state.log

    # Update each Episode in the list
    episodes, changed = [], False
    for update_obj in update_episodes:
        # Get this Episode, raise 404 if DNE
        episode = get_episode(db, update_obj.episode_id, raise_exc=True)

        # Apply changes
        changed |= update_episode_config(
            db, episode, update_obj.update_episode, log=log
        )

        # Append updated Episode
        episodes.append(episode)

    # If any values were changed, commit to database; refresh card types
    if changed:
        db.commit()
        refresh_remote_card_types(db, log=log)

    return episodes


@episodes_router.patch('/episode/{episode_id}')
def update_episode_config_(
        request: Request,
        episode_id: int,
        update_episode: UpdateEpisode = Body(...),
        db: Session = Depends(get_database),
    ) -> Episode:
    """
    Update the Epiode with the given ID. Only provided fields are
    updated.

    - episode_id: ID of the Episode to update.
    - update_episode: UpdateEpisode containing fields to update.
    """

    # Get contextual logger
    log: Logger = request.state.log

    # Get this Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # If any values were changed, commit to database
    if update_episode_config(db, episode, update_episode, log=log):
        db.commit()

        # Refresh card types in case new remote type was specified
        refresh_remote_card_types(db, log=log)

    return episode


@episodes_router.get('/series/{series_id}', tags=['Series'])
def get_all_series_episodes(
        series_id: int,
        order_by: Literal['index', 'absolute', 'id'] = 'index',
        db: Session = Depends(get_database),
    ) -> Page[Episode]:
    """
    Get all the episodes associated with the given series.

    - series_id: Series being queried.
    - order_by: How to order the returned episodes.
    """

    # Query for Episodes of this Series
    query = db.query(EpisodeModel).filter_by(series_id=series_id)

    # Order by indicated attribute
    if order_by == 'index':
        sorted_query = query.order_by(EpisodeModel.season_number)\
            .order_by(EpisodeModel.episode_number)
    elif order_by == 'absolute':
        sorted_query = query.order_by(EpisodeModel.absolute_number)
    elif order_by == 'id':
        sorted_query = query

    return paginate(sorted_query)


@episodes_router.get('/series/{series_id}/overview', tags=['Series'])
def get_series_episode_overview_data(
        series_id: int,
        order_by: Literal['index', 'absolute', 'id'] = 'index',
        db: Session = Depends(get_database),
    ) -> Page[EpisodeOverview]:
    """
    Get all the episodes associated with the given series.

    - series_id: Series being queried.
    - order_by: How to order the returned episodes.
    """

    # Query for Episodes of this Series
    query = db.query(EpisodeModel).filter_by(series_id=series_id)

    # Order by indicated attribute
    if order_by == 'index':
        sorted_query = query.order_by(EpisodeModel.season_number)\
            .order_by(EpisodeModel.episode_number)
    elif order_by == 'absolute':
        sorted_query = query.order_by(EpisodeModel.absolute_number)
    elif order_by == 'id':
        sorted_query = query

    return paginate(sorted_query)


@episodes_router.delete('/batch/delete')
def batch_delete_episodes(
        request: Request,
        series_ids: list[int] = Body(...),
        delete_title_cards: bool = Query(default=True),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Perform a batch operation to delete all the Episodes, Cards, and
    Loaded queries for all the Series with the given IDs.
    """

    for series in db.query(Series).filter(Series.id.in_(series_ids)).all():
        if delete_title_cards:
            delete_cards(
                db,
                db.query(Card).filter_by(series_id=series.id),
                db.query(Loaded).filter_by(series_id=series.id),
                log=request.state.log,
            )
        db.query(EpisodeModel).filter_by(series_id=series.id).delete()
        db.commit()
