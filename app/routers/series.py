from pathlib import Path
from requests import get
from typing import Annotated, Any, Literal, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Form, HTTPException, Query, Response, UploadFile
from starlette.responses import RedirectResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from modules.Debug import log
from modules.SeriesInfo import SeriesInfo

from app.dependencies import get_database, get_preferences, get_emby_interface,\
    get_jellyfin_interface, get_plex_interface, get_sonarr_interface, \
    get_tmdb_interface
import app.models as models
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import EpisodeDataSource, MediaServer,\
    MediaServerToggle
from app.schemas.series import (
    NewSeries, Series, SortedImageSourceToggle, UpdateSeries
)
from app.schemas.episode import Episode


def join_lists(keys: list[Any], vals: list[Any], desc: str,
        default: Any = None) -> Union[dict[str, Any], None]:

    is_null = lambda v: (v is None) or (v == UNSPECIFIED)

    if is_null(keys) ^ is_null(vals):
        raise HTTPException(
            status_code=400,
            detail=f'Provide same number of {desc}',
        )
    elif not is_null(keys) and not is_null(vals):
        if len(keys) != len(vals):
            raise HTTPException(
                status_code=400,
                detail=f'Provide same number of {desc}',
            )
        else:
            return {key: val for key, val in zip(keys, vals) if len(key) > 0}

    return UNSPECIFIED if keys == UNSPECIFIED else default


def set_series_database_ids(
        series: Series,
        db: 'Database',
        emby_library_name: Optional[str],
        jellyfin_library_name: Optional[str],
        plex_library_name: Optional[str],
        emby_interface: 'EmbyInterface',
        jellyfin_interface: 'JellyfinInterface',
        plex_interface: 'PlexInterface',
        sonarr_interface: 'SonarrInterface',
        tmdb_interface: 'TMDbInterface') -> Series:

    # Create SeriesInfo object for this entry, query all interfaces
    series_info = SeriesInfo(
        series.name, series.year, emby_id=series.emby_id,
        jellyfin_id=series.jellyfin_id, sonarr_id=series.sonarr_id,
        tmdb_id=series.tmdb_id, tvdb_id=series.tvdb_id,
        tvrage_id=series.tvrage_id,
    )
    if emby_interface is not None and emby_library_name is not None:
        emby_interface.set_series_ids(emby_library_name, series_info)
    if jellyfin_interface is not None and jellyfin_library_name is not None:
        jellyfin_interface.set_series_ids(jellyfin_library_name, series_info)
    if plex_interface is not None and plex_library_name is not None:
        plex_interface.set_series_ids(plex_library_name, series_info)
    if sonarr_interface is not None:
        sonarr_interface.set_series_ids(series_info)
    if tmdb_interface is not None:
        tmdb_interface.set_series_ids(series_info)

    # Update database if new ID's are available
    if series.emby_id is None and series_info.has_id('emby_id'):
        series.emby_id = series_info.emby_id
    if series.jellyfin_id is None and series_info.has_id('jellyfin_id'):
        series.jellyfin_id = series_info.jellyfin_id
    if series.sonarr_id is None and series_info.has_id('sonarr_id'):
        series.sonarr_id = series_info.sonarr_id
    if series.tmdb_id is None and series_info.has_id('tmdb_id'):
        series.tmdb_id = series_info.tmdb_id
    if series.tvdb_id is None and series_info.has_id('tvdb_id'):
        series.tvdb_id = series_info.tvdb_id
    if series.tvrage_id is None and series_info.has_id('tvrage_id'):
        series.tvrage_id = series_info.tvrage_id
    db.commit()

    return series


def download_series_poster(
        series: Series,
        db: 'Database',
        preferences: 'Preferences',
        tmdb_interface: 'TMDbInterface') -> None:

    # Exit if no TMDbInterface
    if tmdb_interface is None:
        return None

    # If series poster exists and is not a placeholder, return that
    path = Path(series.poster_path)
    if path.exists() and path.name != 'placeholder.jpg':
        return series.poster_url

    # Attempt to download poster
    series_info = SeriesInfo(
        series.name, series.year, emby_id=series.emby_id,
        jellyfin_id=series.jellyfin_id, sonarr_id=series.sonarr_id,
        tmdb_id=series.tmdb_id, tvdb_id=series.tvdb_id,
        tvrage_id=series.tvrage_id,
    )

    poster_url = tmdb_interface.get_series_poster(series_info)
    if poster_url is None:
        log.debug(f'TMDb returned no valid posters')
    else:
        path = preferences.asset_directory / 'posters' / f'{series.id}.jpg'
        try:
            path.write_bytes(get(poster_url).content)
            series.poster_path = str(path)
            series.poster_url = f'/assets/posters/{series.id}.jpg'
            db.commit()
            log.debug(f'Downloaded poster') 
        except Exception as e:
            log.error(f'Error downloading poster', e)

    return None


series_router = APIRouter(
    prefix='/series',
    tags=['Series'],
)


