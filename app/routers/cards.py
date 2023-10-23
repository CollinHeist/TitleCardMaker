from typing import Union

from pydantic import PositiveInt

from fastapi import (
    APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request
)
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.database.query import get_card, get_connection, get_episode, get_font, get_interface, get_series
from app.database.session import Page
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app import models
from app.internal.auth import get_current_user
from app.internal.cards import (
    create_episode_card, delete_cards, update_episode_watch_statuses,
    validate_card_type_model
)
from app.internal.episodes import refresh_episode_data
from app.internal.series import load_all_series_title_cards, load_episode_title_card, load_series_title_cards
from app.internal.sources import download_episode_source_image
from app.internal.translate import translate_episode
from app.models.episode import Episode
from app.models.series import Series
from app.schemas.card import CardActions, TitleCard, PreviewTitleCard
from app.schemas.connection import SonarrWebhook
from app.schemas.font import DefaultFont
from modules.EpisodeInfo2 import EpisodeInfo

from modules.PlexInterface2 import PlexInterface
from modules.SeriesInfo import SeriesInfo
from modules.TieredSettings import TieredSettings


# Create sub router for all /cards API requests
card_router = APIRouter(
    prefix='/cards',
    tags=['Title Cards'],
)


@card_router.post('/preview', status_code=201,
                  dependencies=[Depends(get_current_user)])
