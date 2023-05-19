from modules.Debug import log

from app.dependencies import get_database, get_tmdb_interface
from app.internal.templates import get_effective_templates
import app.models as models
from app.database.query import get_template
from app.schemas.episode import Episode
from app.schemas.series import Series

from modules.TieredSettings import TieredSettings
from modules.TMDbInterface2 import TMDbInterface


def translate_all_series() -> None:
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
                # TODO skip unmonitored Series
                # Get the Series Template
                try:
                    series_template = get_template(
                        db, series.template_id, raise_exc=True
                    )
                except Exception as e:
                    log.warning(f'{series.log_str} skipping - missing Template')
                    continue

                # Get all Episodes of this Series
                episodes = db.query(models.episode.Episode)\
                    .filter_by(series_id=series.id).all()
                
                # Translate each Episode
                for episode in episodes:
                    translate_episode(
                        db, series, series_template, episode, tmdb_interface
                    )
    except Exception as e:
        log.exception(f'Failed to add translations', e)

    return None


def translate_episode(
        db: 'Database',
        series: Series,
        episode: Episode,
        tmdb_interface: TMDbInterface) -> None:
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

    # Get the Series and Episode Template
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
            log.debug(f'{series.log_str} {episode.log_str} already has "{data_key}" - skipping')
            continue

        # Get new translation from TMDb, add to Episode
        translation = tmdb_interface.get_episode_title(
            series.as_series_info, episode.as_episode_info, language_code
        )
        if translation is not None:
            episode.translations[data_key] = translation
            log.info(f'{series.log_str} {episode.log_str} translated {language_code} -> "{translation}" -> {data_key}')
            changed = True

    # If any translations were added, commit updates to database
    if changed:
        db.commit()

    return None