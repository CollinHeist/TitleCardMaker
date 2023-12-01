from logging import Logger
from pathlib import Path
from re import compile as re_compile, IGNORECASE
from time import sleep

from fastapi import HTTPException
from requests import get
from sqlalchemy.orm import Session

from app.dependencies import get_preferences
from app.models.blueprint import Blueprint, BlueprintSeries
from app.models.episode import Episode
from app.models.font import Font
from app.models.series import Series
from app.models.template import Template
from app.schemas.blueprint import ExportBlueprint
from app.schemas.episode import UpdateEpisode
from app.schemas.font import NewNamedFont
from app.schemas.series import NewTemplate, UpdateSeries
from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
from modules.SeriesInfo2 import SeriesInfo
from modules.TieredSettings import TieredSettings

"""
Regex to extract the season and episode number from an Episode override
key.
"""
EPISODE_REGEX = re_compile(
    r'^s(?P<season_number>\d+)e(?P<episode_number>\d+)$',
    IGNORECASE
)

"""Root URL of the Blueprint Repository"""
REPO_URL = 'https://github.com/TitleCardMaker/Blueprints/raw/master'

"""URL under which all Blueprint subdirectories are located"""
BLUEPRINTS_URL = f'{REPO_URL}/blueprints'


def delay_zip_deletion(zip_directory: Path, zip_file: Path) -> None:
    """
    Delete the given zip directory and files. A delay is utilized so
    that the browser is able to download the content before they are
    deleted.

    Args:
        zip_directory: Directory containing zipped files to be deleted.
            The contents are deleted, then the directory itself.
        zip_file: Zip file to delete directly.
    """

    # Wait a while to give the browser time to download the zips
    sleep(5)

    # Delete zip file
    zip_file.unlink(missing_ok=True)
    log.debug(f'Deleted "{zip_file}"')

    # Delete zip directory contents
    for file in zip_directory.glob('*'):
        file.unlink(missing_ok=True)
        log.debug(f'Deleted "{file}"')

    # Delete zip directory
    zip_directory.rmdir()
    log.debug(f'Deleted {zip_directory}')


