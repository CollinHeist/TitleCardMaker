from logging import Logger
from re import compile as re_compile, IGNORECASE

from fastapi import HTTPException
from requests import get, JSONDecodeError
from sqlalchemy.orm import Session

from app.models.episode import Episode
from app.models.font import Font
from app.models.preferences import Preferences
from app.models.series import Series
from app.models.template import Template
from app.schemas.blueprint import Blueprint, RemoteBlueprint
from app.schemas.font import NewNamedFont
from app.schemas.series import NewTemplate, UpdateSeries

from modules.Debug import log
from modules.TieredSettings import TieredSettings


EPISODE_REGEX = re_compile(
    r'^s(?P<season_number>\d+)e(?P<episode_number>\d+)$',
    IGNORECASE
)

BLUEPRINT_URL = (
    'https://github.com/CollinHeist/TitleCardMaker-Blueprints/'
    'raw/master/blueprints'
)


def generate_series_blueprint(
        series: Series,
        include_global_defaults: bool,
        include_episode_overrides: bool,
        preferences: Preferences
    ) -> Blueprint:
    """
    Generate the Blueprint for the given Series. This Blueprint can be
    imported to completely recreate a Series' (and all associated
    Episodes') configuration. 

    Args:
        series: Series to generate the Blueprint of.
        include_global_defaults: Whether to write global settings if the
            Series has no corresponding override, primarily for the
            card type.
        include_episode_overrides: Whether to include Episode-level
            overrides in the exported Blueprint. If True, then any
            Episode Font and Template assignments are also included.
        preferences: Global default Preferences.

    Returns:
        Blueprint that can be used to recreate the Series configuration.
    """

    # Get all Episodes if indicates
    episodes: list[Episode]=series.episodes if include_episode_overrides else []

    # Get all Templates
    templates = list(set(
        template for obj in [series] + episodes for template in obj.templates
    ))

    # Get all associated Fonts
    fonts: list[Font] = list(set(
        obj.font for obj in [series] + episodes + templates if obj.font
    ))

    # Create exported JSON object
    export_obj = {'series': {}, 'episodes': {}, 'templates': [], 'fonts': []}

    # Append Series config
    if include_global_defaults:
        export_obj['series'] =TieredSettings.new_settings(
            preferences.export_properties,
            series.export_properties,
        )
    else:
        export_obj['series'] = series.export_properties
    export_obj['series'] =  TieredSettings.filter(export_obj['series'])

    # Add Episode configs
    for episode in episodes:
        # Skip Episodes with no customization
        key = f's{episode.season_number}e{episode.episode_number}'
        episode_properties =  TieredSettings.filter(episode.export_properties)
        if not episode_properties and not episode.templates:
            continue

        # Assign Template indices
        export_obj['episodes'][key] = episode_properties
        export_obj['episodes'][key]['template_ids'] = [
            templates.index(template) for template in episode.templates
        ]
        # Assign Font index
        if episode.font:
            export_obj['episodes'][key]['font_id'] = fonts.index(episode.font)

    # Assign correct Template indices to Series
    export_obj['series']['template_ids'] = [
        templates.index(template) for template in series.templates
    ]

    # Assign correct Font index to Series
    if series.font:
        export_obj['series']['font_id'] = fonts.index(series.font)

    # Add list of exported Templates
    export_obj['templates'] = [
        {key: value for key, value in template.export_properties.items() if value}
        for template in templates
    ]

    # Add list of exported Fonts
    export_obj['fonts'] = [
        {key: value for key, value in font.export_properties.items() if value}
        for font in fonts
    ]

    # Add Font IDs to Templates if indicated
    for index, template in enumerate(templates):
        if template.font:
            export_obj['templates'][index]['font_id'] = fonts.index(template.font)

    return export_obj


def query_series_blueprints(
        series: Series,
        *,
        log: Logger = log,
    ) -> list[RemoteBlueprint]:
    """
    Query for all RemoteBlueprints on GitHub for the given Series.

    Args:
        series: Series whose Blueprints are being queried.
        log: (Keyword) Logger for all log messages.

    Returns:
        List of RemoteBlueprints found for the given Series.

    Raises:
        HTTPException (500) if the blueprints JSON file cannot be
            decoded.
    """

    # Get subfolder for this Series
    subfolder = f'{series.sort_name.upper()[0]}/{series.full_name}'

    # Read the JSON file of Blueprint definitions
    blueprint_url = f'{BLUEPRINT_URL}/{subfolder}/blueprints.json'
    response = get(blueprint_url)

    # If no file was found, there are no Blueprints for this Series, return
    if response.status_code == 404:
        log.debug(f'No blueprints.json file found at "{blueprint_url}"')
        return []

    try:
        # Blueprint file found, parse as JSON
        blueprints: list[dict] = response.json()
    except JSONDecodeError as e:
        log.exception(f'Error parsing Blueprints - {e}', e)
        raise HTTPException(
            status_code=500,
            detail=f'Unable to parse Blueprints JSON',
        )

    # Blueprints found, transform preview URLs and add ID
    for blueprint_id, blueprint in enumerate(blueprints):
        # Skip null Blueprints
        if blueprint is None:
            continue

        blueprints[blueprint_id]['id'] = blueprint_id
        preview_filename = blueprints[blueprint_id]['preview']
        blueprints[blueprint_id]['preview'] = (
            f'{BLUEPRINT_URL}/{subfolder}/{blueprint_id}/{preview_filename}'
        )

    # Return all Blueprints, omitting nulls
    return [blueprint for blueprint in blueprints if blueprint]


