from shutil import copy as file_copy
from typing import Literal, Optional

from fastapi import (
    APIRouter, BackgroundTasks, Body, Depends, Form, HTTPException, Query,
    Request, UploadFile
)
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import paginate as paginate_sequence
from requests import get
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.database.session import Page
from app.database.query import get_interface, get_series
from app import models
from app.internal.series import (
    add_series, delete_series, download_series_poster,
    lookup_series, process_series, update_series,
)
from app.internal.auth import get_current_user
from app.schemas.series import (
    BatchUpdateSeries, NewSeries, SearchResult, Series, UpdateSeries
)


series_router = APIRouter(
    prefix='/series',
    tags=['Series'],
    dependencies=[Depends(get_current_user)],
)


OrderBy = Literal[
    'alphabetical', 'reverse-alphabetical',
    'cards', 'reverse-cards',
    'id', 'reverse-id',
    'sync',
    'year', 'reverse-year'
]
@series_router.get('/all', status_code=200)
def get_all_series(
        db: Session = Depends(get_database),
        order_by: OrderBy = Query(default='alphabetical'),
        # filter: SeriesFilter = Query(default={}),
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
        series = query.order_by(desc(models.series.Series.sort_name))\
            .order_by(models.series.Series.year)
    # Order by Cards
    elif order_by == 'cards':
        series = query.outerjoin(models.card.Card)\
            .group_by(models.series.Series.id)\
            .order_by(func.count(models.series.Series.id))
    elif order_by == 'reverse-cards':
        series = query.outerjoin(models.card.Card)\
            .group_by(models.series.Series.id)\
            .order_by(func.count(models.series.Series.id).desc())
    # Order by Sync
    elif order_by == 'sync':
        series = query.order_by(models.series.Series.sync_id.desc(),
                                models.series.Series.sort_name,
                                models.series.Series.year)
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


@series_router.get('/series/{series_id}/previous', status_code=200)
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


@series_router.get('/series/{series_id}/next', status_code=200)
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
    ) -> Series:
    """
    Create a new Series. This also creates background tasks to set the
    database ID's of the series, as well as find and download a poster.

    - new_series: Series definition to create.
    """

    return add_series(new_series, background_tasks, db, log=request.state.log)


