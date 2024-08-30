from logging import Logger
from time import sleep
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import not_
from sqlalchemy.orm import Session

from app.database.query import (
    get_card,
    get_episode,
    get_font,
    get_interface,
    get_series
)
from app.database.session import Page
from app.dependencies import (
    get_database,
    get_preferences,
    require_plex_interface,
    PlexInterface,
    Preferences
)
from app import models
from app.internal.auth import get_current_user
from app.internal.cards import (
    create_episode_cards,
    delete_cards,
    get_watched_statuses,
    resolve_card_settings,
    validate_card_type_model
)
from app.internal.episodes import refresh_episode_data, update_episode_config
from app.internal.series import (
    load_all_series_title_cards,
    load_episode_title_card,
    load_series_title_cards,
    update_series_config
)
from app.internal.sources import download_episode_source_images
from app.internal.translate import translate_episode
from app.internal.webhooks import process_rating_key
from app.models.episode import Episode
from app.models.series import Series
from app.schemas.card import CardActions, PreviewTitleCard, TitleCard
from app.schemas.episode import Episode as EpisodeSchema, UpdateEpisode
from app.schemas.font import DefaultFont
from app.schemas.series import UpdateSeries
from app.schemas.webhooks import SonarrWebhook

from modules.Debug import InvalidCardSettings, MissingSourceImage
from modules.EpisodeInfo2 import EpisodeInfo
from modules.FormatString import FormatString
from modules.SeriesInfo2 import SeriesInfo
from modules.TieredSettings import TieredSettings


# Create sub router for all /cards API requests
card_router = APIRouter(
    prefix='/cards',
    tags=['Title Cards'],
    # dependencies=[Depends(get_current_user)], # TODO add after webhooks are removed
)


@card_router.post('/preview', dependencies=[Depends(get_current_user)])
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

    # Fake data
    format_data = {
        'series_full_name': 'Test Series (2020)', 'series_name': 'Test Series',
        'season_episode_max': 10, 'series_episode_max': 20,
        'logo_file': preferences.INTERNAL_ASSET_DIRECTORY / 'logo.png',
        'poster_file': preferences.INTERNAL_ASSET_DIRECTORY / 'preview' / 'poster.webp',
        'backdrop_file': preferences.INTERNAL_ASSET_DIRECTORY / 'preview' / 'art.jpg',
    }

    # Get preview season and episode text
    if card.season_text is None:
        # Apply season text formatting if indicated
        try:
            if getattr(CardClass, 'SEASON_TEXT_FORMATTER', None) is None:
                card.season_text = FormatString(
                    'Season {season_number}',
                    data=format_data | card.dict(),
                ).result
            else:
                fake_ei = EpisodeInfo(
                    title=card.title_text, season_number=card.season_number,
                    episode_number=card.episode_number,
                    absolute_number=card.absolute_number
                )
                card.season_text = FormatString(
                    getattr(CardClass, 'SEASON_TEXT_FORMATTER')(fake_ei),
                    data=format_data | card.dict(),
                ).result
        except InvalidCardSettings as exc:
            raise HTTPException(
                status_code=400,
                detail='Invalid season text format',
            ) from exc
    if card.episode_text is None:
        try:
            card.episode_text = FormatString(
                (card.episode_text_format or CardClass.EPISODE_TEXT_FORMAT),
                data=format_data | card.dict(),
            ).result
        except InvalidCardSettings as exc:
            raise HTTPException(
                status_code=400,
                detail='Invalid episode text format',
            ) from exc

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
        preferences.global_extras.get(card.card_type, {}),
        format_data,
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


@card_router.post('/preview/episode/{episode_id}', tags=['Episodes'],
                  dependencies=[Depends(get_current_user)])
