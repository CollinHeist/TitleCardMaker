from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.query import get_episode, get_series
from app.dependencies import get_database, get_tmdb_interface
from app.internal.auth import get_current_user
from app.internal.translate import translate_episode
from app.schemas.episode import Episode

from modules.TMDbInterface2 import TMDbInterface


translation_router = APIRouter(
    prefix='/translate',
    tags=['Translations'],
    dependencies=[Depends(get_current_user)],
)


@translation_router.post('/series/{series_id}', status_code=201)
def add_series_translations(
        series_id: int,
        background_tasks: BackgroundTasks,
        request: Request,
        # force_refresh: bool = Query(default=False),
        db: Session = Depends(get_database),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
    ) -> None:
    """
    Get all translations for all Episodes of the given Series.

    - series_id: ID of the Series whose Episodes are being translated.
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
            db, episode, tmdb_interface, log=request.state.log,
        )


@translation_router.post('/episode/{episode_id}', status_code=200)
def add_episode_translations(
        episode_id: int,
        request: Request,
        db: Session = Depends(get_database),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
    ) -> Episode:
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

    # Translating this Episode
    translate_episode(db, episode, tmdb_interface, log=request.state.log)

    return episode