def import_blueprint(
        db: Session,
        preferences: Preferences,
        series: Series,
        blueprint: Blueprint,
        *,
        log: Logger = log,
    ) -> Series:
    """

    """

    # Get subfolder for this Series
    blueprint_folder = (
        f'{BLUEPRINT_URL}/{series.sort_name.upper()[0]}/{series.full_name}/'
        f'{blueprint.id}'
    )

    # Import Fonts
    font_map: dict[int, Font] = {}
    for font_id, font in enumerate(blueprint.fonts):
        # TODO See if this Font matches an existing one?
        # This Font has a file that can be directly downloaded
        font_content = None
        if getattr(font, 'file', None) is not None:
            file_url = f'{blueprint_folder}/{font.file}'
            response = get(file_url)
            if response.status_code == 404:
                log.error(f'Specified Font file does not exist at "{file_url}"')
                raise HTTPException(
                    status_code=404,
                    detail=f'Blueprint Font file not found',
                )
            font_content = response.content

        # Create new Font model, add to database and store in map
        new_font = Font(**NewNamedFont(**font.dict()).dict())
        font_map[font_id] = new_font
        db.add(new_font)
        db.commit()
        log.info(f'Created Named Font "{new_font.name}"')

        # Download Font file if provided
        if font_content:
            font_directory = preferences.asset_directory / 'fonts'
            file_path = font_directory / str(new_font.id) / font.file
            file_path.parent.mkdir(exist_ok=True, parents=True)
            file_path.write_bytes(font_content)
            log.info(f'{new_font.log_str} Downloaded File "{font.file}"')

            # Update object and database
            new_font.file = str(file_path)

    # Commit Fonts to database so Font objects have ID's
    if font_map:
        db.commit()

    # Import Templates
    template_map: dict[int, Template] = {}
    for template_id, template in enumerate(blueprint.templates):
        # TODO see if this Template matches an existing one
        # Update Font ID from Font map if indicated
        if template.font_id is not None:
            template.font_id = font_map[template.font_id].id

        # Create new Template model, add to database and store in map
        new_template = Template(**NewTemplate(**template.dict()).dict())
        template_map[template_id] = new_template
        db.add(new_template)
        log.info(f'Created Template "{template.name}"')

    # Commit Templates to database so Template objects have ID's
    if template_map:
        db.commit()

    # Assign updated Fonts and Templates to Series
    changed = False
    series_blueprint = blueprint.series.dict()
    if (new_font_id := series_blueprint.pop('font_id', None)) is not None:
        log.debug(f'Series[{series.id}].font_id = {font_map[new_font_id].id}')
        series.font = font_map[new_font_id]
        changed = True

    if (new_template_ids := series_blueprint.pop('template_ids', [])):
        template_ids = [template_map[id_].id for id_ in new_template_ids]
        log.debug(f'Series[{series.id}].template_ids = {template_ids}')
        series.templates = [template_map[id_] for id_ in new_template_ids]
        changed = True

    # Update each attribute of the Series object based on import
    update_series = UpdateSeries(**series_blueprint)
    for attr, value in update_series.dict().items():
        if getattr(series, attr) != value:
            log.debug(f'Series[{series.id}].{attr} = {value}')
            setattr(series, attr, value)
            changed = True

    # Import Episode overrides
    for episode_key, episode_blueprint in blueprint.episodes.items():
        # Identify indices for this override
        if (indices := EPISODE_REGEX.match(episode_key)) is None:
            log.error(f'Cannot identify index of Episode override "{episode_key}"')
            continue

        # Try and find Episode with this index
        indices = indices.groupdict()
        episode = db.query(Episode)\
            .filter(Episode.season_number==indices['season_number'],
                    Episode.episode_number==indices['episode_number'])\
            .first()
        
        # Episode not found, skip
        if episode is None:
            log.warning(f'Cannot find matching Episode for override "{episode_key}"')
            continue

        # Episode found, update attributes
        ...

    if changed:
        db.commit()

    return series