from time import sleep
from typing import Optional

from fastapi import (
    APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Request
)
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import not_
from sqlalchemy.orm import Session

from app.database.query import (
    get_card, get_episode, get_font, get_interface, get_series
)
from app.database.session import Page
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app import models
from app.internal.auth import get_current_user
from app.internal.cards import (
    create_episode_cards, delete_cards, get_watched_statuses,
    validate_card_type_model
)
from app.internal.episodes import refresh_episode_data
from app.internal.series import (
    load_all_series_title_cards, load_episode_title_card,load_series_title_cards
)
from app.internal.snapshot import take_snapshot
from app.internal.sources import download_episode_source_images
from app.internal.translate import translate_episode
from app.models.episode import Episode
from app.models.series import Series
from app.schemas.card import CardActions, TitleCard, PreviewTitleCard
from app.schemas.connection import SonarrWebhook
from app.schemas.episode import Episode as EpisodeSchema
from app.schemas.font import DefaultFont
from modules.Debug import InvalidCardSettings, MissingSourceImage

from modules.EpisodeInfo2 import EpisodeInfo
from modules.SeriesInfo2 import SeriesInfo
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
        {'logo_file': preferences.INTERNAL_ASSET_DIRECTORY / 'logo.png'},
        DefaultFont,
        preferences.card_properties,
        font_template_dict,
        {'source_file': source, 'card_file': output},
        card.dict(),
        card.extras,
    )

    # Add card default font stuff
    if card_settings.get('font_file') is None:
        card_settings['font_file'] = CardClass.TITLE_FONT
    if card_settings.get('font_color') is None:
        card_settings['font_color'] = CardClass.TITLE_COLOR

    # Turn manually entered \n into newline
    card_settings['title_text'] = card_settings['title_text'].replace(r'\n', '\n')

    # Apply title text case function
    if card_settings.get('font_title_case') is None:
        case_func = CardClass.CASE_FUNCTIONS[CardClass.DEFAULT_FONT_CASE]
    else:
        case_func = CardClass.CASE_FUNCTIONS[card_settings['font_title_case']]
    card_settings['title_text'] = case_func(card_settings['title_text'])

    # Delete output if it exists, then create Card
    CardClass, CardTypeModel = validate_card_type_model(card_settings, log=log)
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


@card_router.get('/all', dependencies=[Depends(get_current_user)])
def get_all_title_cards(db: Session = Depends(get_database)) -> Page[TitleCard]:
    """
    Get all defined Title Cards.

    - order_by: How to order the Cards in the returned list.
    """

    return paginate(db.query(models.card.Card))


@card_router.get('/card/{card_id}', dependencies=[Depends(get_current_user)])
def get_title_card(
        card_id: int,
        db: Session = Depends(get_database)
    ) -> TitleCard:
    """
    Get the details of the given TitleCard.

    - card_id: ID of the TitleCard to get the details of.
    """

    return get_card(db, card_id, raise_exc=True)


