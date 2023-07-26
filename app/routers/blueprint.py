from json import dump
from pathlib import Path
from shutil import copy as copy_file, make_archive as zip_directory
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi_pagination import paginate as paginate_sequence
from sqlalchemy.orm import Session
from app.database.query import get_series

from app.database.session import Page
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.blueprint import (
    generate_series_blueprint, get_blueprint_by_id, get_blueprint_font_files,
    import_blueprint, query_all_blueprints, query_series_blueprints
)
from app.internal.episodes import get_all_episode_data
from app.internal.series import add_series
from app import models
from app.schemas.blueprint import (
    BlankBlueprint, DownloadableFile, RemoteBlueprint, RemoteMasterBlueprint
)
from app.schemas.series import NewSeries, Series
from modules.SeriesInfo import SeriesInfo


# Create sub router for all /blueprints API requests
blueprint_router = APIRouter(
    prefix='/blueprints',
    tags=['Blueprints'],
)


@blueprint_router.get('/export/series/{series_id}', status_code=200)
def export_series_blueprint(
        request: Request,
        series_id: int,
        include_global_defaults: bool = Query(default=True),
        include_episode_overrides: bool = Query(default=True),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        sonarr_interface: Optional[SonarrInterface] = Depends(get_sonarr_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
    ) -> BlankBlueprint:
    """
    Generate the Blueprint for the given Series. This Blueprint can be
    imported to completely recreate a Series' (and all associated
    Episodes') configuration.

    - series_id: ID of the Series to export the Blueprint of.
    - include_global_defaults: Whether to write global settings if the
    Series has no corresponding override, primarily for the card type.
    - include_episode_overrides: Whether to include Episode-level
    overrides in the exported Blueprint. If True, then any Episode Font
    and Template assignments are also included.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get raw Episode data
    episode_data = []
    if include_episode_overrides:
        episode_data = get_all_episode_data(
            preferences, series, emby_interface, jellyfin_interface,
            plex_interface, sonarr_interface, tmdb_interface, raise_exc=False,
            log=request.state.log,
        )

    return generate_series_blueprint(
        series, episode_data, include_global_defaults,
        include_episode_overrides, preferences,
    )


@blueprint_router.get('/export/series/{series_id}/font-files', status_code=200)
def get_series_blueprint_font_files(
        series_id: int,
        include_episode_overrides: bool = Query(default=True),
        db: Session = Depends(get_database),
    ) -> list[DownloadableFile]:
    """
    Get the URI's to the associated Blueprint's Font files so they can
    be downloaded.

    - series_id: ID of the Series to export the Blueprint of.
    - include_episode_overrides: Whether to include Episode-level
    overrides. If True, then any Episode Font are also included.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get list of Font files for this Series' Blueprint
    font_files = get_blueprint_font_files(
        series,
        series.episodes if include_episode_overrides else [],
    )

    # Return downloadable files for these
    return [
        {
            'url': f'/assets/fonts/{font_file.parent.name}/{font_file.name}',
            'filename': font_file.name
        }
        for font_file in font_files
    ]


@blueprint_router.get('/export/series/{series_id}/zip', status_code=200)
async def export_series_blueprint_as_zip(
        request: Request,
        series_id: int,
        include_global_defaults: bool = Query(default=True),
        include_episode_overrides: bool = Query(default=True),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        sonarr_interface: Optional[SonarrInterface] = Depends(get_sonarr_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
    ) -> FileResponse:
    """
    Export a zipped file of the given Series' Blueprint (as JSON), any
    associated Font files, and a preview image.

    - series_id: ID of the Series to export the Blueprint of.
    - include_global_defaults: Whether to write global settings if the
    Series has no corresponding override, primarily for the card type.
    - include_episode_overrides: Whether to include Episode-level
    overrides in the exported Blueprint. If True, then any Episode Font
    and Template assignments are also included.
    """

    # Get contextual logger
    log = request.state.log

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get raw Episode data
    episode_data = []
    if include_episode_overrides:
        episode_data = get_all_episode_data(
            preferences, series, emby_interface, jellyfin_interface,
            plex_interface, sonarr_interface, tmdb_interface, raise_exc=False,
            log=request.state.log,
        )

    # Generate Blueprint
    blueprint = generate_series_blueprint(
        series, episode_data, include_global_defaults,
        include_episode_overrides, preferences,
    )
    blueprint = BlankBlueprint(**blueprint).dict()

    # Get list of Font files for this Series' Blueprint
    font_files = get_blueprint_font_files(
        series,
        series.episodes if include_episode_overrides else [],
    )

    # Get preview image for this Series - use first non-stylized existing Card
    cards = db.query(models.card.Card)\
        .filter_by(series_id=series_id, blur=False, grayscale=False)\
        .filter(models.card.Card.season_number>0)\
        .order_by(models.card.Card.season_number,
                  models.card.Card.episode_number)\
        .all()

    card_file = None
    for card in cards:
        if (this_card_file := Path(card.card_file)).exists():
            card_file = this_card_file
            break

    # Get directory for zipping
    zip_dir = preferences.TEMPORARY_DIRECTORY / 'zips' / log.extra['context_id']

    # Copy all files into the directory to be zipped
    zip_dir.mkdir(parents=True, exist_ok=True)
    for file in font_files:
        copy_file(file, zip_dir / file.name)
        log.debug(f'Copied "{file}" into zip directory "{zip_dir}"')
    if card_file:
        copy_file(card_file, zip_dir / f'preview{card_file.suffix}')
        blueprint['preview'] = f'preview{card_file.suffix}'

    # Write Blueprint as JSON into zip directory
    blueprint_file = zip_dir / 'blueprint.json'
    with blueprint_file.open('w') as file_handle:
        dump(blueprint, file_handle, indent=2)
    log.debug(f'Dumped Blueprint JSON into "{blueprint_file}"')

    # Zip directory, return zipped file
    return FileResponse(zip_directory(zip_dir, 'zip', zip_dir))


@blueprint_router.put('/query/blacklist')
def blacklist_blueprint(
        request: Request,
        series_full_name: str = Query(..., min_length=8),
        blueprint_id: int = Query(...),
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Blacklist the indicated Blueprint. Once blacklisted, this Blueprint
    should not by returned by the `/query/all` endpoint.

    - series_full_name: Full name of the Series associated with this
    Blueprint.
    - blueprint_id: Unique ID of the Blueprint.
    """

    # Get contextual logger
    log = request.state.log

    # Add to blacklist, commit changes
    preferences.blacklisted_blueprints.add((series_full_name, blueprint_id))
    preferences.commit(log=log)

    log.debug(f'Blacklisted Blueprint[{series_full_name}, {blueprint_id}]')


@blueprint_router.get('/query/all', status_code=200)
def query_all_blueprints_(
        request: Request,
        preferences: Preferences = Depends(get_preferences),
    ) -> Page[RemoteMasterBlueprint]:
    """
    Query for all available Blueprints for all Series. Blacklisted
    Blueprints are excluded from the return.
    """

    blacklist = preferences.blacklisted_blueprints
    return paginate_sequence([
        blueprint for blueprint in query_all_blueprints(log=request.state.log)
        if (blueprint['series_full_name'], blueprint['id']) not in blacklist
    ])


@blueprint_router.get('/query/series/{series_id}', status_code=200)
def query_series_blueprints_(
        request: Request,
        series_id: int,
        db: Session = Depends(get_database),
    ) -> list[RemoteBlueprint]:
    """
    Search for any Blueprints for the given Series.

    - series_id: ID of the Series to search for Blueprints of.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return query_series_blueprints(series.full_name, log=request.state.log)


@blueprint_router.get('/query/series', status_code=200)
def query_blueprints_by_name(
        request: Request,
        name: str = Query(..., min_length=1),
        year: int = Query(..., min=1900),
    ) -> list[RemoteBlueprint]:
    """
    Search for any Blueprints for the given Series not yet added to TCM.

    - name: Name of the Series to look up Blueprints for.
    - year: Year of the Series to look up Blueprints for.
    """

    return query_series_blueprints(f'{name} ({year})', log=request.state.log)


@blueprint_router.put('/import/blueprint', status_code=200)
def import_blueprint_and_series(
        background_tasks: BackgroundTasks,
        request: Request,
        blueprint: RemoteMasterBlueprint = Body(...),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        imagemagick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        sonarr_interface: Optional[SonarrInterface] = Depends(get_sonarr_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface),
    ) -> Series:
    """
    Import the given Blueprint - creating the associated Series if it
    does not already exist.

    - blueprint: Blueprint to import.
    """

    # Get contextual logger
    log = request.state.log

    try:
        series_info = SeriesInfo(blueprint.series_full_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f'Cannot identify Series associated with Blueprint'
        ) from exc

    # Determine if this Series already exists
    series = db.query(models.series.Series)\
        .filter(series_info.filter_conditions(models.series.Series))\
        .first()

    # Series does not exist, create and add to database
    if not series:
        log.debug(f'Blueprint Series {series_info} not found - adding to database')
        series = add_series(
            NewSeries(name=series_info.name, year=series_info.year),
            background_tasks, db, preferences, emby_interface,
            imagemagick_interface, jellyfin_interface, plex_interface,
            sonarr_interface, tmdb_interface, log=log,
        )

    # Import Blueprint
    import_blueprint(db, preferences, series, blueprint, log=log)

    return series


@blueprint_router.put('/import/series/{series_id}/blueprint/{blueprint_id}', status_code=200)
def import_series_blueprint_by_id(
        request: Request,
        series_id: int,
        blueprint_id: int,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Import the Blueprint with the given ID to the given Series.

    - series_id: ID of the Series to query for Blueprints of and to
    import into.
    - blueprint_id: ID of the Blueprint to import.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get Blueprint with this ID, raise 404 if DNE
    blueprint = get_blueprint_by_id(series, blueprint_id, log=request.state.log)

    # Import Blueprint
    import_blueprint(db, preferences, series, blueprint, log=request.state.log)


@blueprint_router.put('/import/series/{series_id}', status_code=200)
def import_series_blueprint_(
        request: Request,
        series_id: int,
        blueprint: RemoteBlueprint = Body(...),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences)
    ) -> None:
    """
    Import the given Blueprint into the given Series.

    - series_id: ID of the Series to import the given Blueprint into.
    - blueprint: Blueprint object to import.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Import Blueprint
    import_blueprint(db, preferences, series, blueprint, log=request.state.log)
