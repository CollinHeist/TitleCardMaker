from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.query import get_interface
from app.dependencies import PlexInterface
from app.internal.cards import create_episode_cards
from app.internal.episodes import refresh_episode_data
from app.internal.series import load_episode_title_card
from app.internal.snapshot import take_snapshot
from app.internal.sources import download_episode_source_images
from app.internal.translate import translate_episode
from app.models.episode import Episode
from app.models.series import Series
from modules.Debug import Logger, log


def process_rating_key(
        db: Session,
        plex_interface: PlexInterface,
        key: int,
        new_only: bool = False,
        *,
        snapshot: bool = True,
        log: Logger = log,
    ) -> None:
    """
    Create the Title Card for the item associated with the given Plex
    Rating Key. This item can be a Show, Season, or Episode.

    Args:
        db: Database to query for Card details.
        plex_interface: Interface to Plex which has the details
            associated with this Key.
        key: Rating Key within Plex that identifies the item to create
            the Card(s) for.
        new_only: Whether to only process newly added Episodes. If False
            then ALL Episodes associated with the given Key will be
            reloaded.
        snapshot: Whether to take a snapshot of the database afterwards.
        log: Logger for all log messages.

    Raises:
        HTTPException (404): There are no details associated with the
            given Rating Key.
    """

    # Get details of each key from Plex, raise 404 if not found/invalid
    if len(details := plex_interface.get_episode_details(key, log=log)) == 0:
        raise HTTPException(
            status_code=404,
            detail=f'Rating key {key} does not correspond to any content'
        )
    log.debug(f'Identified {len(details)} entries from RatingKey {key}')

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
        elif new_only:
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
        create_episode_cards(db, episode, log=log)

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
            load_episode_title_card(
                episode, db, library['name'], library['interface_id'],
                get_interface(library['interface_id']),
                attempts=5 if library['interface'] == 'Plex' else 1,
                log=log,
            )

    if snapshot:
        take_snapshot(db, log=log)
