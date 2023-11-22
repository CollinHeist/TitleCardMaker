from logging import Logger

from sqlalchemy.orm import Session

from app.dependencies import get_tmdb_interfaces
from app.internal.templates import get_effective_templates
from app.schemas.episode import Episode

from modules.Debug import log
from modules.TieredSettings import TieredSettings


def translate_episode(
        db: Session,
        episode: Episode,
        *,
        commit: bool = True,
        log: Logger = log,
    ) -> None:
    """
    Add the given Episode's translations to the Database.

    Args:
        db: Database to query and update.
        series_template: Template of the Series that can define
            translations.
        episode: Episode to translate and add translations to.
        commit: Whether to commit the translations to the database.
        log: Logger for all log messages.
    """

    # Skip if there are no TMDbInterfaces
    if not get_tmdb_interfaces():
        return None

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
        for _, interface in get_tmdb_interfaces():
            translation = interface.get_episode_title(
                series.as_series_info, episode.as_episode_info, language_code,
                log=log,
            )
            if translation is not None:
                episode.translations[data_key] = translation
                log.info(f'{series.log_str} {episode.log_str} translated '
                         f'{language_code} -> "{translation}" -> {data_key}')
                changed = True
                break

    # If any translations were added, commit updates to database
    if commit and changed:
        db.commit()

    return None
