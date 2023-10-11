from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from app.database.query import get_episode, get_series
from app.dependencies import get_database
from app.internal.auth import get_current_user
from app.internal.translate import translate_episode
from app.schemas.episode import Episode



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
        db: Session = Depends(get_database),
    ) -> None:
    """
    Get all translations for all Episodes of the given Series.

    - series_id: ID of the Series whose Episodes are being translated.
    """

    # Find Series and Template with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Add background task to translate each Episode
    for episode in series.episodes:
        background_tasks.add_task(
            # Function
            translate_episode,
            # Arguments
            db, episode, log=request.state.log,
        )


@translation_router.post('/episode/{episode_id}', status_code=200)
def add_episode_translations(
        episode_id: int,
        request: Request,
        db: Session = Depends(get_database),
    ) -> Episode:
    """
    Get all translations for the given Episode.

    - episode_id: ID of the Episode to translate.
    """

    # Find this Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Translate this Episode
    translate_episode(db, episode, log=request.state.log)

    return episode
