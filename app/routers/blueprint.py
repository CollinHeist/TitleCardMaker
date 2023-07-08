from json import dump
from pathlib import Path
from shutil import copy as copy_file, make_archive as zip_directory
from typing import Union

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.responses import FileResponse
from fastapi_pagination import paginate
from sqlalchemy.orm import Session
from app.database.query import get_series

from app.database.session import Page
from app.dependencies import *
from app.internal.blueprint import (
    generate_series_blueprint, get_blueprint_by_id, get_blueprint_font_files,
    import_blueprint, query_all_blueprints, query_series_blueprints
)
import app.models as models
from app.schemas.blueprint import (
    Blueprint, BlankBlueprint, DownloadableFile, RemoteBlueprint,
    RemoteMasterBlueprint
)


# Create sub router for all /blueprints API requests
blueprint_router = APIRouter(
    prefix='/blueprints',
    tags=['Blueprints'],
)


@blueprint_router.get('/export/series/{series_id}', status_code=200)
def export_series_blueprint(
        series_id: int,
        include_global_defaults: bool = Query(default=True),
        include_episode_overrides: bool = Query(default=True),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
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

    return generate_series_blueprint(
        series, include_global_defaults, include_episode_overrides, preferences,
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

    # Generate Blueprint
    blueprint = generate_series_blueprint(
        series, include_global_defaults, include_episode_overrides, preferences,
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


@blueprint_router.get('/query/all', status_code=200)
def query_all_blueprints_(
        request: Request,
    ) -> Page[RemoteMasterBlueprint]:
    """
    Query for all Blueprints for all Series on GitHub.
    """

    return paginate(query_all_blueprints(log=request.state.log))


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

    return query_series_blueprints(series, log=request.state.log)


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

    return None


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

    return None