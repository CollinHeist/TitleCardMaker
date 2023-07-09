from requests import get
from typing import Optional

from fastapi import (
    APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, Request,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.database.query import get_episode, get_series
from app.dependencies import *
from app.internal.cards import delete_cards
from app.internal.sources import (
    get_source_image, download_episode_source_image, download_series_logo
)
import app.models as models
from app.schemas.card import SourceImage, TMDbImage

from modules.Debug import log
from modules.WebInterface import WebInterface

source_router = APIRouter(
    prefix='/sources',
    tags=['Source Images'],
)


# TODO implement blacklist bypassing all over?
@source_router.post('/series/{series_id}', status_code=200)
def download_series_source_images(
        background_tasks: BackgroundTasks,
        request: Request,
        series_id: int,
        ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
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

    return None


@source_router.post('/series/{series_id}/backdrop', status_code=200)
def download_series_backdrop(
        series_id: int,
        request: Request,
        ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        # emby_interface = Depends(get_emby_interface),
        # jellyfin_interface = Depends(get_jellyfin_interface),
        # plex_interface = Depends(get_plex_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
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
        else:
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
        ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        imagemagick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
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
        ignore_blacklist: bool = Query(default=False),
        db: Session = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
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
def get_all_tmdb_episode_source_images(
        episode_id: int,
        request: Request,
        db: Session = Depends(get_database),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
    ) -> list[TMDbImage]:
    """
    Get all Source Images on TMDb for the given Episode.

    - episode_id: ID of the Episode to get the Source Images of.
    """

    # If no TMDb connection, raise 409
    if tmdb_interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'No connection to TMDb'
        )

    # Get the Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Determine title matching
    if episode.match_title is not None:
        match_title = episode.match_title
    else:
        match_title = episode.series.match_titles

    # Get all source images
    source_images = tmdb_interface.get_all_source_images(
        episode.series.as_series_info,
        episode.as_episode_info,
        match_title=match_title,
        bypass_blacklist=True,
        log=request.state.log,
    )
    return [] if source_images is None else source_images


@source_router.get('/series/{series_id}', status_code=200)
def get_existing_series_source_images(
        series_id: int,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        imagemagick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface)
    ) -> list[SourceImage]:
    """
    Get the SourceImage details for the given Series.

    - series_id: ID of the Series to get the details of.
    """

    # Get all Episodes for this Series
    all_episodes = db.query(models.episode.Episode)\
        .filter_by(series_id=series_id)

    # Get all source files
    sources = [
        get_source_image(preferences, imagemagick_interface, episode)
        for episode in all_episodes
    ]

    return sorted(
        sources,
        key=lambda s: (s['season_number']*1000) + s['episode_number']
    )


@source_router.get('/episode/{episode_id}', status_code=200)
def get_existing_episode_source_images(
        episode_id: int,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        imagemagick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface)
    ) -> SourceImage:
    """
    Get the SourceImage details for the given Episode.

    - episode_id: ID of the Episode to get the details of.
    """

    # Get the Episode and Series with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    return get_source_image(preferences, imagemagick_interface, episode)


@source_router.post('/episode/{episode_id}/upload', status_code=201)
async def set_source_image(
        episode_id: int,
        source_url: Optional[str] = Form(default=None),
        source_file: Optional[UploadFile] = None,
        db: Session = Depends(get_database),
        preferences = Depends(get_preferences),
        imagemagick_interface = Depends(get_imagemagick_interface),
    ) -> SourceImage:
    """
    Set the Source Image for the given Episode. If there is an existing
    Title Card associated with this Episode, it is deleted.

    - episode_id: ID of the Episode to set the Source Image of.
    - source_url: URL to the Source Image to download and utilize.
    - source_file: Source Image file content to utilize.
    """

    # Get Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Get image contents
    uploaded_file = b''
    if source_file is not None:
        uploaded_file = await source_file.read()

    # Send error if both a URL and file were provided
    if source_url is not None and len(uploaded_file) > 0:
        raise HTTPException(
            status_code=422,
            detail='Cannot provide multiple sources'
        )

    # Send error if neither were provided
    if source_url is None and len(uploaded_file) == 0:
        raise HTTPException(
            status_code=422,
            detail='URL or file are required',
        )

    # If only URL was required, attempt to download, error if unable
    if source_url is not None:
        try:
            content = get(source_url).content
        except Exception as e:
            log.exception(f'Download failed', e)
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download image - {e}'
            )
    # Use uploaded file if provided
    else:
        content = uploaded_file

    # Get Episode source file
    source_file = episode.get_source_file(
        preferences.source_directory,
        episode.series.path_safe_name,
        'unique',
    )

    # If file already exists, warn about overwriting
    if source_file.exists():
        log.warning(f'{episode.series.log_str} {episode.log_str} source file '
                    f'"{source_file.resolve()}" exists - replacing')

    # Write new file to the disk
    source_file.write_bytes(content)

    # Delete associated Card and Loaded entry to initiate future reload
    delete_cards(
        db,
        db.query(models.card.Card).filter_by(episode_id=episode_id),
        db.query(models.loaded.Loaded).filter_by(episode_id=episode_id),
    )

    # Return created SourceImage
    return get_source_image(preferences, imagemagick_interface, episode)