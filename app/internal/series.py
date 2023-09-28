from logging import Logger
from pathlib import Path
from shutil import copy as file_copy
from time import sleep
from typing import Literal, Optional, Union

from fastapi import BackgroundTasks, HTTPException
from requests import get
from sqlalchemy.exc import InvalidRequestError, OperationalError
from sqlalchemy.orm import Session
from app.database.query import get_all_templates, get_font

from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app import models
from app.internal.cards import refresh_remote_card_types
from app.internal.episodes import refresh_episode_data
from app.internal.sources import download_series_logo
from app.models.card import Card
from app.models.episode import Episode
from app.models.loaded import Loaded
from app.models.series import Series
from app.schemas.base import MediaServer
from app.schemas.connection import EpisodeDataSourceInterface
from app.schemas.preferences import Preferences
from app.schemas.series import NewSeries, SearchResult

from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.ImageMagickInterface import ImageMagickInterface
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface


def set_all_series_ids(*, log: Logger = log) -> None:
    """
    Schedule-able function to set any missing Series ID's for all Series
    in the Database.

    Args:
        log: Logger for all log messages.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get all Series
            changed = False
            for series in db.query(Series).all():
                try:
                    changed |= set_series_database_ids(
                        series, db,
                        get_emby_interfaces(),
                        get_jellyfin_interfaces(),
                        get_plex_interfaces(),
                        get_sonarr_interfaces(),
                        get_tmdb_interface(),
                        commit=False,
                    )
                except HTTPException:
                    log.warning(f'{series.log_str} Skipping ID assignment')
                    continue

            # Commit changes if any were made
            if changed:
                db.commit()
    except Exception as e:
        log.exception(f'Failed to set Series IDs', e)


def load_all_media_servers(*, log: Logger = log) -> None:
    """
    Schedule-able function to load all Title Cards in the Database to
    the media servers.

    Args:
        log: Logger for all log messages.
    """

    try:
        # Get the Database
        retries = 0
        with next(get_database()) as db:
            # Get all Series
            for series in db.query(Series).all():
                # Get the primary Media Server to load cards into
                # TODO update
                if series.emby_library_name is not None:
                    media_server = 'Emby'
                elif series.jellyfin_library_name is not None:
                    media_server = 'Jellyfin'
                elif series.plex_library_name is not None:
                    media_server = 'Plex'
                # Skip this Series if it has no library
                else:
                    log.debug(f'{series.log_str} has no Library, not loading Title Cards')
                    continue

                # Load Title Cards for this Series
                try:
                    load_series_title_cards( # TODO update w/ multi-conn
                        series, media_server, db, get_emby_interface(),
                        get_jellyfin_interface(), get_plex_interface(), log=log,
                    )
                except HTTPException:
                    log.warning(f'{series.log_str} Skipping Title Card loading')
                    continue
                except OperationalError:
                    if (retries := retries + 1) > 10:
                        log.warning(f'Database is very busy - stopping Task')
                        break

                    log.debug(f'Database is busy, sleeping..')
                    sleep(30)
    except Exception as e:
        log.exception(f'Failed to load Title Cards', e)


def download_all_series_posters(*, log: Logger = log) -> None:
    """
    Schedule-able function to download all posters for all monitored
    Series in the Database.

    Args:
        log: Logger for all log messages.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get all Series
            for series in db.query(Series).all():
                try:
                    download_series_poster(
                        db, get_preferences(), series,
                        get_emby_interfaces(),
                        get_imagemagick_interface(),
                        get_jellyfin_interfaces(),
                        get_plex_interfaces(),
                        get_tmdb_interface(),
                        log=log,
                    )
                except HTTPException:
                    log.warning(f'{series.log_str} Skipping poster selection')
                    continue
    except Exception as e:
        log.exception(f'Failed to download Series posters', e)


