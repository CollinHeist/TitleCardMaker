from typing import Literal, Optional

from fastapi import (
    APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request
)
from pydantic.error_wrappers import ValidationError
from sqlalchemy.orm import Session

from app.database.query import get_all_templates, get_series
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.auth import get_current_user
from app.internal.imports import (
    import_cards, parse_emby, parse_fonts, parse_jellyfin, parse_plex,
    parse_preferences, parse_raw_yaml, parse_series, parse_sonarr, parse_syncs,
    parse_templates, parse_tmdb
)
from app.internal.series import download_series_poster, set_series_database_ids
from app.internal.sources import download_series_logo
from app import models
from app.schemas.font import NamedFont
from app.schemas.imports import (
    ImportCardDirectory, ImportSeriesYaml, ImportYaml, MultiCardImport
)
from app.schemas.preferences import Preferences
from app.schemas.series import Series, Template
from app.schemas.sync import Sync


import_router = APIRouter(
    prefix='/import',
    tags=['Import'],
    dependencies=[Depends(get_current_user)],
)


@import_router.post('/preferences/options', status_code=201)
def import_global_options_yaml(
        request: Request,
        import_yaml: ImportYaml = Body(...),
        preferences: Preferences = Depends(get_preferences),
    ) -> Preferences:
    """
    Import the global options from the preferences defined in the given
    YAML. This imports the options and imagemagick sections.

    - import_yaml: The YAML string to parse.
    """

    # Get contextual logger
    log = request.state.log

    # Parse raw YAML into dictionary
    yaml_dict = parse_raw_yaml(import_yaml.yaml)
    if len(yaml_dict) == 0:
        return preferences

    # Modify the preferences  from the YAML dictionary
    try:
        return parse_preferences(preferences, yaml_dict, log=log)
    except ValidationError as e:
        log.exception(f'Invalid YAML', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {e}'
        ) from e


@import_router.post('/preferences/connection/{connection}', status_code=201)
def import_connection_yaml(
        request: Request,
        connection: Literal['all', 'emby', 'jellyfin', 'plex', 'sonarr', 'tmdb'],
        import_yaml: ImportYaml = Body(...),
        preferences: Preferences = Depends(get_preferences)
    ) -> Preferences:
    """
    Import the connection preferences defined in the given YAML. This
    does NOT import any Sync settings.

    - connection: Which connection is being modified.
    - import_yaml: The YAML string to parse.
    """

    # Get contextual logger
    log = request.state.log

    # Parse raw YAML into dictionary
    yaml_dict = parse_raw_yaml(import_yaml.yaml)
    if len(yaml_dict) == 0:
        return preferences

    def _parse_all(*args, **kwargs):
        parse_emby(*args, **kwargs)
        parse_jellyfin(*args, **kwargs)
        parse_plex(*args, **kwargs)
        parse_sonarr(*args, **kwargs)
        parse_tmdb(*args, **kwargs)

        return preferences

    parse_function = {
        'all': _parse_all,
        'emby': parse_emby,
        'jellyfin': parse_jellyfin,
        'plex': parse_plex,
        'tmdb': parse_tmdb,
        'sonarr': parse_sonarr,
    }[connection]

    try:
        return parse_function(preferences, yaml_dict, log=log)
    except ValidationError as e:
        log.exception(f'Invalid YAML', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {e}'
        ) from e


@import_router.post('/preferences/sync', status_code=201)
def import_sync_yaml(
        request: Request,
        import_yaml: ImportYaml = Body(...),
        db: Session = Depends(get_database)
    ) -> list[Sync]:
    """
    Import all Syncs defined in the given YAML.

    - import_yaml: The YAML string to parse.
    """

    # Get contextual logger
    log = request.state.log

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
        ) from e

    # Add each defined Sync to the database
    all_syncs = []
    for new_sync in new_syncs:
        new_sync_dict = new_sync.dict()
        templates = get_all_templates(db, new_sync_dict)
        sync = models.sync.Sync(**new_sync_dict)
        db.add(sync)
        db.commit()
        log.info(f'{sync.log_str} imported to Database')
        all_syncs.append(sync)

        # Assign Templates
        sync.assign_templates(templates, log=log)
        db.commit()

    return all_syncs


