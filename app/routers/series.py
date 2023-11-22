from shutil import copy as file_copy
from typing import Literal, Optional, Union

from fastapi import (
    APIRouter, BackgroundTasks, Body, Depends, Form, HTTPException, Query,
    Request, UploadFile
)
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import paginate as paginate_sequence
from requests import get
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.database.session import Page
from app.database.query import get_all_templates, get_font, get_series
from app.internal.episodes import refresh_episode_data
from app.internal.translate import translate_episode
from app import models
from app.internal.cards import (
    create_episode_card, refresh_remote_card_types,
    update_episode_watch_statuses
)
from app.internal.series import (
    add_series, delete_series_and_episodes, download_series_poster,
    load_series_title_cards,
)
from app.internal.sources import download_episode_source_image
from app.internal.auth import get_current_user
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import EpisodeDataSource, MediaServer
from app.schemas.series import NewSeries, SearchResult, Series, UpdateSeries

from modules.EmbyInterface2 import EmbyInterface
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface


series_router = APIRouter(
    prefix='/series',
    tags=['Series'],
    dependencies=[Depends(get_current_user)],
)


OrderBy = Literal[
    'alphabetical', 'reverse-alphabetical',
    'id', 'reverse-id',
    'year', 'reverse-year'
]
@series_router.get('/all', status_code=200)
def get_all_series(
        db: Session = Depends(get_database),
        order_by: OrderBy = 'id',
    ) -> Page[Series]:
    """
    Get all defined Series.

    - order_by: How to order the Series in the returned list.
    """

    # Order by Name > Year
    query = db.query(models.series.Series)
    if order_by == 'alphabetical':
        series = query.order_by(models.series.Series.sort_name)\
            .order_by(models.series.Series.year)
    elif order_by == 'reverse-alphabetical':
        series = query.order_by(models.series.Series.sort_name.desc())\
            .order_by(models.series.Series.year)
    # Order by ID
    elif order_by == 'id':
        series = query.order_by(models.series.Series.id)
    elif order_by == 'reverse-id':
        series = query.order_by(models.series.Series.id.desc())
    # Order by Year > Name
    elif order_by == 'year':
        series = query.order_by(models.series.Series.year)\
            .order_by(func.lower(models.series.Series.sort_name))
    elif order_by == 'reverse-year':
        series = query.order_by(models.series.Series.year.desc())\
            .order_by(func.lower(models.series.Series.sort_name))

    # Return paginated results
    return paginate(series)