def set_series_database_ids(
        series: Series,
        db: Session,
        emby_interfaces: InterfaceGroup[int, EmbyInterface],
        jellyfin_interfaces: InterfaceGroup[int, JellyfinInterface],
        plex_interfaces: InterfaceGroup[int, PlexInterface],
        sonarr_interfaces: InterfaceGroup[int, SonarrInterface],
        tmdb_interface: Optional[TMDbInterface],
        *,
        commit: bool = True,
        log: Logger = log,
    ) -> bool:
    """
    Set the database ID's of the given Series.

    Args:
        series: Series to set the ID's of.
        db: Database to commit changes to.
        *_interface: Interface to query for database ID's from.
        commit: Whether to commit changes after setting any ID's.
        log: Logger for all log messages.

    Returns:
        Whether the Series was modified.
    """

    # Create SeriesInfo object for this entry, query all interfaces
    series_info = series.as_series_info
    for interface_id, library_name in series.get_libraries('Emby'):
        if (interface := emby_interfaces[interface_id]):
            interface.set_series_ids(library_name, series_info, log=log)
    for interface_id, library_name in series.get_libraries('Jellyfin'):
        if (interface := jellyfin_interfaces[interface_id]):
            interface.set_series_ids(library_name, series_info, log=log)
    for interface_id, library_name in series.get_libraries('Plex'):
        if (interface := plex_interfaces[interface_id]):
            interface.set_series_ids(library_name, series_info, log=log)
    if series.primary_sonarr_interface_id is None:
        for _, interface in sonarr_interfaces:
            interface.set_series_ids(None, series_info, log=log)
            break
    elif (interface := sonarr_interfaces[series.primary_sonarr_interface_id]):
        interface.set_series_ids(None, series_info, log=log)
    if tmdb_interface:
        tmdb_interface.set_series_ids(None, series_info, log=log)

    # Update database if new ID's are available; first do basic IDs
    changed = False
    for id_type in ('imdb_id', 'tmdb_id', 'tvdb_id', 'tvrage_id'):
        if getattr(series, id_type) is None and series_info.has_id(id_type):
            setattr(series, id_type, getattr(series_info, id_type))
            changed = True

    # Update interface IDs
    for id_type in ('emby_id', 'jellyfin_id', 'sonarr_id'): # TODO add rating key
        # If this InterfaceID contains more data than currently defined, add
        if getattr(series, id_type) is None:
            continue # TODO remove when DB migration is added for None -> ''
        if getattr(series_info, id_type) > getattr(series, id_type):
            setattr(
                series,
                id_type,
                str(getattr(series_info, id_type) + getattr(series, id_type))
            )
            changed = True
            log.info(f'series.{id_type} = {getattr(series, id_type)}') # TODO temporary logging

    if commit and changed:
        db.commit()

    return changed


