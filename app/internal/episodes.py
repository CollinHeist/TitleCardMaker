from logging import Logger
from time import sleep
from typing import Optional, Union

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.templates import get_effective_series_template
from app import models
from app.models.episode import Episode
from app.models.series import Series
from app.models.preferences import Preferences
from app.schemas.preferences import EpisodeDataSource

from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.EpisodeInfo2 import EpisodeInfo
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TieredSettings import TieredSettings
from modules.TMDbInterface2 import TMDbInterface


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
                    refresh_episode_data(
                        db, get_preferences(), series, get_emby_interface(),
                        get_jellyfin_interface(), get_plex_interface(),
                        get_sonarr_interface(), get_tmdb_interface(), log=log,
                    )
                except OperationalError:
                    log.debug(f'Database is busy, sleeping..')
                    sleep(30)
    except Exception as e:
        log.exception(f'Failed to refresh all episode data - {e}', e)


def set_episode_ids(
        db: Session,
        series: Series,
        episodes: list[Episode],
        emby_interfaces: InterfaceGroup[int, EmbyInterface],
        jellyfin_interfaces: InterfaceGroup[int, JellyfinInterface],
        plex_interfaces: InterfaceGroup[int, PlexInterface],
        sonarr_interfaces: InterfaceGroup[int, SonarrInterface],
        tmdb_interface: Optional[TMDbInterface],
        *,
        log: Logger = log,
    ) -> None:
    """
    Set the database ID's of the given Episodes using the given
    Interfaces.

    Args:
        db: Database to read/update/modify.
        series: Series of the Episodes whose ID's are being set.
        episodes: List of Episodes to set the ID's of.
        *_interface(s): Interface(s) to set ID's from.
        log: Logger for all log messages.
    """

    # Get corresponding EpisodeInfo object for this Episode
    episode_infos = [episode.as_episode_info for episode in episodes]

    # Set ID's from all possible interfaces
    for interface_id, library in series.get_libraries('Emby'):
        if (interface := emby_interfaces[interface_id]):
            interface.set_episode_ids(
                library, series.as_series_info, episode_infos, log=log
            )
    for interface_id, library in series.get_libraries('Jellyfin'):
        if (interface := jellyfin_interfaces[interface_id]):
            interface.set_episode_ids(
                library, series.as_series_info, episode_infos, log=log
            )
    for interface_id, library in series.get_libraries('Plex'):
        if (interface := plex_interfaces[interface_id]):
            interface.set_episode_ids(
                library, series.as_series_info, episode_infos, log=log
            )
    for _, interface in sonarr_interfaces:
        interface.set_episode_ids(
            None, series.as_series_info, episode_infos, log=log
        )
    if tmdb_interface:
        tmdb_interface.set_episode_ids(
            None, series.as_series_info, episode_infos, log=log
        )

    # Update database if new ID's are available
    changed = False
    for episode, episode_info in zip(episodes, episode_infos):
        for id_type in episode_info.ids.keys():
            if (getattr(episode, id_type) is None
                and episode_info.has_id(id_type)):
                setattr(episode, id_type, getattr(episode_info, id_type))
                changed = True

    # Write any changes to the DB
    if changed:
        db.commit()


