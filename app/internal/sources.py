from logging import Logger
from pathlib import Path
from time import sleep
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.templates import get_effective_templates
from app import models
from app.schemas.card import SourceImage
from app.schemas.episode import Episode
from app.schemas.preferences import Preferences, Style
from app.schemas.series import Series

from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.ImageMagickInterface import ImageMagickInterface
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.TMDbInterface2 import TMDbInterface
from modules.TieredSettings import TieredSettings
from modules.WebInterface import WebInterface


def download_all_source_images(*, log: Logger = log) -> None:
    """
    Schedule-able function to attempt to download all source images for
    all monitored Series and Episodes in the Database.
    """

    try:
        # Get the Database
        with next(get_database()) as db:
            # Get all Series
            failures = 0
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
                            get_tmdb_interface(), episode, log=log,
                        )
                    except HTTPException:
                        log.warning(f'{series.log_str} {episode.log_str} '
                                    f'Skipping source selection')
                        continue
                    except OperationalError:
                        if failures > 10:
                            break
                        failures += 1
                        log.debug(f'Database is busy, sleeping..')
                        sleep(30)
    except Exception as exc:
        log.exception(f'Failed to download source images', exc)


def download_all_series_logos(*, log: Logger = log) -> None:
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
                        get_tmdb_interface(), series, log=log,
                    )
                except HTTPException:
                    log.warning(f'{series.log_str} Skipping logo selection')
                    continue
    except Exception as exc:
        log.exception(f'Failed to download series logos', exc)


def resolve_source_settings(
        preferences: Preferences,
        episode: Episode,
    ) -> tuple[Style, Path]:
    """
    Get the Episode style and source file for the given Episode.

    Args:
        preferences: Preferences whose global style settings to use in
            Style resolution.
        episode: Episode being evaluated.

    Returns:
        Tuple of the effective Style and the Path to the source file for
        the given Episode.
    """

    # Get effective Template for this Series and Episode
    series = episode.series
    series_template, episode_template = get_effective_templates(series, episode)

    # Resolve styles
    watched_style = TieredSettings.resolve_singular_setting(
        preferences.default_watched_style,
        getattr(series_template, 'watched_style', None),
        series.watched_style,
        getattr(series.extras, 'watched_style', None),
        getattr(episode_template, 'watched_style', None),
        episode.watched_style,
    )
    unwatched_style = TieredSettings.resolve_singular_setting(
        preferences.default_unwatched_style,
        getattr(series_template, 'unwatched_style', None),
        series.unwatched_style,
        getattr(series.extras, 'unwatched_style', None),
        getattr(episode_template, 'unwatched_style', None),
        episode.unwatched_style,
    )

    # Styles are the same, Episode watch status does not matter
    if (('art' in watched_style and 'art' in unwatched_style)
        or ('unique' in watched_style and 'unique' in unwatched_style)):
        return watched_style, episode.get_source_file(
            preferences.source_directory, series.path_safe_name, watched_style
        )
    # Episode watch status is unset, use unwatched style
    if episode.watched is None:
        return unwatched_style, episode.get_source_file(
            preferences.source_directory, series.path_safe_name, unwatched_style
        )
    # Episode is watched, use watched style
    if episode.watched:
        return watched_style, episode.get_source_file(
            preferences.source_directory, series.path_safe_name, watched_style
        )

    # Episode is unwatched, use unwatched style
    return unwatched_style, episode.get_source_file(
        preferences.source_directory, series.path_safe_name, unwatched_style
    )