@series_router.get('/all')
def get_all_series(
        db = Depends(get_database)) -> list[Series]:
    """
    Get all defines Series.
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
    log.critical(f'{new_series.dict()=}')
    # If a template or font was indicated, verify they exist
    if getattr(new_series, 'template_id', None) is not None:
        if (db.query(models.template.Template)\
            .filter_by(id=new_series.template_id).first()) is None:
            raise HTTPException(
                status_code=404,
                detail=f'Template {new_series.template_id} not found',
            )
    if getattr(new_series, 'font_id', None) is not None:
        if (db.query(models.font.Font)\
            .filter_by(id=new_series.font_id).first()) is None:
            raise HTTPException(
                status_code=404,
                detail=f'Font {new_series.font_id} not found',
            )

    # Add to database
    series = models.series.Series(**new_series.dict())
    db.add(series)
    db.commit()

    # Add background tasks to set ID's and download poster
    background_tasks.add_task(
        set_series_database_ids,
        series, db, series.emby_library_name, series.jellyfin_library_name,
        series.plex_library_name, emby_interface, jellyfin_interface,
        plex_interface, sonarr_interface, tmdb_interface,
    )
    background_tasks.add_task(
        download_series_poster, series, db, preferences, tmdb_interface
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
    series = db.query(models.series.Series).filter_by(id=series_id).first()
    if series is None:
        raise HTTPException(
            status_code=404,
            detail=f'Series {series_id} not found',
        )

    # Delete poster if not the placeholder
    series_poster = Path(series.poster_path)
    if series_poster.name != 'placeholder.jpg' and series_poster.exists():
        ...
        Path(series.poster_path).unlink(missing_ok=True)

    # Delete series and episodes from database
    db.query(models.series.Series).filter_by(id=series_id).delete()
    db.query(models.episode.Episode).filter_by(series_id=series_id).delete()
    db.commit()

    return None


@series_router.get('/search')
def search_series(
        name: Optional[str] = None,
        template_id: Optional[int] = None,
        font_id: Optional[int] = None,
        max_results: Optional[int] = None,
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
    
    # Query for this series, raise 404 if DNE
    series = db.query(models.series.Series).filter_by(id=series_id).first()
    if series is None:
        raise HTTPException(
            status_code=404,
            detail=f'Series {series_id} not found',
        )

    return series


@series_router.patch('/{series_id}')
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
    if getattr(update_series, 'template_id', None) is not None:
        if (db.query(models.template.Template)\
            .filter_by(id=update_series.template_id).first() is None):
            raise HTTPException(
                status_code=404,
                detail=f'Template {update_series.template_id} not found',
            )
    if getattr(update_series, 'font_id', None) is not None:
        if (db.query(models.font.Font)\
            .filter_by(id=update_series.font_id).first() is None):
            raise HTTPException(
                status_code=404,
                detail=f'Font {update_series.font_id} not found',
            )

    # Update each attribute of the object
    changed = False
    for attr, value in update_series.dict().items():
        if value != UNSPECIFIED and getattr(series, attr) != value:
            setattr(series, attr, value)
            changed = True

    # If any values were changed, commit to database
    if changed:
        db.commit()
    
    return series


@series_router.post('/{series_id}/load/{media_server}', status_code=201)
def load_title_cards(
        series_id: int,
        media_server: MediaServer,
        db = Depends(get_database)) -> None:

    # Query for this series, raise 404 if DNE
    series = db.query(models.series.Series).filter_by(id=series_id).first()
    if series is None:
        raise HTTPException(
            status_code=404,
            detail=f'Series {series_id} not found',
        )

    ...


@series_router.post('/{series_id}/reload/{media_server}', status_code=201)
def reload_title_cards(
        series_id: int,
        media_server: MediaServer,
        db = Depends(get_database)) -> None:

    # Query for this series, raise 404 if DNE
    series = db.query(models.series.Series).filter_by(id=series_id).first()
    if series is None:
        raise HTTPException(
            status_code=404,
            detail=f'Series {series_id} not found',
        )

    ...


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

    # Query for this series, raise 404 if DNE
    series = db.query(models.series.Series).filter_by(id=series_id).first()
    if series is None:
        raise HTTPException(
            status_code=404,
            detail=f'Series {series_id} not found',
        )

    return download_series_poster(series, db, preferences, tmdb_interface)


@series_router.post('/{series_id}/poster')
async def set_series_poster(
        series_id: int,
        poster_url: Optional[str] = Form(default=None),
        poster_file: Optional[UploadFile] = None,
        db = Depends(get_database),
        preferences = Depends(get_preferences)) -> str:

    # Query for this series, raise 404 if DNE
    series = db.query(models.series.Series).filter_by(id=series_id).first()
    if series is None:
        raise HTTPException(
            status_code=404,
            detail=f'Series {series_id} not found',
        )

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
    series.poster_path = str(poster_path)
    poster_path.write_bytes(poster_content)

    # Update poster, commit to database
    series.poster_url = f'/assets/posters/{poster_path.name}'
    db.commit()
    
    return series.poster_url