def get_all_episode_data(
        preferences: Preferences,
        series: Series,
        emby_interface: Optional[EmbyInterface],
        jellyfin_interface: Optional[JellyfinInterface],
        plex_interface: Optional[PlexInterface],
        sonarr_interface: Optional[SonarrInterface],
        tmdb_interface: Optional[TMDbInterface],
        *,
        raise_exc: bool = True,
        log: Logger = log,
    ) -> list[tuple[EpisodeInfo, Optional[bool]]]:
    """
    Get all EpisodeInfo for the given Series from it's indicated Episode
    data source.

    Args:
        preferences: Global Preferences to use for setting resolution.
        series: Series whose Episode data is being queried.
        *_interface: Interface to potentially query for Episode data.
        raise_exc: (Keyword): Whether to raise any HTTPExceptions caused
            by disabled interfaces or missing libraries.
        log: (Keyword) Logger for all log messages.

    Returns:
        List of tuples of the EpisodeInfo from the given Series' Episode
        data source and whether that Episode has been watched (or None
        of that cannot be determined). If the data cannot be queried and
        `raise_exc` is False, then an empty list is returned.

    Raises:
        HTTPException (404) if the Series Template DNE.
        HTTPException (409) if the indicted Episode data source cannot
            be communicated with.
    """

    # Get effective Series Episode data source
    series_template_dict = get_effective_series_template(series, as_dict=True)
    episode_data_source = TieredSettings.resolve_singular_setting(
        preferences.episode_data_source,
        series_template_dict.get('episode_data_source', None),
        series.episode_data_source,
    )

    # Raise 409 if cannot communicate with the series episode data source
    interface = {
        'Emby': emby_interface,
        'Jellyfin': jellyfin_interface,
        'Plex': plex_interface,
        'Sonarr': sonarr_interface,
        'TMDb': tmdb_interface,
    }.get(episode_data_source, None)
    if interface is None:
        if raise_exc:
            raise HTTPException(
                status_code=409,
                detail=f'Unable to communicate with {episode_data_source}'
            )
        return []

    # Verify Series has an associated Library
    library = getattr(series,f'{episode_data_source.lower()}_library_name',None)
    if episode_data_source in ('Emby', 'Jellyfin', 'Plex') and library is None:
        if raise_exc:
            raise HTTPException(
                status_code=409,
                detail=f'Series does not have an associated {episode_data_source} library'
            )
        return []

    interface: Union[EmbyInterface, JellyfinInterface, PlexInterface,
                     SonarrInterface, TMDbInterface] = interface
    return interface.get_all_episodes(library, series.as_series_info, log=log)


def refresh_episode_data(
        db: Session,
        preferences: Preferences,
        series: Series,
        emby_interface: Optional[EmbyInterface],
        jellyfin_interface: Optional[JellyfinInterface],
        plex_interface: Optional[PlexInterface],
        sonarr_interface: Optional[SonarrInterface],
        tmdb_interface: Optional[TMDbInterface],
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
        preferences: Preferences to reference global settings.
        series: Series whose episodes are being refreshed.
        *_interface: Interface(s) to set ID's from.
        background_tasks: Optional BackgroundTasks queue to add the
            Episode ID assignment task to, if provided. If omitted then
            the assignment is done in a blocking manner.
        log: (Keyword) Logger for all log messages.

    Raises:
        HTTPException (404) if the Series Template DNE.
        HTTPException (409) if the indicted Episode data source cannot
            be communicated with.
    """

    # Get all Episodes for this Series from the Episode data source
    all_episodes = get_all_episode_data(
        preferences, series, emby_interface, jellyfin_interface, plex_interface,
        sonarr_interface, tmdb_interface, raise_exc=True, log=log,
    )

    # Get effective episode data source and sync specials toggle
    series_template = get_effective_series_template(series)
    sync_specials: bool = TieredSettings.resolve_singular_setting(
        preferences.sync_specials,
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
        existing = db.query(models.episode.Episode)\
            .filter(episode_info.filter_conditions(models.episode.Episode))\
            .first()

        # Episode does not exist, add
        if existing is None:
            log.info(f'{series.log_str} New Episode "{episode_info.title.full_title}"')
            episode = models.episode.Episode(
                series=series,
                title=episode_info.title.full_title,
                **episode_info.indices,
                **episode_info.ids,
                watched=watched,
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
            add = False
            if (do_title_match
                and existing.title != episode_info.title.full_title):
                existing.title = episode_info.title.full_title
                log.debug(f'{series.log_str} {existing.log_str} Updating title')
                changed, add = True, True

            # Update watched status
            if watched is not None and existing.watched != watched:
                log.debug(f'{series.log_str} {existing.log_str} Updating watched status')
                existing.watched = watched
                changed, add = True, True

            if add:
                episodes.append(existing)

    # Set Episode ID's for all new Episodes as background task or directly
    if background_tasks is None:
        set_episode_ids(
            db, series, episodes,
            emby_interface, jellyfin_interface, plex_interface,
            sonarr_interface, tmdb_interface, log=log,
        )
    else:
        background_tasks.add_task(
            set_episode_ids,
            db, series, episodes,
            emby_interface, jellyfin_interface, plex_interface, sonarr_interface,
            tmdb_interface, log=log
        )

    # Commit to database if changed
    if changed:
        db.commit()
