from json import dump
from pathlib import Path
from random import choice as random_choice
from shutil import copy as copy_file, make_archive as zip_directory
from typing import Literal, Optional

from fastapi import (
    APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Request
)
from fastapi.responses import FileResponse
from fastapi_pagination import paginate as paginate_sequence
from sqlalchemy.orm import Session

from app.database.query import get_blueprint, get_blueprint_set, get_series
from app.database.session import Page
from app.dependencies import (
    Preferences, get_blueprint_database, get_database, get_preferences
)
from app.internal.auth import get_current_user
from app.internal.blueprint import (
    delay_zip_deletion, generate_series_blueprint, get_blueprint_font_files,
    import_blueprint, query_series_blueprints
)
from app.internal.episodes import get_all_episode_data
from app.internal.series import add_series
from app import models
from app.models.blueprint import Blueprint, BlueprintSeries
from app.models.card import Card
from app.schemas.blueprint import (
    DownloadableFile, ExportBlueprint, RemoteBlueprint, RemoteBlueprintSet,
)
from app.schemas.series import Series

from modules.Debug import generate_context_id
from modules.SeriesInfo2 import SeriesInfo


# Create sub router for all /blueprints API requests
blueprint_router = APIRouter(
    prefix='/blueprints',
    tags=['Blueprints'],
    dependencies=[Depends(get_current_user)],
)


@blueprint_router.get('/export/series/{series_id}')
def export_series_blueprint(
        request: Request,
        series_id: int,
        include_global_defaults: bool = Query(default=True),
        include_episode_overrides: bool = Query(default=True),
        db: Session = Depends(get_database),
    ) -> ExportBlueprint:
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
            series, raise_exc=False, log=request.state.log,
        )

    return generate_series_blueprint(
        series, episode_data, include_global_defaults, include_episode_overrides
    )


@blueprint_router.get('/export/series/{series_id}/font-files')
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