@card_router.post('/series/{series_id}', tags=['Series'],
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
    get_watched_statuses(db, series, series.episodes, log=log)
    db.commit()

    # Create each associated Episode's Card
    for episode in series.episodes:
        try:
            create_episode_cards(db, background_tasks, episode, log=log)
        except Exception as e:
            log.exception(f'{series} {episode} Card creation failed - {e}', e)

    return None


@card_router.get('/series/{series_id}', tags=['Series'],
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
            .filter(models.card.Card.series_id == series_id)\
            .join(models.episode.Episode)\
            .order_by(models.episode.Episode.season_number)\
            .order_by(models.episode.Episode.episode_number)\
            .order_by(models.card.Card.library_name)
    )


@card_router.put('/series/{series_id}/load/all', tags=['Series'],
                 dependencies=[Depends(get_current_user)])
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


@card_router.put('/series/{series_id}/load/library', tags=['Series'],
                 dependencies=[Depends(get_current_user)])
def load_series_title_cards_into_library(
        request: Request,
        series_id: int,
        interface_id: int = Query(...),
        library_name: str = Query(...),
        reload: bool = Query(default=False),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Load the Title Cards for the given Series into the library with the
    given index.

    - series_id: ID of the Series whose Cards are being loaded.
    - library_index: Index in Series' library list of the library to
    load the Cards into.
    - reload: Whether to "force" reload all Cards, even those that have
    already been loaded. If false, only Cards that have not been loaded
    previously (or that have changed) are loaded.
    """

    # Get this Series and Interface, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)
    interface = get_interface(interface_id, raise_exc=True)

    # Load this Library's Cards
    load_series_title_cards(
        series, library_name, interface_id, db, interface,
        reload, log=request.state.log,
    )


@card_router.get('/episode/{episode_id}', tags=['Episodes'],
                 dependencies=[Depends(get_current_user)])
def get_episode_cards(
        episode_id: int,
        db: Session = Depends(get_database),
    ) -> Page[TitleCard]:
    """
    Get all TitleCards for the given Episode.

    - episode_id: ID of the Episode to get the cards of.
    """

    return paginate(
        db.query(models.card.Card).filter_by(episode_id=episode_id).all()
    )


@card_router.delete('/series/{series_id}', tags=['Series'],
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

    # Create queries for Cards of this Series
    card_query = db.query(models.card.Card).filter_by(series_id=series_id)
    loaded_query = db.query(models.loaded.Loaded).filter_by(series_id=series_id)

    # Delete cards
    deleted = delete_cards(db, card_query, loaded_query, log=request.state.log)

    return CardActions(deleted=len(deleted))


@card_router.delete('/episode/{episode_id}', tags=['Episodes'],
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


@card_router.delete('/card/{card_id}',
                    dependencies=[Depends(get_current_user)])
def delete_title_card(
        card_id: int,
        request: Request,
        db: Session = Depends(get_database)
    ) -> CardActions:
    """
    Delete the Title Card with the given ID. Also removes the associated
    Loaded object (if it exists).

    - card_id: ID of the Title Card to delete.
    """

    # Create Queries for Cards of this Episode
    card_query = db.query(models.card.Card).filter_by(id=card_id)
    loaded_query = db.query(models.loaded.Loaded).filter_by(id=card_id)

    # Delete cards
    deleted = delete_cards(db, card_query, loaded_query, log=request.state.log)

    return CardActions(deleted=len(deleted))


@card_router.post('/episode/{episode_id}', tags=['Episodes'],
                  dependencies=[Depends(get_current_user)])
def create_card_for_episode(
        request: Request,
        episode_id: int,
        query_watched_statuses: bool = Query(default=False),
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
    if query_watched_statuses:
        get_watched_statuses(
            db, episode.series, [episode], log=request.state.log,
        )

    # Create Card for this Episode
    try:
        create_episode_cards(db, None, episode, log=request.state.log)
    except MissingSourceImage as exc:
        raise HTTPException(
            status_code=404,
            detail=f'Missing the required Source Image',
        ) from exc
    except InvalidCardSettings as exc:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid Card settings',
        ) from exc


@card_router.post('/key', tags=['Plex', 'Tautulli'])
def create_cards_for_plex_rating_key(
        request: Request,
        key: int = Body(...),
        db: Session = Depends(get_database),
        plex_interface: PlexInterface = Depends(require_plex_interface),
    ) -> None:
    """
    Create the Title Card for the item associated with the given Plex
    Rating Key. This item can be a Show, Season, or Episode. This
    endpoint does NOT require an authenticated User so that Tautulli can
    trigger this without any credentials. The `interface_id` of the
    appropriate Plex Connection must be passed via a Query parameter.

    - plex_rating_keys: Unique keys within Plex that identifies the item
    to remake the card of.
    """

    # Get contextual logger
    log = request.state.log

    # Get details of each key from Plex, raise 404 if not found/invalid
    if len(details := plex_interface.get_episode_details(key, log=log)) == 0:
        raise HTTPException(
            status_code=404,
            detail=f'Rating key {key} is invalid'
        )
    log.debug(f'Identified {len(details)} entries from RatingKey={key}')

    # Process each set of details
    episodes_to_load: list[Episode] = []
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
        episode.add_watched_status(watched_status)

        # Look for source, add translation, create card if source exists
        images = download_episode_source_images(db, episode, log=log)
        translate_episode(db, episode, log=log)
        if not any(images):
            log.info(f'{episode} has no source image - skipping')
            continue
        create_episode_cards(db, None, episode, log=log)

        # Add this Series to list of Series to load
        if episode not in episodes_to_load:
            episodes_to_load.append(episode)

    # Load all Episodes that require reloading
    for episode in episodes_to_load:
        # Refresh this Episode so that relational Card objects are
        # updated, preventing stale (deleted) Cards from being used in
        # the Loaded asset evaluation. Not sure why this is required
        # because SQLAlchemy should update child objects when the DELETE
        # is committed; but this does not happen.
        db.refresh(episode)

        # Reload into all associated libraries
        for library in episode.series.libraries:
            interface = get_interface(library['interface_id'])
            load_episode_title_card(
                episode, db, library['name'], library['interface_id'],
                interface, attempts=6, log=log,
            )

    take_snapshot(db, log=log)
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
        log.info(f'Cannot find Series {series_info}')
        return None

    def _find_episode(episode_info: EpisodeInfo) -> Optional[Episode]:
        """Attempt to find the associated Episode up to three times."""

        for _ in range(3):
            # Search for this Episode
            episode = db.query(Episode)\
                .filter(Episode.series_id==series.id,
                        episode_info.filter_conditions(Episode))\
                .first()

            # Episode exists, return it
            if episode:
                return episode

            # Sleep and re-query Episode data
            log.debug(f'Cannot find Episode, waiting..')
            sleep(30)
            refresh_episode_data(db, series, log=log)

        return None

    # Find each Episode in the payload
    for webhook_episode in webhook.episodes:
        episode_info = EpisodeInfo(
            title=webhook_episode.title,
            season_number=webhook_episode.seasonNumber,
            episode_number=webhook_episode.episodeNumber,
            tvdb_id=webhook_episode.tvdbId,
        )

        # Find this Episode
        if (episode := _find_episode(episode_info)) is None:
            log.info(f'Cannot find Episode for {series_info} {episode_info}')
            return None

        # Assume Episode is unwatched
        episode.watched = False

        # Look for source, add translation, create Card if source exists
        images = download_episode_source_images(db, episode, log=log)
        translate_episode(db, episode, log=log)
        if not images:
            log.info(f'{episode} has no source image - skipping')
            continue
        create_episode_cards(db, None, episode, log=log)

        # Refresh this Episode so that relational Card objects are
        # updated, preventing stale (deleted) Cards from being used in
        # the Loaded asset evaluation. Not sure why this is required
        # because SQLAlchemy should update child objects when the DELETE
        # is committed; but this does not happen.
        db.refresh(episode)

        # Reload into all associated libraries
        for library in series.libraries:
            if (interface := get_interface(library['interface_id'], raise_exc=False)):
                load_episode_title_card(
                    episode, db, library['name'], library['interface_id'], interface,
                    attempts=6, log=log,
                )
            else:
                log.debug(f'Not loading {series_info} {episode_info} into '
                          f'library "{library["name"]}" - no valid Connection')
                continue

    return None


@card_router.get('/missing', dependencies=[Depends(get_current_user)])
def get_missing_cards(
        db: Session = Depends(get_database),
    ) -> Page[EpisodeSchema]:
    """
    Get all the Episodes that do not have any associated Cards.
    """

    return paginate(
        db.query(Episode)\
            .filter(not_(Episode.id.in_(
                db.query(models.card.Card.episode_id).distinct()
            )))
    )


@card_router.delete('/batch', dependencies=[Depends(get_current_user)])
def batch_delete_title_cards(
        request: Request,
        series_ids: list[int] = Body(...),
        db: Session = Depends(get_database),
    ) -> CardActions:
    """
    Batch delete all the Title Cards associated with the given Series.

    - series_ids: List of IDs of Series whose Title Cards are being
    deleted.
    """

    cards = db.query(models.card.Card)\
        .filter(models.card.Card.series_id.in_(series_ids))

    return CardActions(
        deleted=len(delete_cards(db, cards, log=request.state.log)),
    )


@card_router.put('/batch/load', dependencies=[Depends(get_current_user)])
def batch_load_title_cards_into_all_libraries(
        request: Request,
        series_ids: list[int] = Body(...),
        reload: bool = Query(default=False),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Batch operation to load all Title Cards for all Series into all
    libraries.

    - series_ids: IDs of the Series whose Cards are being loaded.
    - reload: Whether to "force" reload all Cards, even those that have
    already been loaded. If false, only Cards that have not been loaded
    previously (or that have changed) are loaded.
    """

    for series_id in series_ids:
        load_all_series_title_cards(
            get_series(db, series_id, raise_exc=True),
            db,
            force_reload=reload,
            log=request.state.log,
        )
