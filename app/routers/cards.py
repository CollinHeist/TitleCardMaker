from pathlib import Path
from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, HTTPException, UploadFile, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.dependencies import (
    get_database, get_emby_interface, get_jellyfin_interface, get_preferences,
    get_plex_interface, get_scheduler
)
import app.models as models
from app.routers.episodes import get_episode
from app.routers.fonts import get_font
from app.routers.series import get_series
from app.routers.templates import get_template
from app.schemas.font import DefaultFont
from app.schemas.card import TitleCard, NewTitleCard, PreviewTitleCard
from modules.CleanPath import CleanPath
from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
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
                # Get all Episodes of this Series
                episodes = db.query(models.episode.Episode)\
                    .filter_by(series_id=series.id).all()
                
                # Set watch statuses of the episodes
                _update_episode_watch_statuses(
                    get_emby_interface(), get_jellyfin_interface(),
                    get_plex_interface(),
                    series, episodes
                )

                # Create title cards for each Episode
                for episode in episodes:
                    _create_episode_card(
                        db, get_preferences(), None, series, episode
                    )
    except Exception as e:
        log.exception(f'Failed to create title cards', e)


# Create sub router for all /cards API requests
card_router = APIRouter(
    prefix='/cards',
    tags=['Title Cards'],
)


def create_card(db, preferences, card_model, card_settings):
    # Initialize class of the card type being created

    CardClass = TitleCardCreator.CARD_TYPES[card_settings.get('card_type')]
    card_maker = CardClass(
        **(card_settings | card_settings['extras']),
        preferences=preferences,
    )

    # Create card
    card_maker.create()

    # If file exists, card was created successfully - add to database
    if card_settings['card_file'].exists():
        # Create new card entry
        card_model.filesize = card_settings['card_file'].stat().st_size
        card = models.card.Card(**card_model.dict())
        db.add(card)
        db.commit()
        log.debug(f'Card[{card.id}] Created "{card_settings["card_file"].resolve()}"')
    # Card file does not exist, log failure
    else:
        log.warning(f'Card creation failed')
        card_maker.image_magick.print_command_history()


