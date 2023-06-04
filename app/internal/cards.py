from pathlib import Path
from typing import Any, Optional, Union

from fastapi import BackgroundTasks

from app.dependencies import (
    get_database, get_emby_interface, get_jellyfin_interface, get_preferences,
    get_plex_interface
)
from app.internal.templates import get_effective_templates
import app.models as models
from app.schemas.font import DefaultFont
from app.schemas.card import NewTitleCard
from app.schemas.episode import Episode
from app.schemas.preferences import Preferences
from app.schemas.series import Series

from modules.CleanPath import CleanPath
from modules.Debug import log
from modules.RemoteCardType2 import RemoteCardType
from modules.RemoteFile import RemoteFile
from modules.SeasonTitleRanges import SeasonTitleRanges
from modules.TieredSettings import TieredSettings
from modules.Title import Title
from modules.TitleCard import TitleCard as TitleCardCreator


def create_all_title_cards():
    """
    Schedule-able function to re/create all Title Cards for all Series
    and Episodes in the Database.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get all Series
            all_series = db.query(models.series.Series).all()
            for series in all_series:
                # Set watch statuses of all Episodes
                update_episode_watch_statuses(
                    get_emby_interface(), get_jellyfin_interface(),
                    get_plex_interface(),
                    series, series.episodes
                )

                # Create Cards for all Episodes
                for episode in series.episodes:
                    create_episode_card(db, get_preferences(), None, episode)
    except Exception as e:
        log.exception(f'Failed to create title cards', e)


def refresh_all_remote_card_types():
    """
    Schedule-able function to refresh all specified RemoteCardTypes.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            refresh_remote_card_types(db, reset=True)
    except Exception as e:
        log.exception(f'Failed to refresh remote card types', e)


def refresh_remote_card_types(
        db: 'Database',
        reset: bool = False) -> None:
    """
    Refresh all specified RemoteCardTypes. This re-downloads all
    RemoteCardType and RemoteFile files.

    Args:
        db: Database to query for remote card type identifiers.
    """

    # Function to get all unique card types for the table model
    def _get_unique_card_types(model) -> set[str]:
        return set(obj[0] for obj in db.query(model.card_type).distinct().all())

    # Get all card types globally, from Templates, Series, and Episodes
    preferences = get_preferences()
    card_identifiers = {preferences.default_card_type} \
        | _get_unique_card_types(models.template.Template) \
        | _get_unique_card_types(models.series.Series) \
        | _get_unique_card_types(models.episode.Episode)

    # Reset loaded remote file(s)
    if reset:
        RemoteFile.reset_loaded_database()

    # Refresh all remote card types
    for card_identifier in card_identifiers:
        # Card type is remote
        if (card_identifier is not None
            and card_identifier not in TitleCardCreator.CARD_TYPES):
            # If not resetting, skip already loaded types
            if not reset and card_identifier in preferences.remote_card_types:
                continue

            # Load new type
            log.debug(f'Loading RemoteCardType[{card_identifier}]..')
            remote_card_type = RemoteCardType(card_identifier)
            if remote_card_type.valid and remote_card_type is not None:
                preferences.remote_card_types[card_identifier] =\
                    remote_card_type.card_class

    return None


def add_card_to_database(
        db: 'Database',
        card_model: NewTitleCard,
        card_file: Path) -> 'Card':
    """
    Add the given Card to the Database.

    Args:
        db: Database to add the Card entry to.
        card_model: NewTitleCard model being added to the Database.
        card_file: Path to the Card associated with the given model
            being added to the Database.

    Returns:
        Created Card entry within the Database.
    """

    card_model.filesize = card_file.stat().st_size
    card = models.card.Card(**card_model.dict())
    db.add(card)
    db.commit()

    return card


