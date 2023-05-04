from pathlib import Path
from requests import get
from shutil import copy as file_copy
from typing import Annotated, Any, Literal, Optional, Union

from fastapi import (
    APIRouter, BackgroundTasks, Body, Depends, Form, HTTPException, UploadFile
)
from starlette.responses import RedirectResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from modules.Debug import log
from modules.SeriesInfo import SeriesInfo

from app.dependencies import (
    get_database, get_preferences, get_emby_interface, get_imagemagick_interface,
    get_jellyfin_interface, get_plex_interface, get_sonarr_interface,
    get_tmdb_interface
)
import app.models as models
from app.routers.fonts import get_font
from app.routers.templates import get_template
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import MediaServer
from app.schemas.series import NewSeries, Series, UpdateSeries
from app.schemas.episode import Episode


def get_series(db, series_id, *, raise_exc=True) -> Optional[Series]:
    """
    Get the Series with the given ID from the given Database.

    Args:
        db: SQL Database to query for the given Series.
        series_id: ID of the Series to query for.
        raise_exc: Whether to raise 404 if the given Series does not 
            exist. If False, then only an error message is logged.

    Returns:
        Series with the given ID. If one cannot be found and raise_exc
        is False, or if the given ID is None, then None is returned.

    Raises:
        HTTPException with a 404 status code if the Series cannot be
        found and raise_exc is True.
    """

    # No series ID provided, return immediately
    if series_id is None:
        return None

    series = db.query(models.series.Series).filter_by(id=series_id).first()
    if series is None:
        if raise_exc:
            raise HTTPException(
                status_code=404,
                detail=f'Series {series_id} not found',
            )
        else:
            log.error(f'Series {series_id} not found')
            return None

    return series


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


series_router = APIRouter(
    prefix='/series',
    tags=['Series'],
)


@series_router.get('/all', status_code=200)
def get_all_series(
        db = Depends(get_database)) -> list[Series]:
    """
    Get all defined Series.
    """
    
    return db.query(models.series.Series).all()


@series_router.post('/new', status_code=201)
def add_new_series(
        background_tasks: BackgroundTasks,
        new_series: NewSeries = Body(...),
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface),
        sonarr_interface = Depends(get_sonarr_interface),
        tmdb_interface = Depends(get_tmdb_interface)) -> Series:
    """
    Create a new Series. This also creates background tasks to set the
    database ID's of the series, as well as find and download a poster.

    - new_series: Series definition to create.
    """

    # If a template or font was indicated, verify they exist
    get_template(db, getattr(new_series, 'template_id', None), raise_exc=True)
    if getattr(new_series, 'font_id', None) is not None:
        get_font(db, new_series.font_id, raise_exc=True)

    # Add to database
    series = models.series.Series(**new_series.dict())
    db.add(series)
    db.commit()

    # Add background tasks to set ID's and download poster
    background_tasks.add_task(
        set_series_database_ids,
        series, db,
        emby_interface, jellyfin_interface, plex_interface, sonarr_interface,
        tmdb_interface,
    )
    background_tasks.add_task(
        download_series_poster, db, preferences, series, tmdb_interface,
    )

    return series


@series_router.delete('/{series_id}', status_code=204)
def delete_series(
        series_id: int,
        db = Depends(get_database)) -> None:
    """
    Delete the Series with the given ID. This also deletes the poster
    file, as well as any episodes associated with this series.

    - series_id: ID of the Series to delete.
    """

    # Find series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Delete poster if not the placeholder
    series_poster = Path(series.poster_file)
    if series_poster.stem != 'placeholder' and series_poster.exists():
        series_poster.unlink(missing_ok=True)

    # Delete series and episodes from database
    db.query(models.series.Series).filter_by(id=series_id).delete()
    db.query(models.episode.Episode).filter_by(series_id=series_id).delete()
    db.commit()

    return None


@series_router.get('/search', status_code=200)
def search_series(
        name: Optional[str] = None,
        template_id: Optional[int] = None,
        font_id: Optional[int] = None,
        max_results: Optional[int] = 50,
        db = Depends(get_database)):
    """
    Query all defined defined series by the given parameters. This
    performs an AND operation with the given conditions.

    - name: Substring to search for in the series names.
    - max_results: Maximum number of results to return.
    """

    conditions = []
    if name is not None:
        conditions.append(models.series.Series.name.contains(name))
    if template_id is not None:
        conditions.append(models.series.Series.template_id==template_id)
    if font_id is not None:
        conditions.append(models.series.Series.font_id==font_id)

    # Query by all given conditions
    all_series = db.query(models.series.Series).filter(*conditions).all()

    # Limit number of results if indicated
    results = all_series
    if max_results is not None:
        results = all_series[:max_results]

    return {
        'results': results,
        'total_count': len(all_series),
    }


