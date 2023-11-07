from logging import Logger
from pathlib import Path
from time import sleep
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database.query import get_interface
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.templates import get_effective_templates
from app.models.episode import Episode
from app.models.series import Library, Series
from app.schemas.card import SourceImage
from app.schemas.preferences import Style

from modules.Debug import log
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
            for series in db.query(Series).all():
                # Skip if Series is unmonitored
                if not series.monitored:
                    log.debug(f'{series.log_str} is not monitored, skipping')
                    continue

                # Download source image for all Episodes
                for episode in series.episodes:
                    try:
                        download_episode_source_images(db, episode, log=log)
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
            all_series = db.query(Series).all()
            for series in all_series:
                # If Series is unmonitored, skip
                if not series.monitored:
                    log.debug(f'{series.log_str} is not monitored, skipping')
                    continue

                try:
                    download_series_logo(series, log=log)
                except HTTPException:
                    log.warning(f'{series.log_str} Skipping logo selection')
                    continue
    except Exception as exc:
        log.exception(f'Failed to download series logos', exc)


def resolve_source_settings(
        episode: Episode,
        library: Optional[Library] = None,
    ) -> tuple[Style, Path]:
    """
    Get the Episode style and source file for the given Episode.

    Args:
        episode: Episode being evaluated.

    Returns:
        Tuple of the effective Style and the Path to the source file for
        the given Episode.
    """

    # Get effective Template for this Series and Episode
    series = episode.series
    series_template, episode_template = get_effective_templates(
        series, episode, library,
    )

    # Resolve styles
    preferences = get_preferences()
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
            preferences.source_directory, watched_style
        )

    # Episode is watched, use watched style
    # TODO modify
    if episode.watched:
        return watched_style, episode.get_source_file(
            preferences.source_directory, watched_style
        )

    # Watch status is unset or Episode is unwatched, use unwatched style
    return unwatched_style, episode.get_source_file(
        preferences.source_directory, unwatched_style
    )


def resolve_all_source_settings(episode: Episode) -> list[tuple[Style, Path]]:
    """
    Get all the style and source files for the given Episode. This
    evaluates source settings for all libraries of the parent Series.

    Args:
        episode: Episode being evaluated.

    Returns:
        List of tuples of the effective Style and the Path to the source
        file for the given Episode.
    """

    if episode.series.libraries:
        return [
            resolve_source_settings(episode, library)
            for library in episode.series.libraries
        ]

    return [resolve_source_settings(episode)]


