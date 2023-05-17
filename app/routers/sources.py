from requests import get
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, UploadFile

from app.database.query import get_episode, get_series, get_template
from app.dependencies import (
    get_database, get_preferences, get_emby_interface,
    get_imagemagick_interface, get_jellyfin_interface, get_plex_interface,
    get_tmdb_interface
)
from app.internal.cards import delete_cards
from app.internal.sources import (
    create_source_image, download_episode_source_image, download_series_logo
)
import app.models as models
from app.schemas.card import SourceImage

from modules.Debug import log
from modules.WebInterface import WebInterface


source_router = APIRouter(
    prefix='/sources',
    tags=['Source Images'],
)


@source_router.post('/series/{series_id}', status_code=200)
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


@source_router.post('/series/{series_id}/backdrop', status_code=200)
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


@source_router.post('/series/{series_id}/logo', status_code=200)
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


@source_router.post('/episode/{episode_id}', status_code=200)
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


@source_router.get('/episode/{episode_id}/browse', status_code=200)
def get_all_tmdb_episode_source_images(
        episode_id: int,
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        tmdb_interface = Depends(get_tmdb_interface)) -> Optional[list[str]]:
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

    # Get the Episode and Series with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)
    series = get_series(db, episode.series_id, raise_exc=True)

    # Get the Templates for these items
    series_template = get_template(db, series.template_id, raise_exc=True)
    episode_template = get_template(db, episode.template_id, raise_exc=True)

    # Determine title matching
    if episode.match_title is not None:
        match_title = episode.match_title
    else:
        match_title = series.match_titles

    # Determine whether to skip localized images
    if (episode_template is not None
        and episode_template.skip_localized_images is not None):
        skip_localized_images = episode_template.skip_localized_images
    elif series.skip_localized_images is not None:
        skip_localized_images = series.skip_localized_images
    elif (series_template is not None
        and series_template.skip_localized_images is not None):
        skip_localized_images = series_template.skip_localized_images
    else:
        skip_localized_images = preferences.tmdb_skip_localized

    # Get all sources
    sources = tmdb_interface.get_all_source_images(
        series.as_series_info,
        episode.as_episode_info,
        match_title=match_title,
        skip_localized_images=skip_localized_images,
    )

    return sources


@source_router.get('/series/{series_id}', status_code=200)
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
    sources = [
        create_source_image(
            preferences, imagemagick_interface, series, episode
        ) for episode in all_episodes
    ]

    return sorted(
        sources,
        key=lambda s: (s['season_number']*1000) + s['episode_number']
    )


@source_router.get('/episode/{episode_id}', status_code=200)
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

    # Get the Episode and Series with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)
    series = get_series(db, episode.series_id, raise_exc=True)

    return create_source_image(
        preferences, imagemagick_interface, series, episode
    )


@source_router.post('/episode/{episode_id}/upload', status_code=201)
async def set_source_image(
        episode_id: int,
        source_url: Optional[str] = Form(default=None),
        source_file: Optional[UploadFile] = None,
        db = Depends(get_database),
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

    # Get Episode and Series with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)
    series = get_series(db, episode.series_id, raise_exc=True)

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
        series.path_safe_name,
    )

    # If file already exists, warn about overwriting
    if source_file.exists():
        log.warning(f'{series.log_str} {episode.log_str} source file "{source_file.resolve()}" exists - replacing')

    # Write new file to the disk
    source_file.write_bytes(content)

    # Delete associated Card and Loaded entry to initiate future reload
    delete_cards(
        db,
        db.query(models.card.Card).filter_by(episode_id=episode_id),
        db.query(models.loaded.Loaded).filter_by(episode_id=episode_id),
    )

    # Return created SourceImage
    return create_source_image(
        preferences, imagemagick_interface, series, episode
    )