from typing import Optional

from fastapi import (
    APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request,
    UploadFile,
)
from fastapi_pagination.ext.sqlalchemy import paginate
from PIL import Image, ImageOps
from requests import get
from sqlalchemy.orm import Session

from app.database.query import get_episode, get_series
from app.database.session import Page
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.auth import get_current_user
from app.internal.cards import delete_cards
from app.internal.sources import (
    get_source_image, download_episode_source_image, download_series_logo,
    process_svg_logo, resolve_source_settings
)
from app import models
from app.schemas.card import SourceImage, ExternalSourceImage

from modules.WebInterface import WebInterface


source_router = APIRouter(
    prefix='/sources',
    tags=['Source Images'],
    dependencies=[Depends(get_current_user)],
)


# TODO implement blacklist bypassing all over?
@source_router.post('/series/{series_id}', status_code=200)
def download_series_source_images(
        background_tasks: BackgroundTasks,
        request: Request,
        series_id: int,
        # ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
    ) -> None:
    """
    Download a Source image for all Episodes in the given Series. This
    uses the most relevant image source indicated by the appropriate
    image source priority attrbute.

    - series_id: ID of the Series whose Episodes to download Source
    images for.
    - ignore_blacklist: Whether to force a download from TMDb, even if
    the associated Episode has been internally blacklisted.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Add task to download source image for each Episode
    for episode in series.episodes:
        background_tasks.add_task(
            # Function
            download_episode_source_image,
            # Arguments
            db, preferences, emby_interface, jellyfin_interface, plex_interface,
            tmdb_interface, episode, raise_exc=False, log=request.state.log,
        )


@source_router.post('/series/{series_id}/backdrop', status_code=200)
def download_series_backdrop(
        series_id: int,
        request: Request,
        # ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        # emby_interface = Depends(get_emby_interface),
        # jellyfin_interface = Depends(get_jellyfin_interface),
        # plex_interface = Depends(get_plex_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
    ) -> Optional[str]:
    """
    Download a backdrop (art image) for the given Series. This only uses
    TMDb.

    - series_id: ID of the Series to download a backdrop for.
    - ignore_blacklist: Whether to force a download from TMDb, even if
    the associated Series backdrop has been internally blacklisted.
    """
    # TODO add ability to download art from a media server
    # Get contextual logger
    log = request.state.log

    # Get this Series, raise 404 if DNE
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
        if WebInterface.download_image(backdrop, backdrop_file, log=log):
            log.debug(f'{series.log_str} Downloaded {backdrop_file.resolve()} from TMDb')
            return f'/source/{series.path_safe_name}/backdrop.jpg'

        raise HTTPException(
            status_code=400,
            detail=f'Unable to download backdrop'
        )

    # No backdrop returned
    return None


@source_router.post('/series/{series_id}/logo', status_code=200)
def download_series_logo_(
        series_id: int,
        request: Request,
        # ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        imagemagick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
    ) -> Optional[str]:
    """
    Download a logo for the given Series. This uses the most relevant
    image source indicated by the appropriate image source priority
    attrbute.

    - series_id: ID of the Series to download a logo for.
    - ignore_blacklist: Whether to force a download from TMDb, even if
    the associated Series logo has been internally blacklisted.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return download_series_logo(
        preferences, emby_interface, imagemagick_interface,
        jellyfin_interface, tmdb_interface, series, log=request.state.log,
    )


@source_router.post('/episode/{episode_id}', status_code=200)
def download_episode_source_image_(
        episode_id: int,
        request: Request,
        # ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
    ) -> Optional[str]:
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

    return download_episode_source_image(
        db, preferences, emby_interface, jellyfin_interface, plex_interface,
        tmdb_interface, episode, raise_exc=True, log=request.state.log,
    )


@source_router.get('/episode/{episode_id}/browse', status_code=200)
def get_all_episode_source_images(
        request: Request,
        episode_id: int,
        db: Session = Depends(get_database),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
    ) -> list[ExternalSourceImage]:
    """
    Get all Source Images on TMDb for the given Episode.

    - episode_id: ID of the Episode to get the Source Images of.
    """

    # Get the Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # If no TMDb connection, raise 409
    if tmdb_interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'No connection to TMDb'
        )

    # Determine title matching
    if episode.match_title is not None:
        match_title = episode.match_title
    else:
        match_title = episode.series.match_titles

    # Get all Source Images from TMDb
    tmdb_images = tmdb_interface.get_all_source_images(
        episode.series.as_series_info,
        episode.as_episode_info,
        match_title=match_title,
        bypass_blacklist=True,
        log=request.state.log,
    ) or []

    # Get Source Image from Plex if possible
    plex_images = []
    if plex_interface and episode.series.plex_library_name:
        plex_image_url = plex_interface.get_source_image(
            episode.series.plex_library_name,
            episode.series.as_series_info,
            episode.as_episode_info,
            proxy_url=True,
            log=log,
        )
        if plex_image_url:
            plex_images = [{'url': plex_image_url}]

    return tmdb_images + plex_images