def create_card(
        db: 'Database',
        preferences: Preferences,
        card_model: NewTitleCard,
        card_settings: dict[str, Any]) -> None:
    """
    Create the given Card, adding the resulting entry to the Database.

    Args:
        db: Database to add the Card entry to.
        preferences: Preferences to pass to the CardType class.
        card_model: TitleCard model to update and add to the Database.
        card_settings: Settings to pass to the CardType class to
            initialize and create the actual card.
    """

    # Initialize class of the card type being created
    CardClass = preferences.get_card_type_class(card_settings['card_type'])
    if CardClass is None:
        log.error(f'Unable to identify card type "{card_settings["card_type"]}", skipping')
        return None

    card_maker = CardClass(
        **(card_settings | card_settings['extras']),
        preferences=preferences,
    )

    # Create card
    card_maker.create()

    # If file exists, card was created successfully - add to database
    if card_settings['card_file'].exists():
        card = add_card_to_database(db, card_model, card_settings['card_file'])
        log.debug(f'Card[{card.id}] Created "{card_settings["card_file"].resolve()}"')
    # Card file does not exist, log failure
    else:
        log.warning(f'Card creation failed')
        card_maker.image_magick.print_command_history()
    
    return None


def resolve_card_settings(
        preferences: Preferences,
        episode: Episode) -> Union[list[str], dict[str, Any]]:
    """
    Resolve the Title Card settings for the given Episode. This evalutes
    all global, Series, and Template overrides.

    Args:
        preferences: Preferences with the default global settings.
        episode: Episode whose Card settings are being resolved.

    Returns:
        List of CardAction strings if some error occured in setting
        resolution; or the settings themselves as a dictionary.
    """

    # Get effective Template for this Series and Episode
    series = episode.series
    series_template, episode_template = get_effective_templates(series, episode)
    series_template_dict, episode_template_dict = {}, {}
    if series_template is not None:
        series_template_dict = series_template.card_properties
    if episode_template is not None:
        episode_template_dict = episode_template.card_properties

    # Get effective Font for this Series and Episode
    series_font_dict, episode_font_dict = {}, {}
    if episode.font:
        episode_font_dict = episode.font.card_properties
    elif episode_template and episode_template.font:
        episode_font_dict = episode_template.font.card_properties
    elif series.font:
        series_font_dict = series.font.card_properties
    elif series_template and series_template.font:
        series_font_dict = series_template.font.card_properties

    # Resolve all settings from global -> Episode
    card_settings = TieredSettings.new_settings(
        {'hide_season_text': False, 'hide_episode_text': False},
        DefaultFont,
        preferences.card_properties,
        series_template_dict,
        series_font_dict,
        series.card_properties,
        {'logo_file': series.get_logo_file(preferences.source_directory)},
        episode_template_dict,
        episode_font_dict,
        episode.card_properties,
    )

    # Resolve all extras
    card_extras = TieredSettings.new_settings(
        series_template_dict.get('extras', {}),
        series.card_properties.get('extras', {}),
        episode_template_dict.get('extras', {}),
        episode.card_properties.get('extras', {}),
    )

    # Override settings with extras, and merge translations into extras
    TieredSettings(card_settings, card_extras)
    TieredSettings(card_extras, episode.translations)
    card_settings['extras'] = card_extras | episode.translations

    # Resolve logo file format string if indicated
    try:
        card_settings['logo_file'] = Path(card_settings['logo_file'])
        filename = card_settings['logo_file'].stem
        formatted_filename = filename.format(
            season_number=episode.season_number,
            episode_number=episode.episode_number,
            absolute_number=episode.absolute_number,
        )
        card_settings['logo_file'] = Path(series.source_directory) \
            / f"{formatted_filename}{card_settings['logo_file'].suffix}"
    except KeyError as e:
        log.exception(f'Cannot format logo filename - missing data', e)
        return ['invalid']

    # Get the effective card class
    CardClass = preferences.get_card_type_class(card_settings['card_type'])
    if CardClass is None:
        return ['invalid']

    # Add card default font stuff
    if card_settings.get('font_file', None) is None:
        card_settings['font_file'] = CardClass.TITLE_FONT
    if card_settings.get('font_color', None) is None:
        card_settings['font_color'] = CardClass.TITLE_COLOR

    # Determine effective title text
    if card_settings.get('auto_split_title', True):
        title = Title(card_settings['title'])
        card_settings['title_text'] = '\n'.join(title.split(
            **CardClass.TITLE_CHARACTERISTICS
        ))
    else:
        card_settings['title_text'] = card_settings['title']

    # Apply title text case function
    if card_settings.get('font_title_case', None) is None:
        case_func = CardClass.CASE_FUNCTIONS[CardClass.DEFAULT_FONT_CASE]
    else:
        case_func = CardClass.CASE_FUNCTIONS[card_settings['font_title_case']]
    card_settings['title_text'] = case_func(card_settings['title_text'])

    # Get EpisodeInfo for this Episode
    episode_info = episode.as_episode_info

    # If no season text was indicated, determine
    if card_settings.get('season_text', None) is None:
        ranges = SeasonTitleRanges(card_settings.get('season_titles', {}))
        card_settings['season_text'] = ranges.get_season_text(
            episode_info, card_settings,
        )
    
    # If no episode text was indicated, determine
    if card_settings.get('episode_text', None) is None:
        if card_settings.get('episode_text_format', None) is None:
            card_settings['episode_text'] =\
                CardClass.EPISODE_TEXT_FORMAT.format(**card_settings)
        else:
            try:
                fmt = card_settings['episode_text_format']
                card_settings['episode_text'] = fmt.format(**card_settings)
            except KeyError as e:
                log.exception(f'{series.log_str} {episode.log_str} Episode Text Format is invalid - {e}', e)
                return ['invalid']

    # Turn styles into boolean style toggles
    if (watched := card_settings.get('watched', None)) is not None:
        prefix = 'watched' if watched else 'unwatched'
        style = card_settings[f'{prefix}_style']
        card_settings['blur'] = 'blur' in style
        card_settings['grayscale'] = 'grayscale' in style
    # Indeterminate watch status, set styles if both styles match
    elif card_settings['watched_style'] == card_settings['unwatched_style']:
        style = card_settings['watched_style']
        card_settings['blur'] = 'blur' in style
        card_settings['grayscale'] = 'grayscale' in style
    # Indeterminate watch status, cannot determine styles
    else:
        card_settings['blur'] = False
        card_settings['grayscale'] = False 
    
    # Add source and output keys
    card_settings['source_file'] = episode.get_source_file(
        preferences.source_directory,
        series.path_safe_name,
        card_settings['watched_style' if watched else 'unwatched_style'],
    )

    # Exit if the source file does not exist
    if (CardClass.USES_UNIQUE_SOURCES
        and not card_settings['source_file'].exists()):
        log.debug(f'{series.log_str} {episode.log_str} Card source image '
                    f'({card_settings["source_file"]}) is missing')
        return ['missing_source']

    # Get card folder
    if card_settings.get('directory', None) is None:
        series_directory = Path(preferences.card_directory) \
            / series.path_safe_name
    else:
        series_directory = Path(card_settings.get('directory'))

    # If an explicit card file was indicated, use it vs. default
    try:
        if card_settings.get('card_file', None) is None:
            card_settings['card_file'] = series_directory \
                / preferences.get_folder_format(episode_info) \
                / card_settings['card_filename_format'].format(**card_settings)
        else:
            card_settings['card_file'] = series_directory \
                / preferences.get_folder_format(episode_info) \
                / card_settings['card_file']
    except KeyError as e:
        log.exception(f'Cannot format filename - missing data', e)
        return ['invalid']

    # Add extension if needed
    card_file_name = card_settings['card_file'].name
    if not card_file_name.endswith(preferences.VALID_IMAGE_EXTENSIONS):
        new_name = card_file_name + preferences.card_extension
        card_settings['card_file'] = card_settings['card_file'].parent /new_name
    card_settings['card_file'] = CleanPath(card_settings['card_file']).sanitize()

    return card_settings


