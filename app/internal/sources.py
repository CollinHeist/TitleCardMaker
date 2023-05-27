from typing import Optional

from fastapi import HTTPException

from modules.Debug import log

from app.dependencies import (
    get_database, get_preferences, get_emby_interface,
    get_imagemagick_interface, get_jellyfin_interface, get_plex_interface,
    get_tmdb_interface
)
from app.internal.templates import (
    get_effective_series_template, get_effective_templates
)
import app.models as models
from app.schemas.card import SourceImage
from app.schemas.episode import Episode
from app.schemas.preferences import Preferences
from app.schemas.series import Series
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

                # Download source image for all Episodes
                for episode in series.episodes:
                    try:
                        download_episode_source_image(
                            db, get_preferences(), get_emby_interface(),
                            get_jellyfin_interface(), get_plex_interface(),
                            get_tmdb_interface(), episode
                        )
                    except HTTPException as e:
                        log.warning(f'{series.log_str} {episode.log_str} Skipping source selection')
                        continue
    except Exception as e:
        log.exception(f'Failed to download source images', e)

    return None


def download_all_series_logos() -> None:
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
                    download_series_logo(
                        get_preferences(), get_emby_interface(),
                        get_imagemagick_interface(), get_jellyfin_interface(),
                        get_tmdb_interface(), series,
                    )
                except HTTPException as e:
                    log.warning(f'{series.log_str} Skipping logo selection')
                    continue
    except Exception as e:
        log.exception(f'Failed to download series logos', e)

    return None


def download_series_logo(
        preferences: Preferences,
        emby_interface: 'EmbyInterface',
        imagemagick_interface: 'ImageMagickInterface',
        jellyfin_interface: 'JellyfinInterface',
        tmdb_interface: 'TMDbInterface',
        series: Series) -> Optional[str]:
    """
    Download the logo for the given Series.

    Returns:
        The URI to the Series logo. If one cannot be downloaded, None is
        returned instead.

    Raises:
        HTTPException (409) if an SVG image was returned but cannot be
            converted into PNG.
        HTTPException (400) if the logo cannot be downloaded.
    """

    # Get the Series logo, return if already exists
    logo_file = series.get_logo_file(preferences.source_directory)
    if logo_file.exists():
        log.debug(f'{series.log_str} Logo exists')
        return f'/source/{series.path_safe_name}/logo.png'

    # Get Template and Template dictionary
    series_template_dict = get_effective_series_template(series, as_dict=True)

    # Resolve ISP setting
    image_source_priority = TieredSettings.resolve_singular_setting(
        preferences.image_source_priority,
        series_template_dict.get('image_source_priority', None),
        series.image_source_properties.get('image_source_priority', None),
    )

    # Go through all image sources    
    for image_source in image_source_priority:
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


def download_episode_source_image(
        db: 'Database',
        preferences: Preferences,
        emby_interface: Optional['EmbyInterface'],
        jellyfin_interface: Optional['JellyfinInterface'],
        plex_interface: Optional['PlexInterface'],
        tmdb_interface: Optional['TMDbInterface'],
        episode: Episode,
        raise_exc: bool = False) -> Optional[str]:
    """
    Download the source image for the given Episode.

    Returns:
        The URI to the Episode source image. If one cannot be
        downloaded, None is returned instead.

    Raises:
        HTTPException (400) if the image cannot be downloaded.
    """

    # If source already exists, return path to that
    series = episode.series
    source_file = episode.get_source_file(
        preferences.source_directory, series.path_safe_name
    )
    if source_file.exists():
        log.debug(f'{series.log_str} {episode.log_str} Source image already exists')
        return f'/source/{series.path_safe_name}/{source_file.name}'

    # Get effective Templates
    series_template, episode_template = get_effective_templates(series, episode)

    # Get source image settings
    skip_localized_images = TieredSettings.resolve_singular_setting(
        preferences.tmdb_skip_localized,
        getattr(series_template, 'skip_localized_images', None),
        series.skip_localized_images,
        getattr(episode_template, 'skip_localized_images', None),
    )

    # Go through all image sources    
    for image_source in preferences.image_source_priority:
        if image_source == 'Emby' and emby_interface:
            source_image = emby_interface.get_source_image(
                episode.as_episode_info, raise_exc=raise_exc,
            )
        elif image_source == 'Jellyfin' and jellyfin_interface:
            source_image = jellyfin_interface.get_source_image(
                episode.as_episode_info, raise_exc=raise_exc,
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
                raise_exc=raise_exc,
            )
        elif image_source == 'TMDb' and tmdb_interface:
            # TODO implement blacklist bypassing
            source_image = tmdb_interface.get_source_image(
                series.as_series_info,
                episode.as_episode_info,
                skip_localized_images=skip_localized_images,
                raise_exc=raise_exc,
            )
        else:
            log.warning(f'{series.log_str} {episode.log_str} Cannot source images from {image_source}')
            continue

        # If no source image was returned, increment attempts counter
        if source_image is None:
            episode.image_source_attempts[image_source] += 1
            db.commit()
            continue

        # Source image is valid, download - error if download fails
        if WebInterface.download_image(source_image, source_file):
            log.debug(f'{series.log_str} {episode.log_str} Downloaded {source_file.resolve()} from {image_source}')
            return f'/source/{series.path_safe_name}/{source_file.name}'
        else:
            if raise_exc:
                raise HTTPException(
                    status_code=400,
                    detail=f'Unable to download source image'
                )

    # No image source returned a valid image, return None
    return None


def get_source_image(
        preferences: Preferences,
        imagemagick_interface: Optional['ImageMagickInterface'],
        episode: Episode) -> SourceImage:
    """
    Get the SourceImage details for the given objects.

    Args:
        preferences: Preferences to reference the global source
            directory from.
        imagemagick_interface: ImageMagickInterface to query the image
            dimensions from.
        episode: Episode of the SourceImage.
    """

    # Get Episode source file
    source_file = episode.get_source_file(
        preferences.source_directory,
        episode.series.path_safe_name,
    )

    # All sources have these details
    source = {
        'episode_id': episode.id,
        'season_number': episode.season_number,
        'episode_number': episode.episode_number,
        'source_file_name': source_file.name,
        'source_file': str(source_file.resolve()),
        'source_url': f'/source/{source_file.parent.name}/{source_file.name}',
        'exists': source_file.exists(),
    }

    # If the source file exists, add the filesize and dimensions
    if source_file.exists():
        # Get image dimensions if ImageMagickInterface is provided
        width, height = None, None
        if imagemagick_interface is not None:
            width, height = imagemagick_interface.get_image_dimensions(
                source_file
            )

        source |= {
            'filesize': source_file.stat().st_size,
            'width': width,
            'height': height,
        }

    return source