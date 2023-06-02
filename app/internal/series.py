from pathlib import Path
from requests import get
from shutil import copy as file_copy
from typing import Optional

from fastapi import HTTPException

from modules.Debug import log
from modules.ImageMagickInterface import ImageMagickInterface
from modules.TMDbInterface2 import TMDbInterface

from app.dependencies import (
    get_database, get_emby_interface, get_jellyfin_interface,
    get_plex_interface,
)
import app.models as models
from app.schemas.preferences import MediaServer, Preferences
from app.schemas.series import Series


def load_all_media_servers() -> None:
    """
    Schedule-able function to load all Title Cards in the Database to 
    the media servers.
    """

    try:
        # Get the Database
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
                        get_jellyfin_interface(), get_plex_interface(),
                    )
                except HTTPException as e:
                    log.warning(f'{series.log_str} Skipping Title Card loading')
                    continue
    except Exception as e:
        log.exception(f'Failed to load Title Cards', e)


def set_series_database_ids(
        series: Series,
        db: 'Database',
        emby_interface: 'EmbyInterface',
        jellyfin_interface: 'JellyfinInterface',
        plex_interface: 'PlexInterface',
        sonarr_interface: 'SonarrInterface',
        tmdb_interface: 'TMDbInterface') -> Series:
    """
    Set the database ID's of the given Series.

    Args:
        series: Series to set the ID's of.
        db: Database to commit changes to.
        *_interface: Interface to query for database ID's from.

    Returns:
        Modified Series with the database ID's set.
    """

    # Create SeriesInfo object for this entry, query all interfaces
    series_info = series.as_series_info
    if emby_interface and series.emby_library_name:
        emby_interface.set_series_ids(series.emby_library_name, series_info)
    if jellyfin_interface and series.jellyfin_library_name:
        jellyfin_interface.set_series_ids(
            series.jellyfin_library_name, series_info
        )
    if plex_interface and series.plex_library_name:
        plex_interface.set_series_ids(series.plex_library_name, series_info)
    if sonarr_interface:
        sonarr_interface.set_series_ids(series_info)
    if tmdb_interface:
        tmdb_interface.set_series_ids(series_info)

    # Update database if new ID's are available
    changed = False
    for id_type in ('emby_id', 'imdb_id', 'jellyfin_id', 'sonarr_id', 'tmdb_id',
                    'tvdb_id', 'tvrage_id'):
        if getattr(series, id_type) is None and series_info.has_id(id_type):
            setattr(series, id_type, getattr(series_info, id_type))
            changed = True

    if changed:
        db.commit()

    return series


def download_series_poster(
        db: 'Database',
        preferences: Preferences,
        series: Series,
        tmdb_interface: Optional[TMDbInterface],
        image_magick_interface: Optional[ImageMagickInterface]) -> None:
    """
    Download the poster for the given Series.

    Args:
        db: Database to commit any changes to.
        preferences: Base Preferences to get the global asset directory.
        series: Series to download the poster of.
        tmdb_interface: Interface to TMDb to download a poster from.
    """

    # Exit if no TMDbInterface
    if tmdb_interface is None:
        log.debug(f'Series[{series.id}] Cannot download poster, TMDb interface disabled')
        return None

    # If Series poster exists and is not a placeholder, return that
    path = Path(series.poster_file)
    if path.name != 'placeholder.jpg' and path.exists():
        series.poster_url = f'/assets/{series.id}/poster.jpg'
        db.commit()
        log.debug(f'Series[{series.id}] Poster already exists, using {path.resolve()}')
        return None

    # Attempt to download poster
    series_info = series.as_series_info
    if (poster_url := tmdb_interface.get_series_poster(series_info)) is None:
        log.debug(f'Series[{series.id}] TMDb returned no valid posters')
        return None
    # Poster downloaded, write file, update database
    else:
        path = preferences.asset_directory / str(series.id) / 'poster.jpg'
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Download
            path.write_bytes(get(poster_url).content)
            series.poster_file = str(path)
            series.poster_url = f'/assets/{series.id}/poster.jpg'

            # Create resized small poster
            resized_path = path.parent / 'poster-750.jpg'
            if image_magick_interface is None:
                file_copy(
                    preferences.INTERNAL_ASSET_DIRECTORY / 'placeholder.jpg',
                    resized_path,
                )
            else:
                image_magick_interface.resize_image(
                    path, resized_path, by='width', width=750,
                )

            db.commit()
            log.debug(f'Series[{series.id}] Downloaded poster {path.resolve()}')
        except Exception as e:
            log.error(f'Error downloading poster', e)
            return None

    return None


def delete_series_and_episodes(
        db: 'Database',
        series: Series, *,
        commit_changes: bool = True) -> None:
    """
    Delete the given Series, it's poster, and all associated Episodes.

    Args:
        db: Database to commit any deletion to.
        series: Series to delete.
        commit_changes: Whether to commit Database changes.
    """

    # Delete poster if not the placeholder
    series_poster = Path(series.poster_file)
    if series_poster.stem != 'placeholder' and series_poster.exists():
        series_poster.unlink(missing_ok=True)
        small_poster = series_poster.parent / 'poster-750.jpg'
        small_poster.unlink(missing_ok=True)

        log.debug(f'{series.log_str} Deleted poster(s)')

    # Delete series and episodes from database
    log.info(f'Deleting {series.log_str}')
    db.delete(series)
    [db.delete(episode) for episode in series.episodes]

    # Commit changes if indicated
    if commit_changes:
        db.commit()

    return None


def load_series_title_cards(
        series: Series,
        media_server: MediaServer,
        db: 'Database',
        emby_interface: Optional['EmbyInterface'],
        jellyfin_interface: Optional['JellyfinInterface'],
        plex_interface: Optional['PlexInterface'],
        force_reload: bool = False) -> None:
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
    """

    # Get associated library for the indicated media server
    library = getattr(series, f'{media_server.lower()}_library_name', None)
    interface = {
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
    elif interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with {media_server}',
        )
    
    # Get list of episodes to reload
    episodes_to_load = []
    changed = False
    for episode in series.episodes:
        # Only load if episode has a Card
        if not episode.card:
            log.debug(f'{series.log_str} {episode.log_str} - no associated card')
            continue
        card = episode.card[0]

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
            log.debug(f'{series.log_str} {episode.log_str} Not loading card - has not changed')
            continue

    # Load into indicated interface
    loaded_assets = interface.load_title_cards(
        library, series.as_series_info, episodes_to_load
    )

    # Update database with loaded entries
    for loaded_episode, loaded_card in loaded_assets:
        db.add(
            models.loaded.Loaded(
                media_server=media_server,
                series=series,
                episode=loaded_episode,
                card=loaded_card,
                filesize=loaded_card.filesize,
            )
        )

    # If any cards were (re)loaded, commit updates to database
    if changed or loaded_assets:
        db.commit()

    return None