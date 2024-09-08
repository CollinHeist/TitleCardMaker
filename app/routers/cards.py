from logging import Logger

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
    Preferences,
)
from app import models
from app.internal.auth import get_current_user
from app.internal.cards import (
    create_episode_cards,
    delete_cards,
    get_watched_statuses,
    resolve_card_settings,
    validate_card_type_model,
)
from app.internal.episodes import update_episode_config
from app.internal.series import (
    load_all_series_title_cards,
    load_series_title_cards,
    update_series_config,
)
from app.models.episode import Episode
from app.schemas.card import CardActions, PreviewTitleCard, TitleCard
from app.schemas.episode import Episode as EpisodeSchema, UpdateEpisode
from app.schemas.font import DefaultFont
from app.schemas.series import UpdateSeries

from modules.Debug import InvalidCardSettings, MissingSourceImage
from modules.EpisodeInfo2 import EpisodeInfo
from modules.FormatString import FormatString
from modules.TieredSettings import TieredSettings


# Create sub router for all /cards API requests
card_router = APIRouter(
    prefix='/cards',
    tags=['Title Cards'],
    dependencies=[Depends(get_current_user)],
)


@card_router.post('/preview')
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


@card_router.post('/preview/episode/{episode_id}', tags=['Episodes'])
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


@card_router.get('/all')
def get_all_title_cards(db: Session = Depends(get_database)) -> Page[TitleCard]:
    """
    Get all defined Title Cards.

    - order_by: How to order the Cards in the returned list.
    """

    return paginate(db.query(models.card.Card))


@card_router.get('/card/{card_id}')
def get_title_card(
        card_id: int,
        db: Session = Depends(get_database)
    ) -> TitleCard:
    """
    Get the details of the given TitleCard.

    - card_id: ID of the TitleCard to get the details of.
    """

    return get_card(db, card_id, raise_exc=True)


@card_router.post('/series/{series_id}', tags=['Series'])
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


@card_router.put('/series/{series_id}/load/all', tags=['Series'])
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


@card_router.put('/series/{series_id}/load/library', tags=['Series'])
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


@card_router.get('/episode/{episode_id}', tags=['Episodes'])
def get_episode_cards(
        episode_id: int,
        db: Session = Depends(get_database),
    ) -> Page[TitleCard]:
    """
    Get all TitleCards for the given Episode.

    - episode_id: ID of the Episode to get the cards of.
    """

    return paginate(db.query(models.card.Card).filter_by(episode_id=episode_id))


@card_router.delete('/series/{series_id}', tags=['Series'])
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


@card_router.delete('/episode/{episode_id}', tags=['Episodes'])
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


@card_router.delete('/card/{card_id}')
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


@card_router.post('/episode/{episode_id}', tags=['Episodes'])
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


@card_router.get('/missing', deprecated=True)
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


@card_router.delete('/batch')
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


@card_router.put('/batch/load')
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
