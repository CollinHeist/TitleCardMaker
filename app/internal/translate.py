from logging import Logger
from time import sleep

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_tmdb_interface
from app.internal.templates import get_effective_templates
import app.models as models
from app.schemas.episode import Episode

from modules.Debug import log
from modules.TieredSettings import TieredSettings
from modules.TMDbInterface2 import TMDbInterface


def translate_all_series(*, log: Logger = log) -> None:
    """
    Schedule-able function to add missing translations to all Series and
    Episodes in the Database.
    """

    try:
        # Cannot translate if no TMDbInterface
        if (tmdb_interface := get_tmdb_interface()) is None:
            log.warning(f'Not translating any Episodes - no TMDbInterface')
            return None

        # Get the Database
        with next(get_database()) as db:
            # Get all Series
            all_series = db.query(models.series.Series).all()
            for series in all_series:
                if not series.monitored:
                    log.debug(f'{series.log_str} is Unmonitored, skipping')
                    continue

                # Translate each Episode
                try:
                    for episode in series.episodes:
                        translate_episode(db, episode, tmdb_interface, log=log)
                except OperationalError:
                    log.debug(f'Database is busy, sleeping..')
                    sleep(30)
    except Exception as e:
        log.exception(f'Failed to add translations - {e}', e)

    return None


def translate_episode(
        db: Session,
        episode: Episode,
        tmdb_interface: TMDbInterface,
        *,
        log: Logger = log,
    ) -> None:
    """
    Add the given Episode's translations to the Database.

    Args:
        db: Database to query and update.
        series_template: Template of the Series that can define
            translations.
        episode: Episode to translate and add translations to.
        tmdb_interface: TMDbInterface to query for translations.
        log: (Keyword) Logger for all log messages.
    """

    # Get the Series and Episode Template
    series = episode.series
    series_template, episode_template = get_effective_templates(series, episode)

    # Get the highest priority translation setting
    translations = TieredSettings.resolve_singular_setting(
        getattr(series_template, 'translations', None),
        series.translations,
        getattr(episode_template, 'translations', None)
    )

    # Exit if there are no translations to add
    if translations is None or len(translations) == 0:
        return None

    # Look for and add each translation for this Episode
    changed = False
    for translation in translations:
        # Get this translation's data key and language code
        data_key = translation['data_key']
        language_code = translation['language_code']

        # Skip if this translation already exists
        if data_key in episode.translations:
            continue

        # Get new translation from TMDb, add to Episode
        translation = tmdb_interface.get_episode_title(
            series.as_series_info, episode.as_episode_info, language_code,
            log=log,
        )
        if translation is not None:
            episode.translations[data_key] = translation
            log.info(f'{series.log_str} {episode.log_str} translated '
                     f'{language_code} -> "{translation}" -> {data_key}')
            changed = True

    # If any translations were added, commit updates to database
    if changed:
        db.commit()

    return None
