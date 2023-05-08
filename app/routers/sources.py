from pathlib import Path
from requests import get
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile

from modules.Debug import log
from modules.SeriesInfo import SeriesInfo

from app.database.query import get_episode, get_series, get_template
from app.dependencies import (
    get_database, get_preferences, get_emby_interface,
    get_imagemagick_interface, get_jellyfin_interface, get_plex_interface,
    get_sonarr_interface, get_tmdb_interface
)
from app.internal.sources import (
    download_episode_source_image, download_series_logo
)
import app.models as models
from app.schemas.base import UNSPECIFIED
from app.schemas.card import SourceImage
from modules.WebInterface import WebInterface


source_router = APIRouter(
    prefix='/sources',
    tags=['Source Images'],
)


@source_router.post('/series/{series_id}')
def download_series_source_images(
        background_tasks: BackgroundTasks,
        series_id: int,
        ignore_blacklist: bool = Query(default=False),
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface),
        tmdb_interface = Depends(get_tmdb_interface)) -> None:
    """
    Download a Source image for all Episodes in the given Series. This
    uses the most relevant image source indicated by the appropriate
    image source priority attrbute.

    - series_id: ID of the Series whose Episodes to download Source
    images for.
    - ignore_blacklist: Whether to force a download from TMDb, even if
    the associated Episode has been internally blacklisted. 
    """

    # Get this series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get all episodes for this series
    all_episodes = db.query(models.episode.Episode)\
        .filter_by(series_id=series_id).all()

    # Add task to download source image for each episode
    for episode in all_episodes:
        background_tasks.add_task(
            # Function
            download_episode_source_image,
            # Arguments
            db, preferences, emby_interface, jellyfin_interface, plex_interface,
            tmdb_interface, series, episode
        )

    return None


@source_router.post('/series/{series_id}/backdrop')
def download_series_backdrop(
        series_id: int,
        ignore_blacklist: bool = Query(default=False),
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        # emby_interface = Depends(get_emby_interface),
        # jellyfin_interface = Depends(get_jellyfin_interface),
        # plex_interface = Depends(get_plex_interface),
        tmdb_interface = Depends(get_tmdb_interface)) -> Optional[str]:
    """
    Download a backdrop (art image) for the given Series. This only uses
    TMDb.

    - series_id: ID of the Series to download a backdrop for.
    - ignore_blacklist: Whether to force a download from TMDb, even if
    the associated Series backdrop has been internally blacklisted.
    """
    # TODO add ability to download art from a media server
    # Get this series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get backdrop, return if exists
    backdrop_file = series.get_series_backdrop(preferences.source_directory)
    if backdrop_file.exists():
        log.debug(f'{series.log_str} Backdrop file exists')
        return f'/source/{series.path_safe_name}/backdrop.jpg'

    # Download new backdrop
    if tmdb_interface:
        backdrop = tmdb_interface.get_series_backdrop(
            series.as_series_info,
            # TODO skip localized images
        )
        if WebInterface.download_image(backdrop, backdrop_file):
            log.debug(f'{series.log_str} Downloaded {backdrop_file.resolve()} from TMDb')
            return f'/source/{series.path_safe_name}/backdrop.jpg'
        else:
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download backdrop'
            )

    # No backdrop returned
    return None


@source_router.post('/series/{series_id}/logo')
def download_series_logo_(
        series_id: int,
        ignore_blacklist: bool = Query(default=False),
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface = Depends(get_emby_interface),
        imagemagick_interface = Depends(get_imagemagick_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        tmdb_interface = Depends(get_tmdb_interface)) -> Optional[str]:
    """
    Download a logo for the given Series. This uses the most relevant
    image source indicated by the appropriate image source priority
    attrbute.

    - series_id: ID of the Series to download a logo for.
    - ignore_blacklist: Whether to force a download from TMDb, even if
    the associated Series logo has been internally blacklisted.
    """

    # Get this series and associated Template, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return download_series_logo(
        db, preferences, emby_interface, imagemagick_interface,
        jellyfin_interface, tmdb_interface, series,
    )


@source_router.post('/episode/{episode_id}')
def download_episode_source_image_(
        episode_id: int,
        ignore_blacklist: bool = Query(default=False),
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface),
        tmdb_interface = Depends(get_tmdb_interface)) -> Optional[str]:
    """
    Download a Source image for the given Episode. This uses the most
    relevant image source indicated by the appropriate
    image_source_priority attrbute. Returns URI to the source image
    resource.

    - episode_id: ID of the Episode to download a Source image of.
    - ignore_blacklist: Whether to force a download from TMDb, even if
    the Episode has been internally blacklisted. 
    """

    # Get the Episode and Series with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)
    series = get_series(db, episode.series_id, raise_exc=True)

    return download_episode_source_image(
        db, preferences, emby_interface, jellyfin_interface, plex_interface,
        tmdb_interface, series, episode
    )


@source_router.get('/series/{series_id}')
def get_existing_series_source_images(
        series_id: int,
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        imagemagick_interface = Depends(get_imagemagick_interface)
        ) -> list[SourceImage]:
    """
    Get the SourceImage details for the given Series.

    - series_id: ID of the Series to get the details of.
    """

    # Get the Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)
    all_episodes = db.query(models.episode.Episode)\
        .filter_by(series_id=series_id)

    # Get all source files
    sources = []
    for episode in all_episodes:
        # Get this Episode's source file
        source_file = episode.get_source_file(
            preferences.source_directory, series.path_safe_name,
        )

        # All sources have these details
        source = {
            'season_number': episode.season_number,
            'episode_number': episode.episode_number,
            'source_file': str(source_file.resolve()),
            'source_url': f'/source/{source_file.parent}/{source_file.name}',
            'exists': source_file.exists(),
        }

        # If the source file exists, add the filesize and dimensions
        if source_file.exists():
            w, h = imagemagick_interface.get_image_dimensions(source_file)
            source |= {
                'filesize': source_file.stat().st_size,
                'width': w,
                'height': h,
            }
        sources.append(source)

    return sorted(
        sources,
        key=lambda s: (s['season_number']*1000) + s['episode_number']
    )


@source_router.get('/episode/{episode_id}')
def get_existing_episode_source_images(
        episode_id: int,
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        imagemagick_interface = Depends(get_imagemagick_interface)
        ) -> SourceImage:
    """
    Get the SourceImage details for the given Episode.

    - episode_id: ID of the Episode to get the details of.
    """

    # Get the Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Get this Episode's source file
    source_file = episode.get_source_file(
        preferences.source_directory, series.path_safe_name,
    )

    # All sources have these details
    source = {
        'season_number': episode.season_number,
        'episode_number': episode.episode_number,
        'source_file': str(source_file.resolve()),
        'source_url': f'/source/{source_file.parent}/{source_file.name}',
        'exists': source_file.exists(),
    }

    # If the source file exists, add the filesize and dimensions
    if source_file.exists():
        width, height = imagemagick_interface.get_image_dimensions(source_file)
        source |= {
            'filesize': source_file.stat().st_size,
            'width': width,
            'height': height,
        }
        
    return source