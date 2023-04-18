from pathlib import Path
from requests import get
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Response, UploadFile

from modules.Debug import log
from modules.SeriesInfo import SeriesInfo

from app.dependencies import get_database, get_preferences, get_emby_interface,\
    get_jellyfin_interface, get_plex_interface, get_sonarr_interface, \
    get_tmdb_interface
import app.models as models
from app.routers.cards import priority_merge_v2
from app.routers.episodes import get_episode
from app.routers.series import get_series
from app.routers.templates import get_template
from app.schemas.base import UNSPECIFIED
from app.schemas.episode import Episode, NewEpisode, UpdateEpisode
from modules.WebInterface import WebInterface


source_router = APIRouter(
    prefix='/sources',
    tags=['Source Images'],
)


def download_source_image(
        db, preferences, emby_interface, jellyfin_interface, plex_interface,
        tmdb_interface, series, episode) -> Optional[str]:
    """

    """

    # If source already exists, return path to that
    source_file = episode.get_source_file(
        preferences.source_directory, series.path_safe_name
    )
    if source_file.exists():
        log.debug(f'Episode[{episode.id}] Source image already exists')
        return f'/source/{series.path_safe_name}/{source_file.name}'

    # Get effective template
    series_template_dict, episode_template_dict = {}, {}
    if episode.template_id is not None:
        episode_template_dict = get_template(
            db, episode.template_id, raise_exc=True
        ).image_source_properties
    elif series.template_id is not None:
        series_template_dict = get_template(
            db, series.template_id, raise_exc=True
        ).image_source_properties

    # Resolve all settings from global -> episode
    image_source_settings = {}
    priority_merge_v2(
        image_source_settings,
        {'image_source_priority': preferences.image_source_priority,
         'skip_localized_images': preferences.tmdb_skip_localized},
        series_template_dict,
        series.image_source_properties,
        episode_template_dict,
    )
    skip_localized_images = image_source_settings['skip_localized_images']

    # Go through all image sources    
    for image_source in image_source_settings['image_source_priority']:
        log.debug(f'Episode[{episode.id}] Sourcing images from {image_source}')
        if image_source == 'Emby' and emby_interface:
            source_image = emby_interface.get_source_image(
                episode.as_episode_info
            )
        elif image_source == 'Jellyfin' and jellyfin_interface:
            source_image = jellyfin_interface.get_source_image(
                episode.as_episode_info
            )
        elif image_source == 'Plex' and plex_interface:
            # Verify series has a library
            if series.plex_library_name is None:
                log.warning(f'Series "{series.name}" has no Plex library')
                continue
            source_image = plex_interface.get_source_image(
                series.plex_library_name,
                series.as_series_info,
                episode.as_episode_info,
            )
        elif image_source == 'TMDb' and tmdb_interface:
            # TODO implement blacklist bypassing w/ force
            source_image = tmdb_interface.get_source_image(
                series.as_series_info,
                episode.as_episode_info,
                skip_localized_images=skip_localized_images
            )
        else:
            log.warning(f'Cannot source images from {image_source}')
            continue

        # If no source image was returned, increment attemps counter
        if source_image is None:
            episode.image_source_attempts[image_source] += 1
            continue

        # Source image is valid, download - error if download fails
        if WebInterface.download_image(source_image, source_file):
            log.debug(f'Episode[{episode.id}] Downloaded {source_file.resolve()} from {image_source}')
        else:
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download source image'
            )

        return f'/source/{series.path_safe_name}/{source_file.name}'

    # No image source returned a valid image, return None
    return None


@source_router.get('/series/{series_id}')
def download_series_source_image(
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
    image_source_priority attrbute.

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
            download_source_image,
            # Arguments
            db, preferences, emby_interface, jellyfin_interface, plex_interface,
            tmdb_interface, series, episode
        )

    return None


@source_router.get('/series/{series_id}/backdrop')
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

    """
    # TODO add ability to download art from a media server
    # Get this series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get backdrop, return if exists
    backdrop_file = series.get_series_backdrop(preferences.source_directory)
    if backdrop_file.exists():
        log.debug(f'Series[{series_id}] Backdrop file exists')
        return f'/source/{series.path_safe_name}/backdrop.jpg'

    # Download new backdrop
    if tmdb_interface:
        backdrop = tmdb_interface.get_series_backdrop(
            series.as_series_info,
            # TODO skip localized images
        )
        if WebInterface.download_image(backdrop, backdrop_file):
            log.debug(f'Series[{series_id}] Downloaded {backdrop_file.resolve()} from TMDb')
            return f'/source/{series.path_safe_name}/backdrop.jpg'
        else:
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download backdrop'
            )

    # No logo returned
    return None


@source_router.get('/episode/{episode_id}')
def download_episode_source_image(
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

    # Get the Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Get the Series for this Episode, raise 404 if DNE
    series = get_series(db, episode.series_id, raise_exc=True)

    return download_source_image(
        db, preferences, emby_interface, jellyfin_interface, plex_interface,
        tmdb_interface, series, episode
    )


@source_router.get('/series/{series_id}/logo')
def download_series_logo(
        series_id: int,
        ignore_blacklist: bool = Query(default=False),
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        tmdb_interface = Depends(get_tmdb_interface)) -> Optional[str]:
    """
    Download a Logo for the given Series. This only queries TMDb.
    Returns URI to the source image resource.

    - series_id: ID of the Series to download a Logo for.
    - ignore_blacklist: Whether to force a download from TMDb, even if
    the logo has been blacklisted.
    """

    # Get series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get logo, return if exists
    logo_file = series.get_logo_file(preferences.source_directory)
    if logo_file.exists():
        log.debug(f'Series[{series_id}] Logo file exists')
        return f'/source/{series.path_safe_name}/logo.png'

    # Download new logo
    if tmdb_interface:
        logo = tmdb_interface.get_series_logo(series.as_series_info)
        if WebInterface.download_image(logo, logo_file):
            log.debug(f'Series[{series_id}] Downloaded {logo_file.resolve()} from TMDb')
            return f'/source/{series.path_safe_name}/logo.png'
        else:
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download logo'
            )

    # No logo returned
    return None