from logging import Logger
from pathlib import Path
from time import sleep
from typing import Any, Optional

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.exc import OperationalError, PendingRollbackError
from sqlalchemy.orm import Query, Session

from app.database.query import get_interface
from app.dependencies import get_database, get_preferences
from app.internal.episodes import refresh_episode_data
from app.internal.sources import download_episode_source_images
from app.internal.templates import get_effective_templates
from app.internal.translate import translate_episode
from app.models.card import Card
from app.models.episode import Episode
from app.models.font import Font
from app.models.loaded import Loaded
from app.models.series import Library, Series
from app.models.template import Template
from app.schemas.base import Base
from app.schemas.font import DefaultFont
from app.schemas.card import NewTitleCard
from app.schemas.card_type import LocalCardTypeModels

from modules.BaseCardType import BaseCardType
from modules.CleanPath import CleanPath
from modules.Debug import InvalidCardSettings, MissingSourceImage, log
from modules.FormatString import FormatString
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
            for series in db.query(Series).all():
                log.trace(f'Starting to process {series}')
                try:
                    # Refresh Episode data if Series is monitored
                    if series.monitored:
                        try:
                            refresh_episode_data(db, series, log=log)
                        except HTTPException:
                            log.exception(f'Cannot refresh Episode data of {series}')
                    else:
                        log.trace(f'{series} is unmonitored, not refreshing '
                                  f'Episode data')

                    # Set watch statuses of all Episodes
                    try:
                        get_watched_statuses(
                            db, series, series.episodes, log=log
                        )
                    except HTTPException as exc:
                        log.debug(f'Cannot query watched statuses of {series} - {exc}')

                    # Add translations if monitored
                    if series.monitored:
                        for episode in series.episodes:
                            translate_episode(db, episode, commit=False, log=log)
                        db.commit()
                    else:
                        log.trace(f'{series} is unmonitored, skipping translations')

                    # Download Source Images
                    if series.monitored:
                        for episode in series.episodes:
                            download_episode_source_images(
                                db, episode,
                                commit=False, raise_exc=False, log=log
                            )
                        db.commit()
                    else:
                        log.trace(f'{series} is unmonitored, skipping Source '
                                  f'Image selection')

                    # Create Cards for all Episodes
                    for episode in series.episodes:
                        try:
                            create_episode_cards(
                                db, episode, raise_exc=False, log=log
                            )
                        except InvalidCardSettings:
                            log.trace(f'{episode} - skipping Card creation')
                            continue
                        except HTTPException as e:
                            if e.status_code != 404:
                                log.exception(f'{episode} - skipping Card')
                except (PendingRollbackError, OperationalError):
                    if failures > 10:
                        log.error(f'Database is extremely busy, stopping Task')
                        break
                    failures += 1
                    log.debug(f'Database is busy, sleeping..')
                    sleep(30)
    except Exception as e:
        log.exception(f'Failed to create title cards')