def _create_episode_card(
        db: 'Database',
        preferences: 'Preferences',
        background_tasks: Optional[BackgroundTasks],
        series: 'Series',
        episode: 'Episode') -> str:
    """

    """

    # Get effective template for this episode
    series_template_dict, episode_template_dict = {}, {}
    if episode.template_id is not None:
        template = get_template(db, episode.template_id, raise_exc=True)
        episode_template_dict = template.card_properties
    elif series.template_id is not None:
        template = get_template(db, series.template_id, raise_exc=True)
        series_template_dict = template.card_properties

    # Get effective font for this episode
    series_font_dict, episode_font_dict = {}, {}
    # Episode has custom font
    if episode.font_id is not None:
        if (font := get_font(db, episode.font_id, raise_exc=False)) is None:
            return ['invalid']
        episode_font_dict = font.card_properties
    # Episode template has custom font
    elif episode_template_dict.get('font_id', None) is not None:
        if (font := get_font(db, episode_template_dict['font_id'],
                                raise_exc=False)) is None:
            return ['invalid']
        episode_font_dict = font.card_properties
    # Series has custom font
    elif series.font_id is not None:
        if (font := get_font(db, series.font_id, raise_exc=False)) is None:
            return ['invalid']
        series_font_dict = font.card_properties
    # Series template has custom font
    elif series_template_dict.get('font_id', None) is not None:
        if (font := get_font(db, series_template_dict['font_id'],
                                raise_exc=False)) is None:
            return ['invalid']
        series_font_dict = font.card_properties

    # Get any existing card for this episode
    existing_card = db.query(models.card.Card)\
        .filter_by(episode_id=episode.id).first()
    
    # Resolve all settings from global -> episode
    card_settings = {}
    TieredSettings(
        card_settings,
        # TODO use card-specific hiding enables
        {'hide_season_text': False, 'hide_episode_text': False},
        DefaultFont,
        preferences.card_properties, # Global preferences are the lowest priority
        series_template_dict,        # Series template
        series_font_dict,            # Series font/template font
        series.card_properties,      # Series
        {'logo_file': series.get_logo_file(preferences.source_directory)},
        episode_template_dict,       # Episode template
        episode_font_dict,           # Episode font/template font
        episode.card_properties,     # Episode
    )
    # Resolve all extras
    card_extras = {}
    TieredSettings(
        card_extras,
        series_template_dict.get('extras', {}),
        series.card_properties.get('extras', {}),
        episode_template_dict.get('extras', {}),
        episode.card_properties.get('extras', {}),
    )
    # Override settings with extras
    TieredSettings(card_settings, card_extras)
    # Merge translations into extras
    TieredSettings(card_extras, episode.translations)
    card_settings['extras'] = card_extras | episode.translations

    # Get the effective card type class
    CardClass = TitleCardCreator.CARD_TYPES[card_settings.get('card_type')]

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
    # TODO modify CardType objects to use title_text attribute instead of title
    card_settings['title'] = card_settings['title_text'] 

    # Get EpisodeInfo for this episode
    episode_info = episode.as_episode_info

    # If no season text was indicated, determine
    if card_settings.get('season_text', None) is None:
        # TODO calculate using season titles
        ranges = SeasonTitleRanges(card_settings.get('season_titles', {}))
        card_settings['season_text'] = ranges.get_season_text(
            episode_info, card_settings,
        )
    
    # If no episode text was indicated, determine
    if card_settings.get('episode_text', None) is None:
        # TODO calculate using episode text format
        card_settings['episode_text'] = 'Episode {episode_number}'.format(**card_settings)

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
        preferences.source_directory, series.path_safe_name
    )

    # Exit if the source file does not exist
    if (CardClass.USES_UNIQUE_SOURCES
        and not card_settings['source_file'].exists()):
        log.debug(f'Episode[{episode.id}] Skipping Card, no source image '
                    f'("{card_settings["source_file"]}")')
        # TODO Maybe not use invalid flag here
        return ['invalid']

    # Get card folder
    if card_settings.get('directory', None) is None:
        series_directory = Path(preferences.card_directory) \
            / series.path_safe_name
    else:
        series_directory = Path(card_settings.get('directory'))

    # If an explicit card file was indicated, use it vs. default
    # TODO get season folder format from preferences object directly
    try:
        if card_settings.get('card_file', None) is None:
            card_settings['card_file'] = series_directory \
                / preferences.season_folder_format.format(**episode_info.indices) \
                / card_settings['card_filename_format'].format(**card_settings)
        else:
            card_settings['card_file'] = series_directory \
                / preferences.season_folder_format.format(**episode_info.indices) \
                / card_settings['card_file']
    except KeyError as e:
        log.exception(f'Cannot format filename - missing data', e)
        return ['invalid']

    # Add extension if needed
    card_file_name = card_settings['card_file'].name
    if not card_file_name.endswith(preferences.VALID_IMAGE_EXTENSIONS):
        path = card_settings['card_file'].parent
        new_name = card_file_name + preferences.card_extension
        card_settings['card_file'] = path / new_name
    card_settings['card_file'] = CleanPath(card_settings['card_file']).sanitize()

    # Create parent directories if needed
    card_settings['card_file'].parent.mkdir(parents=True, exist_ok=True)

    # No existing card, add task to create and add to database
    # card = NewTitleCard(**(card_settings | card_extras))
    card = NewTitleCard(**card_settings)
    if existing_card is None:
        if background_tasks is None:
            create_card(db, preferences, card, card_settings)
        else:
            background_tasks.add_task(
                create_card, db, preferences, card, card_settings
            )
        return ['creating']
    # Existing card doesn't match, delete and remake
    elif any(str(val) != str(getattr(card, attr))
                for attr, val in existing_card.comparison_properties.items()):
        # temporary logging
        for attr, val in existing_card.comparison_properties.items():
            if str(val) != str(getattr(card, attr)):
                log.info(f'Card.{attr} | existing={val}, new={getattr(card, attr)}')
        log.debug(f'Card[{existing_card.id}] Detected change - recreating')
        # Delete existing card file, remove from database
        card_settings['card_file'].unlink(missing_ok=True)
        db.delete(existing_card)
        if background_tasks is None:
            create_card(db, preferences, card, card_settings)
        else:
            background_tasks.add_task(
                create_card, db, preferences, card, card_settings
            )
        return ['creating', 'deleted']
        
    # Existing card matches, do nothing
    return []


