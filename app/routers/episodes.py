from pathlib import Path
from requests import get
from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, UploadFile

from modules.Debug import log
from modules.SeriesInfo import SeriesInfo

from app.dependencies import get_database, get_preferences, get_emby_interface,\
    get_jellyfin_interface, get_plex_interface, get_sonarr_interface, \
    get_tmdb_interface
import app.models as models
from app.routers.cards import priority_merge_v2
from app.schemas.base import UNSPECIFIED
from app.schemas.episode import Episode, NewEpisode, UpdateEpisode

episodes_router = APIRouter(
    prefix='/episodes',
    tags=['Episodes'],
)

# /api/episodes/{series_id}/new
@episodes_router.post('/{series_id}/new', status_code=201)
def add_new_episode(
        series_id: int,
        new_episode: NewEpisode = Body(...),
        db = Depends(get_database)) -> Episode:
    """
    Add a new episode to the given series.

    - series_id: Series to add the episode to.
    - new_episode: NewEpisode to add.
    """

    # Verify series exists
    if db.query(models.series.Series).filter_by(id=series_id).first() is None:
        raise HTTPException(
            status_code=404,
            detail=f'Series {series_id} not found',
        )

    # Create new entry, add to database
    episode = models.episode.Episode(
        series_id=series_id,
        **new_episode.dict()
    )
    db.add(episode)
    db.commit()

    return episode


@episodes_router.get('/{episode_id}', status_code=200)
def get_episode_by_id(
        episode_id: int,
        db = Depends(get_database)) -> Episode:
    """
    Get the Episode with the given ID.

    - episode_id: ID of the Episode to retrieve.
    """

    episode = db.query(models.episode.Episode).filter_by(id=episode_id).first()
    if episode is None:
        raise HTTPException(
            status_code=404,
            detail=f'Episode {font_id} not found',
        )

    return episode


@episodes_router.delete('/{episode_id}', status_code=204)
def delete_episode(
        episode_id: int,
        db = Depends(get_database)) -> None:
    """
    Delete the Episode with the ID.

    - episode_id: ID of the Episode to delete.
    """

    # Find episode with this ID, raise 404 if DNE
    episode = db.query(models.episode.Episode).filter_by(id=episode_id).first()
    if episode is None:
        raise HTTPException(
            status_code=404,
            detail=f'Episode {episode_id} not found',
        )

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


@episodes_router.post('/{series_id}/refresh', status_code=201)
def refresh_episode_data(
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
    series = db.query(models.series.Series).filter_by(id=series_id).first()
    if series is None:
        raise HTTPException(
            status_code=404,
            detail=f'Series {series_id} not found',
        )

    # Query for template if indicated
    template_dict = {}
    if series.template_id is not None:  
        template = db.query(models.template.Template)\
            .filter_by(id=series.template_id)
        if template is None:
            raise HTTPException(
                status_code=404,
                detail=f'Series Template {template_id} not found',
            )
        template_dict = template.__dict__

    # Get highest priority options
    series_options = {}
    priority_merge_v2(
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
    }[episode_data_source]
    if interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with {episode_data_source}'
        )

    # Create SeriesInfo for this object to use in querying
    series_info = SeriesInfo(
        series.name, series.year,
        emby_id=series.emby_id, jellyfin_id=series.jellyfin_id,
        sonarr_id=series.sonarr_id, tmdb_id=series.tmdb_id,
        tvdb_id=series.tvdb_id, tvrage_id=series.tvrage_id,
    )

    if episode_data_source == 'Emby':
        all_episodes = emby_interface.get_all_episodes(series)
    elif episode_data_source == 'Jellyfin':
        all_episodes = jellyfin_interface.get_all_episodes(
            series_info, preferences=preferences
        )
    elif episode_data_source == 'Plex':
        # Raise 409 if source is Plex but series has no library
        if series.plex_library_name is None: 
            raise HTTPException(
                status_code=409,
                detail=f'Series does not have an associated library'
            )
        all_episodes = plex_interface.get_all_episodes(
            series.plex_library_name, series_info,
        )
    elif episode_data_source == 'Sonarr':
        all_episodes = sonarr_interface.get_all_episodes(
            series_info, preferences=preferences
        )
    elif episode_data_source == 'TMDb':
        all_episodes = tmdb_interface.get_all_episodes(series_info)

    # Filter episodes
    changed = False
    for episode in all_episodes:
        # Skip specials if indicated
        if not sync_specials and episode.season_number == 0:
            log.debug(f'Skipping {episode} - not syncing specials')
            continue

        # Check if this episode exists in the database currently
        existing = db.query(models.episode.Episode)\
            .filter_by(
                series_id=series_id,
                season_number=episode.season_number,
                episode_number=episode.episode_number,
            ).first() 

        # Episode does not exist, add
        if existing is None:
            log.debug(f'Added {episode} - new episode')
            episode = models.episode.Episode(
                series_id=series.id,
                title=episode.title.full_title,
                **episode.indices,
                **episode.ids,
            )
            db.add(episode)
            changed = True
        # Episode exists, check for title match
        elif ((series.match_titles or existing.match_title)
            and existing.title != episode.title.full_title):
            # TODO Replace card, update title, etc.
            ...
            existing.title = episode.title.full_title
            log.debug(f'Updating title of {episode}')
            changed = True

    # Commit to database if changed
    if changed:
        db.commit()
    
    return db.query(models.episode.Episode).filter_by(series_id=series_id).all()


# /api/episodes/{episode_id}
@episodes_router.patch('/{episode_id}')
def update_episode_config(
        episode_id: int,
        update_episode: UpdateEpisode = Body(...),
        db = Depends(get_database)) -> Episode:
    log.critical(f'{update_episode.dict()=}')
    # Get this episode, raise 404 if DNE
    episode = db.query(models.episode.Episode).filter_by(id=episode_id).first()
    if episode is None:
        raise HTTPException(
            status_code=404,
            detail=f'Episode {episode_id} not found',
        )
    
    # If any reference ID's were indicated, verify referenced object exists
    checks = [
        {'attr': 'series_id', 'model': models.series.Series, 'name': 'Series'},
        {'attr': 'template_id', 'model': models.template.Template, 'name': 'Template'},
        {'attr': 'font_id', 'model': models.font.Font, 'name': 'Font'},
    ]
    for to_check in checks:
        if (id_ := getattr(update_episode, to_check['attr'], None)) is not None:
            if (db.query(to_check['model']).filter_by(id=id_).first()) is None:
                raise HTTPException(
                    status_code=404,
                    detail=f'{to_check["name"]} {id_} not found',
                )

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
    

@episodes_router.get('/{series_id}/all', status_code=200)
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


@episodes_router.get('/all', status_code=201)
def get_all_episodes(
        db = Depends(get_database)) -> list[Episode]:
    """
    Get all defines Episodes.
    """

    return db.query(models.episode.Episode).all()