@blueprint_router.get('/export/series/{series_id}/zip')
async def export_series_blueprint_as_zip(
        background_tasks: BackgroundTasks,
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

    # Get raw Episode data
    episode_data = []
    if include_episode_overrides:
        episode_data = get_all_episode_data(
            series, raise_exc=False, log=request.state.log,
        )
        # Get just the EpisodeInfo objects
        episode_data = [data[0] for data in episode_data]

    # Generate Blueprint
    blueprint = generate_series_blueprint(
        series, episode_data, include_global_defaults,
        include_episode_overrides,
    )

    # Get list of Font files for this Series' Blueprint
    font_files = get_blueprint_font_files(
        series,
        series.episodes if include_episode_overrides else [],
    )

    # Get all non-Specials Cards for this Series
    cards = db.query(Card)\
        .join(models.episode.Episode)\
        .filter(Card.series_id==series_id,
                models.episode.Episode.season_number>0)\
        .order_by(models.episode.Episode.season_number,
                  models.episode.Episode.episode_number)\
        .all()

    # Filter out Cards which are stylized or DNE
    filtered_cards = [
        card.card_file
        for card in cards
        if (not card.model_json.get('blur', False)
            and not card.model_json.get('grayscale', False)
            and card.exists)
    ]

    # Select random Card if possible
    card_file = Path(random_choice(filtered_cards)) if filtered_cards else None

    # Directories for zipping
    ZIPS_DIR = preferences.TEMPORARY_DIRECTORY / 'zips'
    cid = generate_context_id()
    font_zip_dir = ZIPS_DIR / f"fonts_{cid}"
    font_zip_dir.mkdir(exist_ok=True, parents=True)
    zip_dir: Path = ZIPS_DIR / cid
    zip_dir.mkdir(exist_ok=True, parents=True)

    # Copy all files into the zip directory
    for file in font_files:
        copy_file(file, font_zip_dir / file.name)
        log.debug(f'Copied "{file}" into Font zip directory')

    # Zip files, copy into main zip directory, delete after some delay
    if font_files:
        font_zip = Path(zip_directory(font_zip_dir, 'zip', font_zip_dir))
        background_tasks.add_task(delay_zip_deletion, font_zip_dir, font_zip)
        copy_file(font_zip, zip_dir / 'fonts.zip')

    # Copy preview into main zip directory
    if card_file is None:
        log.warning(f'No applicable Title Cards found for preview')
    else:
        copy_file(card_file, zip_dir / f'preview{card_file.suffix}')
        log.debug(f'Copied "{card_file}" into zip directory')

    # Write Blueprint as JSON into zip directory
    blueprint_file = zip_dir / 'blueprint.json'
    with blueprint_file.open('w') as file_handle:
        dump(blueprint.dict(), file_handle, indent=2)
    log.debug(f'Wrote "blueprint.json" into zip directory')

    # Create zip of Font zip + preview file + Blueprint JSON
    zip_ = zip_directory(zip_dir, 'zip', zip_dir)
    background_tasks.add_task(delay_zip_deletion, zip_dir, Path(zip_))

    # Zip directory, return zipped file
    return FileResponse(zip_)


@blueprint_router.put('/blacklist/{blueprint_id}')
def blacklist_blueprint(
        blueprint_id: int,
        request: Request,
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Blacklist the indicated Blueprint. Once blacklisted, this Blueprint
    should not by returned by the `/query/all` endpoint.

    - blueprint_id: Unique ID of the Blueprint.
    """

    # Add to blacklist, commit changes
    preferences.blacklisted_blueprints.add(blueprint_id)
    preferences.commit()

    request.state.log.debug(f'Blacklisted Blueprint[{blueprint_id}]')


@blueprint_router.delete('/blacklist/{blueprint_id}')
def remove_blueprint_from_blacklist(
        blueprint_id: int,
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Un-blacklist the Blueprint for the indicated Series.

    - blueprint_id: Unique ID of the Blueprint.
    """

    try:
        preferences.blacklisted_blueprints.remove(blueprint_id)
        preferences.commit()
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f'Blueprint {blueprint_id} is not blacklisted',
        ) from exc


@blueprint_router.get('/query/all')
def query_all_blueprints_(
        db: Session = Depends(get_database),
        blueprint_db: Session = Depends(get_blueprint_database),
        order_by: Literal['date', 'name'] = Query(default='date'),
        include_blacklisted: bool = Query(default=False),
        include_imported: bool = Query(default=False),
        include_missing_series: bool = Query(default=True),
        preferences: Preferences = Depends(get_preferences),
    ) -> Page[RemoteBlueprint]: # pyright: ignore[reportInvalidTypeForm]
    """
    Query for all available Blueprints for all Series. Blacklisted
    Blueprints are excluded from the return.

    - order_by: How to order the returned Blueprints.
    - include_blacklisted: Whether to include Blacklisted Blueprints in
    the return.
    - include_imported: Whether to include previously imported
    Blueprints in the return.
    - include_missing_series: Whether to include Blueprints for Series
    that are not present in the database.
    """

    def include(blueprint: Blueprint) -> bool:
        """
        Determine whether to include the given Blueprint.

        Args:
            blueprint: Blueprint being evaluated.

        Returns:
            Whether the Blueprint should be included in the return.
        """

        # Exclude if blacklisted (and filtering)
        if (not include_blacklisted
            and blueprint.id in preferences.blacklisted_blueprints):
            return False

        # Exclude if previously imported (and filtering)
        if (not include_imported
            and blueprint.id in preferences.imported_blueprints):
            return False

        # Exclude if Series is not present
        if not include_missing_series:
            # Determine if this Series already exists
            series_info = blueprint.series.as_series_info
            series = db.query(models.series.Series)\
                .filter(series_info.filter_conditions(models.series.Series))\
                .first()

            # Series not present, do not include
            if series is None:
                return False

        return True

    # Get list of Blueprints
    if order_by == 'date':
        sequence = blueprint_db.query(Blueprint)\
            .order_by(Blueprint.created.desc())
    else:
        sequence = blueprint_db.query(Blueprint)\
            .join(BlueprintSeries,
                  Blueprint.series_id==BlueprintSeries.id, isouter=True)\
            .order_by(BlueprintSeries.sort_name)

    return paginate_sequence([
        blueprint for blueprint in sequence.all() if include(blueprint)
    ])


@blueprint_router.get('/query/series/{series_id}')
def query_series_blueprints_(
        series_id: int,
        db: Session = Depends(get_database),
        blueprint_db: Session = Depends(get_blueprint_database),
    ) -> list[RemoteBlueprint]:
    """
    Search for any Blueprints for the given Series.

    - series_id: ID of the Series to search for Blueprints of.
    """

    return query_series_blueprints(
        blueprint_db,
        get_series(db, series_id, raise_exc=True).as_series_info
    )


@blueprint_router.get('/query/series')
def query_blueprints_by_info(
        name: str = Query(..., min_length=1),
        year: int = Query(..., min=1900),
        imdb_id: Optional[str] = Query(default=None),
        tmdb_id: Optional[int] = Query(default=None),
        tvdb_id: Optional[int] = Query(default=None),
        blueprint_db: Session = Depends(get_blueprint_database),
    ) -> list[RemoteBlueprint]:
    """
    Search for any Blueprints for the given Series not yet added to TCM.

    - name: Name of the Series to look up Blueprints for.
    - year: Year of the Series to look up Blueprints for.
    """

    series_info = SeriesInfo(
        name=name, year=year,
        imdb_id=imdb_id, tmdb_id=tmdb_id, tvdb_id=tvdb_id,
    )

    return query_series_blueprints(blueprint_db, series_info)


@blueprint_router.post('/import/blueprint/{blueprint_id}', status_code=201)
def import_blueprint_and_series(
        background_tasks: BackgroundTasks,
        request: Request,
        blueprint_id: int,
        db: Session = Depends(get_database),
        blueprint_db: Session = Depends(get_blueprint_database),
    ) -> Series:
    """
    Import the given Blueprint - creating the associated Series if it
    does not already exist.

    - blueprint_id: ID of the Blueprint to import.
    """

    # Get contextual logger
    log = request.state.log

    # Get this Blueprint, raise 404 if DNE
    blueprint = get_blueprint(blueprint_db, blueprint_id, raise_exc=True)

    # Query for this Blueprint's Series
    series_info = blueprint.series.as_series_info
    series = db.query(models.series.Series)\
        .filter(series_info.filter_conditions(models.series.Series))\
        .first()

    # Series does not exist, create and add to database
    if not series:
        log.debug(f'Blueprint Series {blueprint.series.as_series_info} not '
                  f'found - adding to database')
        series = add_series(
            blueprint.series.as_new_series, background_tasks, db, log=log,
        )

    # Import Blueprint
    background_tasks.add_task(
        import_blueprint,
        db, series, blueprint, log=log
    )

    return series


@blueprint_router.put('/import/series/{series_id}/blueprint/{blueprint_id}')
def import_series_blueprint_by_id(
        request: Request,
        series_id: int,
        blueprint_id: int,
        db: Session = Depends(get_database),
        blueprint_db: Session = Depends(get_blueprint_database),
    ) -> None:
    """
    Import the Blueprint with the given ID to the given Series.

    - series_id: ID of the Series to import into.
    - blueprint_id: ID of the Blueprint to import.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get Blueprint with this ID, raise 404 if DNE
    blueprint = get_blueprint(blueprint_db, blueprint_id, raise_exc=True)

    # Import Blueprint
    import_blueprint(db, series, blueprint, log=request.state.log)


@blueprint_router.put('/import/series/{series_id}')
def import_series_blueprint_(
        request: Request,
        series_id: int,
        blueprint: RemoteBlueprint = Body(...),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Import the given Blueprint object into the given Series.

    - series_id: ID of the Series to import the given Blueprint into.
    - blueprint: Blueprint object to import.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Import Blueprint
    import_blueprint(db, series, blueprint, log=request.state.log)


@blueprint_router.get('/sets/set/{set_id}')
def get_blueprint_set_by_id(
        set_id: int,
        blueprint_db: Session = Depends(get_blueprint_database),
    ) -> RemoteBlueprintSet:
    """
    Get the BlueprintSet with the given ID.

    - set_id: ID of the Set to get the details of.
    """

    return get_blueprint_set(blueprint_db, set_id, raise_exc=True)


@blueprint_router.get('/sets/blueprint/{blueprint_id}')
def get_blueprint_set_by_blueprint_id(
        blueprint_id: int,
        blueprint_db: Session = Depends(get_blueprint_database),
    ) -> list[RemoteBlueprintSet]:
    """
    Get the BlueprintSet for the Blueprint with the given ID.

    - blueprint_id: ID of the Blueprint to get the details of.
    """

    return get_blueprint(blueprint_db, blueprint_id, raise_exc=True).sets


@blueprint_router.get('/sets/series/{series_id}')
def get_blueprint_sets_for_series(
        series_id: int,
        db: Session = Depends(get_database),
        blueprint_db: Session = Depends(get_blueprint_database),
    ) -> list[RemoteBlueprintSet]:
    """
    Get all BlueprintSets which contain a Blueprint for the Series with
    the given ID.

    - series_id: ID of the Series whose Sets are being queried.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return list(set(
        set
        for blueprint in
        query_series_blueprints(blueprint_db,series.as_series_info)
        for set in blueprint.sets
    ))
