from logging import Logger
from time import sleep
from typing import Iterable, Optional

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database.query import get_interface
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.templates import get_effective_series_template
from app import models
from app.models.episode import Episode
from app.models.series import Series

from modules.Debug import log
from modules.EpisodeDataSource2 import WatchedStatus
from modules.EpisodeInfo2 import EpisodeInfo
from modules.TieredSettings import TieredSettings


def refresh_all_episode_data(*, log: Logger = log) -> None:
    """
    Schedule-able function to refresh the episode data for all Series in
    the Database.

    Args:
        log: Logger for all log messages.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get through each Series, refresh Episode data
            all_series = db.query(models.series.Series).all()
            for series in all_series:
                # If Series is unmonitored, skip
                if not series.monitored:
                    log.debug(f'{series.log_str} is Unmonitored, skipping')
                    continue

                try:
                    refresh_episode_data(db, series, log=log)
                except OperationalError:
                    log.debug(f'Database is busy, sleeping..')
                    sleep(30)
    except Exception as e:
        log.exception(f'Failed to refresh all episode data - {e}', e)


def set_episode_ids(
        db: Session,
        series: Series,
        episodes: Iterable[Episode],
        *,
        log: Logger = log,
    ) -> None:
    """
    Set the database IDs of the given Episodes.

    Args:
        db: Database to read/update/modify.
        series: Series of the Episodes whose IDs are being set.
        episodes: Any Episodes to set the IDs of.
        log: Logger for all log messages.
    """

    # Get corresponding EpisodeInfo object for this Episode
    episode_infos = [episode.as_episode_info for episode in episodes]

    # Set ID's from all possible interfaces
    for library in series.libraries:
        if (interface := get_interface(library['interface_id'], raise_exc=False)):
            interface.set_episode_ids(
                library['name'], series.as_series_info, episode_infos, log=log,
            )
        else:
            log.debug(f'Skipping Library "{library["name"]}" - no applicable '
                      f'interface')

    # Set from Sonarr and TMDb
    for _, interface in get_sonarr_interfaces():
        interface.set_episode_ids(
            None, series.as_series_info, episode_infos, log=log
        )
    for _, interface in get_tmdb_interfaces():
        interface.set_episode_ids(
            None, series.as_series_info, episode_infos, log=log
        )

    # Update database if new ID's are available
    changed = False
    for episode, episode_info in zip(episodes, episode_infos):
        changed |= episode.update_from_info(episode_info, log=log)

    # Write any changes to the DB
    if changed:
        db.commit()


def get_all_episode_data(
        series: Series,
        *,
        raise_exc: bool = True,
        log: Logger = log,
    ) -> list[tuple[EpisodeInfo, WatchedStatus]]:
    """
    Get all EpisodeInfo for the given Series from it's indicated Episode
    data source.

    Args:
        series: Series whose Episode data is being queried.
        raise_exc: Whether to raise any HTTPExceptions caused by
            disabled interfaces or missing libraries.
        log: Logger for all log messages.

    Returns:
        List of tuples of the EpisodeInfo from the given Series' episode
        data source and the WatchedStatus for that Episode. If the data
        cannot be queried and `raise_exc` is False, then an empty list
        is returned.

    Raises:
        HTTPException (404): A Series Template does not exist.
        HTTPException (409): The indicated Episode Data Source cannot be
            communicated with.
    """

    # Get Series' effective Episode data source
    series_template_dict = get_effective_series_template(series, as_dict=True)
    interface_id = TieredSettings.resolve_singular_setting(
        get_preferences().episode_data_source,
        series_template_dict.get('data_source_id', None),
        series.data_source_id,
    )

    # Raise 409 if cannot communicate with the Series' Episode data source
    if (interface := get_interface(interface_id, raise_exc=False)) is None:
        if raise_exc:
            raise HTTPException(
                status_code=409,
                detail=f'Unable to communicate with Connection[{interface_id}]'
            )
        return []

    # Sonarr and TMDb do not have libraries, query separately
    # TODO modify to return a WatchStatus object
    if interface.INTERFACE_TYPE in ('Sonarr', 'TMDb'):
        return interface.get_all_episodes(None, series.as_series_info, log=log)

    # Verify Series has an associated Library if EDS is a media server
    if not (libraries := list(series.get_libraries(interface_id))):
        if raise_exc:
            raise HTTPException(
                status_code=409,
                detail=f'Series does not have a Library for Connection[{interface_id}]'
            )
        log.error(f'Series does not have a Library for Connection[{interface_id}]')
        return []

    # Get Episodes from the Series' first (primary) library
    return interface.get_all_episodes(
        libraries[0][1], series.as_series_info, log=log
    )


def refresh_episode_data(
        db: Session,
        series: Series,
        background_tasks: Optional[BackgroundTasks] = None,
        *,
        log: Logger = log,
    ) -> None:
    """
    Refresh the episode data for the given Series. This adds any new
    Episodes on the associated episode data source to the Database,
    updates the titles of any existing Episodes (if indicated), and
    assigns the database ID's of all added/modified Episodes.

    Args:
        db: Database to read/update/modify.
        series: Series whose episodes are being refreshed.
        background_tasks: Optional BackgroundTasks queue to add the
            Episode ID assignment task to, if provided. If omitted then
            the assignment is done in a blocking manner.
        log: Logger for all log messages.

    Raises:
        HTTPException (404): A Series Template does not exist.
        HTTPException (409): The indicted Episode data source cannot
            be communicated with.
    """

    # Get all Episodes for this Series from the Episode data source
    all_episodes = get_all_episode_data(series, raise_exc=True, log=log)

    # Get effective episode data source and sync specials toggle
    series_template = get_effective_series_template(series)
    sync_specials: bool = TieredSettings.resolve_singular_setting(
        get_preferences().sync_specials,
        getattr(series_template, 'sync_specials', None),
        series.sync_specials,
    )

    # Filter episodes
    changed, episodes = False, []
    for episode_info, watched in all_episodes:
        # Skip specials if indicated
        if not sync_specials and episode_info.season_number == 0:
            log.debug(f'{series.log_str} Skipping {episode_info} - not syncing specials')
            continue

        # Check if this Episode exists in the database already
        existing = db.query(Episode)\
            .filter(episode_info.filter_conditions(Episode))\
            .first()

        # Episode does not exist, add
        if existing is None:
            log.info(f'{series.log_str} New Episode "{episode_info.title.full_title}"')
            episode = Episode(
                series=series,
                title=episode_info.title.full_title,
                **episode_info.indices,
                **episode_info.ids,
                watched_statuses=watched.as_db_entry,
                airdate=episode_info.airdate,
            )
            db.add(episode)
            changed = True
            episodes.append(episode)
        # Episode exists, check title matches and update watch status
        else:
            # If title matching, update if title does not match
            do_title_match = (
                existing.match_title
                or (existing.match_title is None and series.match_titles)
            )
            if (do_title_match
                and existing.title != episode_info.title.full_title):
                existing.title = episode_info.title.full_title
                log.debug(f'{series.log_str} {existing.log_str} Updating title')
                changed = True
                episodes.append(existing)

            # Update watched status
            if episode.add_watched_status(watched):
                log.debug(f'{series.log_str} {existing.log_str} Updating watched status')
                changed = True

    # Set Episode ID's for all new Episodes as background task or directly
    if background_tasks is None:
        set_episode_ids(db, series, episodes, log=log)
    else:
        background_tasks.add_task(
            set_episode_ids,
            # Arguments
            db, series, episodes, log=log
        )

    # Commit to database if changed
    if changed:
        db.commit()