def create_preview_card_for_episode(
        request: Request,
        episode_id: int,
        update_episode: UpdateEpisode = Body(...),
        update_series: UpdateSeries = Body(...),
        query_watched_statuses: bool = Query(default=False),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> str:
    """
    Create a preview Title Card for the given Episode.

    - episode_id: ID of the Episode to create the Title Card for.
    
    - query_watched_statuses: Whether to query the watched statuses
    associated with this Episode.
    """

    # Get contextual logger
    log: Logger = request.state.log

    # Find associated Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Raise exception if Template IDs are part of update object; cannot
    # be reflected in the live preview because relationship objects will
    # not be reflected until a database commit
    if (getattr(update_episode, 'template_ids', []) != episode.template_ids or
        getattr(update_series,'template_ids',[]) !=episode.series.template_ids):
        raise HTTPException(
            status_code=422,
            detail=(
                'Preview Cards cannot reflect Template changes - save changes '
                'and try again'
            )
        )

    update_episode_config(db, episode, update_episode, log=log)
    update_series_config(db, episode.series, update_series, commit=False, log=log)

    # Set watch status(es) of the Episode
    if query_watched_statuses:
        get_watched_statuses(db, episode.series, [episode], log=log)

    # Determine appropriate Source and Output file
    output = preferences.INTERNAL_ASSET_DIRECTORY / 'preview' \
        / f'card-unique{preferences.card_extension}'
    output.unlink(missing_ok=True)

    # Create Card for this Episode
    library = None
    if episode.series.libraries:
        library = episode.series.libraries[0]

    try:
        card_settings = resolve_card_settings(episode, library, log=log)
        card_settings['card_file'] = output
    except MissingSourceImage as exc:
        raise HTTPException(
            status_code=404,
            detail=f'Missing the required Source Image',
        ) from exc
    except (HTTPException, InvalidCardSettings) as exc:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid Card settings',
        ) from exc

    # Delete output if it exists, then create Card
    CardClass, CardTypeModel = validate_card_type_model(card_settings, log=log)
    card_maker = CardClass(**CardTypeModel.dict(), preferences=preferences)
    card_maker.create()

    # Card created, return URI
    if output.exists():
        return f'/internal_assets/preview/{output.name}'

    card_maker.image_magick.print_command_history(log=log)
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
    log: Logger = request.state.log

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Set watch statuses of the Episodes
    get_watched_statuses(db, series, series.episodes, log=log)
    db.commit()

    # Create each associated Episode's Card
    for episode in series.episodes:
        try:
            create_episode_cards(db, episode, log=log)
        except Exception as exc:
            log.exception(f'{episode} Card creation failed - {exc}')


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

    # Load Cards
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

    return paginate(db.query(models.card.Card).filter_by(episode_id=episode_id))


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
    Delete all Title Cards for the given Episode. Return a list of the
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
    - query_watched_statuses: Whether to query the watched statuses
    associated with this Episode.
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
        create_episode_cards(db, episode, log=request.state.log)
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


@card_router.post('/key', tags=['Plex', 'Webhooks'], deprecated=True)
def create_cards_for_plex_rating_key(
        request: Request,
        key: int = Body(...),
        snapshot: bool = Query(default=True),
        db: Session = Depends(get_database),
        plex_interface: PlexInterface = Depends(require_plex_interface),
    ) -> None:
    """
    Create the Title Card for the item associated with the given Plex
    Rating Key. This item can be a Show, Season, or Episode. This
    endpoint does NOT require an authenticated User so that Tautulli can
    trigger this without any credentials.

    - interface_id: Interface ID of the Plex Connection associated with
    this Key.
    - key: Rating Key within Plex that identifies the item to create the
    Card(s) for.
    - snapshot: Whether to take snapshot of the database after all Cards
    have been processed.
    """

    return process_rating_key(
        db, plex_interface, key, snapshot=snapshot, log=request.state.log,
    )


@card_router.post('/sonarr', tags=['Webhooks'], deprecated=True)
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

    # Skip if payload has no Episodes to create Cards for
    if not webhook.episodes:
        return None

    # Get contextual logger
    log: Logger = request.state.log

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
        create_episode_cards(db, episode, log=log)

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
