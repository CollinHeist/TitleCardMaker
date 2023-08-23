from logging import Logger
from pathlib import Path
from shutil import copy as file_copy
from time import sleep
from typing import Optional, Union

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
from app.schemas.preferences import MediaServer, Preferences
from app.schemas.series import NewSeries, Series

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
        log: (Keyword) Logger for all log messages.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get all Series
            changed = False
            for series in db.query(models.series.Series).all():
                try:
                    changed |= set_series_database_ids(
                        series, db, get_emby_interface(),
                        get_jellyfin_interface(), get_plex_interface(),
                        get_sonarr_interface(), get_tmdb_interface(),
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
        log: (Keyword) Logger for all log messages.
    """

    try:
        # Get the Database
        retries = 0
        with next(get_database()) as db:
            # Get all Series
            for series in db.query(models.series.Series).all():
                # Get the primary Media Server to load cards into
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
                    load_series_title_cards(
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
        log: (Keyword) Logger for all log messages.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get all Series
            for series in db.query(models.series.Series).all():
                try:
                    download_series_poster(
                        db, get_preferences(), series, get_emby_interface(),
                        get_imagemagick_interface(), get_jellyfin_interface(),
                        get_plex_interface(), get_tmdb_interface(), log=log,
                    )
                except HTTPException:
                    log.warning(f'{series.log_str} Skipping poster selection')
                    continue
    except Exception as e:
        log.exception(f'Failed to download Series posters', e)


def set_series_database_ids(
        series: Series,
        db: Session,
        emby_interface: Optional[EmbyInterface] = None,
        jellyfin_interface: Optional[JellyfinInterface] = None,
        plex_interface: Optional[PlexInterface] = None,
        sonarr_interface: Optional[SonarrInterface] = None,
        tmdb_interface: Optional[TMDbInterface] = None,
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
        log: (Keyword) Logger for all log messages.

    Returns:
        Whether the Series was modified.
    """

    # Create SeriesInfo object for this entry, query all interfaces
    series_info = series.as_series_info
    if emby_interface and series.emby_library_name:
        emby_interface.set_series_ids(
            series.emby_library_name, series_info, log=log
        )
    if jellyfin_interface and series.jellyfin_library_name:
        jellyfin_interface.set_series_ids(
            series.jellyfin_library_name, series_info, log=log
        )
    if plex_interface and series.plex_library_name:
        plex_interface.set_series_ids(
            series.plex_library_name, series_info, log=log,
        )
    if sonarr_interface:
        sonarr_interface.set_series_ids(None, series_info, log=log)
    if tmdb_interface:
        tmdb_interface.set_series_ids(None, series_info, log=log)

    # Update database if new ID's are available
    changed = False
    for id_type in ('emby_id', 'imdb_id', 'jellyfin_id', 'sonarr_id', 'tmdb_id',
                    'tvdb_id', 'tvrage_id'):
        if getattr(series, id_type) is None and series_info.has_id(id_type):
            setattr(series, id_type, getattr(series_info, id_type))
            changed = True

    if commit and changed:
        db.commit()

    return changed


def download_series_poster(
        db: Session,
        preferences: Preferences,
        series: Series,
        emby_interface: Optional[EmbyInterface] = None,
        image_magick_interface: Optional[ImageMagickInterface] = None,
        jellyfin_interface: Optional[JellyfinInterface] = None,
        plex_interface: Optional[PlexInterface] = None,
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
        log: (Keyword) Logger for all log messages.
    """

    # Exit if no interface
    if not any((emby_interface, jellyfin_interface, plex_interface,
                tmdb_interface)):
        log.warning(f'{series.log_str} Cannot download poster')
        return None

    # If Series poster exists and is not a placeholder, return that
    path = Path(series.poster_file)
    if path.name != 'placeholder.jpg' and path.exists():
        poster_url = f'/assets/{series.id}/poster.jpg'
        if series.poster_url != poster_url:
            series.poster_url = poster_url
            db.commit()
            log.debug(f'Series[{series.id}] Poster already exists, using {path.resolve()}')
        return None

    # Download poster from Media Server if possible
    series_info = series.as_series_info
    poster = None
    if series.emby_library_name and emby_interface:
        poster = emby_interface.get_series_poster(
            series.emby_library_name, series_info, log=log
        )
    elif series.jellyfin_library_name and jellyfin_interface:
        poster = jellyfin_interface.get_series_poster(
            series.jellyfin_library_name, series_info, log=log,
        )
    elif series.plex_library_name and plex_interface:
        poster = plex_interface.get_series_poster(
            series.plex_library_name, series_info, log=log,
        )

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
    if image_magick_interface is None:
        file_copy(series.poster_path, resized_path)
    else:
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
        log: (Keyword) Logger for all log messages.
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
        emby_interface: Optional[EmbyInterface] = None,
        jellyfin_interface: Optional[JellyfinInterface] = None,
        plex_interface: Optional[PlexInterface] = None,
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
        *_interface: Interface to the applicable Media Server to load
            Title Cards into.
        force_reload: Whether to reload Title Cards even if no changes
            are detected.
        log: (Keyword) Logger for all log messages.
    """

    # Get associated library for the indicated media server
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
            detail=f'{series.log_str} has no {media_server} Library',
        )
    if interface is None:
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
        card = episode.card[-1]

        # Find previously loaded Card
        previously_loaded = None
        for loaded in episode.loaded:
            if loaded.media_server == media_server:
                previously_loaded = loaded
                break

        # No previously loaded Cards for this Episode in this server, load
        if not previously_loaded:
            episodes_to_load.append((episode, card))
            continue

        # There is a previously loaded card, delete loaded entry, reload
        if force_reload or previously_loaded.filesize != card.filesize:
            # Delete previosly loaded entries for this server
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
        log.debug(f'{series.log_str} {loaded_episode.log_str} Loaded card {card.log_str}')
        db.add(models.loaded.Loaded(
            media_server=media_server,
            series=series,
            episode=loaded_episode,
            card=loaded_card,
            filesize=loaded_card.filesize,
        ))

    # If any cards were (re)loaded, commit updates to database
    if changed or loaded_assets:
        db.commit()
        log.info(f'{series.log_str} Loaded {len(loaded_assets)} Cards into {media_server}')


def add_series(
        new_series: NewSeries,
        background_tasks: BackgroundTasks,
        db: Session,
        preferences: Preferences,
        emby_interface: Optional[EmbyInterface] = None,
        imagemagick_interface: Optional[ImageMagickInterface] = None,
        jellyfin_interface: Optional[JellyfinInterface] = None,
        plex_interface: Optional[PlexInterface] = None,
        sonarr_interface: Optional[SonarrInterface] = None,
        tmdb_interface: Optional[TMDbInterface] = None,
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
        log: (Keyword) Logger for all log messages.

    Returns:
        The Created Series.

    Raises:
        HTTPException (404) if any specified linked objects do not exist.
    """

    # Convert object to dictionary
    new_series_dict = new_series.dict()

    # If a Font or any Templates were indicated, verify they exist
    get_font(db, getattr(new_series, 'font_id', None), raise_exc=True)
    templates = get_all_templates(db, new_series_dict)

    # Add to database
    series = models.series.Series(**new_series_dict, templates=templates)
    db.add(series)
    db.commit()

    # Create source directory if DNE
    Path(series.source_directory).mkdir(parents=True, exist_ok=True)

    # Set Series ID's, download poster and logo
    set_series_database_ids(
        series, db, emby_interface, jellyfin_interface, plex_interface,
        sonarr_interface, tmdb_interface, log=log,
    )
    download_series_poster(
        db, preferences, series, emby_interface, imagemagick_interface,
        jellyfin_interface, plex_interface, tmdb_interface, log=log
    )
    download_series_logo(
        preferences, emby_interface, imagemagick_interface, jellyfin_interface,
        tmdb_interface, series, log=log,
    )

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=log)

    # Refresh Episode data
    background_tasks.add_task(
        # Function
        refresh_episode_data,
        # Arguments
        db, preferences, series, emby_interface, jellyfin_interface,
        plex_interface, sonarr_interface, tmdb_interface, background_tasks,
        log=log,
    )

    return series
