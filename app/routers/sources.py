from base64 import b64encode, b64decode
from logging import Logger
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi_pagination.ext.sqlalchemy import paginate
from PIL import Image, ImageOps
from requests import get
from sqlalchemy.orm import Session

from app.database.query import get_connection, get_episode, get_series
from app.database.session import Page
from app.dependencies import *
from app.internal.auth import get_current_user
from app.internal.cards import delete_cards
from app.internal.sources import (
    get_source_image,
    download_episode_source_images,
    download_series_logo,
    process_svg_logo,
    resolve_all_source_settings,
    resolve_source_settings,
)
from app import models
from app.models.preferences import Preferences
from app.schemas.card import SourceImage, ExternalSourceImage
from modules.InterfaceGroup import InterfaceGroup
from modules.WebInterface import WebInterface


source_router = APIRouter(
    prefix='/sources',
    tags=['Source Images'],
    dependencies=[Depends(get_current_user)],
)


@source_router.post('/series/{series_id}')
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

    for episode in get_series(db, series_id, raise_exc=True).episodes:
        background_tasks.add_task(
            # Function
            download_episode_source_images,
            # Arguments
            db, episode, raise_exc=False, log=request.state.log,
        )


@source_router.post('/series/{series_id}/backdrop', deprecated=True)
def download_series_backdrop_deprecated(
        series_id: int,
        request: Request,
        # ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
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
    log: Logger = request.state.log

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get backdrop, return if exists
    if (backdrop_file := series.get_series_backdrop()).exists():
        log.debug(f'{series} Backdrop file exists')
        return f'/source/{series.path_safe_name}/backdrop.jpg'

    # Download new backdrop
    if tmdb_interfaces:
        for _, interface in tmdb_interfaces:
            backdrop = interface.get_series_backdrop(
                series.as_series_info, raise_exc=True,
            )
            if (backdrop
                and WebInterface.download_image(backdrop,backdrop_file,log=log)):
                log.debug(f'{series} Downloaded backdrop from TMDb')
                return f'/source/{series.path_safe_name}/backdrop.jpg'

    raise HTTPException(
        status_code=400,
        detail=f'Unable to download backdrop'
    )


@source_router.post('/series/{series_id}/backdrop/tmdb')
def download_series_backdrop_from_tmdb(
        series_id: int,
        request: Request,
        # ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
        tmdb_interfaces: InterfaceGroup[int, TMDbInterface] = Depends(get_tmdb_interfaces),
    ) -> str:
    """
    Download a backdrop (art image) for the given Series from TMDb.

    - series_id: ID of the Series to download a backdrop for.
    - ignore_blacklist: Whether to force a download from TMDb, even if
    the associated Series backdrop has been internally blacklisted.
    """
    # TODO add ability to download art from a media server
    # Get contextual logger
    log: Logger = request.state.log

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get backdrop, return if exists
    if (backdrop_file := series.get_series_backdrop()).exists():
        log.debug(f'{series} Backdrop file exists')
        return f'/source/{series.path_safe_name}/backdrop.jpg'

    # Download new backdrop
    if tmdb_interfaces:
        for _, interface in tmdb_interfaces:
            backdrop = interface.get_series_backdrop(
                series.as_series_info, raise_exc=True,
            )
            if (backdrop
                and WebInterface.download_image(backdrop,backdrop_file,log=log)):
                log.debug(f'{series} Downloaded backdrop from TMDb')
                return f'/source/{series.path_safe_name}/backdrop.jpg'

    raise HTTPException(
        status_code=400,
        detail=f'Unable to download backdrop'
    )


@source_router.post('/series/{series_id}/backdrop/tvdb')
def download_series_backdrop_from_tvdb(
        series_id: int,
        request: Request,
        db: Session = Depends(get_database),
        tvdb_interfaces: InterfaceGroup[int, TVDbInterface] = Depends(get_tvdb_interfaces),
    ) -> str:
    """
    Download a backdrop (art image) for the given Series from TVDb.

    - series_id: ID of the Series to download a backdrop for.
    """
    # TODO add ability to download art from a media server
    # Get contextual logger
    log: Logger = request.state.log

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get backdrop, return if exists
    if (backdrop_file := series.get_series_backdrop()).exists():
        log.debug(f'{series} Backdrop file exists')
        return f'/source/{series.path_safe_name}/backdrop.jpg'

    # Download new backdrop
    if tvdb_interfaces:
        for _, interface in tvdb_interfaces:
            backdrop = interface.get_series_backdrop(
                series.as_series_info, raise_exc=True,
            )
            if (backdrop
                and WebInterface.download_image(backdrop,backdrop_file,log=log)):
                log.debug(f'{series} Downloaded backdrop from TVDb')
                return f'/source/{series.path_safe_name}/backdrop.jpg'

    raise HTTPException(
        status_code=400,
        detail=f'Unable to download backdrop'
    )


@source_router.post('/series/{series_id}/logo')
def download_series_logo_(
        series_id: int,
        request: Request,
        db: Session = Depends(get_database),
    ) -> Optional[str]:
    """
    Download a logo for the given Series. This uses the most relevant
    image source indicated by the appropriate image source priority
    attrbute.

    - series_id: ID of the Series to download a logo for.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return download_series_logo(series, log=request.state.log)


@source_router.post('/episode/{episode_id}')
def download_episode_source_images_(
        episode_id: int,
        request: Request,
        db: Session = Depends(get_database),
    ) -> list[str]:
    """
    Download the Source Images for the given Episode. This uses the most
    relevant image source indicated by the global image source priority.
    Returns URIs to the source image resources.

    - episode_id: ID of the Episode to download a Source image of.
    """

    # Get the Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    return download_episode_source_images(
        db, episode, raise_exc=True, log=request.state.log,
    )


@source_router.get('/episode/{episode_id}/browse')
def get_all_episode_source_images(
        request: Request,
        episode_id: int,
        db: Session = Depends(get_database),
        emby_interfaces: InterfaceGroup[int, EmbyInterface] = Depends(get_emby_interfaces),
        jellyfin_interfaces: InterfaceGroup[int, JellyfinInterface] = Depends(get_jellyfin_interfaces),
        plex_interfaces: InterfaceGroup[int, PlexInterface] = Depends(get_plex_interfaces),
        tmdb_interface: TMDbInterface = Depends(require_tmdb_interface),
        tvdb_interface: Optional[TVDbInterface] = Depends(get_first_tvdb_interface),
    ) -> list[ExternalSourceImage]:
    """
    Get all Source Images on all interfaces for the given Episode.

    - episode_id: ID of the Episode to get the Source Images of.
    """

    # Get contextual logger
    log: Logger = request.state.log

    # Get the Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Determine title matching
    if episode.match_title is not None:
        match_title = episode.match_title
    else:
        match_title = episode.series.match_titles

    # Get all Source Images from TMDb and TVDb
    images = []
    try:
        images += tmdb_interface.get_all_source_images(
            episode.series.as_series_info,
            episode.as_episode_info,
            match_title=match_title,
            bypass_blacklist=True,
            log=log,
        )
    except HTTPException:
        pass

    if tvdb_interface:
        tvdb_image = tvdb_interface.get_source_image(
            episode.series.as_series_info,
            episode.as_episode_info,
            log=log,
        )
        if tvdb_image:
            images.append({'url': tvdb_image, 'interface_type': 'TVDb'})

    # Grab raw image bytes from Emby and Jellyfin
    for interface_type, interface_group in (('Emby', emby_interfaces),
                                            ('Jellyfin', jellyfin_interfaces)):
        for library in episode.series.libraries:
            if not (interface := interface_group[library['interface_id']]):
                continue

            image = interface.get_source_image(
                library['name'],
                episode.series.as_series_info,
                episode.as_episode_info,
                log=log,
            )
            if image:
                # Encode image bytes as Base64 string
                image_str = b64encode(image).decode('ascii')
                images.append({
                    'data': f'data:image/jpg;base64,{image_str}',
                    'interface_type': interface_type,
                })
            else:
                log.debug(f'No Source Image available from "{library["name"]}"')

    # Get Source Images from Plex if possible
    for library in episode.series.libraries:
        if not (plex_interface := plex_interfaces[library['interface_id']]):
            continue

        url = plex_interface.get_source_image(
            library['name'],
            episode.series.as_series_info,
            episode.as_episode_info,
            proxy_url=True,
            log=request.state.log,
        )
        if url:
            images.append({'url': url, 'interface_type': 'Plex'})
        else:
            log.debug(f'No Source Image available from "{library["name"]}"')

    return images


@source_router.get('/series/{series_id}/logo/browse')
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

    return tmdb_interface.get_all_logos(
        series.as_series_info,
        bypass_blacklist=True,
        log=request.state.log,
    ) or []


@source_router.get('/series/{series_id}/backdrop/browse')
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


@source_router.get('/series/{series_id}')
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
    log: Logger = request.state.log

    # Get Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    for episode in series.episodes:
        for _, source_file in resolve_all_source_settings(episode):
            if source_file.exists():
                log.debug(f'Deleting {episode} "{source_file.name}"')
                source_file.unlink(missing_ok=True)


@source_router.get('/episode/{episode_id}')
def get_existing_episode_source_image(
        episode_id: int,
        db: Session = Depends(get_database),
    ) -> SourceImage:
    """
    Get the Source Image details for the given Episode.

    - episode_id: ID of the Episode to get the details of.
    """

    return get_source_image(get_episode(db, episode_id, raise_exc=True))


@source_router.delete('/episode/{episode_id}')
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
    log: Logger = request.state.log

    # Get the Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    for _, source_file in resolve_all_source_settings(episode):
        if source_file.exists():
            log.debug(f'Deleting {episode} "{source_file.name}"')
            source_file.unlink(missing_ok=True)

    return None


@source_router.put('/episode/{episode_id}/upload')
async def set_episode_source_image(
        request: Request,
        episode_id: int,
        url: Optional[str] = Form(default=None),
        file: Optional[UploadFile] = None,
        interface_id: Optional[int] = Query(default=None),
        db: Session = Depends(get_database),
        plex_interfaces: InterfaceGroup[int, PlexInterface] = Depends(get_plex_interfaces),
    ) -> SourceImage:
    """
    Set the Source Image for the given Episode. If there is an existing
    Title Card associated with this Episode, it is deleted. This always
    replaces the unique image for the Episode, not the art image.

    - episode_id: ID of the Episode to set the Source Image of.
    - url: URL to the Source Image to download and utilize. This can
    also be a base64 encoded image to decode and write.
    - file: Source Image file content to utilize.
    - interface_id: ID of the interface associated with the proxy URL;
    only required if `url` is a proxied API URL from Plex.
    """

    # Get contextual logger
    log: Logger = request.state.log

    # Get Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Get image contents
    uploaded_file = b''
    if file is not None:
        uploaded_file = await file.read()
    elif url and url.startswith('data:image/jpg;base64,'):
        uploaded_file = b64decode(url.removeprefix('data:image/jpg;base64,'))

    # Send error if both a URL and file were provided
    if (url is not None
        and not url.startswith('data:image/jpg;base64,')
        and len(uploaded_file) > 0):
        raise HTTPException(
            status_code=422,
            detail='Cannot provide multiple sources'
        )

    # Send error if neither were provided
    if not url and not uploaded_file:
        raise HTTPException(
            status_code=422,
            detail='URL or file are required',
        )

    # Get Episode source file
    source_file = episode.get_source_file('unique')

    # If file already exists, warn about overwriting
    if source_file.exists():
        log.info(f'{episode.series} {episode} source file '
                 f'"{source_file.resolve()}" exists - replacing')

    # Either download URL or write content directly
    if uploaded_file:
        source_file.write_bytes(uploaded_file)
        log.debug(f'Wrote {len(uploaded_file)} bytes to {source_file}')
    else:
        # If proxied, de-proxy using associated interface
        if url.startswith('/api/proxy/plex?url='):
            # Use first Plex Connection if no ID provided
            interface_id = interface_id or plex_interfaces.first_interface_id

            # If no interface ID, raise
            if interface_id is None:
                raise HTTPException(
                    status_code=422,
                    detail='Interface ID is required'
                )

            # Get Connection with this ID, raise 404 if DNE
            connection = get_connection(db, interface_id, raise_exc=True)

            # Use server URL, de-proxied URL, and add the token as a param
            url = connection.decrypted_url.removesuffix('/') \
                + url.split('/api/proxy/plex?url=', maxsplit=1)[1] \
                + f'?X-Plex-Token={connection.decrypted_api_key}'

        if not WebInterface.download_image(url, source_file, log=log):
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download image'
            )

    # Delete associated Card and Loaded entry to initiate future reload
    delete_cards(
        db,
        db.query(models.card.Card).filter_by(episode_id=episode_id),
        db.query(models.loaded.Loaded).filter_by(episode_id=episode_id),
        log=log,
    )

    # Return created Source Image
    return get_source_image(episode)


@source_router.put('/episode/{episode_id}/mirror')
def mirror_episode_source_image(
        request: Request,
        episode_id: int,
        db: Session = Depends(get_database),
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
            detail=f'Episode {episode} has no Source Image'
        )

    # Mirror Source and overwrite existing file
    ImageOps.mirror(Image.open(source_image)).save(source_image)

    # Delete existing Card and Loaded entries for this Episode
    delete_cards(
        db,
        db.query(models.card.Card).filter_by(episode_id=episode_id),
        db.query(models.loaded.Loaded).filter_by(episode_id=episode_id),
        log=request.state.log,
    )

    return get_source_image(episode)


@source_router.put('/series/{series_id}/logo/upload')
async def set_series_logo(
        request: Request,
        series_id: int,
        url: Optional[str] = Form(default=None),
        file: Optional[UploadFile] = None,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Set the logo for the given Series. If there is an existing logo
    associated with this Series, it is deleted.

    - series_id: ID of the Series to set the logo of.
    - url: URL to the logo to download and utilize.
    - file: Logo file content to utilize.
    """

    # Get contextual logger
    log: Logger = request.state.log

    # Get Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get image contents
    uploaded_file = b''
    if file is not None:
        uploaded_file = await file.read()

    # Send error if both a URL and file were provided
    if url and uploaded_file:
        raise HTTPException(
            status_code=422,
            detail='Cannot provide multiple images',
        )

    # Send error if neither were provided
    if not url and not uploaded_file:
        raise HTTPException(
            status_code=422,
            detail='URL or file are required',
        )

    # Get Series logo file
    logo_file = series.get_logo_file()

    # If file already exists, warn about overwriting
    if logo_file.exists():
        log.info(f'{series} logo file exists - replacing')

    # If only URL was required, attempt to download, error if unable
    if url is not None:
        # If logo is SVG, handle separately
        if url.endswith('.svg'):
            process_svg_logo(url, series, logo_file, log=log)
            return None

        try:
            content = get(url, timeout=30).content
            log.debug(f'Downloaded {len(content)} bytes from {url}')
        except Exception as exc:
            log.exception('Download failed')
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download image - {exc}'
            ) from exc
    # Use uploaded file if provided
    else:
        content = uploaded_file

    # Write new file to the disk
    logo_file.write_bytes(content)
    return None


