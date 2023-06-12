from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException

from app.database.query import get_card, get_episode, get_font, get_series
from app.dependencies import (
    get_database, get_emby_interface, get_jellyfin_interface, get_preferences,
    get_plex_interface, get_sonarr_interface, get_tmdb_interface,
)
import app.models as models
from app.internal.cards import (
    create_episode_card, delete_cards, update_episode_watch_statuses,
    validate_card_type_model
)
from app.internal.episodes import refresh_episode_data
from app.internal.series import load_series_title_cards
from app.internal.sources import download_episode_source_image
from app.internal.translate import translate_episode
from app.schemas.card import CardActions, TitleCard, PreviewTitleCard
from app.schemas.font import DefaultFont

from modules.Debug import log
from modules.TieredSettings import TieredSettings

# Create sub router for all /cards API requests
card_router = APIRouter(
    prefix='/cards',
    tags=['Title Cards'],
)


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

    # Get the effective card class
    CardClass = preferences.get_card_type_class(card.card_type)
    if CardClass is None:
        raise HTTPException(
            status_code=400,
            detail=f'Cannot create preview for card type "{card.card_type}"',
        )
    
    # Get Font if indicated
    font_template_dict = {}
    if getattr(card, 'font_id', None) is not None:
        font = get_font(db, card.font_id, raise_exc=True)
        font_template_dict = font.card_properties
    
    # Determine appropriate Source and Output file
    preview_dir = preferences.INTERNAL_ASSET_DIRECTORY / 'preview'
    source = preview_dir / (('art' if 'art' in card.style else 'unique') + '.jpg')
    output = preview_dir / f'card-{card.style}.png'

    # Resolve all settings
    card_settings = TieredSettings.new_settings(
        {'hide_season_text': False, 'hide_episode_text': False},
        {'logo_file': preferences.INTERNAL_ASSET_DIRECTORY / 'logo512.png'},
        DefaultFont,
        preferences.card_properties,
        font_template_dict,
        {'source_file': source, 'card_file': output},
        card.dict(),
        card.extras,
    )

    # Add card default font stuff
    if card_settings.get('font_file', None) is None:
        card_settings['font_file'] = CardClass.TITLE_FONT
    if card_settings.get('font_color', None) is None:
        card_settings['font_color'] = CardClass.TITLE_COLOR

    # Apply title text case function
    if card_settings.get('font_title_case', None) is None:
        case_func = CardClass.CASE_FUNCTIONS[CardClass.DEFAULT_FONT_CASE]
    else:
        case_func = CardClass.CASE_FUNCTIONS[card_settings['font_title_case']]
    card_settings['title_text'] = case_func(card_settings['title_text'])

    CardClass, CardTypeModel = validate_card_type_model(
        preferences, card_settings
    )

    # Delete output if it exists, then create Card
    output.unlink(missing_ok=True)
    card_maker = CardClass(**CardTypeModel.dict(), preferences=preferences)
    card_maker.create()

    # Card created, return URI
    if output.exists():
        return f'/internal_assets/preview/{output.name}'

    raise HTTPException(
        status_code=500,
        detail='Failed to create preview card'
    )


@card_router.get('/{card_id}', status_code=200)
def get_title_card(
        card_id: int,
        db = Depends(get_database)) -> TitleCard:
    """
    Get the details of the given TitleCard.

    - card_id: ID of the TitleCard to get the details of.
    """

    return get_card(db, card_id, raise_exc=True)


