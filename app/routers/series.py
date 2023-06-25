from pathlib import Path
from requests import get
from shutil import copy as file_copy
from typing import Literal, Optional

from fastapi import (
    APIRouter, Body, Depends, Form, HTTPException, Query, UploadFile
)
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.dependencies import *
from app.database.session import Page
from app.database.query import get_all_templates, get_font, get_series
import app.models as models
from app.internal.cards import refresh_remote_card_types
from app.internal.series import (
    delete_series_and_episodes, download_series_poster, load_series_title_cards,
    set_series_database_ids
)
from app.internal.sources import download_series_logo
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import MediaServer
from app.schemas.series import NewSeries, Series, UpdateSeries

from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface


series_router = APIRouter(
    prefix='/series',
    tags=['Series'],
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
        series = query.order_by(func.lower(models.series.Series.name))\
            .order_by(models.series.Series.year)
    elif order_by == 'reverse-alphabetical':
        series = query.order_by(func.lower(models.series.Series.name).desc())\
            .order_by(models.series.Series.year)
    # Order by ID
    elif order_by == 'id':
        series = query.order_by(models.series.Series.id)
    elif order_by == 'reverse-id':
        series = query.order_by(models.series.Series.id.desc())
    # Order by Year > Name
    elif order_by == 'year':
        series = query.order_by(models.series.Series.year)\
            .order_by(func.lower(models.series.Series.name))
    elif order_by == 'reverse-year':
        series = query.order_by(models.series.Series.year.desc())\
            .order_by(func.lower(models.series.Series.name))

    # Return paginated results
    return paginate(series)


@series_router.post('/new', status_code=201)
def add_new_series(
        new_series: NewSeries = Body(...),
        db: Session = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        imagemagick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        sonarr_interface: Optional[SonarrInterface] = Depends(get_sonarr_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
    ) -> Series:
    """
    Create a new Series. This also creates background tasks to set the
    database ID's of the series, as well as find and download a poster.

    - new_series: Series definition to create.
    """

    # Convert object to dictionary
    new_series_dict = new_series.dict()

    # If a Font or any Templates were indicated, verify they exist
    get_font(db, getattr(new_series, 'font_id', None), raise_exc=True)
    templates = get_all_templates(db, new_series_dict)

    # Add to database
    series = models.series.Series(**new_series_dict, templates=templates)
    db.add(series)
    db.commit()

    # Create source directory if DNE
    Path(series.source_directory).mkdir(parents=True, exist_ok=True)

    # Set Series ID's, download poster and logo
    set_series_database_ids(
        series, db, emby_interface, jellyfin_interface, plex_interface,
        sonarr_interface, tmdb_interface,
    )
    download_series_poster(
        db, preferences, series, emby_interface, imagemagick_interface,
        jellyfin_interface, plex_interface, tmdb_interface,
    )
    download_series_logo(
        preferences, emby_interface, imagemagick_interface, jellyfin_interface,
        tmdb_interface, series
    )

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db)

    return series


@series_router.delete('/{series_id}', status_code=204)
def delete_series(
        series_id: int,
        db: Session = Depends(get_database)) -> None:
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
        db: Session = Depends(get_database),
    ) -> Page[Series]:
    """
    Query all defined defined series by the given parameters. This
    performs an AND operation with the given conditions.

    - Arguments: Search arguments to filter the results by.
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
        return paginate(db.query(models.series.Series)\
            .join(models.series.Series.templates)\
            .filter(models.template.Template.id==template_id))

    # Query by all given conditions
    return paginate(
        db.query(models.series.Series).filter(*conditions)\
            .order_by(func.lower(models.series.Series.name))
    )


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
def update_series(
        series_id: int,
        update_series: UpdateSeries = Body(...),
        db: Session = Depends(get_database)
    ) -> Series:
    """
    Update the config of the given Series.

    - series_id: ID of the Series to update.
    - update_series: Attributes of the Series to update.
    """
    log.debug(f'{update_series.dict()=}')
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
            series.templates = get_all_templates(db, update_series_dict)
            log.debug(f'{series.log_str}.templates = {template_ids}')
            changed = True

    # Update each attribute of the object
    for attr, value in update_series.dict().items():
        if value != UNSPECIFIED and getattr(series, attr) != value:
            log.debug(f'Series[{series_id}].{attr} = {value}')
            setattr(series, attr, value)
            changed = True

    # If any values were changed, commit to database
    if changed:
        db.commit()

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db)
    
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
    log.debug(f'{series.log_str}.monitored={series.monitored}')
    db.commit()

    return series


@series_router.post('/{series_id}/load/{media_server}', status_code=201,
        tags=['Emby', 'Jellyfin', 'Plex'])
def load_title_cards_into_media_server(
        series_id: int,
        media_server: MediaServer,
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
        plex_interface, force_reload=False
    )

    return None


@series_router.post('/{series_id}/reload/{media_server}', status_code=201,
        tags=['Emby', 'Jellyfin', 'Plex'])
def reload_title_cards_into_media_server(
        series_id: int,
        media_server: MediaServer,
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
        plex_interface, force_reload=True
    )


@series_router.delete('/{series_id}/plex-labels', status_code=204)
def remove_series_labels(
        series_id: int,
        labels: list[str] = Query(default=[]),
        db: Session = Depends(get_database),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface)
    ) -> None:
    """
    Remove the given labels from the given Series' Episodes within Plex.
    This can be used to reset PMM overlays.

    - series_id: ID of the Series whose Episode labels are being remove.
    - labels: Any number of labels to remove.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Raise 409 if no library, or the server's interface is invalid
    if series.plex_library_name is None:
        raise HTTPException(
            status_code=409,
            detail=f'{series.log_str} has no Plex Library',
        )
    elif plex_interface is None:
        raise HTTPException(
            status_code=409,
            detail=f'Unable to communicate with Plex',
        )

    # Remove labels
    plex_interface.remove_series_labels(
        series.plex_library_name, series.as_series_info, labels,
    )
    
    return None


@series_router.get('/{series_id}/poster', status_code=200)
def download_series_poster_(
        series_id: int,
        db: Session = Depends(get_database),
        preferences = Depends(get_preferences),
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
            poster_content = get(poster_url).content
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f'Unable to download poster - {e}'
            )

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