def process_svg_logo(
        url: str,
        series: Series,
        logo_file: Path,
        imagemagick_interface: Optional[ImageMagickInterface],
        *,
        log: Logger = log,
    ) -> str:
    """
    Process the given SVG logo URL, converting it to a PNG file and
    downloading it.

    Args:
        url: URL to the SVG file to download and process.
        series: Series whose logo this is (for logging).
        logo_file: Path to the directory where the logo will be written.
        imagemagick_interface: Interface to use for SVG -> PNG
            conversion.
        log: (Keyword) Logger for all log messages.

    Returns:
        String of the asset path for the processed logo.

    Raises:
        HTTPException (409) if an SVG image was returned but cannot be
            converted into PNG.
        HTTPException (400) if the logo cannot be downloaded.
    """

    # If no ImageMagick, raise 409
    if not imagemagick_interface:
        raise HTTPException(
            status_code=409,
            detail=f'Cannot convert SVG logo, no valid ImageMagick interface'
        )

    # Download to temporary location pre-conversion
    success = WebInterface.download_image(
        url, imagemagick_interface.TEMPORARY_SVG_FILE, log=log,
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

        log.debug(f'{series.log_str} Converted SVG logo to PNG')
        log.info(f'{series.log_str} Downloaded logo')
        return f'/source/{series.path_safe_name}/{logo_file.name}'

    # Download failed, raise 400
    raise HTTPException(
        status_code=400,
        detail=f'Unable to download logo'
    )


def download_series_logo(
        preferences: Preferences,
        emby_interface: Optional[EmbyInterface],
        imagemagick_interface: Optional[ImageMagickInterface],
        jellyfin_interface: Optional[JellyfinInterface],
        tmdb_interface: Optional[TMDbInterface],
        series: Series,
        *,
        log: Logger = log,
    ) -> Optional[str]:
    """
    Download the logo for the given Series.

    Args:
        preferences: Preferences to use for global settings
        *_interface: Interface to query for any logos.
        series: Series whose logo to download.
        log: (Keyword) Logger for all log messages.

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
        return f'/source/{series.path_safe_name}/logo.png'

    # Go through all image sources
    for image_source in preferences.image_source_priority:
        if (image_source == 'Emby'
            and emby_interface is not None
            and series.emby_library_name is not None):
            logo = emby_interface.get_series_logo(
                series.emby_library_name, series.as_series_info, log=log,
            )
        elif (image_source == 'Jellyfin'
            and jellyfin_interface is not None
            and series.jellyfin_library_name is not None):
            logo = jellyfin_interface.get_series_logo(
                series.jellyfin_library_name, series.as_series_info, log=log
            )
        elif image_source == 'TMDb' and tmdb_interface:
            logo = tmdb_interface.get_series_logo(series.as_series_info)
        else:
            continue

        # If no logo was returned, move on to next image source
        if logo is None:
            continue

        # If logo is an svg, convert
        if logo.endswith('.svg'):
            return process_svg_logo(
                logo, series, logo_file, imagemagick_interface, log=log
            )

        # Logo is png and valid, download
        if WebInterface.download_image(logo, logo_file, log=log):
            log.info(f'{series.log_str} Downloaded logo from {image_source}')
            return f'/source/{series.path_safe_name}/{logo_file.name}'

        # Download failed, raise 400
        raise HTTPException(
            status_code=400,
            detail=f'Unable to download logo'
        )

    # No logo returned
    return None


def download_episode_source_image(
        db: Session,
        preferences: Preferences,
        emby_interface: Optional[EmbyInterface],
        jellyfin_interface: Optional[JellyfinInterface],
        plex_interface: Optional[PlexInterface],
        tmdb_interface: Optional[TMDbInterface],
        episode: Episode,
        raise_exc: bool = False,
        *,
        log: Logger = log,
    ) -> Optional[str]:
    """
    Download the source image for the given Episode.

    Args:
        db: Database to update.
        preferences: Preferences to utilize for global settings.
        *_interface: Interface to query for each source image.
        episode: Episode whose source image is being downloaded.
        raise_exc: Whether to raise any HTTPExceptions.
        log: (Keyword) Logger for all log messages.

    Returns:
        The URI to the Episode source image. If one cannot be
        downloaded, None is returned instead.

    Raises:
        HTTPException (400) if the image cannot be downloaded.
    """

    # Determine Episode style and source file
    style, source_file = resolve_source_settings(preferences, episode)

    # If source already exists, return that
    series: Series = episode.series
    if source_file.exists():
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
        # Skip and do not warn if this interface is outright disabled
        if not getattr(preferences, f'use_{image_source.lower()}', False):
            continue

        # Verify Series has a library, skip if not
        library_attribute = f'{image_source.lower()}_library_name'
        if (image_source in ('Emby', 'Jellyfin', 'Plex')
            and getattr(series, library_attribute, None) is None):
            log.warning(f'{series.log_str} Has no {image_source} library')
            continue

        # Skip if sourcing art from a media server
        if (image_source in ('Emby', 'Jellyfin', 'Plex')
            and 'art' in style):
            log.debug(f'Cannot source Art images from {image_source} - skipping')
            continue

        if image_source == 'Emby' and emby_interface:
            source_image = emby_interface.get_source_image(
                series.emby_library_name,
                series.as_series_info,
                episode.as_episode_info,
                log=log,
            )
        elif image_source == 'Jellyfin' and jellyfin_interface:
            source_image = jellyfin_interface.get_source_image(
                series.jellyfin_library_name,
                series.as_series_info,
                episode.as_episode_info,
            )
        elif image_source == 'Plex' and plex_interface:
            source_image = plex_interface.get_source_image(
                series.plex_library_name,
                series.as_series_info,
                episode.as_episode_info,
                log=log,
            )
        elif image_source == 'TMDb' and tmdb_interface:
            # TODO implement blacklist bypassing
            # Get art backdrop
            if 'art' in style:
                source_image = tmdb_interface.get_series_backdrop(
                    series.as_series_info,
                    skip_localized_images=skip_localized_images,
                    raise_exc=raise_exc,
                )
            # Get source image
            else:
                source_image = tmdb_interface.get_source_image(
                    series.as_series_info,
                    episode.as_episode_info,
                    skip_localized_images=skip_localized_images,
                    raise_exc=raise_exc,
                    log=log,
                )
        else:
            log.warning(f'{series.log_str} {episode.log_str} Cannot source '
                        f'images from {image_source}')
            continue

        # If no source image was returned, increment attempts counter
        if source_image is None:
            episode.image_source_attempts[image_source] += 1
            db.commit()
            continue

        # Source image is valid, download - error if download fails
        if WebInterface.download_image(source_image, source_file, log=log):
            log.info(f'{series.log_str} {episode.log_str} Downloaded '
                      f'"{source_file.name}" from {image_source}')
            return f'/source/{series.path_safe_name}/{source_file.name}'

        if raise_exc:
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download source image'
            )

    # No image source returned a valid image, return None
    log.debug(f'{series.log_str} {episode.log_str} No source images found')
    return None


def get_source_image(
        preferences: Preferences,
        imagemagick_interface: Optional[ImageMagickInterface],
        episode: Episode,
    ) -> SourceImage:
    """
    Get the SourceImage details for the given objects.

    Args:
        preferences: Preferences to reference the global source
            directory from.
        imagemagick_interface: ImageMagickInterface to query the image
            dimensions from.
        episode: Episode of the SourceImage.

    Returns:
        Details of the Source Image for the given Episode.
    """

    # Determine Episode (style not used) source file
    _, source_file = resolve_source_settings(preferences, episode)

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
    if source['exists']:
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
