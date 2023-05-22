from pathlib import Path
from re import match, IGNORECASE
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from pydantic.error_wrappers import ValidationError

from app.database.query import get_all_templates, get_series
from app.dependencies import (
    get_database, get_preferences, get_emby_interface,
    get_imagemagick_interface, get_jellyfin_interface, get_plex_interface,
    get_sonarr_interface, get_tmdb_interface
)
from app.internal.cards import add_card_to_database, resolve_card_settings
from app.internal.imports import (
    parse_emby, parse_fonts, parse_jellyfin, parse_plex, parse_preferences, parse_raw_yaml, parse_series, parse_sonarr, parse_syncs, parse_templates, parse_tmdb
)
from app.internal.series import download_series_poster, set_series_database_ids
from app.internal.sources import download_series_logo
import app.models as models
from app.schemas.card import CardActions, NewTitleCard
from app.schemas.font import NamedFont
from app.schemas.imports import ImportCardDirectory, ImportSeriesYaml, ImportYaml
from app.schemas.preferences import Preferences
from app.schemas.series import Series, Template
from app.schemas.sync import Sync

from modules.Debug import log


import_router = APIRouter(
    prefix='/import',
    tags=['Import'],
)


@import_router.post('/preferences/options', status_code=201)
def import_global_options_yaml(
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


@import_router.post('/preferences/connection/{connection}', status_code=201)
def import_connection_yaml(
        connection: Literal['all', 'emby', 'jellyfin', 'plex', 'sonarr', 'tmdb'],
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
    
    def _parse_all(*args, **kwargs):
        parse_emby(*args, **kwargs)
        parse_jellyfin(*args, **kwargs)
        parse_plex(*args, **kwargs)
        parse_plex(*args, **kwargs)
        parse_sonarr(*args, **kwargs)

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
        return parse_function(preferences, yaml_dict)
    except ValidationError as e:
        log.exception(f'Invalid YAML', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {e}'
        )
    

@import_router.post('/preferences/sync', status_code=201)
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
        new_sync_dict = new_sync.dict()
        templates = get_all_templates(db, new_sync_dict)
        sync = models.sync.Sync(**new_sync_dict, templates=templates)
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
        new_series_dict = new_series.dict()
        templates = get_all_templates(db, new_series_dict)
        series = models.series.Series(**new_series_dict, templates=templates)
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
            preferences, emby_interface, imagemagick_interface,
            jellyfin_interface, tmdb_interface, series
        )
        all_series.append(series)
    db.commit()

    return all_series


@import_router.post('/series/{series_id}/cards', status_code=200, tags=['Cards', 'Series'])
def import_cards_for_series(
        series_id: int,
        card_directory: ImportCardDirectory = Body(...),
        preferences = Depends(get_preferences),
        db = Depends(get_database)) -> CardActions:
    """
    Import any existing Title Cards for the given Series. This finds
    card files by filename, and makes the assumption that each file
    exactly matches the Episode's currently specified config.

    - series_id: ID of the Series whose cards are being imported.
    - card_directory: Directory details to parse for cards to import.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # If explicit directory was not provided, use Series default
    if card_directory.directory is None:
        card_directory.directory = series.card_directory

    # Glob directory for images to import
    all_images = list(
        card_directory.directory.glob(f'**/*{card_directory.image_extension}')
    )

    # No images to import, return empty actions
    if len(all_images) == 0:
        return []

    # For each image, identify associated Episode
    actions = CardActions()
    for image in all_images:
        if (groups := match(r'.*s(\d+).*e(\d+)', image.name, IGNORECASE)):
            season_number, episode_number = map(int, groups.groups())
        else:
            log.warning(f'Cannot identify index of {image.resolve()} - skipping')
            actions.invalid += 1
            continue

        # Find associated Episode
        episode = db.query(models.episode.Episode).filter(
            models.episode.Episode.series_id==series_id,
            models.episode.Episode.season_number==season_number,
            models.episode.Episode.episode_number==episode_number,
        ).first()

        # No associated Episode, skip
        if episode is None:
            log.warning(f'{series.log_str} No associated Episode for {image.resolve()} - skipping')
            actions.invalid += 1
            continue

        # Episode has an existing Card, skip if not forced
        if episode.card and not card_directory.force_reload:
            log.info(f'{series.log_str} {episode.log_str} has an associated Card - skipping')
            actions.existing += 1
            continue
        # Episode has card, delete if reloading
        elif episode.card and card_directory.force_reload:
            for card in episode.card:
                log.debug(f'{card.log_str} deleting record')
                db.query(models.card.Card).filter_by(id=card.id).delete()
                log.info(f'{series.log_str} {episode.log_str} has associated Card - reloading')
                actions.deleted += 1

        # Get finalized Card settings for this Episode, override card file
        card_settings = resolve_card_settings(preferences, episode)

        # If a list of CardActions were returned, update actions and skip
        if isinstance(card_settings, list):
            for action in card_settings:
                setattr(actions, action, getattr(actions, action)+1)
            continue

        # Card is valid, create and add to Database
        card_settings['card_file'] = image
        title_card = NewTitleCard(
            **card_settings,
            series_id=series.id,
            episode_id=episode.id,
        )

        card = add_card_to_database(db, title_card, card_settings['card_file'])
        log.debug(f'{series.log_str} {episode.log_str} Imported {image.resolve()}')
        actions.imported += 1

    return actions