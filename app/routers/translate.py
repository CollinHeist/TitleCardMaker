from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.query import get_episode, get_series
from app.dependencies import get_database, get_tmdb_interface
from app.internal.translate import translate_episode
from app.schemas.episode import Episode

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
        db: Session = Depends(get_database),
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

    # Add background task to translate each Episode
    for episode in series.episodes:
        background_tasks.add_task(
            # Function
            translate_episode,
            # Arguments
            db, episode, tmdb_interface
        )

    return None


@translation_router.post('/episode/{episode_id}', status_code=200)
def add_episode_translations(
        episode_id: int,
        db: Session = Depends(get_database),
        tmdb_interface = Depends(get_tmdb_interface)) -> Episode:
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

    # Find this Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Translate this Episode
    translate_episode(db, episode.series, episode, tmdb_interface)

    return Episode