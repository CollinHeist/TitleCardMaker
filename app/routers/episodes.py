from pathlib import Path
from requests import get
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Response, UploadFile

from modules.Debug import log
from modules.SeriesInfo import SeriesInfo

from app.dependencies import (
    get_database, get_preferences, get_emby_interface, get_jellyfin_interface,
    get_plex_interface, get_sonarr_interface, get_tmdb_interface
)
import app.models as models
from app.routers.fonts import get_font
from app.routers.series import get_series
from app.routers.templates import get_template
from app.schemas.base import UNSPECIFIED
from app.schemas.episode import Episode, NewEpisode, UpdateEpisode
from modules.TieredSettings import TieredSettings


def get_episode(db, episode_id, *, raise_exc=True) -> Optional[Episode]:
    """
    Get the Episode with the given ID from the given Database.

    Args:
        db: SQL Database to query for the given Episode.
        episode_id: ID of the Episode to query for.
        raise_exc: Whether to raise 404 if the given Episode does not 
            exist. If False, then only an error message is logged.

    Returns:
        Episode with the given ID. If one cannot be found and raise_exc
        is False, or if the given ID is None, then None is returned.

    Raises:
        HTTPException with a 404 status code if the Episode cannot be
        found and raise_exc is True.
    """

    # No ID provided, return immediately
    if episode_id is None:
        return None

    episode = db.query(models.episode.Episode).filter_by(id=episode_id).first()
    if episode is None:
        if raise_exc:
            raise HTTPException(
                status_code=404,
                detail=f'Episode {episode_id} not found',
            )
        else:
            log.error(f'Episode {episode_id} not found')
            return None

    return episode


