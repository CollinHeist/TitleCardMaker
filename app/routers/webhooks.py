from logging import Logger
from time import sleep
from typing import Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Query,
    Request
)
from fastapi.exceptions import HTTPException
from pydantic.error_wrappers import ValidationError
from sqlalchemy.orm import Session

from app.database.query import get_interface
from app.dependencies import get_database, require_plex_interface, PlexInterface
from app.internal.cards import create_episode_cards, delete_cards
from app.internal.episodes import refresh_episode_data
from app.internal.series import delete_series, load_episode_title_card
from app.internal.sources import download_episode_source_images
from app.internal.translate import translate_episode
from app.internal.webhooks import process_rating_key
from app.models.card import Card
from app.models.episode import Episode
from app.models.loaded import Loaded
from app.models.series import Series
from app.schemas.webhooks import PlexWebhook, SonarrWebhook
from modules.EpisodeInfo2 import EpisodeInfo
from modules.SeriesInfo2 import SeriesInfo


# Create sub router for all /webhooks API requests
webhook_router = APIRouter(
    prefix='/webhooks',
    tags=['Webhooks'],
)


@webhook_router.post('/plex/rating-key', tags=['Plex'])
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
        db, plex_interface, key, snapshot=snapshot, log=request.state.log
    )


@webhook_router.post('/plex', tags=['Plex'])
async def process_plex_webhook(
        request: Request,
        # FastAPI cannot parse the payload, for some reason, so this needs to
        # be parsed from the request.form() directly
        # webhook: PlexWebhook = Form(...),
        snapshot: bool = Query(default=True),
        trigger_on: Optional[str] = Query(default=None),
        db: Session = Depends(get_database),
        plex_interface: PlexInterface = Depends(require_plex_interface),
    ) -> None:
    """
    """

    # Get contextual logger
    log: Logger = request.state.log

    try:
        webhook = PlexWebhook.parse_raw((await request.form()).get('payload'))
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail='Webhook format is invalid'
        ) from exc

    # Only process new or watched content
    if (webhook.event not in ('library.new', 'media.scrobble')
        and (not trigger_on
             or (trigger_on and webhook.event not in trigger_on))):
        log.debug(f'Skipping Webhook of type "{webhook.event}"')
        return None

    return process_rating_key(
        db,
        plex_interface,
        webhook.Metadata.ratingKey,
        snapshot=snapshot,
        log=log,
    )


@webhook_router.post('/sonarr/cards', tags=['Sonarr'])
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


@webhook_router.post('/sonarr/series/delete', tags=['Sonarr'])
def delete_series_via_sonarr_webhook(
        request: Request,
        webhook: SonarrWebhook,
        delete_title_cards: bool = Query(default=True),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Delete the Series defined in the given Webhook.

    - webhook: Webhook payload containing the details of the Series to
    delete.
    - delete_title_cards: Whether to delete Title Cards.
    """

    # Skip if Webhook type is not a Series deletion
    if webhook.eventType != 'SeriesDelete':
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
        raise HTTPException(
            status_code=404,
            detail=f'Series {series_info} not found',
        )

    # Delete Card, Loaded, and Series, as well all child content
    if delete_title_cards:
        delete_cards(
            db,
            db.query(Card).filter_by(series_id=series.id),
            db.query(Loaded).filter_by(series_id=series.id),
            log=request.state.log,
        )
    delete_series(db, series, log=request.state.log)
    return None