def process_svg_logo(
        url: str,
        series: Series,
        logo_file: Path,
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
        log: Logger for all log messages.

    Returns:
        String of the asset path for the processed logo.

    Raises:
        HTTPException (409): SVG image was returned but cannot be
            converted into PNG.
        HTTPException (400): The logo cannot be downloaded.
    """

    # Download to temporary location pre-conversion
    imagemagick_interface = get_imagemagick_interface()
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
        series: Series,
        *,
        log: Logger = log,
    ) -> Optional[str]:
    """
    Download the logo for the given Series.

    Args:
        series: Series whose logo to download.
        log: Logger for all log messages.

    Returns:
        The URI to the Series logo. If one cannot be downloaded, None is
        returned instead.

    Raises:
        HTTPException (409): An SVG image was returned but cannot be
            converted into PNG.
        HTTPException (400): The logo cannot be downloaded.
    """

    # Get the Series logo, return if already exists
    preferences = get_preferences()
    logo_file = series.get_logo_file(preferences.source_directory)
    if logo_file.exists():
        return f'/source/{series.path_safe_name}/logo.png'

    # Go through all image sources
    logo = None
    for interface_id in preferences.image_source_priority:
        # Skip if there is no interface for this ID
        if not (interface := get_interface(interface_id)):
            continue

        # Skip interfaces which cannot provide logos
        if interface.INTERFACE_TYPE in ('Plex', 'Sonarr'):
            continue

        # Handle TMDb separately
        if interface.INTERFACE_TYPE == 'TMDb':
            logo = interface.get_series_logo(series.as_series_info)

        # Go through each library of this interface
        for _, library in series.get_libraries(interface_id):
            # Stop when a logo has been found
            if logo:
                break

            logo = interface.get_series_logo(
                library, series.as_series_info, log=log
            )

        # If no logo was returned, move on to next image source
        if logo is None:
            continue

        # If logo is an svg, convert
        if isinstance(logo, str) and logo.endswith('.svg'):
            return process_svg_logo(logo, series, logo_file, log=log)

        # Logo is png and valid, download
        if WebInterface.download_image(logo, logo_file, log=log):
            log.info(f'{series.log_str} Downloaded logo from '
                     f'{interface.INTERFACE_TYPE}[{interface_id}]')
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
        episode: Episode,
        library: Optional[Library] = None,
        *,
        raise_exc: bool = False,
        log: Logger = log,
    ) -> list[str]:
    """
    Download the source image for the given Episode.

    Args:
        db: Database to update.
        episode: Episode whose source image is being downloaded.
        raise_exc: Whether to raise any HTTPExceptions.
        log: Logger for all log messages.

    Returns:
        List of URIs to the Episode source images.

    Raises:
        HTTPException (400): The image cannot be downloaded.
    """

    # Determine Episode style and source file
    style, source_file = resolve_source_settings(episode, library)

    # If source already exists, return that
    series: Series = episode.series
    if source_file.exists():
        return f'/source/{series.path_safe_name}/{source_file.name}'

    # Get effective Templates
    series_template, episode_template = get_effective_templates(
        series, episode, library,
    )

    # Get source image settings
    preferences = get_preferences()
    skip_localized_images = TieredSettings.resolve_singular_setting(
        preferences.tmdb_skip_localized,
        getattr(series_template, 'skip_localized_images', None),
        series.skip_localized_images,
        getattr(episode_template, 'skip_localized_images', None),
    )

    # Go through all image sources
    for interface_id in preferences.image_source_priority:
        # Skip if this interface cannot be communicated with
        if not (interface := get_interface(interface_id, raise_exc=raise_exc)):
            continue

        # Skip if sourcing art from a media server
        if (interface.INTERFACE_TYPE in ('Emby', 'Jellyfin', 'Plex')
            and 'art' in style):
            log.debug(f'Cannot source Art images from '
                      f'{interface.INTERFACE_TYPE} - skipping')
            continue

        # Try each library of each media servers
        if interface.INTERFACE_TYPE in ('Emby', 'Jellyfin', 'Plex'):
            for _, library in series.get_libraries(interface_id):
                source_image = interface.get_source_image(
                    library,
                    series.as_series_info,
                    episode.as_episode_info,
                    log=log,
                )
                if source_image:
                    break
        elif interface.INTERFACE_TYPE == 'TMDb':
            # TODO implement blacklist bypassing
            # Get art backdrop
            if 'art' in style:
                source_image = interface.get_series_backdrop(
                    series.as_series_info,
                    skip_localized_images=skip_localized_images,
                    raise_exc=raise_exc,
                )
            # Get source image
            else:
                source_image = interface.get_source_image(
                    series.as_series_info,
                    episode.as_episode_info,
                    skip_localized_images=skip_localized_images,
                    raise_exc=raise_exc,
                    log=log,
                )

        # If no source image was returned, increment attempts counter
        if source_image is None:
            episode.image_source_attempts[interface.INTERFACE_TYPE] += 1
            db.commit()
            continue

        # Source image is valid, download - error if download fails
        if WebInterface.download_image(source_image, source_file, log=log):
            log.info(f'{series.log_str} {episode.log_str} Downloaded '
                     f'"{source_file.name}" from {interface.INTERFACE_TYPE}')
            return f'/source/{series.path_safe_name}/{source_file.name}'

        if raise_exc:
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download source image'
            )

    # No image source returned a valid image, return None
    log.debug(f'{series.log_str} {episode.log_str} No source images found')
    return None


def download_episode_source_images(
        db: Session,
        episode: Episode,
        *,
        raise_exc: bool = False,
        log: Logger = log,
    ) -> list[str]:
    """
    Download all Source Images for the given Episode.

    Args:
        db: Database to update.
        episode: Episode whose Source Images are being downloaded.
        raise_exc: Whether to raise any HTTPExceptions.
        log: Logger for all log messages.

    Returns:
        List of URIs to the Episode source images.

    Raises:
        HTTPException (400): An image cannot be downloaded.
    """

    if episode.series.libraries:
        return [
            download_episode_source_image(
                db, episode, library, raise_exc=raise_exc, log=log
            ) for library in episode.series.libraries
        ]

    return [download_episode_source_image(
        db, episode, None, raise_exc=raise_exc, log=log
    )]


def get_source_image(episode: Episode) -> SourceImage:
    """
    Get the SourceImage details for the given Episode. This only evalutes

    Args:
        episode: Episode of the Source Image.

    Returns:
        Details of the Source Image for the given Episode.
    """

    # Determine Episode (style not used) source file
    _, source_file = resolve_source_settings(episode)

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
        # Get image dimensions
        width, height = get_imagemagick_interface().get_image_dimensions(
            source_file
        )

        source |= {
            'filesize': source_file.stat().st_size,
            'width': width,
            'height': height,
        }

    return source