@series_router.get('/{series_id}/previous', status_code=200)
def get_previous_series(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> Optional[Series]:
    """
    Get the previous Series (sorted alphabetically, year, then by ID).

    - series_id: ID of the reference Series.
    """

    # Get the reference Series
    series = get_series(db, series_id, raise_exc=True)

    # pylint: disable=no-value-for-parameter,no-member
    return db.query(models.series.Series)\
        .filter(
            models.series.Series.id != series_id,
            or_(models.series.Series.comes_before(series.sort_name),
                and_(models.series.Series.sort_name == series.sort_name,
                     models.series.Series.year < series.year)))\
        .order_by(models.series.Series.sort_name.desc(),
                  models.series.Series.year.desc(),
                  models.series.Series.id.desc())\
        .first()


@series_router.get('/{series_id}/next', status_code=200)
def get_next_series(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> Optional[Series]:
    """
    Get the next Series (sorted alphabetically, year, then by ID).

    - series_id: ID of the reference Series.
    """

    # Get the reference Series
    series = get_series(db, series_id, raise_exc=True)

    # pylint: disable=no-value-for-parameter,no-member
    return db.query(models.series.Series)\
        .filter(
            models.series.Series.id != series_id,
            or_(models.series.Series.comes_after(series.sort_name),
                and_(models.series.Series.sort_name == series.sort_name,
                     models.series.Series.year > series.year)))\
        .order_by(models.series.Series.sort_name,
                  models.series.Series.year,
                  models.series.Series.id)\
        .first()


@series_router.post('/new', status_code=201)
def add_new_series(
        background_tasks: BackgroundTasks,
        request: Request,
        new_series: NewSeries = Body(...),
        db: Session = Depends(get_database),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        imagemagick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        sonarr_interface: Optional[SonarrInterface] = Depends(get_sonarr_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
    ) -> Series:
    """
    Create a new Series. This also creates background tasks to set the
    database ID's of the series, as well as find and download a poster.

    - new_series: Series definition to create.
    """

    return add_series(
        new_series, background_tasks, db, emby_interface,
        imagemagick_interface, jellyfin_interface, plex_interface,
        sonarr_interface, tmdb_interface, log=request.state.log,
    )


@series_router.delete('/{series_id}', status_code=204)
def delete_series(
        series_id: int,
        request: Request,
        db: Session = Depends(get_database)
    ) -> None:
    """
    Delete the Series with the given ID. This also deletes the poster.

    - series_id: ID of the Series to delete.
    """

    # Find series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Delete Series, poster, and associated Episodes
    delete_series_and_episodes(db, series, log=request.state.log)


@series_router.get('/search', status_code=200)
def search_existing_series(
        name: Optional[str] = None,
        year: Optional[int] = None,
        monitored: Optional[bool] = None,
        font_id: Optional[int] = None,
        sync_id: Optional[int] = None,
        template_id: Optional[int] = None,
        db: Session = Depends(get_database),
    ) -> Page[Series]:
    """
    Query all defined defined series by the given parameters. This
    performs an AND operation with the given conditions.

    - name: Name to fuzzy match the Series against.
    - year: Year to exactly filter results by.
    - monitored: Monitored status to filter results by.
    - *_id: Object ID to filter results by.
    """

    # Generate conditions for the given arguments
    conditions = []
    if name is not None:
        conditions.append(or_(
            models.series.Series.name.contains(name),
            models.series.Series.fuzzy_matches(name),
        ))
    if year is not None:
        conditions.append(models.series.Series.year==year)
    if monitored is not None:
        conditions.append(models.series.Series.monitored==monitored)
    if font_id is not None:
        conditions.append(models.series.Series.font_id==font_id)
    if sync_id is not None:
        conditions.append(models.series.Series.sync_id==sync_id)
    if template_id is not None:
        return paginate(
            db.query(models.series.Series)\
                .join(models.template.SeriesTemplates.series)\
                .filter(models.template.SeriesTemplates.template_id==template_id)\
                .filter(*conditions)\
                .order_by(models.series.Series.sort_name)
        )

    # Query by all given conditions - if by name, sort by str difference
    if name is not None:
        return paginate(
            db.query(models.series.Series).filter(*conditions)\
                .order_by(models.series.Series.diff_ratio(name))
        )

    return paginate(
        db.query(models.series.Series).filter(*conditions)\
            .order_by(func.lower(models.series.Series.sort_name))
    )


@series_router.get('/lookup', status_code=200)
def lookup_series(
        request: Request,
        name: str = Query(..., min_length=1),
        year: Optional[int] = Query(default=None),
        interface: EpisodeDataSource = Query(...),
        db: Session = Depends(get_database),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        sonarr_interface: Optional[SonarrInterface] = Depends(get_sonarr_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
    ) -> Page[SearchResult]:
    """
    Look up the given series name on the indicated interface. Returned
    results are not necessary already added to TCM - use the `/search`
    endpoint for that.

    - name: Series name or substring to look up.
    - interface: Which Episode data interface to look up on.
    """

    # Get associated Interface to query
    interface_obj = {
        'Emby': emby_interface,
        'Jellyfin': jellyfin_interface,
        'Plex': plex_interface,
        'Sonarr': sonarr_interface,
        'TMDb': tmdb_interface,
    }.get(interface, None)
    if not interface_obj:
        raise HTTPException(
            status_code=409,
            detail=f'Cannot connect to {interface}',
        )
    interface_obj: Union[EmbyInterface, JellyfinInterface, PlexInterface,
                         SonarrInterface, TMDbInterface] = interface_obj

    # Query Interface, only return max of 25 results TODO temporary?
    results: list[SearchResult] = interface_obj.query_series(
        name, log=request.state.log,
    )

    # Update `added` attributes
    final_results = []
    for result in results:
        # Exit if 25 results have been found
        if len(final_results) >= 25:
            break

        # Filter by year if provided
        if year is not None and result.year != year:
            continue

        # Query database for this result
        existing = db.query(models.series.Series)\
            .filter(result.series_info.filter_conditions(models.series.Series))\
            .first()

        # Result has been added if there is an existing Series
        result.added = existing is not None
        final_results.append(result)

    return paginate_sequence(final_results)


@series_router.get('/{series_id}', status_code=200)
def get_series_config(
        series_id: int,
        db: Session = Depends(get_database)
    ) -> Series:
    """
    Get the config for the given Series.

    - series_id: ID of the series to get the config of.
    """

    return get_series(db, series_id, raise_exc=True)


@series_router.patch('/{series_id}', status_code=200)
def update_series_(
        series_id: int,
        request: Request,
        update_series: UpdateSeries = Body(...),
        db: Session = Depends(get_database),
    ) -> Series:
    """
    Update the config of the given Series.

    - series_id: ID of the Series to update.
    - update_series: Attributes of the Series to update.
    """

    # Get contextual logger
    log = request.state.log

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get object as dictionary
    update_series_dict = update_series.dict()

    # If a Font is indicated, verify it exists
    get_font(db, update_series_dict.get('font_id', None), raise_exc=True)

    # Assign Templates if indicated
    changed = False
    if ((template_ids := update_series_dict.get('template_ids', None))
        not in (None, UNSPECIFIED)):
        if series.template_ids != template_ids:
            templates = get_all_templates(db, update_series_dict)
            series.assign_templates(templates, log=log)
            changed = True

    # Update each attribute of the object
    for attr, value in update_series_dict.items():
        if value != UNSPECIFIED and getattr(series, attr) != value:
            log.debug(f'Series[{series_id}].{attr} = {value}')
            setattr(series, attr, value)
            changed = True

    # If any values were changed, commit to database
    if changed:
        db.commit()

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=log)

    return series


@series_router.post('/{series_id}/toggle-monitor', status_code=201)
def toggle_series_monitored_status(
        series_id: int,
        db: Session = Depends(get_database)
    ) -> Series:
    """
    Toggle the monitored attribute of the given Series.

    - series_id: ID of the Series to toggle the monitored attribute of.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Toggle monitored attribute, update Database
    series.monitored = not series.monitored
    db.commit()

    return series


@series_router.post('/{series_id}/load/{media_server}', status_code=201,
        tags=['Emby', 'Jellyfin', 'Plex'])
def load_title_cards_into_media_server(
        series_id: int,
        media_server: MediaServer,
        request: Request,
        db: Session = Depends(get_database),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface)
    ) -> None:
    """
    Load all of the given Series' unloaded Title Cards into the given
    Media Server. This only loads Cards that have not previously been
    loaded, or whose previously loaded cards have been changed.

    - series_id: ID of the Series whose Cards are being loaded.
    - media_server: Which Media Server to load cards into. Must have an
    active, valid Interface connection.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    load_series_title_cards(
        series, media_server, db, emby_interface, jellyfin_interface,
        plex_interface, force_reload=False, log=request.state.log,
    )


@series_router.post('/{series_id}/reload/{media_server}', status_code=201,
        tags=['Emby', 'Jellyfin', 'Plex'])
def reload_title_cards_into_media_server(
        series_id: int,
        media_server: MediaServer,
        request: Request,
        db: Session = Depends(get_database),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface)
    ) -> None:
    """
    Reload all of the given Series' Title Cards into the given Media
    Server. This loads all Cards, even those that have not changed.

    - series_id: ID of the Series whose Cards are being loaded.
    - media_server: Which Media Server to load cards into. Must have an
    active, valid Interface connection.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return load_series_title_cards(
        series, media_server, db, emby_interface, jellyfin_interface,
        plex_interface, force_reload=True, log=request.state.log,
    )


@series_router.post('/{series_id}/process', status_code=200)
def process_series(
        background_tasks: BackgroundTasks,
        request: Request,
        series_id: int,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        sonarr_interface: Optional[SonarrInterface] = Depends(get_sonarr_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
    ) -> None:
    """
    Completely process the given Series. This does all major "tasks,"
    including:

    1. Refreshing Episode data.
    2. Downloading Source images
    3. Adding any Episode translations
    4. Updating Episode watch statuses
    5. Create Title Cards for all Episodes

    - series_id: ID of the Series to process.
    """

    # Get contextual logger
    log = request.state.log

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Begin processing the Series
    # Refresh episode data, use BackgroundTasks for ID assignment
    log.debug(f'{series.log_str} Started refreshing Episode data')
    refresh_episode_data(
        db, preferences, series, emby_interface, jellyfin_interface,
        plex_interface, sonarr_interface, tmdb_interface,
        log=log,
    )

    # Begin downloading Source images - use BackgroundTasks
    log.debug(f'{series.log_str} Started downloading source images')
    for episode in series.episodes:
        background_tasks.add_task(
            # Function
            download_episode_source_image,
            # Arguments
            db, preferences, emby_interface, jellyfin_interface, plex_interface,
            tmdb_interface, episode, raise_exc=False, log=log,
        )

    # Begin Episode translation - use BackgroundTasks
    log.debug(f'{series.log_str} Started adding translations')
    for episode in series.episodes:
        background_tasks.add_task(
            # Function
            translate_episode,
            # Arguments
            db, episode, tmdb_interface, log=log,
        )

    # Update watch statuses
    update_episode_watch_statuses(
        emby_interface, jellyfin_interface, plex_interface,
        series, series.episodes, log=log,
    )
    db.commit()

    # Begin Card creation - use BackgroundTasks
    for episode in series.episodes:
        background_tasks.add_task(
            # Function
            create_episode_card,
            # Arguments
            db, preferences, background_tasks, episode, raise_exc=False, log=log
        )


@series_router.delete('/{series_id}/plex-labels', status_code=204)
def remove_series_labels(
        request: Request,
        series_id: int,
        labels: list[str] = Query(default=['TCM', 'Overlay']),
        db: Session = Depends(get_database),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
    ) -> None:
    """
    Remove the given labels from the given Series' Episodes within Plex.
    This can be used to reset PMM overlays.

    - series_id: ID of the Series whose Episode labels are being remove.
    - labels: Any labels to remove.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Raise 409 if no library, or the server's interface is invalid
    if series.plex_library_name is None:
        raise HTTPException(
            status_code=409,
            detail=f'{series.log_str} has no Plex Library',
        )
    if not plex_interface:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with Plex',
        )

    # Remove labels
    plex_interface.remove_series_labels(
        series.plex_library_name, series.as_series_info, labels,
        log=request.state.log,
    )


@series_router.get('/{series_id}/poster', status_code=200)
def download_series_poster_(
        series_id: int,
        request: Request,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        imagemagick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
    ) -> None:
    """
    Download and return a poster for the given Series.

    - series_id: Series being queried.
    """

    # Find Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return download_series_poster(
        db, preferences, series, imagemagick_interface, tmdb_interface,
        log=request.state.log,
    )