@source_router.put('/series/{series_id}/backdrop/upload')
async def set_series_backdrop(
        request: Request,
        series_id: int,
        url: Optional[str] = Form(default=None),
        file: Optional[UploadFile] = None,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Set the backdrop for the given Series. If there is an existing
    backdrop associated with this Series, it is deleted.

    - series_id: ID of the Series to set the backdrop of.
    - url: URL to the backdrop to download and utilize.
    - file: Backdrop to utilize.
    """

    # Get contextual logger
    log: Logger = request.state.log

    # Get Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get image contents
    uploaded_file = b''
    if file is not None:
        uploaded_file = await file.read()

    # Send error if both a URL and file were provided
    if url and uploaded_file:
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
    backdrop_file = series.get_series_backdrop()

    # If file already exists, warn about overwriting
    if backdrop_file.exists():
        log.info(f'{series} backdrop file exists - replacing')

    # If only URL was required, attempt to download, error if unable
    if url is not None:
        try:
            content = get(url, timeout=30).content
            log.debug(f'Downloaded {len(content)} bytes from {url}')
        except Exception as exc:
            log.exception('Download failed')
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download image - {exc}'
            ) from exc
    # Use uploaded file if provided
    else:
        content = uploaded_file

    # Write new file to the disk
    backdrop_file.write_bytes(content)
