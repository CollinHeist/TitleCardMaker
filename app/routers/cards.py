from pathlib import Path
from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.dependencies import get_preferences
import app.models as models
from app.routers.fonts import get_font
from app.routers.series import get_series
from app.schemas.font import DefaultFont
from app.schemas.card import TitleCard, NewTitleCard, PreviewTitleCard
from modules.CleanPath import CleanPath
from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
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


def create_card(db, preferences, card_settings):
    # Initialize class of the card type being created
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

# Create sub router for all /connection API requests
card_router = APIRouter(
    prefix='/cards',
    tags=['Title Cards'],
)


@card_router.post('/preview')
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
        get_font(db, card.font_id, raise_exc=True)
        for attr in ('file', 'color', 'title_case', 'size', 'kerning', 
                     'stroke_width', 'interline_spacing', 'vertical_shift'):
            if getattr(font_obj, attr) is not None:
                font[attr] = getattr(font_obj, attr)

    # Use manually specified font attributes if given
    for attr, value in card.dict().items():
        if attr.startswith('font_') and value is not None:
            font[attr[len('font_'):]] = value

    # Update title for given case
    card.title_text = CardClass.CASE_FUNCTIONS[font['title_case']](card.title_text)

    output = preferences.asset_directory / 'tmp' / f'card-{card.style}.png'
    source = preferences.asset_directory / (('art' if 'art' in card.style else 'unique') + '.jpg')

    # Delete card if it already exists
    if output.exists():
        output.unlink()

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


@card_router.get('/{card_id}')
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


@card_router.post('/series/{series_id}', status_code=201, tags=['Series'])
def create_cards_for_series(
        tasks: BackgroundTasks,
        series_id: int,
        preferences = Depends(get_preferences),
        db = Depends(get_database)) -> None:

    # Get this series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get all episodes
    episodes = db.query(models.episode.Episode).filter_by(series_id=series_id).all()
    for episode in episodes:
        # Get EpisodeInfo for this episode
        episode_info = EpisodeInfo(
            episode.title, episode.season_number, episode.episode_number,
        )

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
                continue
            episode_font_dict = font.card_properties
        # Episode template has custom font
        elif episode_template_dict.get('font_id', None) is not None:
            if (font := get_font(db, episode_template_dict['font_id'],
                                 raise_exc=False)) is None:
                continue
            episode_font_dict = font.card_properties
        # Series has custom font
        elif series.font_id is not None:
            if (font := get_font(db, series.font_id, raise_exc=False)) is None:
                continue
            series_font_dict = font.card_properties
        # Series template has custom font
        elif series_template_dict.get('font_id', None) is not None:
            if (font := get_font(db, series_template_dict['font_id'],
                                 raise_exc=False)) is None:
                continue
            series_font_dict = font.card_properties

        # Get any existing card for this episode
        existing_card = db.query(models.card.Card)\
            .filter_by(episode_id=episode.id).first()
        
        # Resolve all settings from global -> episode
        card_settings = {}
        priority_merge_v2(
            card_settings,
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
        CardClass = TitleCardCreator.CARD_TYPES[
            card_settings.get('card_type')
        ]

        # Add card default font stuff
        if card_settings.get('font_file', None) is None:
            card_settings['font_file'] = CardClass.TITLE_FONT
        if card_settings.get('font_color', None) is None:
            card_settings['font_color'] = CardClass.TITLE_COLOR

        # Determine effective title text
        if card_settings.get('auto_split_title', True):
            # TODO split accordingly
            card_settings['title_text'] = card_settings['title']

        # If no season text was indicated, determine
        if card_settings.get('season_text', None) is None:
            # TODO calculate using season titles
            card_settings['season_text'] = 'Season {season_number}'.format(**card_settings)
        
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
        else:
            # TODO Evalute whether default should be false if watched status is undetermined
            card_settings['blur'] = False
            card_settings['grayscale'] = False 
        
        # Add source and output keys
        # If an explicit source file was indicated, use it vs. default
        if card_settings.get('source_file', None) is None:
            card_settings['source_file'] = \
                Path(preferences.source_directory) \
                / series.path_safe_name \
                / f's{episode.season_number}e{episode.episode_number}.jpg'
        else:
            card_settings['source_file'] = \
                Path(preferences.source_directory) \
                / series.path_safe_name \
                / card_settings['source_file']

        # Get card folder
        if card_settings.get('directory', None) is None:
            series_directory = Path(preferences.card_directory) \
                / series.path_safe_name
        else:
            series_directory = Path(card_settings.get('directory'))

        # If an explicit card file was indicated, use it vs. default
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
            tasks.add_task(create_card, db, preferences, card_settings)
        # Existing card doesn't match, delete and remake
        elif any(getattr(existing_card, attr) != getattr(card, attr)
                 for attr in existing_card.comparison_properties.keys()):
            log.debug(f'Detected change to TitleCard[{existing_card.id}], '
                      f'recreating')
            card_settings['card_file'].unlink(missing_ok=True)
            db.delete(existing_card)
            tasks.add_task(create_card, db, preferences, card_settings)

    return None


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

    - series_id: ID of the series whose TitleCards to delete.
    """

    # Get all cards for this series
    query = db.query(models.card.Card).filter_by(series_id=series_id)

    # Delete all associated cards
    deleted = []
    for card in query.all():
        if (card_file := Path(card.card_file)).exists():
            card_file.unlink()
            deleted.append(str(card_file))

    # Delete from database,
    query.delete()
    db.commit()

    return deleted


@card_router.post('/episode/{episode_id}', tags=['Episodes'])
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