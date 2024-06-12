from logging import Logger
from pathlib import Path
from shutil import copyfile
from typing import Any, Literal, Optional

from fastapi import (
    APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Request,
    UploadFile
)
from pydantic.error_wrappers import ValidationError
from sqlalchemy.orm import Session
from yaml import safe_load
from yaml.parser import ParserError

from app.database.query import get_all_templates, get_interface, get_series
from app.dependencies import get_database, get_preferences
from app.internal.auth import get_current_user
from app.internal.imports import (
    import_card_content, import_card_files, import_cards, parse_emby,
    parse_fonts, parse_jellyfin, parse_plex, parse_preferences, parse_raw_yaml,
    parse_series, parse_sonarr, parse_syncs, parse_templates, parse_tmdb
)
from app.internal.series import download_series_poster, load_series_title_cards, set_series_database_ids
from app.internal.sources import download_series_logo
from app import models
from app.models.episode import Episode
from app.schemas.font import NamedFont
from app.schemas.imports import ImportCardDirectory, ImportYaml, MultiCardImport
from app.schemas.preferences import Preferences
from app.schemas.series import Series, Template
from app.schemas.sync import Sync
from modules.WebInterface import WebInterface


import_router = APIRouter(
    prefix='/import',
    tags=['Import'],
    dependencies=[Depends(get_current_user)],
)


@import_router.post('/preferences/options')
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


@import_router.post('/preferences/connection/{connection}')
def import_connection_yaml(
        request: Request,
        connection: Literal['all', 'emby', 'jellyfin', 'plex', 'sonarr', 'tmdb'],
        import_yaml: ImportYaml = Body(...),
        db: Session = Depends(get_database),
    ) -> None:
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
        return None

    try:
        if connection in ('all', 'emby'):
            parse_emby(db, yaml_dict, log=log)
        if connection in ('all', 'jellyfin'):
            parse_jellyfin(db, yaml_dict, log=log)
        if connection in ('all', 'plex'):
            parse_plex(db, yaml_dict, log=log)
        if connection in ('all', 'sonarr'):
            parse_sonarr(db, yaml_dict, log=log)
        if connection in ('all', 'tmdb'):
            parse_tmdb(db, yaml_dict, log=log)
    except ValidationError as exc:
        log.exception(f'Invalid YAML', exc)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {exc}'
        ) from exc


@import_router.post('/preferences/sync')
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
        log.info(f'{sync} imported to Database')
        all_syncs.append(sync)

        # Assign Templates
        sync.assign_templates(templates, log=log)
        db.commit()

    return all_syncs


