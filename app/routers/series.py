from requests import get
from typing import Optional

from fastapi import (
    APIRouter, BackgroundTasks, Body, Depends, Form, HTTPException, UploadFile
)

from app.database.query import get_font, get_series, get_template
from app.dependencies import (
    get_database, get_preferences, get_emby_interface,
    get_imagemagick_interface, get_jellyfin_interface, get_plex_interface,
    get_sonarr_interface, get_tmdb_interface
)
import app.models as models
from app.internal.series import (
    delete_series_and_episodes, download_series_poster, load_series_title_cards,
    set_series_database_ids
)
from app.internal.sources import download_series_logo
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import MediaServer
from app.schemas.series import NewSeries, Series, UpdateSeries

from modules.Debug import log

series_router = APIRouter(
    prefix='/series',
    tags=['Series'],
)


@series_router.get('/all', status_code=200)
def get_all_series(
        db = Depends(get_database)) -> list[Series]:
    """
    Get all defined Series.
    """
    
    return db.query(models.series.Series).all()


@series_router.post('/new', status_code=201)
def add_new_series(
        background_tasks: BackgroundTasks,
        new_series: NewSeries = Body(...),
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface = Depends(get_emby_interface),
        imagemagick_interface = Depends(get_imagemagick_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface),
        sonarr_interface = Depends(get_sonarr_interface),
        tmdb_interface = Depends(get_tmdb_interface)) -> Series:
    """
    Create a new Series. This also creates background tasks to set the
    database ID's of the series, as well as find and download a poster.

    - new_series: Series definition to create.
    """

    # If a Template or Font was indicated, verify they exist
    get_template(db, getattr(new_series, 'template_id', None), raise_exc=True)
    get_font(db, getattr(new_series, 'font_id', None), raise_exc=True)

    # Add to database
    series = models.series.Series(**new_series.dict())
    db.add(series)
    db.commit()

    # Add background tasks to set ID's, download poster and logo
    background_tasks.add_task(
        # Function
        set_series_database_ids,
        # Arguments
        series, db, emby_interface, jellyfin_interface, plex_interface,
        sonarr_interface, tmdb_interface,
    )
    background_tasks.add_task(
        # Function
        download_series_poster,
        # Arguments
        db, preferences, series, tmdb_interface,
    )
    background_tasks.add_task(
        # Function
        download_series_logo,
        # Arguments
        db, preferences, emby_interface, imagemagick_interface,
        jellyfin_interface, tmdb_interface, series
    )

    return series


@series_router.delete('/{series_id}', status_code=204)
def delete_series(
        series_id: int,
        db = Depends(get_database)) -> None:
    """
    Delete the Series with the given ID. This also deletes the poster.

    - series_id: ID of the Series to delete.
    """

    # Find series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Delete Series, poster, and associated Episodes
    delete_series_and_episodes(db, series)

    return None


@series_router.get('/search', status_code=200)
def search_series(
        name: Optional[str] = None,
        year: Optional[int] = None,
        monitored: Optional[bool] = None,
        font_id: Optional[int] = None,
        sync_id: Optional[int] = None,
        template_id: Optional[int] = None,
        max_results: Optional[int] = 50,
        db = Depends(get_database)):
    """
    Query all defined defined series by the given parameters. This
    performs an AND operation with the given conditions.

    - Arguments: Search arguments to filter the results by.
    - max_results: Maximum number of results to return.
    """

    # Generate conditions for the given arguments
    conditions = []
    if name is not None:
        conditions.append(models.series.Series.name.contains(name))
    if year is not None:
        conditions.append(models.series.Series.year==year)
    if monitored is not None:
        conditions.append(models.series.Series.monitored==monitored)
    if font_id is not None:
        conditions.append(models.series.Series.font_id==font_id)
    if sync_id is not None:
        conditions.append(models.series.Series.sync_id==sync_id)
    if template_id is not None:
        conditions.append(models.series.Series.template_id==template_id)

    # Query by all given conditions
    all_series = db.query(models.series.Series).filter(*conditions).all()

    # Limit number of results if indicated
    results = all_series
    if max_results is not None:
        results = all_series[:max_results]

    return {
        'results': results,
        'total_count': len(all_series),
    }


@series_router.get('/{series_id}', status_code=200)
def get_series_config(
        series_id: int,
        db = Depends(get_database)) -> Series:
    """
    Get the config for the given Series.

    - series_id: ID of the series to get the config of.
    """

    return get_series(db, series_id, raise_exc=True)


@series_router.patch('/{series_id}', status_code=200)
def update_series(
        series_id: int,
        update_series: UpdateSeries = Body(...),
        db = Depends(get_database)) -> Series:
    """
    Update the config of the given Series.

    - series_id: ID of the Series to update.
    - update_series: Attributes of the Series to update.
    """
    log.critical(f'{update_series.dict()=}')
    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # If a Template or Font were indicated, verify they exist
    get_template(db, getattr(update_series, 'template_id', None),raise_exc=True)
    get_font(db, getattr(update_series, 'font_id', None), raise_exc=True)

    # Update each attribute of the object
    changed = False
    for attr, value in update_series.dict().items():
        if value != UNSPECIFIED and getattr(series, attr) != value:
            log.debug(f'Series[{series_id}].{attr} = {value}')
            setattr(series, attr, value)
            changed = True

    # If any values were changed, commit to database
    if changed:
        db.commit()
    
    return series


@series_router.post('/{series_id}/toggle-monitor', status_code=201)
def toggle_series_monitored_status(
        series_id: int,
        db = Depends(get_database)) -> Series:
    """
    Toggle the monitored attribute of the given Series.

    - series_id: ID of the Series to toggle the monitored attribute of.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Toggle monitored attribute, update Database
    series.monitored = not series.monitored
    log.debug(f'{series.log_str}.monitored={series.monitored}')
    db.commit()

    return series


@series_router.post('/{series_id}/load/{media_server}', status_code=201,
        tags=['Emby', 'Jellyfin', 'Plex'])
def load_title_cards_into_media_server(
        series_id: int,
        media_server: MediaServer,
        db = Depends(get_database),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface)) -> None:
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

    return load_series_title_cards(
        series, media_server, db, emby_interface, jellyfin_interface,
        plex_interface, force_reload=False
    )


@series_router.post('/{series_id}/reload/{media_server}', status_code=201,
        tags=['Emby', 'Jellyfin', 'Plex'])
def reload_title_cards_into_media_server(
        series_id: int,
        media_server: MediaServer,
        db = Depends(get_database),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface)) -> None:
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
        plex_interface, force_reload=True
    )


@series_router.get('/{series_id}/poster', status_code=200)
def get_series_poster(
        series_id: int,
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        tmdb_interface = Depends(get_tmdb_interface)) -> str:
    """
    Download and return a poster for the given series.

    - series_id: Series being queried.
    """

    # Find series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return download_series_poster(db, preferences, series, tmdb_interface)


@series_router.post('/{series_id}/poster', status_code=201)
async def set_series_poster(
        series_id: int,
        poster_url: Optional[str] = Form(default=None),
        poster_file: Optional[UploadFile] = None,
        db = Depends(get_database),
        preferences = Depends(get_preferences)) -> str:
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
            poster_content = get(poster_url).content
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download poster - {e}'
            )

    # Valid poster provided, download into asset directory
    poster_path = preferences.asset_directory / 'posters' / f'{series.id}.jpg'
    series.poster_file = str(poster_path)
    poster_file.write_bytes(poster_content)

    # Update poster, commit to database
    series.poster_url = f'/assets/posters/{poster_file.name}'
    db.commit()
    
    return series.poster_url