def refresh_all_episode_data():
    """
    Schedule-able function to refresh the episode data for all Series in
    the Database.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get all Series
            all_series = db.query(models.series.Series).all()
            for series in all_series:
                # TODO add check for "monitored" attribute
                _refresh_episode_data(
                    db, get_preferences(), series, get_emby_interface(),
                    get_jellyfin_interface(), get_plex_interface(),
                    get_sonarr_interface(), get_tmdb_interface(),
                )
    except Exception as e:
        log.exception(f'Failed to refresh all episode data', e)


episodes_router = APIRouter(
    prefix='/episodes',
    tags=['Episodes'],
)


def set_episode_ids(
        db,
        series: 'Series',
        episodes: list['Episode'],
        emby_interface: 'EmbyInterface',
        jellyfin_interface: 'JellyfinInterface',
        plex_interface: 'PlexInterface',
        sonarr_interface: 'SonarrInterface',
        tmdb_interface: 'TMDbInterface') -> None:
    """
    Set the database ID's of the given Episodes using the given
    Interfaces.

    Args:
        db: Database to read/update/modify.
        series: Series of the Episodes whose ID's are being set.
        episodes: List of Episodes to set the ID's of.
        *_interface: Interface(s) to set ID's from.
    """

    # Get corresponding EpisodeInfo object for this Episode
    episode_infos = [episode.as_episode_info for episode in episodes]

    # Set ID's from all possible interfaces
    if emby_interface and series.emby_library_name:
        # TODO validate
        emby_interface.set_episode_ids(series.as_series_info, episode_infos)
    if jellyfin_interface and series.jellyfin_library_name:
        # TODO validate
        jellyfin_interface.set_episode_ids(series.as_series_info, episode_infos)
    if plex_interface and series.plex_library_name:
        plex_interface.set_episode_ids(
            series.plex_library_name, series.as_series_info, episode_infos
        )
    if sonarr_interface:
        sonarr_interface.set_episode_ids(series.as_series_info, episode_infos)
    if tmdb_interface:
        tmdb_interface.set_episode_ids(series.as_series_info, episode_infos)

    # Update database if new ID's are available
    changed = False
    for episode, episode_info in zip(episodes, episode_infos):
        for id_type in episode_info.ids.keys():
            if (getattr(episode, id_type) is None
                and episode_info.has_id(id_type)):
                setattr(episode, id_type, getattr(episode_info, id_type))
                changed = True

    if changed:
        db.commit()

    return None


def _refresh_episode_data(
        db,
        preferences: 'Preferences',
        series: 'Series',
        emby_interface: 'EmbyInterface',
        jellyfin_interface: 'JellyfinInterface',
        plex_interface: 'PlexInterface',
        sonarr_interface: 'SonarrInterface',
        tmdb_interface: 'TMDbInterface',
        background_tasks: Optional[BackgroundTasks] = None) -> None:
    """
    Refresh the episode data for the given Series. This adds any new
    Episodes on the associated episode data source to the Database, 
    updates the titles of any existing Episodes (if indicated), and
    assigns the database ID's of all added/modified Episodes.

    Args:
        db: Database to read/update/modify.
        preferences: Preferences to reference global settings.
        series: Series whose episodes are being refreshed.
        *_interface: Interface(s) to set ID's from.
        background_tasks: Optional BackgroundTasks queue to add the
            Episode ID assignment task to, if provided. If omitted then
            the assignment is done in a blocking manner.

    Raises:
        HTTPException (404) if the Series Template DNE.
        HTTPException (409) if the indicted episode data source cannot
            be communicated with.
    """

    # Query for template if indicated
    template_dict = {}
    if series.template_id is not None:
        template = get_template(db, series.template_id, raise_exc=True)
        template_dict = template.__dict__

    # Get highest priority options
    series_options = {}
    TieredSettings(
        series_options,
        preferences.__dict__,
        template_dict,
        series.__dict__,
    )
    episode_data_source = series_options['episode_data_source']
    sync_specials = series_options['sync_specials']

    # Raise 409 if cannot communicate with the series episode data source
    interface = {
        'Emby': emby_interface,
        'Jellyfin': jellyfin_interface,
        'Plex': plex_interface,
        'Sonarr': sonarr_interface,
        'TMDb': tmdb_interface,
    }.get(episode_data_source, None)
    if interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with {episode_data_source}'
        )

    # Create SeriesInfo for this object to use in querying
    if episode_data_source == 'Emby':
        all_episodes = emby_interface.get_all_episodes(series)
    elif episode_data_source == 'Jellyfin':
        all_episodes = jellyfin_interface.get_all_episodes(
            series.as_series_info, preferences=preferences
        )
    elif episode_data_source == 'Plex':
        # Raise 409 if source is Plex but series has no library
        if series.plex_library_name is None: 
            raise HTTPException(
                status_code=409,
                detail=f'Series does not have an associated library'
            )
        all_episodes = plex_interface.get_all_episodes(
            series.plex_library_name, series.as_series_info,
        )
    elif episode_data_source == 'Sonarr':
        all_episodes = sonarr_interface.get_all_episodes(
            series.as_series_info, preferences=preferences
        )
    elif episode_data_source == 'TMDb':
        all_episodes = tmdb_interface.get_all_episodes(series.as_series_info)

    # Filter episodes
    changed, episodes = False, []
    for episode_info in all_episodes:
        # If a tuple, then it's a tuple of EpisodeInfo and watched status
        watched = None
        if isinstance(episode_info, tuple):
            episode_info, watched = episode_info

        # Skip specials if indicated
        if not sync_specials and episode_info.season_number == 0:
            log.debug(f'{series.log_str} Skipping {episode_info} - not syncing specials')
            continue

        # Check if this episode exists in the database currently
        existing = db.query(models.episode.Episode)\
            .filter_by(
                series_id=series.id,
                season_number=episode_info.season_number,
                episode_number=episode_info.episode_number,
            ).first() 

        # Episode does not exist, add
        if existing is None:
            log.debug(f'{series.log_str} New episode "{episode_info.title.full_title}"')
            episode = models.episode.Episode(
                series_id=series.id,
                title=episode_info.title.full_title,
                **episode_info.indices,
                **episode_info.ids,
                watched=watched,
                airdate=episode_info.airdate,
            )
            db.add(episode)
            changed = True
            episodes.append(episode)
        # Episode exists, check title matches and update watch status
        else:
            # If title matching, update if title does not match
            do_title_match = (
                existing.match_title
                or (existing.match_title is None and series.match_titles)
            )
            add = False
            if (do_title_match
                and existing.title != episode_info.title.full_title):
                existing.title = episode_info.title.full_title
                log.debug(f'{series.log_str} {existing.log_str} Updating title')
                changed, add = True, True
            if watched is not None and existing.watched != watched:
                log.debug(f'{series.log_str} {existing.log_str} Updating watched status')
                existing.watched = watched
                changed, add = True, True

            if add:
                episodes.append(existing)

    # Set Episode ID's for all new Episodes as background task or directly
    if background_tasks is None:
        set_episode_ids(
            db, series, episodes,
            emby_interface, jellyfin_interface, plex_interface,
            sonarr_interface, tmdb_interface
        )
    else:
        background_tasks.add_task(
            set_episode_ids,
            db, series, episodes,
            emby_interface, jellyfin_interface, plex_interface, sonarr_interface,
            tmdb_interface
        )

    # Commit to database if changed
    if changed:
        db.commit()

    return None


@episodes_router.post('/new', status_code=201)
def add_new_episode(
        background_tasks: BackgroundTasks,
        new_episode: NewEpisode = Body(...),
        db = Depends(get_database),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface),
        sonarr_interface = Depends(get_sonarr_interface),
        tmdb_interface = Depends(get_tmdb_interface)) -> Episode:
    """
    Add a new episode to the given series.

    - series_id: Series to add the episode to.
    - new_episode: NewEpisode to add.
    """

    # Verify series exists
    series = get_series(db, new_episode.series_id, raise_exc=True)

    # Create new entry, add to database
    episode = models.episode.Episode(**new_episode.dict())
    db.add(episode)
    db.commit()

    # Add background task to add episode ID's for this Episode
    background_tasks.add_task(
        set_episode_ids,
        db, series, [episode],
        emby_interface, jellyfin_interface, plex_interface, sonarr_interface, tmdb_interface
    )

    return episode


@episodes_router.get('/{episode_id}', status_code=200)
def get_episode_by_id(
        episode_id: int,
        db = Depends(get_database)) -> Episode:
    """
    Get the Episode with the given ID.

    - episode_id: ID of the Episode to retrieve.
    """

    return get_episode(db, episode_id, raise_exc=True)


@episodes_router.delete('/{episode_id}', status_code=204)
def delete_episode(
        episode_id: int,
        db = Depends(get_database)) -> None:
    """
    Delete the Episode with the ID.

    - episode_id: ID of the Episode to delete.
    """

    # Find episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # TODO Delete card files
    ...

    # Delete any associated card entries
    card_query = db.query(models.card.Card).filter_by(episode_id=episode_id)
    log.debug(f'Deleted {card_query.count()} assocated cards')
    card_query.delete()

    # Delete episode
    log.debug(f'Deleted Episode {episode_id}')
    db.query(models.episode.Episode).filter_by(id=episode_id).delete()
    db.commit()

    return None


@episodes_router.delete('/series/{series_id}', status_code=200, tags=['Series'])
def delete_all_series_episodes(
        series_id: int,
        db = Depends(get_database)) -> list[int]:
    """
    Delete all Episodes for the Series with the given ID.

    - series_id: ID of the Series to delete the Episodes of.
    """

    # Get list of episode ID's to delete
    query = db.query(models.episode.Episode).filter_by(series_id=series_id)
    deleted = [episode.id for episode in query.all()]

    # Delete all associated Episodes
    query.delete()
    db.commit()

    return deleted


@episodes_router.post('/{series_id}/refresh', status_code=201)
def refresh_episode_data(
        background_tasks: BackgroundTasks,
        series_id: int,
        response: Response,
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface),
        sonarr_interface = Depends(get_sonarr_interface),
        tmdb_interface = Depends(get_tmdb_interface)) -> list[Episode]:
    """
    Refresh the episode data associated with the given series. This
    queries the series' episode data source for any new episodes, and
    returns all the series episodes.

    - series_id: Series whose episode data to refresh.
    """

    # Query for this series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Refresh episode data, use BackgroundTasks for ID assignment
    _refresh_episode_data(
        db, preferences, 
        series,
        emby_interface, jellyfin_interface, plex_interface, sonarr_interface,
        tmdb_interface,
        background_tasks,
    )

    # Return all of this Series Episodes
    return db.query(models.episode.Episode).filter_by(series_id=series_id).all()


@episodes_router.patch('/{episode_id}', status_code=200)
def update_episode_config(
        episode_id: int,
        update_episode: UpdateEpisode = Body(...),
        db = Depends(get_database)) -> Episode:
    """
    Update the Epiode with the given ID. Only provided fields are 
    updated.

    - episode_id: ID of the Episode to update.
    - update_episode: UpdateEpisode containing fields to update.
    """
    log.critical(f'{update_episode.dict()=}')
    # Get this episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)
    
    # If any reference ID's were indicated, verify referenced object exists
    get_series(db, getattr(update_episode, 'series_id', None), raise_exc=True)
    get_template(db, getattr(update_episode, 'template_id', None), raise_exc=True)
    get_font(db, getattr(update_episode, 'font_id', None), raise_exc=True)

    # Update each attribute of the object
    changed = False
    for attr, value in update_episode.dict().items():
        if value != UNSPECIFIED and getattr(episode, attr) != value:
            log.debug(f'Episode[{episode_id}].{attr} = {value}')
            setattr(episode, attr, value)
            changed = True

    # If any values were changed, commit to database
    if changed:
        db.commit()

    return episode
    

@episodes_router.get('/{series_id}/all', status_code=200, tags=['Series'])
def get_all_series_episodes(
        series_id: int,
        order_by: Literal['index', 'absolute'] = 'index', 
        db = Depends(get_database)) -> list[Episode]:
    """
    Get all the episodes associated with the given series.

    - series_id: Series being queried.
    - order_by: How to order the returned episodes.
    """

    query = db.query(models.episode.Episode).filter_by(series_id=series_id)
    
    if order_by == 'index':
        return query.order_by(models.episode.Episode.season_number)\
            .order_by(models.episode.Episode.episode_number)\
            .all()
    elif order_by == 'absolute':
        return query.order_by(models.episode.Episode.absolute_number).all()
    else:
        raise HTTPException(
            status_code=500,
            detail=f'Cannot order by "{order_by}"',
        )