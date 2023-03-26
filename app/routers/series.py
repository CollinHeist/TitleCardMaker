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

@series_router.post('/new')
async def add_new_series(
        name: str,
        year: int,
        template: Optional[str],
        plex_library_name: Optional[str],
        emby_library_name: Optional[str],
        db: Session = Depends(get_database)) -> dict:
    
    pass


@series_router.get('/{series_id}')
async def get_series_config(
        series_id: int,
        db: Session = Depends(get_database)) -> Series:
    
    pass


@series_router.patch('/{series_id}')
async def update_series_config(
        series_id: int,
        # Update args
        db: Session = Depends(get_database)) -> Series:
    
    pass


@series_router.get('/{series_id}/episodes')
async def get_all_episodes(
        series_id: int,
        db: Session = Depends(get_database)) -> list[Episode]:
    
    pass


@series_router.get('/{series_id}/poster')
async def get_series_poster(
        series_id: int,
        db: Session = Depends(get_database)) -> str:
    
    pass


@series_router.post('/{series_id}/poster')
async def set_series_poster(
        series_id: int,
        db: Session = Depends(get_database)) -> str:
    
    pass