@import_router.post('/fonts', status_code=201)
def import_fonts_yaml(
        request: Request,
        import_yaml: ImportYaml = Body(...),
        db: Session = Depends(get_database)
    ) -> list[NamedFont]:
    """
    Import all Fonts defined in the given YAML. This does NOT import any
    custom font files - these will need to be added separately.

    - import_yaml: The YAML string to parse.
    import.
    """

    # Get contextual logger
    log = request.state.log

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
        ) from e

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
        request: Request,
        import_yaml: ImportYaml = Body(...),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences)
    ) -> list[Template]:
    """
    Import all Templates defined in the given YAML.

    - import_yaml: The YAML string to parse.
    """

    # Get contextual logger
    log = request.state.log

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
        ) from e

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
        request: Request,
        import_yaml: ImportSeriesYaml = Body(...),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        imagemagick_interface: Optional[ImageMagickInterface] = Depends(get_imagemagick_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
        sonarr_interface: Optional[SonarrInterface] = Depends(get_sonarr_interface),
        tmdb_interface: Optional[TMDbInterface] = Depends(get_tmdb_interface)
    ) -> list[Series]:
    """
    Import all Series defined in the given YAML.

    - import_yaml: The YAML string and default library name to parse.
    """

    # Get contextual logger
    log = request.state.log

    # Parse raw YAML into dictionary
    yaml_dict = parse_raw_yaml(import_yaml.yaml)
    if len(yaml_dict) == 0:
        return []

    # Create NewSeries objects from the YAML dictionary
    try:
        new_series = parse_series(
            db, preferences, yaml_dict, import_yaml.default_library, log=log,
        )
    except ValidationError as e:
        log.exception(f'Invalid YAML', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {e}'
        ) from e

    # Add each defined Series to the database
    all_series = []
    for series in new_series:
        # Add to batabase
        new_series_dict = series.dict()
        templates = get_all_templates(db, new_series_dict)
        series = models.series.Series(**new_series_dict)
        db.add(series)
        db.commit()
        log.info(f'{series.log_str} imported to Database')

        # Assign Templates
        series.assign_templates(templates, log=log)
        db.commit()

        # Add background tasks for setting ID's, downloading poster and logo
        # Add background tasks to set ID's, download poster and logo
        background_tasks.add_task(
            # Function
            set_series_database_ids,
            # Arguments
            series, db, emby_interface, jellyfin_interface, plex_interface,
            sonarr_interface, tmdb_interface, log=log,
        )
        background_tasks.add_task(
            # Function
            download_series_poster,
            # Arguments
            db, preferences, series, emby_interface, imagemagick_interface,
            jellyfin_interface, plex_interface, tmdb_interface, log=log,
        )
        background_tasks.add_task(
            # Function
            download_series_logo,
            # Arguments
            preferences, emby_interface, imagemagick_interface,
            jellyfin_interface, tmdb_interface, series, log=log,
        )
        all_series.append(series)
    db.commit()

    return all_series


@import_router.post('/series/{series_id}/cards', status_code=200,
                    tags=['Title Cards', 'Series'])
def import_cards_for_series(
        request: Request,
        series_id: int,
        card_directory: ImportCardDirectory = Body(...),
        preferences: Preferences = Depends(get_preferences),
        db: Session = Depends(get_database)
    ) -> None:
    """
    Import any existing Title Cards for the given Series. This finds
    card files by filename, and makes the assumption that each file
    exactly matches the Episode's currently specified config.

    - series_id: ID of the Series whose cards are being imported.
    - card_directory: Directory details to parse for cards to import.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    import_cards(
        db, preferences, series, card_directory.directory,
        card_directory.image_extension, card_directory.force_reload,
        log=request.state.log,
    )


@import_router.post('/series/cards', status_code=200,
                    tags=['Title Cards', 'Series'])
def import_cards_for_multiple_series(
        request: Request,
        card_import: MultiCardImport = Body(...),
        preferences: Preferences = Depends(get_preferences),
        db: Session = Depends(get_database)
    ) -> None:
    """
    Import any existing Title Cards for all the given Series. This finds
    card files by filename, and makes the assumption that each file
    exactly matches the Episode's currently specified config.

    - card_import: Import details to parse for all Cards to import.
    """

    # Import Card for each identified Series
    for series_id in card_import.series_ids:
        # Get this Series, raise 404 if DNE
        series = get_series(db, series_id, raise_exc=True)

        # Import Cards for this Series
        import_cards(
            db, preferences, series, None, card_import.image_extension,
            card_import.force_reload,
            log=request.state.log,
        )
