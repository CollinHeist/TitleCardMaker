from pathlib import Path
from requests import get
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query

from modules.Debug import log

from app.dependencies import get_database, get_preferences, get_tmdb_interface
import app.models as models
from app.routers.episodes import get_episode
from app.routers.series import get_series
from app.routers.templates import get_template
from app.schemas.base import UNSPECIFIED


translation_router = APIRouter(
    prefix='/translate',
    tags=['Translations'],
)


def _translate_episode(
        db,
        series: 'Series',
        series_template: 'Template',
        episode: 'Episode',
        tmdb_interface: 'TMDbInterface') -> None:
    """
    Add the given Episode's translations to the Database.

    Args:
        db: Database to query and update.
        series: Series this Episode belongs to. Can have defined
            translations.
        series_template: Template of the Series that can define
            translations.
        episode: Episode to translate and add translations to.
        tmdb_interface: TMDbInterface to query for translations.
    """

    series_info = series.as_series_info
    episode_info = episode.as_episode_info

    # Get this Episode's Template, exit if specified and DNE
    try:
        episode_template = get_template(db, episode.template_id, raise_exc=True)
    except HTTPException:
        log.warning(f'Episode[{episode.id}] Not translating {episode_info}'
                    f' - missing Template')
        return

    # Get translations for this episode, exit if no translation
    if episode_template is not None and episode_template.translations:
        translations = episode_template.translations
    elif series.translations:
        translations = series.translations
    elif series_template is not None and series_template.translations:
        translations = series_template.translations
    else:
        log.debug(f'Episode[{episode.id}] Has no translation {episode_info}')
        return

    # Look for and add each translation for this Episode
    changed = False
    for translation in translations:
        # Get this translation's data key and language code
        data_key, language_code = translation['data_key'], translation['language_code']

        # Skip if this translation already exists
        if data_key in episode.translations:
            log.debug(f'Episode[{episode.id}] Already has "{data_key}" - skipping')
            continue

        # Get new translation from TMDb, add to Episode
        translation = tmdb_interface.get_episode_title(
            series_info, episode_info, language_code
        )
        if translation is not None:
            episode.translations[data_key] = translation
            log.debug(f'Episode[{episode.id}] Translated {episode_info} {language_code} -> "{translation}" -> {data_key}')
            changed = True

    # If any translations were added, delete existing card, and then
    # commit updates to database
    if changed:
        db.query(models.card.Card).filter_by(episode_id=episode.id).delete()
        db.commit()


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
            _translate_episode,
            db, series, series_template, episode, tmdb_interface
        )


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

    # Find this Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Find associated Series and Template, raise 404 if DNE
    series = get_series(db, episode.series_id, raise_exc=True)
    series_template = get_template(db, series.template_id, raise_exc=True)

    # Add background task for translating this Epiode
    background_tasks.add_task(
        _translate_episode,
        db, series, series_template, episode, tmdb_interface
    )