@source_router.get('/series/{series_id}/logo/browse', status_code=200)
def get_all_series_logos_on_tmdb(
        request: Request,
        series_id: int,
        db: Session = Depends(get_database),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
    ) -> list[ExternalSourceImage]:
    """
    Get a list of all the logos available for the specified Series on
    TMDb.

    - series_id: ID of the Series whose logos are being requested.
    """

    # If no TMDb connection, raise 409
    if tmdb_interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'No connection to TMDb'
        )

    # Get the Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get all logos
    logos = tmdb_interface.get_all_logos(
        series.as_series_info,
        bypass_blacklist=True,
        log=request.state.log,
    )
    return [] if logos is None else logos


@source_router.get('/series/{series_id}/backdrop/browse', status_code=200)
def get_all_series_backdrops_on_tmdb(
        request: Request,
        series_id: int,
        db: Session = Depends(get_database),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
    ) -> list[ExternalSourceImage]:
    """
    Get a list of all the backdrops available for the specified Series
    on TMDb.

    - series_id: ID of the Series whose backdrops are being requested.
    """

    # Get the Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # If no TMDb connection, raise 409
    if tmdb_interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'No connection to TMDb'
        )

    # Get all backdrops
    return tmdb_interface.get_all_backdrops(
        series.as_series_info,
        bypass_blacklist=True,
        log=request.state.log,
    ) or []


@source_router.get('/series/{series_id}', status_code=200)
def get_existing_series_source_images(
        series_id: int,
        db: Session = Depends(get_database),
        imagemagick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface),
    ) -> Page[SourceImage]:
    """
    Get the SourceImage details for the given Series.

    - series_id: ID of the Series to get the details of.
    """

    return paginate(
        db.query(models.episode.Episode)\
            .filter_by(series_id=series_id)\
            .order_by(models.episode.Episode.season_number,
                      models.episode.Episode.episode_number),
        transformer=lambda episodes: [
            get_source_image(imagemagick_interface, episode)
            for episode in episodes
        ]
    )


@source_router.get('/episode/{episode_id}', status_code=200)
def get_existing_episode_source_images(
        episode_id: int,
        db: Session = Depends(get_database),
        imagemagick_interface: ImageMagickInterface = Depends(get_imagemagick_interface),
    ) -> SourceImage:
    """
    Get the SourceImage details for the given Episode.

    - episode_id: ID of the Episode to get the details of.
    """

    # Get the Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    return get_source_image(imagemagick_interface, episode)


@source_router.post('/episode/{episode_id}/upload', status_code=201)
async def set_episode_source_image(
        request: Request,
        episode_id: int,
        url: Optional[str] = Form(default=None),
        file: Optional[UploadFile] = None,
        db: Session = Depends(get_database),
        imagemagick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface),
    ) -> SourceImage:
    """
    Set the Source Image for the given Episode. If there is an existing
    Title Card associated with this Episode, it is deleted.

    - episode_id: ID of the Episode to set the Source Image of.
    - url: URL to the Source Image to download and utilize.
    - file: Source Image file content to utilize.
    """

    # Get contextual logger
    log = request.state.log

    # Get Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Get image contents
    uploaded_file = b''
    if file is not None:
        uploaded_file = await file.read()

    # Send error if both a URL and file were provided
    if url is not None and len(uploaded_file) > 0:
        raise HTTPException(
            status_code=422,
            detail='Cannot provide multiple sources'
        )

    # Send error if neither were provided
    if url is None and len(uploaded_file) == 0:
        raise HTTPException(
            status_code=422,
            detail='URL or file are required',
        )

    # If only URL was required, attempt to download, error if unable
    if url is not None:
        try:
            content = get(url, timeout=30).content
        except Exception as e:
            log.exception(f'Download failed', e)
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download image - {e}'
            ) from e
    # Use uploaded file if provided
    else:
        content = uploaded_file

    # Get Episode source file
    file = episode.get_source_file('unique')

    # If file already exists, warn about overwriting
    if file.exists():
        log.info(f'{episode.series.log_str} {episode.log_str} source file '
                 f'"{file.resolve()}" exists - replacing')

    # Write new file to the disk
    file.write_bytes(content)

    # Delete associated Card and Loaded entry to initiate future reload
    delete_cards(
        db,
        db.query(models.card.Card).filter_by(episode_id=episode_id),
        db.query(models.loaded.Loaded).filter_by(episode_id=episode_id),
        log=log,
    )

    # Return created SourceImage
    return get_source_image(imagemagick_interface, episode)