@card_router.post('/series/{series_id}', status_code=201, tags=['Series'])
def create_cards_for_series(
        background_tasks: BackgroundTasks,
        series_id: int,
        preferences = Depends(get_preferences),
        db = Depends(get_database),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface)) -> None:
    """
    Create the Title Cards for the given Series. This deletes and
    remakes any outdated existing Cards.

    - series_id: ID of the Series to create Title Cards for.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Set watch statuses of the Episodes
    update_episode_watch_statuses(
        emby_interface, jellyfin_interface, plex_interface,
        series, series.episodes
    )
    db.commit()

    # Create each associated Episode's Card
    for episode in series.episodes:
        create_episode_card(db, preferences, background_tasks, episode)

    return None


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
        db = Depends(get_database)) -> CardActions:
    """
    Delete all TitleCards for the given Series. Return a list of the
    deleted files.

    - series_id: ID of the Series whose TitleCards to delete.
    """

    card_query = db.query(models.card.Card).filter_by(series_id=series_id)
    loaded_query = db.query(models.loaded.Loaded).filter_by(series_id=series_id)

    return CardActions(deleted=len(delete_cards(db, card_query, loaded_query)))


@card_router.delete('/episode/{episode_id}', status_code=200, tags=['Episodes'])
def delete_episode_title_cards(
        episode_id: int,
        db = Depends(get_database)) -> CardActions:
    """
    Delete all TitleCards for the given Episode. Return a list of the
    deleted files.

    - episode_id: ID of the Episode whose TitleCards to delete.
    """

    card_query = db.query(models.card.Card).filter_by(episode_id=episode_id)
    loaded_query = db.query(models.loaded.Loaded).filter_by(episode_id=episode_id)

    return CardActions(deleted=len(delete_cards(db, card_query, loaded_query)))


@card_router.delete('/card/{card_id}', status_code=200)
def delete_title_card(
        card_id: int,
        db = Depends(get_database)) -> CardActions:
    """
    Delete the TitleCard with the given ID. Return a list of the
    deleted file(s).

    - card_id: ID of the TitleCard to delete.
    """

    card_query = db.query(models.card.Card).filter_by(id=card_id)
    loaded_query = db.query(models.loaded.Loaded).filter_by(id=card_id)

    return CardActions(deleted=delete_cards(db, card_query, loaded_query))


@card_router.post('/episode/{episode_id}', status_code=200, tags=['Episodes'])
def create_card_for_episode(
        episode_id: int,
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface)) -> CardActions:
    """
    Create the Title Cards for the given Episode. This deletes and
    remakes the existing Title Card if it is outdated.

    - episode_id: ID of the Episode to create the Title Card for.
    """

    # Find associated Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Set watch status of the Episode
    update_episode_watch_statuses(
        emby_interface, jellyfin_interface, plex_interface,
        episode.series, [episode]
    )

    # Create Card for this Episode, record actions
    actions = create_episode_card(db, preferences, None, episode)
    if actions:
        all_actions = CardActions()
        for action in actions:
            setattr(all_actions, action, getattr(all_actions, action)+1)

        return all_actions

    return CardActions()


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
def create_cards_for_plex_key(
        background_tasks: BackgroundTasks,
        plex_rating_key: int = Body(...),
        preferences = Depends(get_preferences),
        db = Depends(get_database),
        plex_interface = Depends(get_plex_interface),
        sonarr_interface = Depends(get_sonarr_interface),
        tmdb_interface = Depends(get_tmdb_interface)) -> None:
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

    series_to_load = []
    for series_info, episode_info, watched_status in details:
        # Find Episode
        episode = db.query(models.episode.Episode)\
            .filter(episode_info.filter_conditions(models.episode.Episode))\
            .first()

        # Episode does not exist, refresh episode data and try again
        if episode is None:
            # Try and find associated Series, skip if DNE
            series = db.query(models.series.Series)\
                .filter(series_info.filter_conditions(models.series.Series))\
                .first()
            if series is None:
                log.error(f'Cannot find Series for {series_info}')
                continue

            # Series found, refresh data and look for Episode again
            refresh_episode_data(
                db, preferences, series, emby_interface=None,
                jellyfin_interface=None, plex_interface=plex_interface,
                sonarr_interface=sonarr_interface,tmdb_interface=tmdb_interface,
            )
            episode = db.query(models.episode.Episode)\
                .filter(episode_info.filter_conditions(models.episode.Episode))\
                .first()
            if episode is None:
                log.error(f'Cannot find Episode for {series_info} {episode_info}')
                continue

        # Update Episode watched status
        if episode.watched != watched_status:
            episode.watched = watched_status
            db.commit()

        # Look for source, add translation, create card if source exists
        image = download_episode_source_image(
            db, preferences,
            emby_interface=None, jellyfin_interface=None,
            plex_interface=plex_interface, tmdb_interface=tmdb_interface,
            episode=episode,
        )
        translate_episode(db, episode, tmdb_interface)
        if image is None:
            log.info(f'{episode.log_str} has no source image - skipping')
            continue
        create_episode_card(db, preferences, background_tasks, episode)

        # Add this Series to list of Series to load
        if episode.series not in series_to_load:
            series_to_load.append(episode.series)

    # Load all series that require reloading
    for series in series_to_load:
        background_tasks.add_task(
            # Function
            load_series_title_cards,
            # Args
            series, 'Plex', db, emby_interface=None, jellyfin_interface=None,
            plex_interface=plex_interface, force_reload=False,
        )

    return None