@series_router.get('/{series_id}', status_code=200)
def get_series_config(
        series_id: int,
        db = Depends(get_database)) -> Series:
    """
    Get the config for the given Series.

    - series_id: ID of the series to get the config of.
    """

    return get_series(db, series_id, raise_exc=True)


@series_router.patch('/{series_id}', status_code=200)
def update_series(
        series_id: int,
        update_series: UpdateSeries = Body(...),
        db = Depends(get_database)) -> Series:
    """
    Update the config of the given Series.

    - series_id: ID of the Series to update.
    - update_series: Attributes of the Series to update.
    """
    log.critical(f'{update_series.dict()=}')
    # Query for this series, raise 404 if DNE
    series = db.query(models.series.Series).filter_by(id=series_id).first()
    if series is None:
        raise HTTPException(
            status_code=404,
            detail=f'Series {series_id} not found',
        )

    # If a template or font were indicated, verify they exist
    get_template(db, getattr(update_series, 'template_id', None),raise_exc=True)
    get_font(db, getattr(update_series, 'font_id', None), raise_exc=True)

    # Update each attribute of the object
    changed = False
    for attr, value in update_series.dict().items():
        if value != UNSPECIFIED and getattr(series, attr) != value:
            log.debug(f'Series[{series_id}].{attr} = {value}')
            setattr(series, attr, value)
            changed = True

    # If any values were changed, commit to database
    if changed:
        db.commit()
    
    return series


@series_router.post('/{series_id}/load/{media_server}', status_code=201,
        tags=['Emby', 'Jellyfin', 'Plex'])
def load_title_cards_into_media_server(
        series_id: int,
        media_server: MediaServer,
        db = Depends(get_database),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface)) -> None:
    """
    Load all of the given Series' unloaded Title Cards into the given
    Media Server. This only loads Cards that have not previously been
    loaded, or whose previously loaded cards have been changed.

    - series_id: ID of the Series whose Cards are being loaded.
    - media_server: Which Media Server to load cards into. Must have an
    active, valid Interface connection.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return load_series_title_cards(
        series, media_server, db, emby_interface, jellyfin_interface,
        plex_interface, force_reload=False
    )


@series_router.post('/{series_id}/reload/{media_server}', status_code=201,
        tags=['Emby', 'Jellyfin', 'Plex'])
def reload_title_cards_into_media_server(
        series_id: int,
        media_server: MediaServer,
        db = Depends(get_database),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface)) -> None:
    """
    Reload all of the given Series' Title Cards into the given Media
    Server. This loads all Cards, even those that have not changed.

    - series_id: ID of the Series whose Cards are being loaded.
    - media_server: Which Media Server to load cards into. Must have an
    active, valid Interface connection.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return load_series_title_cards(
        series, media_server, db, emby_interface, jellyfin_interface,
        plex_interface, force_reload=True
    )


@series_router.get('/{series_id}/poster', status_code=200)
def get_series_poster(
        series_id: int,
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        tmdb_interface = Depends(get_tmdb_interface)) -> str:
    """
    Download and return a poster for the given series.

    - series_id: Series being queried.
    """

    # Find series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return download_series_poster(db, preferences, series, tmdb_interface)


@series_router.post('/{series_id}/poster', status_code=201)
async def set_series_poster(
        series_id: int,
        poster_url: Optional[str] = Form(default=None),
        poster_file: Optional[UploadFile] = None,
        db = Depends(get_database),
        preferences = Depends(get_preferences)) -> str:
    """
    Set the poster for the given series.

    - series_id: ID of the series whose poster is being updated.
    - poster_url: URL to the new poster.
    - poster_file: New poster file.
    """

    # Find series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get poster contents
    uploaded_file = await poster_file.read()

    # Send error if both a URL and file were provided
    if poster_url is not None and len(uploaded_file) > 0:
        raise HTTPException(
            status_code=400,
            detail='Cannot provide multiple posters'
        )

    # Send error if neither were provided
    if poster_url is None and len(uploaded_file) == 0:
        raise HTTPException(
            status_code=400,
            detail='URL or file are required'
        )

    # If an uploaded file was provided, use that
    if len(uploaded_file) > 0:
        poster_content = uploaded_file

    # If only URL was required, attempt to download, error if unable
    if poster_url is not None:
        try:
            poster_content = get(poster_url).content
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download poster - {e}'
            )

    # Valid poster provided, download into asset directory
    poster_path = preferences.asset_directory / 'posters' / f'{series.id}.jpg'
    series.poster_file = str(poster_path)
    poster_file.write_bytes(poster_content)

    # Update poster, commit to database
    series.poster_url = f'/assets/posters/{poster_file.name}'
    db.commit()
    
    return series.poster_url