@source_router.put('/episode/{episode_id}/mirror', status_code=200)
def mirror_episode_source_image(
        episode_id: int,
        db: Session = Depends(get_database),
        imagemagick_interface: ImageMagickInterface = Depends(get_imagemagick_interface),
    ) -> SourceImage:
    """
    Mirror the Source Image for the given Episode. This flips the
    image horizontally. Any associated Card or Loaded asset is deleted.

    - episode_id: ID of the Episode whose Source Image is being
    mirrored.
    """

    # Get the Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Get the Source Image for this Episode, raise 404 if DNE
    _, source_image = resolve_source_settings(episode)
    if not source_image.exists():
        raise HTTPException(
            status_code=404,
            detail=f'Episode {episode.log_str} has no Source Image'
        )

    # Mirror source, overwriting existing file
    ImageOps.mirror(Image.open(source_image)).save(source_image)

    # Delete existing Card and Loaded entries for this Episode
    delete_cards(
        db,
        db.query(models.card.Card).filter_by(episode_id=episode_id),
        db.query(models.loaded.Loaded).filter_by(episode_id=episode_id),
        log=log,
    )

    return get_source_image(imagemagick_interface, episode)


@source_router.post('/series/{series_id}/logo/upload', status_code=201)
async def set_series_logo(
        request: Request,
        series_id: int,
        url: Optional[str] = Form(default=None),
        file: Optional[UploadFile] = None,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        imagemagick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface),
    ) -> None:
    """
    Set the logo for the given Series. If there is an existing logo
    associated with this Series, it is deleted.

    - series_id: ID of the Series to set the logo of.
    - url: URL to the logo to download and utilize.
    - file: Logo file content to utilize.
    """

    # Get contextual logger
    log = request.state.log

    # Get Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get image contents
    uploaded_file = b''
    if file is not None:
        uploaded_file = await file.read()

    # Send error if both a URL and file were provided
    if url is not None and len(uploaded_file) > 0:
        raise HTTPException(
            status_code=422,
            detail='Cannot provide multiple images'
        )

    # Send error if neither were provided
    if url is None and len(uploaded_file) == 0:
        raise HTTPException(
            status_code=422,
            detail='URL or file are required',
        )

    # Get Series logo file
    file = series.get_logo_file(preferences.source_directory)

    # If file already exists, warn about overwriting
    if file.exists():
        log.info(f'{series.log_str} logo file exists - replacing')

    # If only URL was required, attempt to download, error if unable
    if url is not None:
        # If logo is SVG, handle separately
        if url.endswith('.svg'):
            return process_svg_logo(
                url, series, file, imagemagick_interface, log=log,
            )

        try:
            content = get(url, timeout=30).content
            log.debug(f'Downloaded {len(content)} bytes from {url}')
        except Exception as e:
            log.exception(f'Download failed', e)
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download image - {e}'
            ) from e
    # Use uploaded file if provided
    else:
        content = uploaded_file

    # Write new file to the disk
    file.write_bytes(content)


@source_router.post('/series/{series_id}/backdrop/upload', status_code=201)
async def set_series_backdrop(
        request: Request,
        series_id: int,
        url: Optional[str] = Form(default=None),
        file: Optional[UploadFile] = None,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Set the backdrop for the given Series. If there is an existing
    backdrop associated with this Series, it is deleted.

    - series_id: ID of the Series to set the backdrop of.
    - url: URL to the backdrop to download and utilize.
    - file: Backdrop to utilize.
    """

    # Get contextual logger
    log = request.state.log

    # Get Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get image contents
    uploaded_file = b''
    if file is not None:
        uploaded_file = await file.read()

    # Send error if both a URL and file were provided
    if url is not None and len(uploaded_file) > 0:
        raise HTTPException(
            status_code=422,
            detail='Cannot provide multiple images'
        )

    # Send error if neither were provided
    if url is None and len(uploaded_file) == 0:
        raise HTTPException(
            status_code=422,
            detail='URL or file are required',
        )

    # Get Series backdrop file
    file = series.get_series_backdrop(preferences.source_directory)

    # If file already exists, warn about overwriting
    if file.exists():
        log.info(f'{series.log_str} backdrop file exists - replacing')

    # If only URL was required, attempt to download, error if unable
    if url is not None:
        try:
            content = get(url, timeout=30).content
            log.debug(f'Downloaded {len(content)} bytes from {url}')
        except Exception as e:
            log.exception(f'Download failed', e)
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download image - {e}'
            ) from e
    # Use uploaded file if provided
    else:
        content = uploaded_file

    # Write new file to the disk
    file.write_bytes(content)