def create_episode_card(
        db: 'Database',
        preferences: Preferences,
        background_tasks: Optional[BackgroundTasks],
        episode: Episode) -> list[str]:
    """
    Create the Title Card for the given Episode.

    Args:
        db: Database to query and update.
        preferences: Global Preferences to use as lowest priority
            settings.
        background_tasks: Optional BackgroundTasks to queue card
            creation within.
        episode: Episode whose Card is being created.

    Returns:
        List of CardAction strings indicating what ocurred with the
        given Card.
    """

    # Resolve Card settings
    series = episode.series
    card_settings = resolve_card_settings(preferences, episode)

    # If return was a list of CardActions, return those instead of continuing
    if isinstance(card_settings, list):
        return card_settings

    # Create parent directories if needed
    card_settings['card_file'].parent.mkdir(parents=True, exist_ok=True)

    # Create NewTitleCard object for these settings
    card = NewTitleCard(
        **card_settings,
        series_id=series.id,
        episode_id=episode.id,
    )

    # No existing card, create and add to database
    existing_card = episode.card
    if not existing_card:
        if background_tasks is None:
            create_card(db, preferences, card, card_settings)
        else:
            background_tasks.add_task(
                create_card, db, preferences, card, card_settings
            )
        return ['creating']
    
    # Existing card doesn't match, delete and remake
    existing_card = existing_card[0]
    if any(str(val) != str(getattr(card, attr)) 
             for attr, val in existing_card.comparison_properties.items()):
        # TODO delete temporary logging
        for attr, val in existing_card.comparison_properties.items():
            if str(val) != str(getattr(card, attr)):
                log.info(f'Card.{attr} | existing={val}, new={getattr(card, attr)}')
        log.debug(f'{series.log_str} {episode.log_str} Card config changed - recreating')
        # Delete existing card file, remove from database
        Path(existing_card.card_file).unlink(missing_ok=True)
        db.delete(existing_card)
        db.commit()

        # Create new card 
        if background_tasks is None:
            create_card(db, preferences, card, card_settings)
        else:
            background_tasks.add_task(
                create_card, db, preferences, card, card_settings
            )
        return ['creating', 'deleted']

    # Existing card file doesn't exist anymore
    if not Path(existing_card.card_file).exists():
        # Remove existing card from database
        log.debug(f'{series.log_str} {episode.log_str} Card not found - recreating')
        db.delete(existing_card)
        db.commit()

        # Create new card
        if background_tasks is None:
            create_card(db, preferences, card, card_settings)
        else:
            background_tasks.add_task(
                create_card, db, preferences, card, card_settings
            )
        return ['creating']
        
    # Existing card matches, do nothing
    return ['existing']