def download_series_poster(
        db: Session,
        preferences: Preferences,
        series: Series,
        emby_interfaces: InterfaceGroup[int, EmbyInterface],
        image_magick_interface: ImageMagickInterface,
        jellyfin_interfaces: InterfaceGroup[int, JellyfinInterface],
        plex_interfaces: InterfaceGroup[int, PlexInterface],
        tmdb_interface: Optional[TMDbInterface] = None,
        *,
        log: Logger = log,
    ) -> None:
    """
    Download the poster for the given Series.

    Args:
        db: Database to commit any changes to.
        preferences: Base Preferences to get the global asset directory.
        series: Series to download the poster of.
        *_interface: Interface to TMDb to query for posters.
        log: Logger for all log messages.
    """

    # If Series poster exists and is not a placeholder, return
    path = Path(series.poster_file)
    if path.name != 'placeholder.jpg' and path.exists():
        poster_url = f'/assets/{series.id}/poster.jpg'
        if series.poster_url != poster_url:
            series.poster_url = poster_url
            db.commit()
            log.debug(f'Series[{series.id}] Poster already exists, using {path.resolve()}')
        return None

    # Download poster from Media Server if possible
    series_info, poster = series.as_series_info, None
    for library in series.libraries:
        if (library['media_server'] == 'Emby'
            and (interface := emby_interfaces[library['interface_id']])):
            poster = interface.get_series_poster(
                library['name'], series_info, log=log
            )
        elif (library['media_server'] == 'Jellyfin'
            and (interface := jellyfin_interfaces[library['interface_id']])):
            poster = interface.get_series_poster(
                library['name'], series_info, log=log
            )
        elif (library['media_server'] == 'Plex'
            and (interface := plex_interfaces[library['interface_id']])):
            poster = interface.get_series_poster(
                library['name'], series_info, log=log
            )

        # Stop if poster was found
        if poster is not None:
            break

    # If no poster was returned, download from TMDb
    if poster is None and tmdb_interface:
        poster = tmdb_interface.get_series_poster(series_info, log=log)

    # If no posters were returned, log and exit
    if poster is None:
        log.warning(f'{series.log_str} no posters found')
        return None

    # Get path to the poster to download
    path = preferences.asset_directory / str(series.id) / 'poster.jpg'
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Write or download
        if isinstance(poster, bytes):
            path.write_bytes(poster)
        else:
            path.write_bytes(get(poster, timeout=30).content)
    except Exception as e:
        log.error(f'{series.log_str} Error downloading poster', e)
        return None
    series.poster_file = str(path)
    series.poster_url = f'/assets/{series.id}/poster.jpg'
    db.commit()

    # Create resized small poster
    resized_path = path.parent / 'poster-750.jpg'
    image_magick_interface.resize_image(
        path, resized_path, by='width', width=750,
    )

    log.debug(f'Series[{series.id}] Downloaded poster {path.resolve()}')
    return None


def delete_series_and_episodes(
        db: Session,
        series: Series,
        *,
        commit_changes: bool = True,
        log: Logger = log,
    ) -> None:
    """
    Delete the given Series, it's poster, and all associated Episodes.

    Args:
        db: Database to commit any deletion to.
        series: Series to delete.
        commit_changes: Whether to commit Database changes.
        log: Logger for all log messages.
    """

    # Delete poster if not the placeholder
    series_poster = Path(series.poster_file)
    if series_poster.stem != 'placeholder' and series_poster.exists():
        series_poster.unlink(missing_ok=True)
        small_poster = series_poster.parent / 'poster-750.jpg'
        small_poster.unlink(missing_ok=True)

        log.debug(f'{series.log_str} Deleted poster(s)')

    # Delete Series and Episodes from database
    log.info(f'Deleting {series.log_str}')
    db.delete(series)
    for episode in series.episodes:
        db.delete(episode)

    # Commit changes if indicated
    if commit_changes:
        db.commit()


