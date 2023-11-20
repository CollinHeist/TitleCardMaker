from typing import Optional

from fastapi import (
    APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request,
    UploadFile,
)
from fastapi_pagination.ext.sqlalchemy import paginate
from requests import get
from sqlalchemy.orm import Session

from app.database.query import get_episode, get_series
from app.database.session import Page
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.auth import get_current_user
from app.internal.cards import delete_cards
from app.internal.sources import (
    get_source_image, download_episode_source_images, download_series_logo,
    process_svg_logo, resolve_all_source_settings,
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
            download_episode_source_images,
            # Arguments
            db, episode, raise_exc=False, log=request.state.log,
        )


@source_router.post('/series/{series_id}/backdrop', status_code=200)
def download_series_backdrop(
        series_id: int,
        request: Request,
        # ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        tmdb_interfaces: InterfaceGroup[int, TMDbInterface] = Depends(get_tmdb_interfaces),
    ) -> str:
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
    if tmdb_interfaces:
        for _, interface in tmdb_interfaces:
            backdrop = interface.get_series_backdrop(
                series.as_series_info, raise_exc=True,
            )
            if (backdrop
                and WebInterface.download_image(backdrop,backdrop_file,log=log)):
                log.debug(f'{series.log_str} Downloaded backdrop from TMDb')
                return f'/source/{series.path_safe_name}/backdrop.jpg'

    raise HTTPException(
        status_code=400,
        detail=f'Unable to download backdrop'
    )


@source_router.post('/series/{series_id}/logo', status_code=200)
def download_series_logo_(
        series_id: int,
        request: Request,
        # ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
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

    return download_series_logo(series, log=request.state.log)


@source_router.post('/episode/{episode_id}', status_code=200)
def download_episode_source_images_(
        episode_id: int,
        request: Request,
        # ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
    ) -> list[str]:
    """
    Download the Source Images for the given Episode. This uses the most
    relevant image source indicated by the appropriate
    image_source_priority attrbute. Returns URIs to the source image
    resource.

    - episode_id: ID of the Episode to download a Source image of.
    - ignore_blacklist: Whether to force a download from TMDb, even if
    the Episode has been internally blacklisted.
    """

    # Get the Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    return download_episode_source_images(
        db, episode, raise_exc=True, log=request.state.log,
    )


@source_router.get('/episode/{episode_id}/browse', status_code=200)
def get_all_episode_source_images(
        request: Request,
        episode_id: int,
        db: Session = Depends(get_database),
        tmdb_interface: TMDbInterface = Depends(require_tmdb_interface),
        plex_interfaces: InterfaceGroup[int, PlexInterface] = Depends(get_plex_interfaces),
    ) -> list[ExternalSourceImage]:
    """
    Get all Source Images on TMDb for the given Episode.

    - episode_id: ID of the Episode to get the Source Images of.
    """

    # Get the Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

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

    # Get Source Images from Plex if possible
    plex_images = []
    for library in episode.series.libraries:
        if (plex_interface := plex_interfaces[library['interface_id']]):
            url = plex_interface.get_source_image(
                library['name'],
                episode.series.as_series_info,
                episode.as_episode_info,
                proxy_url=True,
                log=log,
            )
            if url:
                plex_images.append({'url': url})

    return tmdb_images + plex_images


@source_router.get('/series/{series_id}/logo/browse', status_code=200)
def get_all_series_logos_on_tmdb(
        request: Request,
        series_id: int,
        db: Session = Depends(get_database),
        tmdb_interface: TMDbInterface = Depends(require_tmdb_interface),
    ) -> list[ExternalSourceImage]:
    """
    Get a list of all the logos available for the specified Series on
    TMDb.

    - series_id: ID of the Series whose logos are being requested.
    """

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
        tmdb_interface: TMDbInterface = Depends(require_tmdb_interface),
    ) -> list[ExternalSourceImage]:
    """
    Get a list of all the backdrops available for the specified Series
    on TMDb.

    - series_id: ID of the Series whose backdrops are being requested.
    """

    # Get the Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

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
            get_source_image(episode) for episode in episodes
        ]
    )


@source_router.delete('/series/{series_id}')
def delete_series_source_images(
        series_id: int,
        request: Request,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Delete all the Source Images for the given Series.

    - series_id: ID of the Series whose Source Images are being deleted.
    """

    # Get contextual logger
    log = request.state.log

    # Get Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    for episode in series.episodes:
        for _, source_file in resolve_all_source_settings(episode):
            if source_file.exists():
                log.debug(f'Deleting {episode} "{source_file.name}"')
                source_file.unlink(missing_ok=True)

    return None


@source_router.get('/episode/{episode_id}', status_code=200)
def get_existing_episode_source_image(
        episode_id: int,
        db: Session = Depends(get_database),
    ) -> SourceImage:
    """
    Get the Source Image details for the given Episode.

    - episode_id: ID of the Episode to get the details of.
    """

    # Get the Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    return get_source_image(episode)


@source_router.delete('/episode/{episode_id}', status_code=200)
def delete_episode_source_images(
        episode_id: int,
        request: Request,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Delete the Source Image(s) for the given Episode.

    - episode_id: ID of the Episode to whose Source Images are being
    deleted.
    """

    # Get contextual logger
    log = request.state.log

    # Get the Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    for _, source_file in resolve_all_source_settings(episode):
        if source_file.exists():
            log.debug(f'Deleting {episode} "{source_file.name}"')
            source_file.unlink(missing_ok=True)

    return None


@source_router.put('/episode/{episode_id}/upload', status_code=201)
async def set_episode_source_image(
        request: Request,
        episode_id: int,
        url: Optional[str] = Form(default=None),
        file: Optional[UploadFile] = None,
        db: Session = Depends(get_database),
    ) -> SourceImage:
    """
    Set the Source Image for the given Episode. If there is an existing
    Title Card associated with this Episode, it is deleted. This always
    replaces the unique image for the Episode, not the art image.

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
    source_file = episode.get_source_file('unique')

    # If file already exists, warn about overwriting
    if source_file.exists():
        log.info(f'{episode.series.log_str} {episode.log_str} source file '
                 f'"{source_file.resolve()}" exists - replacing')

    # Write new file to the disk
    source_file.write_bytes(content)

    # Delete associated Card and Loaded entry to initiate future reload
    delete_cards(
        db,
        db.query(models.card.Card).filter_by(episode_id=episode_id),
        db.query(models.loaded.Loaded).filter_by(episode_id=episode_id),
        log=log,
    )

    # Return created SourceImage
    return get_source_image(episode)


@source_router.put('/series/{series_id}/logo/upload', status_code=201)
async def set_series_logo(
        request: Request,
        series_id: int,
        url: Optional[str] = Form(default=None),
        file: Optional[UploadFile] = None,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
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
            return process_svg_logo(url, series, file, log=log)

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


@source_router.put('/series/{series_id}/backdrop/upload', status_code=201)
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