def update_episode_watch_statuses(
        emby_interface: Optional['EmbyInterface'],
        jellyfin_interface: Optional['JellyfinInterface'],
        plex_interface: Optional['PlexInterface'],
        series: Series,
        episodes: list[Episode]) -> None:
    """
    Update the watch statuses of all Episodes for the given Series.

    Args:
        *_interface: Interface to the media server to query for updated
            watch statuses.
        series: Series whose Episodes are being updated.
        Episodes: List of Episodes to update the statuses of.
    """

    if series.emby_library_name is not None:
        if emby_interface is None:
            log.warning(f'Cannot query watch statuses - no Emby connection')
        else:
            emby_interface.update_watched_statuses(
                series.emby_library_name,
                series.as_series_info,
                episodes,
            )
    elif series.jellyfin_library_name is not None:
        if jellyfin_interface is None:
            log.warning(f'Cannot query watch statuses - no Jellyfin connection')
        else:
            jellyfin_interface.update_watched_statuses(
                series.jellyfin_library_name,
                series.as_series_info,
                episodes,
            )
    elif series.plex_library_name is not None:
        if plex_interface is None:
            log.warning(f'Cannot query watch statuses - no Plex connection')
        else:
            plex_interface.update_watched_statuses(
                series.plex_library_name,
                series.as_series_info,
                episodes,
            )

    return None


def delete_cards(db, card_query, loaded_query) -> list[str]:
    """
    Delete all Title Card files for the given card Query. Also remove
    the two queries from the Database.

    Args:
        db: Database to commit the query deletion to.
        card_query: SQL query for Cards whose card files to delete.
            Query contents itself are also deleted.
        loaded_query: SQL query for loaded assets to delete.

    Returns:
        List of file names of the deleted cards.
    """

    # Delete all associated Card files
    deleted = []
    for card in card_query.all():
        if (card_file := Path(card.card_file)).exists():
            card_file.unlink()
            log.debug(f'Delete "{card_file.resolve()}" card')
            deleted.append(str(card_file))

    # Delete from database
    card_query.delete()
    loaded_query.delete()
    db.commit()

    return deleted