def load_series_title_cards(
        series: Series,
        media_server: MediaServer,
        db: Session,
        emby_interface: InterfaceGroup[int, EmbyInterface],
        jellyfin_interface: InterfaceGroup[int, JellyfinInterface],
        plex_interface: InterfaceGroup[int, PlexInterface],
        force_reload: bool = False,
        *,
        log: Logger = log,
    ) -> None:
    """
    Load the Title Cards for the given Series into the associated media
    server.

    Args:
        series: Series to load the Title Cards of.
        media_server: Where to load the Title Cards into.
        db: Database to look for and add Loaded records from/to.
        *_interfaces: Interfaces to the applicable Media Server to load
            Title Cards into.
        force_reload: Whether to reload Title Cards even if no changes
            are detected.
        log: Logger for all log messages.

    Raises:
        HTTPException (409): The specified Media Server cannot be
            communciated with, or if the given Series does not have an
            associated library.
    """

    # Get associated library for the indicated media server
    # TODO Update
    library = getattr(series, f'{media_server.lower()}_library_name', None)
    interface: Union[EmbyInterface, JellyfinInterface, PlexInterface] = {
        'Emby': emby_interface,
        'Jellyfin': jellyfin_interface,
        'Plex': plex_interface,
    }.get(media_server, None)

    # Raise 409 if no library, or the server's interface is invalid
    if library is None:
        raise HTTPException(
            status_code=409,
            detail=f'{series.log_str} has no linked {media_server} Library',
        )
    if not interface:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with {media_server}',
        )

    # Get list of Episodes to reload
    changed, episodes_to_load = False, []
    for episode in series.episodes:
        # Only load if Episode has a Card
        if not episode.card:
            log.debug(f'{series.log_str} {episode.log_str} - no associated Card')
            continue
        card = episode.card[0]

        # Find previously loaded Card
        previously_loaded = None
        for loaded in episode.loaded:
            if loaded.media_server == media_server:
                previously_loaded = loaded
                break

        # No previously loaded Cards for this Episode in this server, load
        if previously_loaded is None:
            episodes_to_load.append((episode, card))
            continue

        # There is a previously loaded card, delete loaded entry, reload
        if (force_reload or (previously_loaded is not None
                             and previously_loaded.filesize != card.filesize)):
            # Delete previously loaded entries for this server
            for loaded in episode.loaded:
                if loaded.media_server == media_server:
                    db.delete(loaded)
                    changed = True
            episodes_to_load.append((episode, card))
        # Episode does not need to be (re)loaded
        else:
            continue

    # Load into indicated interface
    loaded_assets = interface.load_title_cards(
        library, series.as_series_info, episodes_to_load, log=log,
    )

    # Update database with loaded entries
    for loaded_episode, loaded_card in loaded_assets:
        try:
            db.add(Loaded(
                media_server=media_server,
                series=series,
                episode=loaded_episode,
                card_id=loaded_card.id,
                filesize=loaded_card.filesize,
            ))
            log.debug(f'{series.log_str} {loaded_episode.log_str} Loaded {card.log_str}')
        except InvalidRequestError:
            log.warning(f'Error creating Loaded asset for {loaded_episode.log_str} {card.log_str}')
            continue

    # If any cards were (re)loaded, commit updates to database
    if changed or loaded_assets:
        db.commit()
        log.info(f'{series.log_str} Loaded {len(loaded_assets)} Cards into {media_server}')


def load_episode_title_card(
        episode: Episode,
        db: Session,
        media_server: Literal['Emby', 'Jellyfin', 'Plex'],
        emby_interface: Optional[EmbyInterface] = None,
        jellyfin_interface: Optional[JellyfinInterface] = None,
        plex_interface: Optional[PlexInterface] = None,
        *,
        attempts: int = 1,
        log: Logger = log,
    ) -> Optional[bool]:
    """
    Load the Title Card for the given Episode into the indicated media
    server. This is a forced reload, and any existing Loaded assets are
    deleted.

    Args:
        episode: Episode to load the Title Card of.
        db: Database to look for and add Loaded records from/to.
        media_server: Which media server to load Title Cards into.
        *_interface: Interface to load Title Cards into.
        attempts: How many times to attempt loading the given Card.
        log: Logger for all log messages.

    Returns:
        Whether the Episode's Card was loaded or not. None if there is
        no Card, or no connection to the indicated media server.
    """

    # Only load if Episode has a Card
    if not episode.card:
        log.debug(f'{episode.series.log_str} {episode.log_str} - no associated Card')
        return None
    card: Card = episode.card[-1]

    # Get previously loaded asset for comparison
    previously_loaded = db.query(Loaded)\
        .filter_by(episode_id=episode.id, media_server=media_server)\
        .first()

    # If this asset's filesize has not changed, no need to reload
    if (previously_loaded is not None
        and previously_loaded.filesize == card.filesize):
        return True

    # New Card is different, delete Loaded entry
    if previously_loaded is not None:
        db.delete(previously_loaded)

    # Load into the given server
    interface: Union[EmbyInterface, JellyfinInterface, PlexInterface] = {
        'Emby': emby_interface,
        'Jellyfin': jellyfin_interface,
        'Plex': plex_interface,
    }[media_server]
    if not interface:
        log.debug(f'No {media_server} connection - cannot load Card')
        return None

    loaded_assets = []
    for _ in range(attempts):
        # Load Episode's Card; exit loop if loaded
        loaded_assets = interface.load_title_cards(
            episode.series.plex_library_name,
            episode.series.as_series_info,
            [(episode, card)],
            log=log,
        )
        if loaded_assets:
            break

        log.debug(f'{episode.series.log_str} {episode.log_str} not found - waiting')
        sleep(15)

    # Episode was not loaded, exit
    if not loaded_assets:
        return False

    # Episode loaded, create Loaded asset and commit to database
    db.add(Loaded(
        media_server=media_server,
        series=episode.series,
        episode=episode,
        card=card,
        filesize=card.filesize,
    ))
    log.debug(f'{episode.series.log_str} {episode.log_str} Loaded {card.log_str}')
    db.commit()
    return None

    return True


