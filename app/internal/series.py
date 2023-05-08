from pathlib import Path
from requests import get
from typing import Any, Optional

from fastapi import HTTPException

from modules.Debug import log

from app.dependencies import (
    get_database, get_preferences, get_emby_interface,
    get_imagemagick_interface, get_jellyfin_interface, get_plex_interface,
    get_sonarr_interface, get_tmdb_interface
)
import app.models as models
from app.database.query import get_font, get_template
from app.schemas.preferences import MediaServer
from app.schemas.series import Series


def set_series_database_ids(
        series: Series,
        db: 'Database',
        emby_interface: 'EmbyInterface',
        jellyfin_interface: 'JellyfinInterface',
        plex_interface: 'PlexInterface',
        sonarr_interface: 'SonarrInterface',
        tmdb_interface: 'TMDbInterface') -> Series:

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
        preferences: 'Preferences',
        series: Series,
        tmdb_interface: 'TMDbInterface') -> None:

    # Exit if no TMDbInterface
    if tmdb_interface is None:
        log.debug(f'Series[{series.id}] Cannot download poster, TMDb interface disabled')
        return None

    # If series poster exists and is not a placeholder, return that
    path = Path(series.poster_file)
    if path.name != 'placeholder.jpg' and path.exists():
        series.poster_url = f'/assets/posters/{series.id}.jpg'
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
        path = preferences.asset_directory / 'posters' / f'{series.id}.jpg'
        try:
            path.write_bytes(get(poster_url).content)
            series.poster_file = str(path)
            series.poster_url = f'/assets/posters/{series.id}.jpg'
            db.commit()
            log.debug(f'Series[{series.id}] Downloaded poster {path.resolve()}')
        except Exception as e:
            log.error(f'Error downloading poster', e)
            return None

    return None


def load_series_title_cards(
        series: 'Series',
        media_server: MediaServer,
        db: 'Database',
        emby_interface: 'EmbyInterface',
        jellyfin_interface: 'JellyfinInterface',
        plex_interface: 'PlexInterface',
        force_reload: bool = False):
    """

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
            detail=f'Series {series.id} has no {media_server} Library',
        )
    elif interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with {media_server}',
        )

    # Get all episodes associated with this series
    all_episodes = db.query(models.episode.Episode)\
        .filter_by(series_id=series.id).all()
    
    # Get list of episodes to reload
    episodes_to_load = []
    for episode in all_episodes:
        # Only load if episode has a Card
        card = db.query(models.card.Card)\
            .filter_by(episode_id=episode.id).first()
        if card is None:
            log.debug(f'{series.log_str} {episode.log_str} - no associated card')
            continue

        # Look for a previously loaded asset
        loaded = db.query(models.loaded.Loaded)\
            .filter_by(episode_id=episode.id).first()

        # No previously loaded card for this episode, load
        if loaded is None:
            episodes_to_load.append((episode, card))
        # There is a previously loaded card, delete loaded entry, reload
        elif force_reload or (loaded.filesize != card.filesize):
            db.delete(loaded)
            episodes_to_load.append((episode, card))
        # Episode does not need to be (re)loaded
        else:
            log.debug(f'{series.log_str} {episode.log_str} Not loading card - has not changed')
            continue

    # Load into indicated interface
    loaded = interface.load_title_cards(
        library, series.as_series_info, episodes_to_load
    )

    # Update database with loaded entries
    for loaded_episode, loaded_card in loaded:
        db.add(
            models.loaded.Loaded(
                media_server=media_server,
                series_id=series.id,
                episode_id=loaded_episode.id,
                card_id=loaded_card.id,
                filesize=loaded_card.filesize,
            )
        )

    # If any cards were (re)loaded, commit updates to database
    if loaded:
        db.commit()

    return None
