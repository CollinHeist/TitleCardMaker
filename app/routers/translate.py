from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.database.query import get_episode, get_series, get_template
from app.dependencies import get_database, get_tmdb_interface
from app.internal.translate import translate_episode
import app.models as models

from modules.Debug import log

translation_router = APIRouter(
    prefix='/translate',
    tags=['Translations'],
)


@translation_router.post('/series/{series_id}', status_code=201)
def add_series_translations(
        background_tasks: BackgroundTasks,
        series_id: int,
        # force_refresh: bool = Query(default=False),
        db = Depends(get_database),
        tmdb_interface = Depends(get_tmdb_interface)) -> None:
    """
    Get all translations for all Episodes of the given Series.

    - series_id: ID of the Series whose Episodes are being translated.
    # - force_refresh: Whether to 
    """

    # Exit if no valid interface to TMDb
    if not tmdb_interface:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with TMDb'
        )

    # Find Series and Template with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)
    series_template = get_template(db, series.template_id, raise_exc=True)

    # Get all Episodes for this series
    episodes = db.query(models.episode.Episode)\
        .filter_by(series_id=series_id).all()

    # Add background task to translate each Episode
    for episode in episodes:
        background_tasks.add_task(
            # Function
            translate_episode,
            # Arguments
            db, series, series_template, episode, tmdb_interface
        )

    return None


@translation_router.post('/episode/{episode_id}', status_code=201)
def add_episode_translations(
        background_tasks: BackgroundTasks,
        episode_id: int,
        # force_refresh: bool = Query(default=False),
        db = Depends(get_database),
        tmdb_interface = Depends(get_tmdb_interface)) -> None:
    """
    Get all translations for the given Episode.

    - episode_id: ID of the Episode to translate.
    """

    # Exit if no valid interface to TMDb
    if not tmdb_interface:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with TMDb'
        )

    # Find this Episode, associated Series/Template, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)
    series = get_series(db, episode.series_id, raise_exc=True)
    series_template = get_template(db, series.template_id, raise_exc=True)

    # Add background task for translating this Episode
    background_tasks.add_task(
        # Function
        translate_episode,
        # Arguments
        db, series, series_template, episode, tmdb_interface
    )