from pathlib import Path
from requests import get
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Response, UploadFile

from modules.Debug import log
from modules.SeriesInfo import SeriesInfo

from app.dependencies import (
    get_database, get_preferences, get_emby_interface,
    get_imagemagick_interface, get_jellyfin_interface, get_plex_interface,
    get_sonarr_interface, get_tmdb_interface
)
import app.models as models
from app.routers.episodes import get_episode
from app.routers.series import get_series
from app.routers.templates import get_template
from app.schemas.base import UNSPECIFIED
from app.schemas.episode import Episode, NewEpisode, UpdateEpisode
from modules.TieredSettings import TieredSettings
from modules.WebInterface import WebInterface


def download_all_source_images() -> None:
    """
    Schedule-able function to attempt to download all source images for
    all monitored Series and Episodes in the Database.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get all Series
            for series in db.query(models.series.Series).all():
                # Skip if Series is unmonitored
                if not series.monitored:
                    log.debug(f'{series.log_str} is not monitored, skipping')
                    continue

                # Get all of this Series' Episodes
                all_episodes = db.query(models.episode.Episode)\
                    .filter_by(series_id=series.id)
                for episode in all_episodes:
                    # Download source for this image
                    try:
                        _download_episode_source_image(
                            db, get_preferences(), get_emby_interface(),
                            get_jellyfin_interface(), get_plex_interface(),
                            get_tmdb_interface(), series, episode
                        )
                    except HTTPException as e:
                        log.warning(f'{series.log_str} {episode.log_str} Skipping source selection')
                        continue
    except Exception as e:
        log.exception(f'Failed to download source images', e)


def download_all_series_logos():
    """
    Schedule-able function to download all Logos for all monitored
    Series in the Database.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get all Series
            all_series = db.query(models.series.Series).all()
            for series in all_series:
                # If Series is unmonitored, skip
                if not series.monitored:
                    log.debug(f'{series.log_str} is not monitored, skipping')
                    continue

                try:
                    _download_series_logo(
                        db, get_preferences(), get_emby_interface(),
                        get_imagemagick_interface(), get_jellyfin_interface(),
                        get_tmdb_interface(), series,
                    )
                except HTTPException as e:
                    log.warning(f'{series.log_str} Skipping logo selection')
                    continue
    except Exception as e:
        log.exception(f'Failed to download series logos', e)


source_router = APIRouter(
    prefix='/sources',
    tags=['Source Images'],
)


def _download_episode_source_image(
        db, preferences, emby_interface, jellyfin_interface, plex_interface,
        tmdb_interface, series, episode) -> Optional[str]:
    """

    """

    # If source already exists, return path to that
    source_file = episode.get_source_file(
        preferences.source_directory, series.path_safe_name
    )
    if source_file.exists():
        log.debug(f'{series.log_str} {episode.log_str} Source image already exists')
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
    TieredSettings(
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
                log.warning(f'{series.log_str} Has no Plex library')
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
            log.warning(f'{series.log_str} {episode.log_str} Cannot source images from {image_source}')
            continue

        # If no source image was returned, increment attempts counter
        if source_image is None:
            episode.image_source_attempts[image_source] += 1
            continue

        # Source image is valid, download - error if download fails
        if WebInterface.download_image(source_image, source_file):
            log.debug(f'{series.log_str} {episode.log_str} Downloaded {source_file.resolve()} from {image_source}')
            return f'/source/{series.path_safe_name}/{source_file.name}'
        else:
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download source image'
            )

    # No image source returned a valid image, return None
    return None


def _download_series_logo(
        db: 'Database',
        preferences: 'Preferences',
        emby_interface: 'EmbyInterface',
        imagemagick_interface: 'ImageMagickInterface',
        jellyfin_interface: 'JellyfinInterface',
        tmdb_interface: 'TMDbInterface',
        series: 'Series',):

    # Get the series logo, return if already exists
    logo_file = series.get_logo_file(preferences.source_directory)
    if logo_file.exists():
        log.debug(f'{series.log_str} Logo exists')
        return f'/source/{series.path_safe_name}/logo.png'

    # Get template and template dictionary
    series_template = get_template(db, series.template_id, raise_exc=True)
    series_template_dict = {}
    if series_template is not None:
        series_template_dict = series_template.__dict__

    # Resolve all settings
    image_source_settings = {}
    TieredSettings(
        image_source_settings,
        {'image_source_priority': preferences.image_source_priority},
        series_template_dict,
        series.image_source_properties,
    )

    # Go through all image sources    
    for image_source in image_source_settings['image_source_priority']:
        if image_source == 'Emby' and emby_interface:
            logo = emby_interface.get_series_logo(series.as_series_info)
        elif image_source == 'Jellyfin' and jellyfin_interface:
            logo = jellyfin_interface.get_series_logo(series.as_series_info)
        elif image_source == 'TMDb' and tmdb_interface:
            # TODO implement blacklist bypassing
            logo = tmdb_interface.get_series_logo(series.as_series_info)
        else:
            continue

        # If no logo was returned, skip
        if logo is None:
            continue

        # If logo is an svg, convert
        if logo.endswith('.svg'):
            # If no ImageMagick, raise 409
            if not imagemagick_interface:
                raise HTTPException(
                    status_code=409,
                    detail=f'Cannot convert SVG logo, no valid ImageMagick interface'
                )

            # Download to temporary location pre-conversion
            success = WebInterface.download_image(
                logo, imagemagick_interface.TEMPORARY_SVG_FILE
            )

            # Downloaded, convert svg -> png
            if success:
                converted_logo = imagemagick_interface.convert_svg_to_png(
                    imagemagick_interface.TEMPORARY_SVG_FILE, logo_file,
                )
                # Logo conversion failed, raise 400
                if converted_logo is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f'SVG logo conversion failed'
                    )
                else:
                    log.debug(f'{series.log_str} Converted SVG logo ({logo}) to PNG')
                    log.info(f'{series.log_str} Downloaded {logo_file.resolve()} from {image_source}')
                    return f'/source/{series.path_safe_name}/{logo_file.name}'
            else:
            # Download failed, raise 400
                raise HTTPException(
                    status_code=400,
                    detail=f'Unable to download logo'
                )

        # Logo is png and valid, download
        if WebInterface.download_image(logo, logo_file):
            log.info(f'{series.log_str} Downloaded {logo_file.resolve()} from {image_source}')
            return f'/source/{series.path_safe_name}/{logo_file.name}'
        # Download failed, raise 400
        else:
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download logo'
            )

    # No logo returned
    return None


@source_router.get('/series/{series_id}')
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
            _download_episode_source_image,
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


@source_router.get('/series/{series_id}/logo')
def download_series_logo(
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

    return _download_series_logo(
        db, preferences, emby_interface, imagemagick_interface,
        jellyfin_interface, tmdb_interface, series,
    )


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

    return _download_episode_source_image(
        db, preferences, emby_interface, jellyfin_interface, plex_interface,
        tmdb_interface, series, episode
    )