@series_router.put('/{series_id}/poster/query', status_code=200)
def query_series_poster(
        series_id: int,
        db: Session = Depends(get_database),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
    ) -> Optional[str]:
    """
    Query for a poster of the given Series.

    - series_id: Series being queried.
    """

    # Find Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Return queried poster
    return tmdb_interface.get_series_poster(series.as_series_info)


@series_router.post('/{series_id}/poster', status_code=201)
async def set_series_poster(
        series_id: int,
        poster_url: Optional[str] = Form(default=None),
        poster_file: Optional[UploadFile] = None,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        image_magick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface)
    ) -> str:
    """
    Set the poster for the given series.

    - series_id: ID of the series whose poster is being updated.
    - poster_url: URL to the new poster.
    - poster_file: New poster file.
    """

    # Find Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get poster contents
    uploaded_file = b''
    if poster_file is not None:
        uploaded_file = await poster_file.read()

    # Send error if both a URL and file were provided
    if poster_url is not None and len(uploaded_file) > 0:
        raise HTTPException(
            status_code=422,
            detail='Cannot provide multiple posters'
        )

    # Send error if neither were provided
    if poster_url is None and len(uploaded_file) == 0:
        raise HTTPException(
            status_code=422,
            detail='URL or file are required'
        )

    # If an uploaded file was provided, use that
    if len(uploaded_file) > 0:
        poster_content = uploaded_file

    # If only URL was required, attempt to download, error if unable
    if poster_url is not None:
        try:
            poster_content = get(poster_url, timeout=30).content
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download poster - {e}'
            ) from e

    # Valid poster provided, download into asset directory
    poster_path = preferences.asset_directory / str(series.id) / 'poster.jpg'
    series.poster_file = str(poster_path)
    poster_path.parent.mkdir(exist_ok=True, parents=True)
    poster_path.write_bytes(poster_content)

    # Create resized poster for preview
    resized_path = poster_path.parent / 'poster-750.jpg'
    if image_magick_interface is None:
        file_copy(
            preferences.INTERNAL_ASSET_DIRECTORY / 'placeholder.jpg',
            resized_path,
        )
    else:
        image_magick_interface.resize_image(
            poster_path, resized_path, by='width', width=500,
        )

    # Update poster, commit to database
    series.poster_url = f'/assets/{series.id}/poster.jpg'
    db.commit()

    return series.poster_url