def create_preview_card(
        request: Request,
        card: PreviewTitleCard = Body(...),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> str:
    """
    Create a preview title card. This uses a fixed source file and
    writes the created card only to a temporary directory. Returns a
    URI to the created card.

    - card: Card definition to create.
    """

    # Get contextual logger
    log = request.state.log

    # Get the effective card class
    CardClass = preferences.get_card_type_class(card.card_type, log=log)
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
    output = preview_dir / f'card-{card.style}{preferences.card_extension}'

    # Resolve all settings
    card_settings = TieredSettings.new_settings(
        {'series_full_name': 'Test Series', 'season_number': 1, 'episode_number': 1},
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

    # Turn manually entered \n into newline
    card_settings['title_text'] = card_settings['title_text'].replace(r'\n', '\n')

    # Apply title text case function
    if card_settings.get('font_title_case', None) is None:
        case_func = CardClass.CASE_FUNCTIONS[CardClass.DEFAULT_FONT_CASE]
    else:
        case_func = CardClass.CASE_FUNCTIONS[card_settings['font_title_case']]
    card_settings['title_text'] = case_func(card_settings['title_text'])

    CardClass, CardTypeModel = validate_card_type_model(card_settings, log=log)

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


@card_router.get('/all', status_code=200,
                 dependencies=[Depends(get_current_user)])
def get_all_title_cards(db: Session = Depends(get_database)) -> Page[TitleCard]:
    """
    Get all defined Title Cards.

    - order_by: How to order the Cards in the returned list.
    """

    return paginate(db.query(models.card.Card))


@card_router.get('/{card_id}', status_code=200,
                 dependencies=[Depends(get_current_user)])
def get_title_card(
        card_id: int,
        db: Session = Depends(get_database)
    ) -> TitleCard:
    """
    Get the details of the given TitleCard.

    - card_id: ID of the TitleCard to get the details of.
    """

    return get_card(db, card_id, raise_exc=True)


@card_router.post('/series/{series_id}', status_code=201, tags=['Series'],
                  dependencies=[Depends(get_current_user)])
def create_cards_for_series(
        background_tasks: BackgroundTasks,
        request: Request,
        series_id: int,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Create the Title Cards for the given Series. This deletes and
    remakes any outdated existing Cards.

    - series_id: ID of the Series to create Title Cards for.
    """

    # Get contextual logger
    log = request.state.log

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Set watch statuses of the Episodes
    update_episode_watch_statuses(series, series.episodes, log=log)
    db.commit()

    # Create each associated Episode's Card
    for episode in series.episodes:
        try:
            create_episode_card(db, background_tasks, episode, log=log)
        except HTTPException as e:
            log.exception(f'{series.log_str} {episode.log_str} Card creation '
                          f'failed - {e.detail}', e)

    return None


@card_router.get('/series/{series_id}', status_code=200, tags=['Series'],
                 dependencies=[Depends(get_current_user)])
def get_series_cards(
        series_id: int,
        db: Session = Depends(get_database)
    ) -> Page[TitleCard]:
    """
    Get all TitleCards for the given Series. Cards are returned in the
    order of their release (e.g. season number, episode number).

    - series_id: ID of the Series to get the cards of.
    """

    return paginate(
        db.query(models.card.Card)\
            .filter_by(series_id=series_id)\
            .order_by(models.card.Card.season_number)\
            .order_by(models.card.Card.episode_number)
    )


@card_router.put('/series/{series_id}/load/all', status_code=200, tags=['Series'])
def load_series_title_cards_into_all_libraries(
        series_id: int,
        request: Request,
        reload: bool = Query(default=False),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Load all of the given Series' Cards.

    - series_id: ID of the Series whose Cards are being loaded.
    - reload: Whether to "force" reload all Cards, even those that have
    already been loaded. If false, only Cards that have not been loaded
    previously (or that have changed) are loaded.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    load_all_series_title_cards(
        series, db, force_reload=reload, log=request.state.log,
    )


@card_router.put('/series/{series_id}/load/library/{library_index}',
                 status_code=200,
                 tags=['Series'])
def load_series_title_cards_into_library(
        request: Request,
        series_id: int,
        library_index: int,
        reload: bool = Query(default=False),
        db: Session = Depends(get_database),
    ) -> None:
    """
    
    """

    # Get this Series and Interface, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get library with this index
    try:
        library = series.libraries[library_index]
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f'No Library with index {library_index}',
        )

    # Get this Library's Connection, raise 404 if DNE
    interface = get_interface(library['interface_id'], raise_exc=True)

    # Load this Library's Cards
    load_series_title_cards(
        series, library['name'], library['interface_id'], db, interface,
        reload, log=request.state.log,
    )


@card_router.get('/episode/{episode_id}', tags=['Episodes'],
                 dependencies=[Depends(get_current_user)])
def get_episode_card(
        episode_id: int,
        db: Session = Depends(get_database),
    ) -> list[TitleCard]:
    """
    Get all TitleCards for the given Episode.

    - episode_id: ID of the Episode to get the cards of.
    """

    return db.query(models.card.Card).filter_by(episode_id=episode_id).all()


@card_router.delete('/series/{series_id}', status_code=200, tags=['Series'],
                    dependencies=[Depends(get_current_user)])
def delete_series_title_cards(
        series_id: int,
        request: Request,
        db: Session = Depends(get_database),
    ) -> CardActions:
    """
    Delete all TitleCards for the given Series. Return a list of the
    deleted files.

    - series_id: ID of the Series whose TitleCards to delete.
    """

    # Create Queries for Cards of this Series
    card_query = db.query(models.card.Card).filter_by(series_id=series_id)
    loaded_query = db.query(models.loaded.Loaded).filter_by(series_id=series_id)

    # Delete cards
    deleted = delete_cards(db, card_query, loaded_query, log=request.state.log)

    return CardActions(deleted=len(deleted))


@card_router.delete('/episode/{episode_id}', status_code=200, tags=['Episodes'],
                    dependencies=[Depends(get_current_user)])
def delete_episode_title_cards(
        episode_id: int,
        request: Request,
        db: Session = Depends(get_database),
    ) -> CardActions:
    """
    Delete all TitleCards for the given Episode. Return a list of the
    deleted files.

    - episode_id: ID of the Episode whose TitleCards to delete.
    """

    # Create Queries for Cards of this Episode
    card_query = db.query(models.card.Card).filter_by(episode_id=episode_id)
    loaded_query = db.query(models.loaded.Loaded).filter_by(episode_id=episode_id)

    # Delete cards
    deleted = delete_cards(db, card_query, loaded_query, log=request.state.log)

    return CardActions(deleted=len(deleted))


@card_router.delete('/card/{card_id}', status_code=200,
                    dependencies=[Depends(get_current_user)])
def delete_title_card(
        card_id: int,
        request: Request,
        db: Session = Depends(get_database)
    ) -> CardActions:
    """
    Delete the TitleCard with the given ID. Return a list of the
    deleted file(s).

    - card_id: ID of the TitleCard to delete.
    """

    # Create Queries for Cards of this Episode
    card_query = db.query(models.card.Card).filter_by(id=card_id)
    loaded_query = db.query(models.loaded.Loaded).filter_by(id=card_id)

    # Delete cards
    deleted = delete_cards(db, card_query, loaded_query, log=request.state.log)

    return CardActions(deleted=len(deleted))


@card_router.post('/episode/{episode_id}', status_code=200, tags=['Episodes'],
                  dependencies=[Depends(get_current_user)])
def create_card_for_episode(
        episode_id: int,
        request: Request,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Create the Title Cards for the given Episode. This deletes and
    remakes the existing Title Card if it is outdated.

    - episode_id: ID of the Episode to create the Title Card for.
    """

    # Find associated Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Set watch status of the Episode
    update_episode_watch_statuses(
        episode.series, [episode], log=request.state.log,
    )

    # Create Card for this Episode
    create_episode_card(db,None, episode, log=request.state.log)


@card_router.post('/key', tags=['Plex', 'Tautulli'], status_code=200)
def create_cards_for_plex_rating_keys(
        request: Request,
        plex_rating_keys: Union[int, list[int]] = Body(...),
        db: Session = Depends(get_database),
        # TODO evaluate if Tautulli can pass query param
        plex_interface: PlexInterface = Depends(require_plex_interface),
    ) -> None:
    """
    Create the Title Card for the item associated with the given Plex
    Rating Key. This item can be a Show, Season, or Episode. This
    endpoint does NOT require an authenticated User so that Tautulli can
    trigger this without any credentials.

    - plex_rating_keys: Unique keys within Plex that identifies the item
    to remake the card of.
    """

    # Get contextual logger
    log = request.state.log

    # Convert to list if only a single key was provided
    if isinstance(plex_rating_keys, int):
        plex_rating_keys = [plex_rating_keys]

    # Get details of each key from Plex, raise 404 if not found/invalid
    details = []
    for key in plex_rating_keys:
        if len(deets := plex_interface.get_episode_details(key, log=log)) == 0:
            raise HTTPException(
                status_code=404,
                detail=f'Rating key {key} is invalid'
            )
        log.debug(f'Identified {len(deets)} entries from RatingKey={key}')
        details += deets

    # Process each set of details
    episodes_to_load = []
    for series_info, episode_info, watched_status in details:
        # Find all matching Episodes
        episodes = db.query(Episode)\
            .filter(episode_info.filter_conditions(Episode))\
            .all()

        # Episode does not exist, refresh episode data and try again
        if not episodes:
            # Try and find associated Series, skip if DNE
            series = db.query(Series)\
                .filter(series_info.filter_conditions(Series))\
                .first()
            if series is None:
                log.info(f'Cannot find Series for {series_info}')
                continue

            # Series found, refresh data and look for Episode again
            refresh_episode_data(db, series, log=log)
            episodes = db.query(Episode)\
                .filter(episode_info.filter_conditions(Episode))\
                .all()
            if not episodes:
                log.info(f'Cannot find Episode for {series_info} {episode_info}')
                continue

        # Get first Episode that matches this Series
        episode, found = None, False
        for episode in episodes:
            if episode.series.as_series_info == series_info:
                found = True
                break

        # If no match, exit
        if not found:
            log.info(f'Cannot find Episode for {series_info} {episode_info}')
            continue

        # Update Episode watched status
        if episode.watched != watched_status:
            episode.watched = watched_status
            db.commit()

        # Look for source, add translation, create card if source exists
        image = download_episode_source_image(db, episode, log=log)
        translate_episode(db, episode, log=log)
        if image is None:
            log.info(f'{episode.log_str} has no source image - skipping')
            continue
        create_episode_card(db, None, episode, log=log)

        # Add this Series to list of Series to load
        if episode.series.plex_library_name is None:
            log.info(f'{episode.series.log_str} has no linked Library - skipping')
        elif episode.series not in episodes_to_load:
            episodes_to_load.append(episode)

    # Load all Episodes that require reloading
    for episode in episodes_to_load:
        # Refresh this Episode so that relational Card objects are
        # updated, preventing stale (deleted) Cards from being used in
        # the Loaded asset evaluation. Not sure why this is required
        # because SQLAlchemy SHOULD update child objects when the DELETE
        # is committed; but this does not happen.
        db.refresh(episode)

        # Reload into all associated libraries
        for library in series.libraries:
            interface = get_interface(library['interface_id'])
            load_episode_title_card(
                episode, db, library['name'], library['interface_id'], interface,
                attempts=6, log=log,
            )

    return None


@card_router.post('/sonarr', tags=['Sonarr'])
def create_cards_for_sonarr_webhook(
        request: Request,
        webhook: SonarrWebhook = Body(...),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Create the Title Card for the items associated with the given Sonarr
    Webhook payload. This is practically identical to the `/key`
    endpoint.

    - webhook: Webhook payload containing Series and Episode details to
    create the Title Cards of.
    """

    # Get contextual logger
    log = request.state.log

    # Skip if payload has no Episodes to create Cards for
    if len(webhook.episodes) == 0:
        return None

    # Create SeriesInfo for this payload's series
    series_info = SeriesInfo(
        name=webhook.series.title,
        year=webhook.series.year,
        imdb_id=webhook.series.imdbId,
        tvdb_id=webhook.series.tvdbId,
        tvrage_id=webhook.series.tvRageId,
    )

    # Search for this Series
    series = db.query(Series)\
        .filter(series_info.filter_conditions(Series))\
        .first()

    # Series is not found, exit
    if series is None:
        log.info(f'Cannot find Series for {series_info}')
        return None

    # Find each Episode in the payload
    for episode in webhook.episodes:
        episode_info = EpisodeInfo(
            title=episode.title,
            season_number=episode.seasonNumber,
            episode_number=episode.episodeNumber,
        )

        # Find this Episode
        episode = db.query(Episode)\
            .filter(
                Episode.series_id==series.id,
                episode_info.filter_conditions(Episode),
            ).first()

        # Refresh data and look for Episode again
        if episode is None:
            refresh_episode_data(db, series,log=log)
            episode = db.query(Episode)\
                .filter(
                    Episode.series_id==series.id,
                    episode_info.filter_conditions(Episode)
                ).first()
            if not episode:
                log.info(f'Cannot find Episode for {series_info} {episode_info}')
                return None

        # Assume Episode is unwatched
        episode.watched = False

        # Look for source, add translation, create Card if source exists
        image = download_episode_source_image(db, episode, log=log)
        translate_episode(db, episode, log=log)
        if image is None:
            log.info(f'{episode.log_str} has no source image - skipping')
            return None
        create_episode_card(db, None, episode, log=log)

        # Refresh this Episode so that relational Card objects are
        # updated, preventing stale (deleted) Cards from being used in
        # the Loaded asset evaluation. Not sure why this is required
        # because SQLAlchemy SHOULD update child objects when the DELETE
        # is committed; but this does not happen.
        db.refresh(episode)

        # Reload into all associated libraries
        for library in series.libraries:
            interface = get_interface(library['interface_id'])
            load_episode_title_card(
                episode, db, library['name'], library['interface_id'], interface,
                attempts=6, log=log,
            )

    return None
