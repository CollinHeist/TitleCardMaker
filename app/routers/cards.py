from pathlib import Path
from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.dependencies import (
    get_database, get_emby_interface, get_jellyfin_interface, get_preferences,
    get_plex_interface, get_scheduler
)
import app.models as models
from app.routers.fonts import get_font
from app.routers.series import get_series
from app.routers.templates import get_template
from app.schemas.font import DefaultFont
from app.schemas.card import TitleCard, NewTitleCard, PreviewTitleCard
from modules.CleanPath import CleanPath
from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
from modules.SeasonTitleRanges import SeasonTitleRanges
from modules.Title import Title
from modules.TitleCard import TitleCard as TitleCardCreator


def priority_merge_v2(merge_base: dict[str, Any],
        *dicts: tuple[dict[str, Any]]) -> None:
    """
    Merges an arbitrary number of dictionaries, with the values of later
    dictionaries taking priority over earlier ones.

    The highest priority non-None value is used if the key is present in
    multiple dictionaries.

    Args:
        merge_base: Dictionary to modify in place with the result of the
            merging.
        dicts: Any number of dictionaries to merge.
    """

    for dict_ in dicts:
        for key, value in dict_.items():
            # Skip underscored keys
            if key.startswith('_'):
                continue

            if value is not None:
                merge_base[key] = value


# Create sub router for all /cards API requests
card_router = APIRouter(
    prefix='/cards',
    tags=['Title Cards'],
)


def create_card(db, preferences, card_settings):
    # Initialize class of the card type being created
    log.debug(f'Creating card')
    CardClass = TitleCardCreator.CARD_TYPES[card_settings.get('card_type')]
    card_maker = CardClass(
        **card_settings,
        **card_settings.get('extras', {}),
        preferences=preferences,
    )

    # Create card
    card_maker.create()

    # If file exists, card was created successfully - add to database
    if card_settings['card_file'].exists():
        # Create new card entry
        card = models.card.Card(
            **NewTitleCard(
                **card_settings,
                filesize=card_settings['card_file'].stat().st_size,
            ).dict()
        )
        db.add(card)
        db.commit()
        log.debug(f'Created Card[{card.id}]')
    # Card file does not exist, log failure
    else:
        log.warning(f'Card creation failed')
        card_maker.image_magick.print_command_history()


