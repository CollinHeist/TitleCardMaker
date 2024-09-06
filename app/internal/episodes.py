from logging import Logger
from pathlib import Path
from typing import Iterable, Optional

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.database.query import get_all_templates, get_font, get_interface
from app.dependencies import (
    get_preferences,
    get_sonarr_interfaces,
    get_tmdb_interfaces,
    get_tvdb_interfaces
)
from app.internal.templates import get_effective_templates
from app.models.card import Card
from app.models.episode import Episode
from app.models.series import Series

from app.schemas.base import UNSPECIFIED
from app.schemas.episode import UpdateEpisode
from modules.Debug import log
from modules.EpisodeDataSource2 import WatchedStatus
from modules.EpisodeInfo2 import EpisodeInfo
from modules.TieredSettings import TieredSettings


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

    # Set ID's from all library interfaces
    for library in series.libraries:
        if (interface := get_interface(library['interface_id'], raise_exc=False)):
            interface.set_episode_ids(
                library['name'], series.as_series_info, episode_infos, log=log,
            )
        else:
            log.debug(f'Skipping Library "{library["name"]}" - no applicable '
                      f'interface')

    # Set from Connections which don't require libraries
    for _, interface in get_sonarr_interfaces():
        interface.set_episode_ids(
            None, series.as_series_info, episode_infos, log=log
    )
    for _, interface in get_tmdb_interfaces():
        interface.set_episode_ids(
            None, series.as_series_info, episode_infos, log=log
        )
    for _, interface in get_tvdb_interfaces():
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
        HTTPException (404): A Series' Template does not exist.
        HTTPException (409): The indicated Episode Data Source cannot be
            communicated with.
    """

    # Determine effective Episode data source
    g_template, s_template, _ = get_effective_templates(series)
    interface_id = TieredSettings.resolve_singular_setting(
        get_preferences().episode_data_source,
        getattr(g_template, 'data_source_id', None),
        getattr(s_template, 'data_source_id', None),
        series.data_source_id,
    )

    # Raise 409 if cannot communicate with the Series' Episode data source
    if (interface := get_interface(interface_id, raise_exc=False)) is None:
        log.error('Unable to communicate with Episode Data Source')
        if raise_exc:
            raise HTTPException(
                status_code=409,
                detail=f'Unable to communicate with Connection[{interface_id}]'
            )
        return []

    # Query Connections which do not have libraries
    if interface.INTERFACE_TYPE in ('Sonarr', 'TMDb', 'TVDb'):
        return interface.get_all_episodes(None, series.as_series_info, log=log)

    # Verify Series has an associated Library if EDS is a media server
    if not (libraries := list(series.get_libraries(interface_id))):
        log.error('Series does not have a Library for the assigned Episode '
                  'Data Source')
        if raise_exc:
            raise HTTPException(
                status_code=409,
                detail=f'Series does not have a Library for Connection[{interface_id}]'
            )
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
    ) -> list[Episode]:
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

    Returns:
        List of any newly added Episodes. Empty list of no new Episodes
        were added, or only existing Episodes were modified.

    Raises:
        HTTPException (404): A Series Template does not exist.
        HTTPException (409): The indicted Episode data source cannot
            be communicated with.
    """

    # Get all Episodes for this Series from the Episode data source
    all_episodes = get_all_episode_data(series, raise_exc=True, log=log)

    # Get effective sync specials toggle
    global_template, series_template, _ = get_effective_templates(series)
    sync_specials: bool = TieredSettings.resolve_singular_setting(
        get_preferences().sync_specials,
        getattr(global_template, 'sync_specials', None),
        getattr(series_template, 'sync_specials', None),
        series.sync_specials,
    )

    # Filter Episodes
    new_episodes: list[Episode] = []
    changed, episodes = False, []
    for episode_info, watched in all_episodes:
        # Skip specials if indicated
        if not sync_specials and episode_info.season_number == 0:
            log.debug(f'{series} Skipping {episode_info} - not syncing specials')
            continue

        # Check if this Episode exists in the database already
        existing = db.query(Episode)\
            .filter(Episode.series_id == series.id,
                    episode_info.filter_conditions(Episode))\
            .first()

        # Episode does not exist, add
        if existing is None:
            episode = Episode(
                series=series,
                title=episode_info.title,
                **episode_info.indices,
                **episode_info.ids,
                watched_statuses=watched.as_db_entry,
                airdate=episode_info.airdate,
            )
            new_episodes.append(episode)
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
                and existing.title != episode_info.title):
                existing.title = episode_info.title
                log.debug(f'{existing} Updating title')
                changed = True
                episodes.append(existing)

            # Update watched status
            if existing.add_watched_status(watched):
                log.debug(f'{existing} Updating watched status')
                changed = True

    # Get existing Episodes
    if get_preferences().delete_missing_episodes:
        new_keys = set(ei.index_str for ei, _ in all_episodes)
        all_existing = {ep.index_str: ep for ep in series.episodes}
        for delete_key in set(all_existing) - new_keys:
            # Delete Title Card(s)
            log.info(f'Deleting {all_existing[delete_key]} - not in Episode '
                      f'Data Source')
            cards = db.query(Card)\
                .filter_by(episode_id=all_existing[delete_key].id)\
                .all()
            for card in cards:
                if (card_file := Path(card.card_file)).exists():
                    card_file.unlink(missing_ok=True)
                    log.info(f'Deleted "{card_file.resolve()}" Title Card')

            # Delete Episode (also deleted associated Loaded + Card objects)
            db.delete(all_existing[delete_key])
            changed = True

    # Log any new Episodes
    if len(new_episodes) > 1:
        log.info(f'{series} {len(new_episodes)} new Episodes')
    elif len(new_episodes) == 1:
        log.info(f'{series} new Episode "{new_episodes[0].title}"')

    # Set Episode ID's for all new Episodes as background task or directly
    if background_tasks is None:
        set_episode_ids(db, series, episodes, log=log)
    else:
        background_tasks.add_task(set_episode_ids, db, series, episodes,log=log)

    # Commit to database if changed
    if changed:
        db.commit()

    return new_episodes


def update_episode_config(
        db: Session,
        episode: Episode,
        update_episode: UpdateEpisode,
        *,
        log: Logger = log,
    ) -> bool:
    """
    Update the given Episode.

    Args:
        db: Database to query for Fonts or Templates if indicated.
        episode: Episode to update.
        update_episode: Objet detailing which attributes of the given
            Episode to update.
        log: Logger for all log messages.

    Returns:
        True if the given Episode was modified, False otherwise.
    """

    # If any reference ID's were indicated, verify referenced object exists
    update_episode_dict = update_episode.dict()
    get_font(db, update_episode_dict.get('font_id'), raise_exc=True)

    # Assign Templates if indicated
    changed = False
    if ((template_ids := update_episode_dict.get('template_ids', None))
        not in (None, UNSPECIFIED)):
        if episode.template_ids != template_ids:
            templates = get_all_templates(db, update_episode_dict)
            episode.assign_templates(templates, log=log)
            changed = True

    # Update each attribute of the object
    for attr, value in update_episode_dict.items():
        if value != UNSPECIFIED and getattr(episode, attr) != value:
            log.debug(f'Episode[{episode.id}].{attr} = {value}')
            setattr(episode, attr, value)
            changed = True

    return changed