def clean_database(*, log: Logger = log) -> None:
    """
    Schedule-able function to remove bad / stale Loaded objects from the
    database.
    """

    try:
        with next(get_database()) as db:
            # Delete Loaded assets with no associated Card
            bad_loaded = db.query(Loaded).filter(Loaded.card_id.is_(None))
            if (bad_count := bad_loaded.count()) > 0:
                log.debug(f'Deleting {bad_count} outdated Loaded records')
                bad_loaded.delete()
            db.commit()

            # Delete Cards with no Series ID, Series, Episode ID, or Episode
            unlinked_cards = db.query(Card)\
                .filter(or_(Card.episode_id.is_(None),
                            Card.series_id.is_(None)))\
                .all()
            unlinked_cards += [card for card in db.query(Card)
                               if card.episode is None or card.series is None]
            for card in set(unlinked_cards):
                log.debug(f'Deleting unlinked {card}')
                card.file.unlink(missing_ok=True)
                db.delete(card)
            db.commit()

            # Delete Episodes with no Series ID, or Series
            for episode in db.query(Episode).all():
                if episode.series_id is None or episode.series is None:
                    log.debug(f'Deleting unlinked Episode {episode.id}')
                    db.delete(episode)
            db.commit()

            # Delete duplicate Cards
            for series in db.query(Series).all():
                episode_ids = db.query(Episode.id)\
                    .filter_by(series_id=series.id)\
                    .all()

                for episode_id in episode_ids:
                    cards = db.query(Card)\
                        .filter_by(episode_id=episode_id[0])\
                        .all()

                    if get_preferences().library_unique_cards:
                        ...
                    else:
                        for card in cards[::-1][1:]: # All but the latest Card
                            log.debug(f'Deleting redundant {card}')
                            card.file.unlink(missing_ok=True)
                            db.delete(card)
            db.commit()
    except Exception as exc:
        log.exception(f'Failed to clean the database', exc)


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
    def _get_unique_card_types(model: Any) -> set[str]:
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
    if card_settings['card_type'] in LocalCardTypeModels:
        CardTypeModel = LocalCardTypeModels[card_settings['card_type']] # local
    else:
        CardTypeModel = CardClass.CardModel # remote

    try:
        return CardClass, CardTypeModel(**card_settings)
    except Exception as exc:
        log.exception('Card validation failed')
        raise HTTPException(
            status_code=400,
            detail=f'Cannot create Card - invalid card settings',
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
        log.info(f'Created {card}')
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
        library: Library associated with this Card.
        log: Logger for all log messages.

    Returns:
        The resolved Card settings as a dictionary.

    Raises:
        HTTPException (400): Invalid Card type / class.
        HTTPException (404): A specified Template / Font is missing.
        MissingSourceImage: The required Source Image is missing.
    """

    # Get effective Template for this Series and Episode
    series = episode.series
    global_template, series_template, episode_template =get_effective_templates(
        series, episode, library
    )
    global_template_dict, series_template_dict, episode_template_dict = {},{},{}
    if global_template is not None:
        global_template_dict = global_template.card_properties
    if series_template is not None:
        series_template_dict = series_template.card_properties
    if episode_template is not None:
        episode_template_dict = episode_template.card_properties

    # Get effective Font for this Series and Episode
    global_font_dict, series_font_dict, episode_font_dict = {}, {}, {}
    if episode.font:
        episode_font_dict = episode.font.card_properties
    elif episode_template and episode_template.font:
        episode_font_dict = episode_template.font.card_properties
    elif series.font:
        series_font_dict = series.font.card_properties
    elif series_template and series_template.font:
        series_font_dict = series_template.font.card_properties
    elif global_template and global_template.font:
        global_font_dict = global_template.font.card_properties

    # Resolve all settings from global -> Episode
    preferences = get_preferences()
    card_settings = TieredSettings.new_settings(
        {'hide_season_text': False, 'hide_episode_text': False},
        DefaultFont,
        preferences.card_properties,
        {'logo_file': series.get_logo_file(),
         'backdrop_file': series.get_series_backdrop(),
         'poster_file': series.get_series_poster()},
        global_template_dict,
        global_font_dict,
        series_template_dict,
        series_font_dict,
        series.card_properties,
        episode_template_dict,
        episode_font_dict,
        episode.get_card_properties(library),
    )

    # Resolve all extras
    card_extras = TieredSettings.new_settings(
        preferences.global_extras.get(card_settings['card_type'], {}),
        global_template_dict.get('extras', {}),
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
    logo_file = Path(card_settings['logo_file'])
    filename = FormatString.new(
        logo_file.stem,
        data=card_settings,
        name='logo filename',
        series=series, episode=episode, log=log,
    )
    card_settings['logo_file'] = series.source_directory \
        / f'{filename}{logo_file.suffix}'

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

    # Apply Font pre-replacements
    repl_in = list(CardClass.FONT_REPLACEMENTS.keys())
    repl_out = list(CardClass.FONT_REPLACEMENTS.values())
    if card_settings.get('font_replacements_in', []):
        repl_in = card_settings['font_replacements_in']
    if card_settings.get('font_replacements_out', []):
        repl_out = card_settings['font_replacements_out']
    card_settings['title'] = Font.apply_replacements(
        card_settings['title'], repl_in, repl_out, pre=True
    )

    # Determine effective title text
    if card_settings.get('auto_split_title', True):
        card_settings['title_text'] = Title(card_settings['title']).split(
            CardClass.get_title_split_characteristics(
                # Make a copy of the characteristics to avoid modifying in-place
                {**CardClass.TITLE_CHARACTERISTICS},
                CardClass.TITLE_FONT,
                card_settings
            )
        )
    else:
        card_settings['title_text'] = card_settings['title'].replace('\\n','\n')

    # Apply title text case function
    if card_settings.get('font_title_case') is None:
        case_func = CardClass.CASE_FUNCTIONS[CardClass.DEFAULT_FONT_CASE]
    else:
        case_func = CardClass.CASE_FUNCTIONS[card_settings['font_title_case']]
    card_settings['title_text'] = case_func(card_settings['title_text'])

    # Apply Font post-replacements
    card_settings['title_text'] = Font.apply_replacements(
        card_settings['title_text'], repl_in, repl_out, pre=False,
    )

    # Apply title text format if indicated
    if (title_format := card_settings.get('title_text_format')) is not None:
        card_settings['title_text'] = FormatString.new(
            title_format, data=card_settings,
            name='title text format', series=series, episode=episode, log=log
        )

    # Get EpisodeInfo for this Episode
    episode_info = episode.as_episode_info

    # Add season title specification
    season_title_ranges = SeasonTitleRanges(
        card_settings.get('season_titles', {}),
        fallback=getattr(CardClass, 'SEASON_TEXT_FORMATTER', None),
        log=log,
    )
    card_settings['season_title'] = season_title_ranges.get_season_text(
        episode_info, card_settings,
    )

    # If no season text was indicated, determine
    if card_settings.get('season_text') is None:
        # Apply season text formatting if indicated
        card_settings['season_text'] = card_settings['season_title']
        if card_settings.get('season_text_format') is not None:
            card_settings['season_text'] = FormatString.new(
                card_settings['season_text_format'], data=card_settings,
                name='season text format', series=series, episode=episode,
                log=log,
            )
    card_settings['season_text'] = card_settings['season_text'].replace('\\n','\n')

    # If no episode text was indicated, determine using ETF
    if card_settings.get('episode_text') is None:
        card_settings['episode_text'] = FormatString.new(
            card_settings.get(
                'episode_text_format', CardClass.EPISODE_TEXT_FORMAT,
            ),
            data=card_settings,
            name='episode text format', series=series, episode=episode, log=log,
        )
    card_settings['episode_text'] = card_settings['episode_text'].replace('\\n','\n')

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
    if card_settings.get('source_file') is None:
        card_settings['source_file'] = episode.get_source_file(
            card_settings['watched_style' if watched else 'unwatched_style'],
        )
    else:
        card_settings['source_file'] = CleanPath(preferences.source_directory \
            / series.path_safe_name \
            / FormatString.new(
                card_settings['source_file'], data=card_settings,
                name='source file format', series=series, episode=episode,
                log=log,
            )).sanitize()

    # Exit if the source file does not exist
    if (CardClass.USES_SOURCE_IMAGES
        and not card_settings['source_file'].exists()):
        log.debug(f'{episode} Card source image '
                  f'({card_settings["source_file"]}) is missing')
        raise MissingSourceImage

    # Get card folder
    if card_settings.get('directory') is None:
        series_directory = Path(preferences.card_directory) \
            / series.path_safe_name
    else:
        series_directory = Path(card_settings.get('directory')[:254])

    # If an explicit card file was indicated, use it vs. default
    if card_settings.get('card_file') is None:
        card_settings['title'] = card_settings['title'].replace('\\n', '')
        filename = FormatString.new_path(
            card_settings['card_filename_format'], data=card_settings,
            name='title card filename', series=series, episode=episode, log=log,
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

    # Add extension if needed
    card_file_name = card_settings['card_file'].name
    if not card_file_name.endswith(preferences.VALID_IMAGE_EXTENSIONS):
        new_name = card_file_name + preferences.card_extension
        card_settings['card_file'] = card_settings['card_file'].parent /new_name
    card_settings['card_file'] =CleanPath(card_settings['card_file']).sanitize()

    # Perform any card-class specific format string evaluations
    card_settings = CardClass.resolve_format_strings(**card_settings)

    return card_settings


def create_episode_card(
        db: Session,
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
    except (HTTPException, InvalidCardSettings) as exc:
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
        create_card(db, card, CardClass, CardTypeModel, library, log=log)
        return None

    # Function to get the existing val
    def _get_existing(attribute: str):
        return existing_card.model_json.get(
            attribute,
            CardTypeModel.__fields__[attribute].default,
        )

    # Existing Card file doesn't exist anymore, remove from db and recreate
    if not existing_card.exists:
        log.debug(f'{episode} Card not found - creating')
        db.delete(existing_card)
        db.commit()
        create_card(db, card, CardClass, CardTypeModel, library, log=log)
        return None

    # Determine if this Card is different than existing Card
    new_model_json = _card_type_model_to_json(CardTypeModel)
    different = False
    if card.card_type != existing_card.card_type:
        log.trace(f'{episode}.card_type = {existing_card.card_type} -> '
                  f'{card.card_type}')
        different = True
    elif card.source_file != existing_card.source_file:
        log.trace(f'{episode}.source_file = {existing_card.source_file} -> '
                  f'{card.source_file}')
        different = True
    else:
        for attr in existing_card.model_json:
            if attr not in new_model_json:
                log.trace(f'{episode}.{attr} reverting to default')
                different = True
                break
        if not different:
            for attr, new_val in new_model_json.items():
                if (not attr.endswith('_rotation_angle')
                    and str(new_val) != str(_get_existing(attr))):
                    log.trace(f'{episode}.{attr} = {_get_existing(attr)!r} -> {new_val!r}')
                    different = True
                    break

    # If different, delete existing file, remove from database, create Card
    if different:
        log.debug(f'{episode} Card config changed - recreating')
        Path(existing_card.card_file).unlink(missing_ok=True)
        db.delete(existing_card)
        db.commit()
        create_card(db, card, CardClass, CardTypeModel, library, log=log)

    return None


def create_episode_cards(
        db: Session,
        episode: Episode,
        *,
        raise_exc: bool = True,
        log: Logger = log,
    ) -> None:
    """
    Create all the Title Card for the given Episode.

    Args:
        db: Database to query and update.
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
                    db, episode, library, raise_exc=raise_exc, log=log
                )
        # Only create Card for primary library
        else:
            create_episode_card(
                db, episode, episode.series.libraries[0],
                raise_exc=raise_exc, log=log,
            )
    else:
        create_episode_card(db, episode, None, raise_exc=raise_exc, log=log)


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
        if (interface :=get_interface(library['interface_id'],raise_exc=False)):
            changed |= interface.update_watched_statuses(
                library['name'], series.as_series_info, episodes, log=log,
            )

    if changed:
        db.commit()


def delete_cards(
        db: Session,
        card_query: Optional[Query] = None,
        loaded_query: Optional[Query] = None,
        *,
        commit: bool = True,
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
        commit: Whether to commit the deletion to the database.
        log: Logger for all log messages.

    Returns:
        List of file names of the deleted cards.
    """

    # Delete all associated Card files
    deleted = []
    for card in card_query.all():
        if (card_file := Path(card.card_file)).exists():
            card_file.unlink()
            log.debug(f'Deleted "{card_file.resolve()}" Title Card')
            deleted.append(str(card_file))

    # Delete from database
    if card_query:
        card_query.delete()
    if loaded_query:
        loaded_query.delete()
    if commit:
        db.commit()

    return deleted