def delete_cards(db, card_query, loaded_query) -> list[str]:
    """
    Delete all Title Card files for the given query.

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
        # 'replacements': CardClass.FONT_REPLACEMENTS,
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
        tasks: BackgroundTasks,
        series_id: int,
        preferences = Depends(get_preferences),
        db = Depends(get_database),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface)) -> dict[str, int]:

    # Get this series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get all episodes for this series
    episodes = db.query(models.episode.Episode)\
        .filter_by(series_id=series_id).all()

    # Set watch statuses of the episodes
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

    stats = {'deleted': 0, 'invalid': 0, 'creating': 0}
    for episode in episodes:
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
                stats['invalid'] += 1
                continue
            episode_font_dict = font.card_properties
        # Episode template has custom font
        elif episode_template_dict.get('font_id', None) is not None:
            if (font := get_font(db, episode_template_dict['font_id'],
                                 raise_exc=False)) is None:
                stats['invalid'] += 1
                continue
            episode_font_dict = font.card_properties
        # Series has custom font
        elif series.font_id is not None:
            if (font := get_font(db, series.font_id, raise_exc=False)) is None:
                stats['invalid'] += 1
                continue
            series_font_dict = font.card_properties
        # Series template has custom font
        elif series_template_dict.get('font_id', None) is not None:
            if (font := get_font(db, series_template_dict['font_id'],
                                 raise_exc=False)) is None:
                stats['invalid'] += 1
                continue
            series_font_dict = font.card_properties

        # Get any existing card for this episode
        existing_card = db.query(models.card.Card)\
            .filter_by(episode_id=episode.id).first()
        
        # Resolve all settings from global -> episode
        card_settings = {}
        priority_merge_v2(
            card_settings,
            # TODO use card-specific hiding enables
            {'hide_season_text': False, 'hide_episode_text': False},
            DefaultFont,
            preferences.card_properties, # Global preferences are the lowest priority
            series_template_dict,        # Series template
            series_font_dict,            # Series font/template font
            series.card_properties,      # Series
            episode_template_dict,       # Episode template
            episode_font_dict,           # Episode font/template font
            episode.card_properties,     # Episode
        )

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
        if (card_settings['source_file'].exists()
            and CardClass.USES_UNIQUE_SOURCES):
            log.debug(f'Episode[{episode.id}] Skipping Card, no source image')
            continue

        # Get card folder
        if card_settings.get('directory', None) is None:
            series_directory = Path(preferences.card_directory) \
                / series.path_safe_name
        else:
            series_directory = Path(card_settings.get('directory'))

        # If an explicit card file was indicated, use it vs. default
        # TODO get season folder format from preferences object directly
        if card_settings.get('card_file', None) is None:
            card_settings['card_file'] = series_directory \
                / preferences.season_folder_format.format(**episode_info.indices) \
                / card_settings['filename_format'].format(**card_settings)
        else:
            card_settings['card_file'] = series_directory \
                / preferences.season_folder_format.format(**episode_info.indices) \
                / card_settings['card_file']

        # Add extension if needed
        card_file_name = card_settings['card_file'].name
        if not card_file_name.endswith(preferences.VALID_IMAGE_EXTENSIONS):
            path = card_settings['card_file'].parent
            new_name = card_file_name + preferences.card_extension
            card_settings['card_file'] = path / new_name
        card_settings['card_file'] = CleanPath(card_settings['card_file']).sanitize()

        # Create parent directories if needed
        card_settings['card_file'].parent.mkdir(parents=True, exist_ok=True)

        # Create Card creator
        card = NewTitleCard(**card_settings)
        card_maker = CardClass(
            **card_settings,
            **card_settings.get('extras', {}),
            preferences=preferences,
        )

        # No existing card, add task to create and add to database
        if existing_card is None:
            stats['creating'] += 1
            tasks.add_task(create_card, db, preferences, card_settings)
        # Existing card doesn't match, delete and remake
        elif any(getattr(existing_card, attr) != getattr(card, attr)
                 for attr in existing_card.comparison_properties.keys()):
            log.debug(f'Detected change to TitleCard[{existing_card.id}], '
                      f'recreating')
            card_settings['card_file'].unlink(missing_ok=True)
            db.delete(existing_card)
            stats['deleted'] += 1
            stats['creating'] += 1
            tasks.add_task(create_card, db, preferences, card_settings)
        # Existing card does match, skip
        else:
            continue

    return stats


@card_router.get('/series/{series_id}', status_code=200, tags=['Series'])
def get_series_cards(
        series_id: int,
        db=Depends(get_database)) -> list[TitleCard]:
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


@card_router.post('/episode/{episode_id}', status_code=201, tags=['Episodes'])
def create_card_for_episode(
        episode_id: int,
        db = Depends(get_database)) -> int:

    episode = db.query(models.episode.Episode).filter_by(id=episode_id).first()
    if episode is None:
        raise HTTPException(
            status_code=404,
            detail=f'Episode {episode_id} not found',
        )

    # Get the associated series
    series = db.query(models.series.Series)\
        .filter_by(id=episode.series_id).first()
    if series is None:
        raise HTTPException(
            status_code=404,
            detail=f'Series {episode.series_id} not found',
        )

    ...


@card_router.get('/episode/{episode_id}', tags=['Episodes'])
def get_episode_card(
        episode_id: int,
        db = Depends(get_database)) -> list[TitleCard]:
    """
    Get all TitleCards for the given Episode.

    - episode_id: ID of the Episode to get the cards of.
    """

    return db.query(models.card.Card).filter_by(episode_id=episode_id).all()