def add_series(
        new_series: NewSeries,
        background_tasks: BackgroundTasks,
        db: Session,
        preferences: Preferences,
        emby_interfaces: InterfaceGroup[int, EmbyInterface],
        imagemagick_interface: ImageMagickInterface,
        jellyfin_interfaces: InterfaceGroup[int, JellyfinInterface],
        plex_interfaces: InterfaceGroup[int, PlexInterface],
        sonarr_interfaces: InterfaceGroup[int, SonarrInterface],
        tmdb_interface: Optional[TMDbInterface],
        *,
        log: Logger = log,
    ) -> Series:
    """
    Add the given NewSeries object to the database, and then perform all
    the initial Series processing - e.g. setting Series ID's,
    downloading a poster and logo, and refreshing Episode data.

    Args:
        new_series: NewSeries to add to the Database.
        background_tasks: BackgroundTasks to add the Episode data refresh
            task to.
        db: Database to add the Series to.
        preferences: Global Preferences for setting resolution.
        *_interface: Interface to query.
        log: Logger for all log messages.

    Returns:
        The Created Series.

    Raises:
        HTTPException (404): A linked object does not exist.
    """

    # Convert object to dictionary
    new_series_dict = new_series.dict()

    # If a Font or any Templates were indicated, verify they exist
    get_font(db, getattr(new_series, 'font_id', None), raise_exc=True)
    templates = get_all_templates(db, new_series_dict)

    # Add to database
    series = Series(**new_series_dict, templates=templates)
    db.add(series)
    db.commit()

    # Create source directory if DNE
    Path(series.source_directory).mkdir(parents=True, exist_ok=True)

    # Set Series ID's, download poster and logo
    set_series_database_ids(
        series, db, emby_interfaces, jellyfin_interfaces, plex_interfaces,
        sonarr_interfaces, tmdb_interface, log=log,
    )
    download_series_poster(
        db, preferences, series, emby_interfaces, imagemagick_interface,
        jellyfin_interfaces, plex_interfaces, tmdb_interface, log=log
    )
    download_series_logo(
        preferences, emby_interfaces, imagemagick_interface, jellyfin_interfaces,
        tmdb_interface, series, log=log,
    )

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=log)

    # Refresh Episode data
    background_tasks.add_task(
        # Function
        refresh_episode_data,
        # Arguments
        db, preferences, series, emby_interfaces, jellyfin_interfaces,
        plex_interfaces, sonarr_interfaces, tmdb_interface, background_tasks,
        log=log,
    )

    return series


def lookup_series(
        db: Session,
        interface: EpisodeDataSourceInterface,
        name: str,
        *,
        max_results: int = 25,
        log: Logger = log,
    ) -> list[SearchResult]:
    """
    _summary_

    Args:
        db: _description_
        interface: _description_
        max_results: _description_. Defaults to 25.
        log: _description_. Defaults to log.

    Returns:
        _description_
    """

    # Query Interface, only return max of 25 results TODO temporary?
    results: list[SearchResult] = interface.query_series(name, log=log)
    results = results[:max_results]

    # Update added attribute(s)
    for result in results:
        # Query database for this result
        existing = db.query(models.series.Series)\
            .filter(result.series_info.filter_conditions(models.series.Series))\
            .first()

        # Result has been added if there is an existing Series
        result.added = existing is not None

    return results