def _update_episode_watch_statuses(
        emby_interface: 'EmbyInterface',
        jellyfin_interface: 'JellyfinInterface',
        plex_interface: 'PlexInterface',
        series: 'Series',
        episodes: list['Episode']) -> None:
    """

    """

    if series.emby_library_name is not None:
        if emby_interface is None:
            log.warning(f'Cannot query watch statuses - no Emby connection')
        else:
            emby_interface.update_watched_statuses(
                series.emby_library_name, series.as_series_info, episodes,
            )
    elif series.jellyfin_library_name is not None:
        if jellyfin_interface is None:
            log.warning(f'Cannot query watch statuses - no Jellyfin connection')
        else:
            jellyfin_interface.update_watched_statuses(
                series.jellyfin_library_name, series.as_series_info, episodes,
            )
    elif series.plex_library_name is not None:
        if plex_interface is None:
            log.warning(f'Cannot query watch statuses - no Plex connection')
        else:
            plex_interface.update_watched_statuses(
                series.plex_library_name, series.as_series_info, episodes,
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

    # Delete all associated cards
    deleted = []
    for card in card_query.all():
        if (card_file := Path(card.card_file)).exists():
            card_file.unlink()
            deleted.append(str(card_file))

    # Delete from database
    card_query.delete()
    loaded_query.delete()
    db.commit()

    return deleted


@card_router.post('/preview', status_code=201)
def create_preview_card(
        card: PreviewTitleCard = Body(...),
        db = Depends(get_database),
        preferences = Depends(get_preferences)) -> str:
    """
    Create a preview title card. This uses a fixed source file and
    writes the created card only to a temporary directory. Returns a
    URI to the created card.

    - card: Card definition to create.
    """

    if card.card_type in TitleCardCreator.CARD_TYPES:
        CardClass = TitleCardCreator.CARD_TYPES[card.card_type]
    elif False:
        # TODO handle remote card types
        ...
    else:
        raise HTTPException(
            status_code=400,
            detail=f'Cannot create preview for card type "{card.card_type}"',
        )

    # Get defaults from the card class
    font = {
        'color': CardClass.TITLE_COLOR,
        'title_case': CardClass.DEFAULT_FONT_CASE,
        'file': CardClass.TITLE_FONT,
        'size': 1.0,
    }

    # Query for font if an ID was given, update font with those attributes
    if getattr(card, 'font_id', None) is not None:
        font_object = get_font(db, card.font_id, raise_exc=True)
        for attr in ('file', 'color', 'title_case', 'size', 'kerning', 
                     'stroke_width', 'interline_spacing', 'vertical_shift'):
            if getattr(font_object, attr) is not None:
                font[attr] = getattr(font_object, attr)

    # Use manually specified font attributes if given
    for attr, value in card.dict().items():
        if attr.startswith('font_') and value is not None:
            font[attr[len('font_'):]] = value

    # Update title for given case
    card.title_text = CardClass.CASE_FUNCTIONS[font['title_case']](card.title_text)

    output = preferences.asset_directory / 'tmp' / f'card-{card.style}.png'
    source = preferences.asset_directory / (('art' if 'art' in card.style else 'unique') + '.jpg')

    # Delete card if it already exists
    output.unlink(missing_ok=True)

    kwargs = {
        'source_file': source, 'card_file': output, 'preferences': preferences,
        'title': card.title_text,
        'font_file': font.pop('file'), 'font_color': font['color'],
        'font_size': font.pop('size'),
    } | font | card.dict().pop('extras', {}) | card.dict()
    card = CardClass(**kwargs)
    card.create()

    if output.exists():
        return f'/assets/tmp/{output.name}'

    raise HTTPException(status_code=500, detail='Failed to create preview card')


@card_router.get('/{card_id}', status_code=200)
def get_title_card(
        card_id: int,
        db = Depends(get_database)) -> TitleCard:
    """
    Get the details of the given TitleCard.

    - card_id: ID of the TitleCard to get the details of.
    """

    card = db.query(models.card.Card).filter_by(id=card_id).first()
    if card is None:
        raise HTTPException(
            status_code=404,
            detail=f'Card {card_id} not found',
        )

    return card


@card_router.post('/series/{series_id}', status_code=200, tags=['Series'])
def create_cards_for_series(
        background_tasks: BackgroundTasks,
        series_id: int,
        preferences = Depends(get_preferences),
        db = Depends(get_database),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface)) -> dict[str, int]:
    """
    Create the Title Cards for the given Series. This deletes and
    remakes any outdated existing Cards.

    - series_id: ID of the Series to create Title Cards for.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get all Episodes for this Series
    episodes = db.query(models.episode.Episode)\
        .filter_by(series_id=series_id).all()

    # Set watch statuses of the Episodes
    _update_episode_watch_statuses(
        emby_interface, jellyfin_interface, plex_interface, series, episodes
    )

    stats = {'deleted': 0, 'invalid': 0, 'creating': 0}
    for episode in episodes:
        # Create this flag, get status flags
        flags = _create_episode_card(
            db, preferences, background_tasks, series, episode
        )
        for flag in flags:
            stats[flag] += 1

    return stats


@card_router.get('/series/{series_id}', status_code=200, tags=['Series'])
def get_series_cards(
        series_id: int,
        db = Depends(get_database)) -> list[TitleCard]:
    """
    Get all TitleCards for the given Series.

    - series_id: ID of the Series to get the cards of.
    """

    return db.query(models.card.Card).filter_by(series_id=series_id).all()


@card_router.delete('/series/{series_id}', status_code=200, tags=['Series'])
def delete_series_title_cards(
        series_id: int,
        db = Depends(get_database)) -> list[str]:
    """
    Delete all TitleCards for the given Series. Return a list of the
    deleted files.

    - series_id: ID of the Series whose TitleCards to delete.
    """

    card_query = db.query(models.card.Card).filter_by(series_id=series_id)
    loaded_query = db.query(models.loaded.Loaded).filter_by(series_id=series_id)
    return delete_cards(db, card_query, loaded_query)


@card_router.delete('/episode/{episode_id}', status_code=200, tags=['Episodes'])
def delete_episode_title_cards(
        series_id: int,
        db = Depends(get_database)) -> list[str]:
    """
    Delete all TitleCards for the given Episode. Return a list of the
    deleted files.

    - episode_id: ID of the Episode whose TitleCards to delete.
    """

    card_query = db.query(models.card.Card).filter_by(episode_id=episode_id)
    loaded_query = db.query(models.loaded.Loaded).filter_by(episode_id=episode_id)
    return delete_cards(db, card_query, loaded_query)


@card_router.delete('/card/{card_id}', status_code=200)
def delete_title_card(
        card_id: int,
        db = Depends(get_database)) -> list[str]:
    """
    Delete the TitleCard with the given ID. Return a list of the
    deleted file(s).

    - card_id: ID of the TitleCard to delete.
    """

    card_query = db.query(models.card.Card).filter_by(id=card_id)
    loaded_query = db.query(models.loaded.Loaded).filter_by(id=card_id)
    return delete_cards(db, card_query, loaded_query)


@card_router.post('/episode/{episode_id}', status_code=200, tags=['Episodes'])
def create_card_for_episode(
        episode_id: int,
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface)) -> None:
    """
    Create the Title Cards for the given Episode. This deletes and
    remakes the existing Title Card if it is outdated.

    - episode_id: ID of the Episode to create the Title Card for.
    """

    # Find associated Episode and Series, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)
    series = get_series(db, episode.series_id, raise_exc=True)

    # Set watch status of the Episode
    _update_episode_watch_statuses(
        emby_interface, jellyfin_interface, plex_interface, series, [episode]
    )

    # Create card for this Episode
    _create_episode_card(db, preferences, None, series, episode)


@card_router.get('/episode/{episode_id}', tags=['Episodes'])
def get_episode_card(
        episode_id: int,
        db = Depends(get_database)) -> list[TitleCard]:
    """
    Get all TitleCards for the given Episode.

    - episode_id: ID of the Episode to get the cards of.
    """

    return db.query(models.card.Card).filter_by(episode_id=episode_id).all()


@card_router.post('/key', tags=['Plex', 'Tautulli'], status_code=200)
def remake_card(
        background_tasks: BackgroundTasks,
        plex_rating_key: int = Body(...),
        # TODO other query options
        preferences = Depends(get_preferences),
        db = Depends(get_database),
        plex_interface = Depends(get_plex_interface)) -> None:
    """
    Remake the Title Card for the item associated with the given Plex
    Rating Key. This item can be a Show, Season, or Episode.

    - plex_rating_key: Unique key within Plex that identifies the item
    to remake the card of.
    """

    # Key provided, no PlexInterface, raise 409
    if plex_interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with Plex',
        )

    # Get details of this key from Plex, raise 404 if not found/invalid
    details = plex_interface.get_episode_details(plex_rating_key)
    if len(details) == 0:
        # TODO maybe revise status codes based on exact error
        raise HTTPException(
            status_code=404,
            detail=f'Rating key {plex_rating_key} is invalid'
        )
    log.debug(f'Identified {len(details)} entries from RatingKey={plex_rating_key}')

    Episode = models.episode.Episode
    for library_name, series_info, episode_info, watched_status in details:
        # Find Episode
        episode = db.query(Episode)\
            .filter(episode_info.episode_filter_conditions(Episode))\
            .first()

        # Episode does not exist
        if episode is None:
            # TODO create new episodes?
            ...
        # Episode exists, update card
        else:
            # Get this Episode's associated Series
            series = db.query(models.series.Series)\
                .filter_by(id=episode.series_id).first()

            # If this Series does not exist, raise 404
            if series is None:
                raise HTTPException(
                    status_code=404,
                    detail=f'Episode[{episode.id}] has no associated Series',
                )

            # Update Episode watched status
            if episode.watched != watched_status:
                episode.watched = watched_status
                db.commit()

            # Create card
            _create_episode_card(
                db, preferences, background_tasks, series, episode
            )

    return None