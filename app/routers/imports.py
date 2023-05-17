from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from pydantic.error_wrappers import ValidationError

from app.dependencies import (
    get_database, get_preferences, get_emby_interface,
    get_imagemagick_interface, get_jellyfin_interface, get_plex_interface,
    get_sonarr_interface, get_tmdb_interface
)
from app.internal.imports import (
    parse_emby, parse_fonts, parse_jellyfin, parse_plex, parse_preferences, parse_raw_yaml, parse_series, parse_sonarr, parse_syncs, parse_templates, parse_tmdb
)
from app.internal.series import download_series_poster, set_series_database_ids
from app.internal.sources import download_series_logo
import app.models as models
from app.schemas.font import NamedFont
from app.schemas.imports import ImportSeriesYaml, ImportYaml
from app.schemas.preferences import Preferences
from app.schemas.series import Series, Template
from app.schemas.sync import Sync

from modules.Debug import log


import_router = APIRouter(
    prefix='/import',
    tags=['Import'],
)


@import_router.post('/preferences/options', status_code=201)
def import_preferences_yaml(
        import_yaml: ImportYaml = Body(...),
        preferences = Depends(get_preferences)) -> Preferences:
    """
    Import the global options from the preferences defined in the given
    YAML. This imports the options and imagemagick sections.

    - import_yaml: The YAML string to parse.
    """

    # Parse raw YAML into dictionary
    yaml_dict = parse_raw_yaml(import_yaml.yaml)
    if len(yaml_dict) == 0:
        return preferences
    
    # Modify the preferences  from the YAML dictionary
    try:
        return parse_preferences(preferences, yaml_dict)
    except ValidationError as e:
        log.exception(f'Invalid YAML', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {e}'
        )


@import_router.post('/preferences/{connection}', status_code=201)
def import_connection_yaml(
        connection: Literal['emby', 'jellyfin', 'plex', 'sonarr', 'tmdb'],
        import_yaml: ImportYaml = Body(...),
        preferences = Depends(get_preferences)) -> Preferences:
    """
    Import the connection preferences defined in the given YAML. This
    does NOT import any Sync settings.

    - connection: Which connection is being modified.
    - import_yaml: The YAML string to parse.
    """

    # Parse raw YAML into dictionary
    yaml_dict = parse_raw_yaml(import_yaml.yaml)
    if len(yaml_dict) == 0:
        return preferences

    parse_function = {
        'emby': parse_emby,
        'jellyfin': parse_jellyfin,
        'plex': parse_plex,
        'tmdb': parse_tmdb,
        'sonarr': parse_sonarr,
    }[connection]

    try:
        return parse_function(preferences, yaml_dict)
    except ValidationError as e:
        log.exception(f'Invalid YAML', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {e}'
        )
    

@import_router.post('/sync', status_code=201)
def import_sync_yaml(
        import_yaml: ImportYaml = Body(...),
        db = Depends(get_database)) -> list[Sync]:
    """
    Import all Syncs defined in the given YAML.

    - import_yaml: The YAML string to parse.
    """

    # Parse raw YAML into dictionary
    yaml_dict = parse_raw_yaml(import_yaml.yaml)
    if len(yaml_dict) == 0:
        return []
    
    # Create New*Sync objects from the YAML dictionary
    try:
        new_syncs = parse_syncs(db, yaml_dict)
    except ValidationError as e:
        log.exception(f'Invalid YAML', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {e}'
        )

    # Add each defined Sync to the database
    all_syncs = []
    for new_sync in new_syncs:
        sync = models.sync.Sync(**new_sync.dict())
        db.add(sync)
        log.info(f'{sync.log_str} imported to Database')
        all_syncs.append(sync)
    db.commit()

    return all_syncs


@import_router.post('/fonts', status_code=201)
def import_fonts_yaml(
        import_yaml: ImportYaml = Body(...),
        db = Depends(get_database)) -> list[NamedFont]:
    """
    Import all Fonts defined in the given YAML. This does NOT import any
    custom font files - these will need to be added separately.

    - import_yaml: The YAML string to parse.
    import.
    """

    # Parse raw YAML into dictionary
    yaml_dict = parse_raw_yaml(import_yaml.yaml)
    if len(yaml_dict) == 0:
        return []
    
    # Create NewNamedFont objects from the YAML dictionary
    try:
        new_fonts = parse_fonts(yaml_dict)
    except ValidationError as e:
        log.exception(f'Invalid YAML', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {e}'
        )

    # Add each defined Font to the database
    all_fonts = []
    for new_font in new_fonts:
        font = models.font.Font(**new_font.dict())
        db.add(font)
        log.info(f'{font.log_str} imported to Database')
        all_fonts.append(font)
    db.commit()

    return all_fonts


@import_router.post('/templates', status_code=201)
def import_template_yaml(
        import_yaml: ImportYaml = Body(...),
        db = Depends(get_database),
        preferences = Depends(get_preferences)) -> list[Template]:
    """
    Import all Templates defined in the given YAML.

    - import_yaml: The YAML string to parse.
    """

    # Parse raw YAML into dictionary
    yaml_dict = parse_raw_yaml(import_yaml.yaml)
    if len(yaml_dict) == 0:
        return []

    # Create NewTemplate objects from the YAML dictionary
    try:
        new_templates = parse_templates(db, preferences, yaml_dict)
    except ValidationError as e:
        log.exception(f'Invalid YAML', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {e}'
        )

    # Add each defined Template to the database
    all_templates = []
    for new_template in new_templates:
        template = models.template.Template(**new_template.dict())
        db.add(template)
        log.info(f'{template.log_str} imported to Database')
        all_templates.append(template)
    db.commit()

    return all_templates


@import_router.post('/series', status_code=201)
def import_series_yaml(
        background_tasks: BackgroundTasks,
        import_yaml: ImportSeriesYaml = Body(...),
        db = Depends(get_database),
        preferences = Depends(get_preferences),
        emby_interface = Depends(get_emby_interface),
        imagemagick_interface = Depends(get_imagemagick_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface),
        sonarr_interface = Depends(get_sonarr_interface),
        tmdb_interface = Depends(get_tmdb_interface)) -> list[Series]:
    """
    Import all Series defined in the given YAML.

    - import_yaml: The YAML string and default library name to parse.
    """

    # Parse raw YAML into dictionary
    yaml_dict = parse_raw_yaml(import_yaml.yaml)
    if len(yaml_dict) == 0:
        return []

    # Create NewSeries objects from the YAML dictionary
    try:
        new_series = parse_series(
            db, preferences, yaml_dict, import_yaml.default_library,
        )
    except ValidationError as e:
        log.exception(f'Invalid YAML', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {e}'
        )

    # Add each defined Series to the database
    all_series = []
    for new_series in new_series:
        # Add to batabase
        series = models.series.Series(**new_series.dict())
        db.add(series)
        log.info(f'{series.log_str} imported to Database')

        # Add background tasks for setting ID's, downloading poster and logo
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
        all_series.append(series)
    db.commit()

    return all_series