def generate_series_blueprint(
        series: Series,
        raw_episode_data: list[EpisodeInfo],
        include_global_defaults: bool,
        include_episode_overrides: bool,
    ) -> ExportBlueprint:
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

    Returns:
        Blueprint that can be used to recreate the Series configuration.
    """

    # Get all Episodes if indicates
    episodes: list[Episode]=series.episodes if include_episode_overrides else []

    # Get all Templates
    templates: list[Template] = list(set(
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
        export_obj['series'] = TieredSettings.new_settings(
            get_preferences().export_properties,
            series.export_properties,
        )
    else:
        export_obj['series'] = series.export_properties
    export_obj['series'] =  TieredSettings.filter(export_obj['series'])

    # Get Episode titles for comparison
    episode_titles: dict[str, str] = {
        episode_info.key: episode_info.title.full_title
        for episode_info in raw_episode_data
    }

    # Add Episode configs
    for episode in episodes:
        # Get filtered exportable properties for this Episode
        key = f's{episode.season_number}e{episode.episode_number}'
        episode_properties =  TieredSettings.filter(episode.export_properties)

        # Add title if customized
        if key in episode_titles and episode_titles[key] != episode.title:
            episode_properties['title'] = episode.title

        # Skip Episodes without customization
        if not episode_properties and not episode.templates:
            continue

        # Assign Template indices
        export_obj['episodes'][key] = episode_properties
        if episode.templates:
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

    return ExportBlueprint(**export_obj)


def get_blueprint_font_files(
        series: Series,
        episodes: list[Episode],
    ) -> list[Path]:
    """
    Get Paths to all the Font files for the given Series' Blueprint.

    Args:
        series: Series whose associated Font files to return.
        episodes: Any number of Episodes whose associated Font files to
            return.

    Returns:
        List of Paths to the Font files for any Fonts associated with
        the given Series, Episodes, or their linked Templates.
    """

    # Get all Templates
    templates = list(set(
        template for obj in [series] + episodes for template in obj.templates
    ))

    # Get list of files for the Series, all Episodes, and all Templates
    all_fonts = set(
        obj.font for obj in [series] + episodes + templates if obj.font
    )

    return [Path(font.file) for font in all_fonts if font.file]


def query_series_blueprints(
        blueprint_db: Session,
        series_info: SeriesInfo,
    ) -> list[Blueprint]:
    """
    Get all Blueprints for the given Series.

    Args:
        blueprint_db: Database to the Blueprints to search.
        series_info: Info of the Series whose Blueprints are being
            searched.

    Returns:
        All defined Blueprints found for the given Series.
    """

    blueprint_series = blueprint_db.query(BlueprintSeries)\
        .filter(series_info.filter_conditions(BlueprintSeries))\
        .first()

    if blueprint_series is None:
        return []

    return blueprint_db.query(Blueprint)\
        .filter_by(series_id=blueprint_series.id)\
        .all()


def import_blueprint(
        db: Session,
        series: Series,
        blueprint: Blueprint,
        *,
        log: Logger = log,
    ) -> None:
    """
    Import the given Blueprint into the given Series.

    Args:
        db: Database to add any imported Fonts, and Templates, and to
            query for existing Episodes.
        series: Series the imported Blueprint is affecting.
        blueprint: Blueprint to parse for imported settings.
        log: Logger for all log messages.
    """

    # Get subfolder for this Blueprint
    blueprint_folder = blueprint.get_folder(BLUEPRINTS_URL)

    # Import Fonts
    font_map: dict[int, Font] = {}
    for font_id, font in enumerate(blueprint.blueprint.fonts):
        # See if this Font already exists (match by name)
        if ((existing_font := db.query(Font).filter_by(name=font.name).first())
            is not None):
            font_map[font_id] = existing_font
            log.info(f'Matched Blueprint Font[{font_id}] to existing Font '
                     f'{existing_font.log_str}')
            continue

        # This Font has a file that can be directly downloaded
        font_content = None
        if getattr(font, 'file', None) is not None:
            file_url = f'{blueprint_folder}/{font.file}'
            response = get(file_url, timeout=30)
            if not response.ok:
                log.error(f'Error downloading Font file from "{file_url}"')
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f'Font returned error - {response.reason}',
                )
            log.debug(f'Downloaded Font file from "{file_url}"')
            font_content = response.content

        # Create new Font model, add to database and store in map
        new_font = Font(**NewNamedFont(**font.dict()).dict())
        font_map[font_id] = new_font
        db.add(new_font)
        db.commit()
        log.info(f'Created Named Font "{new_font.name}"')

        # Download Font file if provided
        if font_content:
            font_directory = get_preferences().asset_directory / 'fonts'
            file_path = font_directory / str(new_font.id) / font.file
            file_path.parent.mkdir(exist_ok=True, parents=True)
            file_path.write_bytes(font_content)
            log.info(f'{new_font.log_str} Downloaded File "{font.file}"')

            # Update object and database
            new_font.file_name = file_path.name

    # Commit Fonts to database so Fonts have IDs
    if font_map:
        db.commit()

    # Import Templates
    template_map: dict[int, Template] = {}
    for template_id, template in enumerate(blueprint.blueprint.templates):
        # See if this Template already exists (match by name)
        existing_template = db.query(Template).filter_by(name=template.name)\
            .first()
        if existing_template is not None:
            template_map[template_id] = existing_template
            log.info(f'Matched Blueprint Template[{template_id}] to existing '
                     f'Template {existing_template}')
            continue

        # Update Font ID from Font map if indicated
        if getattr(template, 'font_id', None) is not None:
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
    series_blueprint = blueprint.blueprint.series.dict()
    if (new_font_id := series_blueprint.pop('font_id', None)) is not None:
        log.debug(f'Series[{series.id}].font_id = {font_map[new_font_id].id}')
        series.font = font_map[new_font_id]
        changed = True

    if (new_template_ids := series_blueprint.pop('template_ids', [])):
        templates = [template_map[id_] for id_ in new_template_ids]
        series.assign_templates(templates, log=log)
        changed = True

    # Update each attribute of the Series object based on import
    update_series = UpdateSeries(**series_blueprint)
    for attr, value in update_series.dict().items():
        if getattr(series, attr) != value:
            log.debug(f'Series[{series.id}].{attr} = {value}')
            setattr(series, attr, value)
            changed = True

    # Import Episode overrides
    for episode_key, episode_blueprint in blueprint.blueprint.episodes.items():
        # Identify indices for this override
        if (indices := EPISODE_REGEX.match(episode_key)) is None:
            log.error(f'Cannot identify index of Episode override "{episode_key}"')
            continue

        # Try and find Episode with this index
        indices = indices.groupdict()
        episode = db.query(Episode)\
            .filter(Episode.series_id==series.id,
                    Episode.season_number==indices['season_number'],
                    Episode.episode_number==indices['episode_number'])\
            .first()

        # Episode not found, skip
        if episode is None:
            log.warning(f'Cannot find matching Episode for override "{episode_key}"')
            continue

        # Episode found, update attributes
        episode_dict = episode_blueprint.dict()

        # Assign Font and Templates
        if (new_font_id := episode_dict.pop('font_id', None)) is not None:
            log.debug(f'Episode[{episode.id}].font_id = {font_map[new_font_id].id}')
            episode.font = font_map[new_font_id]
            changed = True

        if (new_template_ids := episode_dict.pop('template_ids', [])):
            templates = [template_map[id_] for id_ in new_template_ids]
            episode.assign_templates(templates, log=log)
            changed = True

        # All other attributes
        update_episode = UpdateEpisode(**episode_dict)
        for attr, value in update_episode.dict().items():
            if getattr(episode, attr) != value:
                log.debug(f'Episode[{episode.id}].{attr} = {value}')
                setattr(episode, attr, value)
                changed = True

    # Import Source Images
    for filename in series_blueprint.pop('source_files', []):
        file_url = f'{blueprint_folder}/{filename}'
        response = get(file_url, timeout=30)
        if not response.ok:
            log.error(f'Error downloading Source Image from "{file_url}"')
            raise HTTPException(
                status_code=response.status_code,
                detail=f'Font returned error - {response.reason}',
            )
        log.debug(f'Downloaded Source image from "{file_url}"')

        if response.content:
            source_file: Path = Path(series.source_directory) / filename
            source_file.write_bytes(response.content)
            log.debug(f'Wrote {len(response.content)} bytes to "{filename}"')

    # Add ID to imported set
    preferences = get_preferences()
    preferences.imported_blueprints.add(blueprint.id)
    preferences.commit()

    # Commit changes to Database
    if changed:
        db.commit()