@series_router.delete('/series/{series_id}', status_code=204)
def delete_series_(
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

    # Delete Series and all child content
    delete_series(db, series, log=request.state.log)


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
def lookup_new_series(
        request: Request,
        name: str = Query(..., min_length=1),
        db: Session = Depends(get_database),
        interface = Depends(require_interface),
    ) -> Page[SearchResult]:
    """
    Look up the given Series name on the indicated Interface. Returned
    results are not necessary already added to TCM - use the `/search`
    endpoint to query existing Series.

    - name: Series name or substring to look up.
    - interface_id: ID of the interface to query.
    """

    return paginate_sequence(
        lookup_series(db, interface, name, log=request.state.log)
    )


@series_router.get('/series/{series_id}', status_code=200)
def get_series_config(
        series_id: int,
        db: Session = Depends(get_database)
    ) -> Series:
    """
    Get the config for the given Series.

    - series_id: ID of the series to get the config of.
    """

    return get_series(db, series_id, raise_exc=True)


@series_router.patch('/series/{series_id}', status_code=200)
def update_series_(
        series_id: int,
        request: Request,
        update: UpdateSeries = Body(...),
        db: Session = Depends(get_database)
    ) -> Series:
    """
    Update the config of the given Series.

    - series_id: ID of the Series to update.
    - update_series: Attributes of the Series to update.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Modify Series
    update_series(db, series, update, commit=True, log=request.state.log)

    return series


@series_router.put('/series/{series_id}/toggle-monitor')
def toggle_series_monitored_status(
        series_id: int,
        db: Session = Depends(get_database),
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


@series_router.post('/series/{series_id}/process', status_code=200)
def process_series_(
        background_tasks: BackgroundTasks,
        request: Request,
        series_id: int,
        db: Session = Depends(get_database),
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

    process_series(
        db,
        get_series(db, series_id, raise_exc=True),
        background_tasks,
        log=request.state.log,
    )


@series_router.delete('/series/{series_id}/plex-labels/library', status_code=204)
def remove_series_labels(
        request: Request,
        series_id: int,
        interface_id: int = Query(...),
        library_name: str = Query(...),
        labels: list[str] = Query(default=['TCM', 'Overlay']),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Remove the given labels from the given Series' Episodes within Plex.
    This can be used to reset PMM overlays.

    - series_id: ID of the Series whose Episode labels are being remove.
    - interface_id: ID of the Interface whose library is being removed.
    - library_name: Name of the library to remove labels from.
    - labels: Any labels to remove.
    """

    # Get this Series and Interface, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)
    interface: PlexInterface = get_interface(interface_id, raise_exc=True)

    # Remove labels from specified library
    interface.remove_series_labels(
        library_name, series.as_series_info, labels,
        log=request.state.log
    )


@series_router.get('/series/{series_id}/poster', status_code=200)
def download_series_poster_(
        series_id: int,
        request: Request,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Download and return a poster for the given Series.

    - series_id: Series being queried.
    """

    # Find Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    download_series_poster(db, series, log=request.state.log)


@series_router.get('/{series_id}/poster/query', status_code=200)
def query_series_poster(
        series_id: int,
        db: Session = Depends(get_database),
        tmdb_interface: TMDbInterface = Depends(require_tmdb_interface)
    ) -> Optional[str]:
    """
    Query for a poster of the given Series.

    - series_id: Series being queried.
    """

    # Find Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Return queried poster
    return tmdb_interface.get_series_poster(series.as_series_info)


@series_router.put('/{series_id}/poster', status_code=201)
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


@series_router.patch('/batch', status_code=200)
def batch_update_series(
        request: Request,
        updates: list[BatchUpdateSeries] = Body(...),
        db: Session = Depends(get_database),
    ) -> list[Series]:
    """
    Update the config of all the given Series.

    - updates: List of Series IDs and the associated changes to make for
    that Series.
    """

    # Iterate through all provided Series
    all_series, changed = [], False
    for update in updates:
        # Get Series with the specified ID
        series = get_series(db, update.series_id, raise_exc=True)
        all_series.append(series)

        # Update this Series
        changed |= update_series(
            db, series, update.update, commit=False, log=request.state.log
        )

    # Commit changes to DB if necessary
    if changed:
        db.commit()

    return all_series


@series_router.put('/batch/monitor')
def batch_monitor_series(
        series_ids: list[int] = Body(...),
        db: Session = Depends(get_database),
    ) -> list[Series]:
    """
    Mark the Series with the given IDs as monitored.

    - series_ids: List of IDs of Series to mark as monitored.
    """

    all_series = []
    for series_id in series_ids:
        # Query for this Series, raise 404 if DNE
        series = get_series(db, series_id, raise_exc=True)
        all_series.append(series)

        # Update monitored attribute
        series.monitored = True
        log.debug(f'{series}.monitored = True')

    db.commit()

    return all_series


@series_router.delete('/batch/delete')
def batch_delete_series(
        request: Request,
        series_ids: list[int] = Body(...),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Batch operation to delete all the given Series.

    - series_ids: List of IDs of Series to delete.
    """

    for series_id in series_ids:
        series = get_series(db, series_id, raise_exc=True)
        delete_series(db, series, log=request.state.log)


@series_router.put('/batch/unmonitor')
def batch_unmonitor_series(
        request: Request,
        series_ids: list[int] = Body(...),
        db: Session = Depends(get_database),
    ) -> list[Series]:
    """
    Mark the Series with the given IDs as unmonitored.

    - series_ids: List of IDs of Series to mark as monitored.
    """

    all_series = []
    for series_id in series_ids:
        # Query for this Series, raise 404 if DNE
        series = get_series(db, series_id, raise_exc=True)
        all_series.append(series)

        # Update monitored attribute
        series.monitored = False
        request.state.log.debug(f'{series}.monitored = False')

    db.commit()

    return all_series


@series_router.post('/batch/process')
def batch_process_series(
        background_tasks: BackgroundTasks,
        request: Request,
        series_ids: list[int] = Body(...),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Completely process all the given Series.

    - series_ids: List of IDs of Series to process.
    """

    for series_id in series_ids:
        process_series(
            db,
            get_series(db, series_id, raise_exc=True),
            background_tasks,
            log=request.state.log,
        )
