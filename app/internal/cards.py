from logging import Logger
from pathlib import Path
from time import sleep
from typing import Optional

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Query, Session

from app.database.query import get_interface
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.episodes import refresh_episode_data
from app.internal.sources import download_episode_source_images 
from app.internal.templates import get_effective_templates
from app.internal.translate import translate_episode
from app.models.card import Card
from app.models.episode import Episode
from app.models.series import Library, Series
from app.models.template import Template
from app.schemas.base import Base
from app.schemas.font import DefaultFont
from app.schemas.card import NewTitleCard
from app.schemas.card_type import LocalCardTypeModels
from modules.BaseCardType import BaseCardType

from modules.CleanPath import CleanPath
from modules.Debug import log
from modules.RemoteCardType2 import RemoteCardType
from modules.RemoteFile import RemoteFile
from modules.SeasonTitleRanges import SeasonTitleRanges
from modules.TieredSettings import TieredSettings
from modules.Title import Title
from modules.TitleCard import TitleCard as TitleCardCreator


def create_all_title_cards(*, log: Logger = log) -> None:
    """
    Schedule-able function to re/create all Title Cards for all Series
    and Episodes in the Database.

    Args:
        log: Logger for all log messages.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get all Series
            failures = 0
            all_series = db.query(Series).all()
            for series in all_series:
                try:
                    # Refresh Episode data if Series is monitored
                    if series.monitored:
                        refresh_episode_data(db, series, log=log)
                    else:
                        log.debug(f'{series!r} is Unmonitored, not refreshing Episode data')

                    # Set watch statuses of all Episodes 
                    get_watched_statuses(db, series, series.episodes, log=log)

                    # Add translations if monitored
                    if series.monitored:
                        for episode in series.episodes:
                            translate_episode(db, episode, commit=False, log=log)
                        db.commit()
                    else:
                        log.debug(f'{series} is Unmonitored, skipping translations')

                    # Download Source Images
                    if series.monitored:
                        for episode in series.episodes:
                            download_episode_source_images(
                                db, episode,
                                commit=False, raise_exc=False, log=log
                            )
                        db.commit()
                    else:
                        log.debug(f'{series} is unmonitored, skipping Source '
                                  f'Image selection')

                    # Create Cards for all Episodes
                    for episode in series.episodes:
                        try:
                            create_episode_cards(
                                db, None, episode, raise_exc=False, log=log
                            )
                        except HTTPException as e:
                            if e.status_code != 404:
                                log.exception(f'{episode} - skipping Card', e)
                except OperationalError:
                    if failures > 10:
                        log.debug(f'Database is extremely busy, stopping Task')
                        break
                    failures += 1
                    log.debug(f'Database is busy, sleeping..')
                    sleep(30)
    except Exception as e:
        log.exception(f'Failed to create title cards', e)


def refresh_all_remote_card_types(*, log: Logger = log) -> None:
    """
    Schedule-able function to refresh all specified RemoteCardTypes.

    Args:
        log: Logger for all log messages.
    """

    try:
        # Refresh the local cards
        get_preferences().parse_local_card_types(log=log)
        # Refresh the remote cards
        with next(get_database()) as db:
            refresh_remote_card_types(db, reset=True, log=log)
    except Exception as e:
        log.exception(f'Failed to refresh RemoteCardTypes', e)


def refresh_remote_card_types(
        db: Session,
        reset: bool = False,
        *,
        log: Logger = log,
    ) -> None:
    """
    Refresh all specified RemoteCardTypes. This re-downloads all
    RemoteCardType and RemoteFile files.

    Args:
        db: Database to query for remote card type identifiers.
        reset: Whether to reset the existing RemoteFile database.
        log: Logger for all log messages.
    """

    # Function to get all unique card types for the table model
    def _get_unique_card_types(model) -> set[str]:
        return set(obj[0] for obj in db.query(model.card_type).distinct().all())

    # Get all card types globally, from Templates, Series, and Episodes
    preferences = get_preferences()
    card_identifiers = {preferences.default_card_type} \
        | _get_unique_card_types(Template) \
        | _get_unique_card_types(Series) \
        | _get_unique_card_types(Episode)

    # Reset loaded remote file(s)
    if reset:
        RemoteFile.reset_loaded_database()

    # Refresh all remote card types
    for card_identifier in card_identifiers:
        # Skip blank identifiers, and builtin or local cards
        if (card_identifier is None
            or card_identifier in TitleCardCreator.CARD_TYPES
            or card_identifier in preferences.local_card_types):
            continue

        # If not resetting, skip already loaded types
        if not reset and card_identifier in preferences.remote_card_types:
            continue

        # Load new type
        log.debug(f'Loading RemoteCardType[{card_identifier}]..')
        card_type = RemoteCardType(card_identifier, log=log)
        if card_type.valid and card_type is not None:
            preferences.remote_card_types[card_identifier] =card_type.card_class


def _card_type_model_to_json(model: Base) -> dict:
    """
    Convert the given Pydantic card type model to JSON (dict) for
    comparison and storing in the Card.model_json Column.

    Args:
        model: Pydantic model to convert.

    Returns:
        JSON conversion of the model (as a dict). All default variables
        are excluded, as well as the `source_file` and `card_file`
        variables.
    """

    return {
        key: str(val.name) if isinstance(val, Path) else str(val)
        for key, val in
        model.dict(
            exclude_defaults=True,
            exclude={'source_file', 'card_file'},
        ).items()
    }


def add_card_to_database(
        db: Session,
        card_model: NewTitleCard,
        CardTypeModel: Base,
        card_file: Path,
        library: Optional[Library],
    ) -> Card:
    """
    Add the given Card to the Database.

    Args:
        db: Database to add the Card entry to.
        card_model: NewTitleCard model being added to the Database.
        card_file: Path to the Card associated with the given model
            being added to the Database.
        library: Library the Card is associated with.

    Returns:
        Created Card entry within the Database.
    """

    # Add Card to database
    card_model.filesize = card_file.stat().st_size
    card = Card(
        **card_model.dict(),
        model_json=_card_type_model_to_json(CardTypeModel),
    )
    db.add(card)

    # Add library details if provided
    if library:
        card.interface_id = library['interface_id']
        card.library_name = library['name']
    db.commit()

    return card


def validate_card_type_model(
        card_settings: dict,
        *,
        log: Logger = log,
    ) -> tuple[type[BaseCardType], Base]:
    """
    Validate the given Card settings into the associated Pydantic model
    and BaseCardType class.

    Args:
        card_settings: Dictionary of Card settings.
        log: Logger for all log messages.

    Returns:
        Tuple of the `BaseCardType` class (to create the card) and the
        Pydantic model of that card (to validate the card parameters).
    """

    # Initialize class of the card type being created
    CardClass = get_preferences().get_card_type_class(
        card_settings['card_type'], log=log
    )
    if CardClass is None:
        raise HTTPException(
            status_code=400,
            detail=f'Cannot create Card - invalid card type {card_settings["card_type"]}',
        )

    # Get Pydantic model for this card type
    if card_settings['card_type'] in LocalCardTypeModels: # Local card type
        CardTypeModel = LocalCardTypeModels[card_settings['card_type']]
    else: # Remote card type
        CardTypeModel = CardClass.CardModel

    try:
        return CardClass, CardTypeModel(**card_settings)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f'Cannot create Card - invalid card settings - {exc}',
        ) from exc


def create_card(
        db: Session,
        card_model: NewTitleCard,
        CardClass: type[BaseCardType],
        CardTypeModel: Base,
        library: Optional[Library],
        *,
        log: Logger = log,
    ) -> None:
    """
    Create the given Card, adding the resulting entry to the Database.

    Args:
        db: Database to add the Card entry to.
        card_model: TitleCard model to update and add to the Database.
        CardClass: Class to initialize for Card creation.
        CardTypeModel: Pydantic model for this Card to pass the
            attributes of to the CardClass.
        library: Library associated with Card.
        log: Logger for all log messages.
    """

    # Create Card
    card_maker = CardClass(**CardTypeModel.dict(),preferences=get_preferences())
    card_maker.create()

    # If file exists, card was created successfully - add to database
    if (card_file := CardTypeModel.card_file).exists():
        card = add_card_to_database(
            db, card_model, CardTypeModel, card_file, library
        )
        log.info(f'Created {card.log_str}')
    # Card file does not exist, log failure
    else:
        log.warning(f'Card creation failed')
        card_maker.image_magick.print_command_history(log=log)


def resolve_card_settings(
        episode: Episode,
        library: Optional[Library] = None,
        *,
        log: Logger = log,
    ) -> dict:
    """
    Resolve the Title Card settings for the given Episode. This evalutes
    all global, Series, and Template overrides.

    Args:
        episode: Episode whose Card settings are being resolved.
        log: Logger for all log messages.

    Returns:
        The resolved Card settings as a dictionary.
    """

    # Get effective Template for this Series and Episode
    series = episode.series
    series_template, episode_template = get_effective_templates(
        series, episode, library
    )
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
    preferences = get_preferences()
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
        episode.get_card_properties(library),
    )

    # Resolve all extras
    card_extras = TieredSettings.new_settings(
        series_template_dict.get('extras', {}),
        series.extras,
        episode_template_dict.get('extras', {}),
        episode.extras,
    )

    # Override settings with extras, and merge translations into extras
    TieredSettings(card_extras, episode.translations)
    TieredSettings(card_settings, card_extras)
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
    except KeyError as exc:
        log.exception(f'{series.log_str} {episode.log_str} Cannot format logo '
                      f'filename - missing data', exc)
        raise HTTPException(
            status_code=400,
            detail=f'Cannot create Card - invalid logo filename format - '
                   f'missing data {exc}',
        ) from exc
    except ValueError as exc:
        log.exception(f'{series.log_str} {episode.log_str} Cannot format logo '
                      f'filename - bad format', exc)
        raise HTTPException(
            status_code=400,
            detail=(
                f'Cannot create Card - invalid logo filename format - bad '
                f'format {exc}'
            )
        ) from exc

    # Get the effective card class
    CardClass = preferences.get_card_type_class(
        card_settings['card_type'], log=log
    )
    if CardClass is None:
        raise HTTPException(
            status_code=400,
            detail=f'Cannot create Card - invalid card type {card_settings["card_type"]}',
        )

    # Add card default font stuff
    if card_settings.get('font_file', None) is None:
        card_settings['font_file'] = CardClass.TITLE_FONT
    if card_settings.get('font_color', None) is None:
        card_settings['font_color'] = CardClass.TITLE_COLOR

    # Apply Font replacements
    replacements = CardClass.FONT_REPLACEMENTS
    if card_settings.get('font_replacements', {}):
        replacements = card_settings['font_replacements']
    for repl_in, repl_out in replacements.items():
        card_settings['title'] = card_settings['title'].replace(
            repl_in, repl_out
        )

    # Determine effective title text
    if card_settings.get('auto_split_title', True):
        title = Title(card_settings['title'])
        card_settings['title_text'] = '\n'.join(title.split(
            **CardClass.TITLE_CHARACTERISTICS
        ))
    else:
        card_settings['title_text'] = card_settings['title'].replace('\\n','\n')

    # Apply title text case function
    if card_settings.get('font_title_case') is None:
        case_func = CardClass.CASE_FUNCTIONS[CardClass.DEFAULT_FONT_CASE]
    else:
        case_func = CardClass.CASE_FUNCTIONS[card_settings['font_title_case']]
    card_settings['title_text'] = case_func(card_settings['title_text'])

    # Apply Font replacements again
    for repl_in, repl_out in replacements.items():
        card_settings['title_text'] = card_settings['title_text'].replace(
            repl_in, repl_out
        )

    # Apply title text format if indicated
    if (title_format := card_settings.get('title_text_format')) is not None:
        try:
            card_settings['title_text'] = title_format.format(**card_settings)
        except KeyError as exc:
            log.exception(f'{series.log_str} {episode.log_str} Title Text '
                          f'Format is invalid - {exc}', exc)
            raise HTTPException(
                status_code=400,
                detail=f'Invalid title text format - missing data {exc}'
            ) from exc
        except ValueError as exc:
            log.exception(f'{series.log_str} {episode.log_str} Title Text '
                          f'Format is invalid - bad format', exc)
            raise HTTPException(
                status_code=400,
                detail=f'Invalid title text format - bad format {exc}'
            ) from exc

    # Get EpisodeInfo for this Episode
    episode_info = episode.as_episode_info

    # If no season text was indicated, determine
    if card_settings.get('season_text') is None:
        ranges = SeasonTitleRanges(
            card_settings.get('season_titles', {}),
            fallback=getattr(CardClass, 'SEASON_TEXT_FORMATTER', None),
            log=log,
        )
        card_settings['season_text'] = ranges.get_season_text(
            episode_info, card_settings,
        )

    # If no episode text was indicated, determine
    if card_settings.get('episode_text') is None:
        if card_settings.get('episode_text_format') is None:
            card_settings['episode_text'] =\
                CardClass.EPISODE_TEXT_FORMAT.format(**card_settings)
        else:
            try:
                fmt = card_settings['episode_text_format']
                card_settings['episode_text'] = fmt.format(**card_settings)
            except KeyError as e:
                log.exception(f'{series.log_str} {episode.log_str} Episode Text'
                              f' Format is invalid - {e}', e)
                raise HTTPException(
                    status_code=400,
                    detail=f'Invalid episode text format - missing data {e}',
                ) from e

    # Set style independent of watched status if both styles match
    watched = None
    if card_settings['watched_style'] == card_settings['unwatched_style']:
        style = card_settings['watched_style']
        card_settings['blur'] = 'blur' in style
        card_settings['grayscale'] = 'grayscale' in style
    # Turn styles into boolean style toggles
    elif (library and
        (watched := episode.get_watched_status(library['interface_id'],
                                              library['name'])) is not None):
        prefix = 'watched' if watched else 'unwatched'
        style = card_settings[f'{prefix}_style']
        card_settings['blur'] = 'blur' in style
        card_settings['grayscale'] = 'grayscale' in style
    # Indeterminate watch status, cannot determine styles
    else:
        card_settings['blur'] = False
        card_settings['grayscale'] = False

    # Add source file
    if card_settings.get('source_file', None) is None:
        card_settings['source_file'] = episode.get_source_file(
            card_settings['watched_style' if watched else 'unwatched_style'],
        )
    else:
        try:
            card_settings['source_file'] = preferences.source_directory \
                / series.path_safe_name \
                / card_settings['source_file'].format(**card_settings)[:254]
        except KeyError as e:
            log.exception(f'{series.log_str} {episode.log_str} Source File '
                            f'Format is invalid - {e}', e)
            raise HTTPException(
                status_code=400,
                detail=f'Cannot create Card - invalid source file format, '
                        f'missing data {e}',
            ) from e

    # Exit if the source file does not exist
    if (CardClass.USES_UNIQUE_SOURCES
        and not card_settings['source_file'].exists()):
        log.debug(f'{series.log_str} {episode.log_str} Card source image '
                    f'({card_settings["source_file"].name}) is missing')
        raise HTTPException(
            status_code=404,
            detail=f'Cannot create Card - missing source image',
        )

    # Get card folder
    if card_settings.get('directory', None) is None:
        series_directory = Path(preferences.card_directory) \
            / series.path_safe_name
    else:
        series_directory = Path(card_settings.get('directory')[:254])

    # If an explicit card file was indicated, use it vs. default
    try:
        if card_settings.get('card_file', None) is None:
            card_settings['title'] = card_settings['title'].replace('\\n', '')
            filename = CleanPath.sanitize_name(
                card_settings['card_filename_format'].format(**card_settings)
            )
            # Add library-specific identifier to filename if indicated
            if library is not None and preferences.library_unique_cards:
                filename += f' [{library["interface"]} {library["name"]}]'
            card_settings['card_file'] = series_directory \
                / preferences.get_folder_format(episode_info) \
                / filename
        else:
            card_settings['card_file'] = series_directory \
                / preferences.get_folder_format(episode_info) \
                / CleanPath.sanitize_name(card_settings['card_file'])
    except KeyError as e:
        log.exception(f'{series.log_str} {episode.log_str} Cannot format Card '
                      f'filename - missing data', e)
        raise HTTPException(
            status_code=400,
            detail=f'Cannot create Card - invalid filename format',
        ) from e

    # Add extension if needed
    card_file_name = card_settings['card_file'].name
    if not card_file_name.endswith(preferences.VALID_IMAGE_EXTENSIONS):
        new_name = card_file_name + preferences.card_extension
        card_settings['card_file'] = card_settings['card_file'].parent /new_name
    card_settings['card_file'] = CleanPath(card_settings['card_file']).sanitize()

    return card_settings


def create_episode_card(
        db: Session,
        background_tasks: Optional[BackgroundTasks],
        episode: Episode,
        library: Optional[Library],
        *,
        raise_exc: bool = True,
        log: Logger = log,
    ) -> None:
    """
    Create the singular Title Card for the given Episode in the given
    library.

    Args:
        db: Database to query and update.
        background_tasks: Optional BackgroundTasks to queue card
            creation within.
        episode: Episode whose Cards are being created.
        raise_exc: Whether to raise any HTTPExceptions.
        log: Logger for all log messages.

    Raises:
        HTTPException: If the card settings are invalid and `raise_exc`
            is True.
    """

    # Resolve Card settings
    series = episode.series
    try:
        card_settings = resolve_card_settings(episode, library, log=log)
    except HTTPException as exc:
        if raise_exc:
            raise exc
        return None

    # Get a validated card class, and card type Pydantic model
    CardClass, CardTypeModel = validate_card_type_model(card_settings, log=log)

    # Create NewTitleCard object for these settings
    card = NewTitleCard(
        **card_settings,
        series_id=series.id,
        episode_id=episode.id,
    )

    # Create Card parent directories if needed
    card_settings['card_file'].parent.mkdir(parents=True, exist_ok=True)

    # Inner function to begin card creation as a background task or immediately
    def _start_card_creation():
        if background_tasks is None:
            create_card(db, card, CardClass, CardTypeModel, library, log=log)
        else:
            background_tasks.add_task(
                create_card,
                db, card, CardClass, CardTypeModel, library, log=log,
            )

    # Find existing Card
    # Library unique mode is disabled, look for any Card for this Episode
    if not get_preferences().library_unique_cards or not library:
        existing_card = db.query(Card).filter_by(episode_id=episode.id).first()
    elif library:
        # Look for Card associated with this library OR no library (if
        # the library was just added to the Series)
        existing_card = db.query(Card)\
            .filter(Card.episode_id==episode.id,
                    or_(and_(Card.interface_id==library['interface_id'],
                             Card.library_name==library['name']),
                        and_(Card.interface_id.is_(None),
                             Card.library_name.is_(None))))\
            .first()

    # No existing Card, begin creation
    if not existing_card:
        _start_card_creation()
        return None

    # Function to get the existing val
    def _get_existing(attribute: str) -> Any:
        return existing_card.model_json.get(
            attribute,
            CardTypeModel.__fields__[attribute].default,
        )

    # Existing Card file doesn't exist anymore, remove from db and recreate
    if not existing_card.exists:
        log.debug(f'{series.log_str} {episode.log_str} Card not found - creating')
        db.delete(existing_card)
        db.commit()
        _start_card_creation()
        return None

    # Determine if this Card is different than existing Card
    new_model_json = _card_type_model_to_json(CardTypeModel)
    different = (
        # Different card type
        card.card_type != existing_card.card_type
        # Old Card defines an attribute not defined by new Card
        or any(attr not in new_model_json for attr in existing_card.model_json)
        # New Card defines a different value than the old Card
        or any(str(new_val) != str(_get_existing(attr))
            for attr, new_val in new_model_json.items()
            # Skip randomized attributes
            if not attr.endswith('_rotation_angle')
        )
    )

    # If different, delete existing file, remove from database, create Card
    if different:
        log.debug(f'{series.log_str} {episode.log_str} Card config changed - recreating')
        Path(existing_card.card_file).unlink(missing_ok=True)
        db.delete(existing_card)
        db.commit()
        _start_card_creation()

    return None


def create_episode_cards(
        db: Session,
        background_tasks: Optional[BackgroundTasks],
        episode: Episode,
        *,
        raise_exc: bool = True,
        log: Logger = log,
    ) -> None:
    """
    Create all the Title Card for the given Episode.

    Args:
        db: Database to query and update.
        background_tasks: Optional BackgroundTasks to queue Card
            creation within.
        episode: Episode whose Cards are being created.
        raise_exc: Whether to raise any HTTPExceptions.
        log: Logger for all log messages.

    Raises:
        HTTPException: If the card settings are invalid and `raise_exc`
            is True.
    """

    # If parent Series has multiple libraries
    if episode.series.libraries:
        # In library unique mode, create Card for each library
        if get_preferences().library_unique_cards:
            for library in episode.series.libraries:
                create_episode_card(
                    db, background_tasks, episode, library,
                    raise_exc=raise_exc, log=log
                )
        # Only create Card for primary library
        else:
            create_episode_card(
                db, background_tasks, episode, episode.series.libraries[0],
                raise_exc=raise_exc, log=log,
            )
    else:
        create_episode_card(
            db, background_tasks, episode, None, raise_exc=raise_exc, log=log
        )


def get_watched_statuses(
        db: Session,
        series: Series,
        episodes: list[Episode],
        *,
        log: Logger = log,
    ) -> None:
    """
    Update the watch statuses of the given Episodes for the given
    Series. This queries all libraries of this Series.

    Args:
        series: Series whose Episodes are being updated.
        episodes: List of Episodes to update the statuses of.
        log: Logger for all log messages.
    """

    # Get statuses for each library of this Series
    changed = False
    for library in series.libraries:
        if (interface := get_interface(library['interface_id'])):
            changed |= interface.update_watched_statuses(
                library['name'], series.as_series_info, episodes, log=log,
            )

    if changed:
        db.commit()


def delete_cards(
        db: Session,
        card_query: Query,
        loaded_query: Optional[Query] = None,
        *,
        log: Logger = log,
    ) -> list[str]:
    """
    Delete all Title Card files for the given card Query. Also remove
    the two queries from the Database.

    Args:
        db: Database to commit the query deletion to.
        card_query: SQL query for Cards whose card files to delete.
            Query contents itself are also deleted.
        loaded_query: SQL query for loaded assets to delete.
        log: Logger for all log messages.

    Returns:
        List of file names of the deleted cards.
    """

    # Delete all associated Card files
    deleted = []
    for card in card_query.all():
        if (card_file := Path(card.card_file)).exists():
            card_file.unlink()
            log.debug(f'Deleted "{card_file.resolve()}" Card')
            deleted.append(str(card_file))

    # Delete from database
    card_query.delete()
    if loaded_query:
        loaded_query.delete()
    db.commit()

    return deleted