@import_router.post('/fonts')
def import_fonts_yaml(
        request: Request,
        import_yaml: ImportYaml = Body(...),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
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
    for new_font, font_file in new_fonts:
        font = models.font.Font(**new_font.dict())
        db.add(font)
        db.commit()
        log.info(f'{font} imported to Database')
        all_fonts.append(font)

        # If there is a Font file, copy into asset directory
        if font_file is not None:
            if font_file.exists():
                font_directory = preferences.asset_directory / 'fonts'
                file_path = font_directory / str(font.id) / font_file.name
                copyfile(font_file, file_path)

                # Update object and database
                font.file_name = file_path.name
                db.commit()
            else:
                log.error(f'Font File "{font_file.resolve()}" does not exist')

    return all_fonts


@import_router.post('/templates')
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
        log.info(f'{template} imported to Database')
        all_templates.append(template)
    db.commit()

    return all_templates


@import_router.post('/series')
def import_series_yaml(
        background_tasks: BackgroundTasks,
        request: Request,
        import_yaml: ImportYaml = Body(...),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
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
        new_series = parse_series(db, preferences, yaml_dict, log=log)
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
        log.info(f'{series} imported to Database')

        # Assign Templates
        series.assign_templates(templates, log=log)
        db.commit()

        # Add background tasks for setting ID's, downloading poster and logo
        # Add background tasks to set ID's, download poster and logo
        background_tasks.add_task(
            # Function
            set_series_database_ids,
            # Arguments
            series, db, log=log,
        )
        background_tasks.add_task(
            # Function
            download_series_poster,
            # Arguments
            db, series, log=log,
        )
        background_tasks.add_task(
            # Function
            download_series_logo,
            # Arguments
            series, log=log,
        )
        all_series.append(series)
    db.commit()

    return all_series

@import_router.post('/series/{series_id}/cards', deprecated=True)
def import_cards_for_series() -> None:
    return None

@import_router.post('/series/{series_id}/cards/files',
                    tags=['Title Cards', 'Series'])
async def import_card_files_for_series(
        request: Request,
        series_id: int,
        cards: list[UploadFile] = [],
        force_reload: bool = Query(default=True),
        textless: bool = Query(default=True),
        library_name: Optional[str] = Query(default=None),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Import any existing Title Cards for the given Series. This finds
    card files by filename, and makes the assumption that each file
    exactly matches the Episode's currently specified config.

    - series_id: ID of the Series whose cards are being imported.
    - cards: List of uploaded Card files to import.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    if (card_files := [(card.filename, await card.read()) for card in cards]):
        import_card_content(
            db, series, card_files, series.get_library(library_name),
            force_reload=force_reload, as_textless=textless,
            log=request.state.log
        )


@import_router.post('/series/{series_id}/cards/mediux')
async def import_mediux_yaml_for_series(
        request: Request,
        series_id: int,
        yaml_str: str = Body(..., alias='yaml'),
        import_poster: bool = Query(default=False),
        import_backdrop: bool = Query(default=False),
        import_season_posters: bool = Query(default=True),
        force_reload: bool = Query(default=True),
        textless: bool = Query(default=True),
        library_names: list[str] = Query(default=[]),
        db: Session = Depends(get_database),
    ) -> None:
    """
    """

    # Get contextual logger
    log: Logger = request.state.log

    # Parse YAML into dictionary; raise 422 if invalid
    try:
        full_yaml: dict[int, dict[str, Any]] = safe_load(yaml_str)
    except ParserError:
        raise HTTPException(
            status_code=422,
            detail='Invalid YAML',
        )

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    images: list[Path] = []
    def _download_image(url: str, /) -> Optional[Path]:
        """
        Download the image at the given URL.

        Args:
            url: URL of the image to download

        Returns:
            Path to the downloaded image. None if the download failed.
        """

        filename = WebInterface.get_random_filename(
            WebInterface._TEMP_DIR / f'temp.{url[:5]}', 'jpg'
        )
        if not WebInterface.download_image(url, filename, log=log):
            log.error(f'Error downloading image {url}')
            return None

        images.append(filename)
        return filename

    # Download all indicated files
    cards: list[tuple[int, int, Path]] = []
    for _, yaml in full_yaml.items():
        # if import_poster and (url := yaml.get('url_poster')):
        #     image = _download_image(url)
        # if import_backdrop and (url := yaml.get('url_background')):
        #     image = _download_image(url)
        for season_number, season_yaml in yaml.get('seasons', {}).items():
            # if import_season_posters and (url := yaml.get('url_poster')):
            #     image = _download_image(url)
            for episode_number, episode_yaml in \
                    season_yaml.get('episodes', {}).items():
                # Skip download if there is no matching Episode
                episode = db.query(Episode)\
                    .filter_by(series_id=series_id,
                               season_number=season_number,
                               episode_number=episode_number)\
                    .first()
                if not episode:
                    log.debug(f'No associated Episode for S{season_number:02}'
                              f'E{episode_number:02}')
                    continue

                # Episode exists, download and add to card list
                if (card := _download_image(episode_yaml['url_poster'])):
                    cards.append((episode, card))

    # Import into all specified libraries
    log.debug(f'Identified {len(cards)} Cards to import')
    for library_name in library_names:
        library = series.get_library(library_name)
        import_card_files(
            db, series, cards, library,
            force_reload=force_reload, as_textless=textless, log=log
        )

        # Load cards into library
        load_series_title_cards(
            series, library['name'], library['interface_id'], db,
            get_interface(library['interface_id'], raise_exc=True),
            force_reload=force_reload,
        )
    else:
        import_card_files(
            db, series, cards, library=None,
            force_reload=force_reload, as_textless=textless, log=log
        )

    # Delete any downloaded images after they've been uploaded
    for image in images:
        image.unlink(missing_ok=True)
        log.trace(f'Deleted temporary image ({image})')


@import_router.post('/series/{series_id}/cards/directory',
                    tags=['Title Cards', 'Series'])
def import_card_directory_for_series(
        request: Request,
        series_id: int,
        card_directory: ImportCardDirectory = Body(...),
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
        db, series, card_directory.directory,
        card_directory.image_extension, card_directory.force_reload,
        log=request.state.log,
    )


@import_router.post('/series/cards', tags=['Title Cards', 'Series'])
def import_cards_for_multiple_series(
        request: Request,
        card_import: MultiCardImport = Body(...),
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
            db, series, None, card_import.image_extension,
            card_import.force_reload, log=request.state.log,
        )
