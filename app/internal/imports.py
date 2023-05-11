from typing import Any, Literal, Optional, Union

from fastapi import HTTPException
from ruamel.yaml import YAML
from sqlalchemy import or_

import app.models as models
from app.schemas.preferences import EpisodeDataSource, Preferences
from app.schemas.series import NewSeries, Series, NewTemplate, Translation
from app.schemas.episode import Episode

from modules.Debug import log
from modules.EpisodeMap import EpisodeMap


def parse_raw_yaml(yaml: str) -> dict[str, Any]:
    """
    Parse the raw YAML string into a Python Dictionary (ordereddict).

    Args:
        yaml: String that represents YAML to parse.

    Returns:
        Dictionary representation of the given YAML string, as parsed
        via ruamel.yaml.

    Raises:
        HTTPException (422) if the YAML parser raises an Exception while
            parsing the given YAML string.
    """

    try:
        return YAML().load(yaml)
    except Exception as e:
        log.exception(f'YAML parsing failed', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid',
        )


def _get(
        yaml_dict: dict[str, Any],
        *keys: tuple[str],
        type_: callable = None,
        default: Any = None) -> Any:
    """
    Get the value at the given location in YAML.

    Args:
        yaml_dict: YAML dictionary to get the value from.
        keys: Any number of keys to get the value of. Sequential keys
            are used for traversing nested dictionaries.
        type_: Optional callable to call on the value within the YAML
            before returning.
        default: Default value to return if the indicated value is not
            present.

    Returns:
        The value within yaml_dict at the given location, if it exists.
        `default` otherwise.

    Raises:
        Exception potentially raised by calling type_ on the value.
    """

    if not isinstance(yaml_dict, dict):
        return default

    value = yaml_dict
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default

        if key in value:
            value = value[key]

    # Return final value, apply type conversion if indicated
    if type_ is not None:
        return type_(value)
    
    return value


def _parse_translations(yaml_dict: dict[str, Any]) -> list[Translation]:
    """
    Parse translations from the given YAML.

    Args:
        yaml_dict: Dictionary of YAML to parse.

    Returns:
        List of Translations defined by the given YAML.

    Raises:
        HTTPException (422) if the YAML is invalid and cannot be parsed.
    """

    if (translations := yaml_dict.get('translation', None)) is None:
        return []
    
    def _parse_single_translation(translation: dict[str, Any]) -> dict[str, str]:
        if (not isinstance(translation, dict)
            or set(translation.keys()) > {'language', 'key'}):
            raise HTTPException(
                status_code=422,
                detail=f'Invalid translations - "language" and "key" are required',
            )
        
        return {
            'language_code': str(translation['language']),
            'data_key': str(translation['key']),
        }

    # List of Translations
    if isinstance(translations, list):
        return [
            _parse_single_translation(translation)
            for translation in translations
        ]

    # Singular translation
    if isinstance(translations, dict):
        return [_parse_single_translation(translations)]
    
    raise HTTPException(
        status_code=422,
        detail=f'Invalid translations',
    )


def _parse_episode_data_source(
        yaml_dict: dict[str, Any]) -> Optional[EpisodeDataSource]:
    """
    Parse the episode data source from the given YAML.

    Args:
        yaml_dict: Dictionary of YAML to parse.

    Returns:
        The updated EpisodeDataSource indicated by the given YAML. If no
        EDS is indicated, then None is returned.

    Raises:
        HTTPException (422) if the YAML is invalid and cannot be parsed,
            or if an invalid EDS is indicated.
    """

    # If no YAML or no EDS indicated, return None
    if (not isinstance(yaml_dict, dict)
        or (eds := yaml_dict.get('episode_data_source', None)) is None):
        return None

    # Convert the lowercase EDS identifiers to their new equivalents
    mapping = {
        'emby': 'Emby',
        'jellyfin': 'Jellyfin',
        'plex': 'Plex',
        'sonarr': 'Sonarr',
        'tmdb': 'TMDb',
    }

    try:
        return mapping[eds.lower()]
    except KeyError:
        raise HTTPException(
            status_code=422,
            detail=f'Invalid episode data source "{eds}"',
        )


def parse_templates(
        db: 'Database',
        preferences: Preferences,
        yaml_dict: dict[str, Any]) -> list[NewTemplate]:
    """
    Create NewTemplate objects for any defined templates in the given
    YAML.

    Args:
        db: Database to query for custom Fonts if indicated by any
            templates.
        preferences: Preferences to standardize styles.
        yaml_dict: Dictionary of YAML attributes to parse.

    Returns:
        List of NewTemplates that match any defined YAML templates.

    Raises:
        HTTPException (422) if there are any YAML formatting errors.
        Pydantic ValidationError if a NewTemplate object cannot be 
            created from the given YAML.
    """

    # If templates header was included, get those
    if 'templates' in yaml_dict:
        all_templates = yaml_dict['templates']
    else:
        all_templates = yaml_dict

    # If not a dictionary of Templates, return empty list
    if not isinstance(all_templates, dict):
        return []

    # Create NewTemplate objects for all listed templates
    templates = []
    for template_name, template_dict in all_templates.items():
        # Parse custom Font
        template_font = _get(template_dict, 'font')
        font_id = None
        if template_font is None:
            pass
        # Font name specified
        elif isinstance(template_font, str):
            # Get Font ID of this Font (if indicated)
            font = db.query(models.font.Font)\
                .filter_by(name=template_font).first()
            if font is None:
                raise HTTPException(
                    status_code=404,
                    detail=f'Font "{template_font}" not found',
                )
            font_id = font.id
        # Custom font specified, unparseable
        elif isinstance(template_font, dict):
            raise HTTPException(
                status_code=422,
                detail=f'Cannot define new Font in Template "{template_name}"',
            )
        # Unrecognized font details
        else:
            raise HTTPException(
                status_code=422,
                detail=f'Unrecognized Font in Template "{template_name}"',
            )

        # Get season titles via episode_ranges or seasons
        episode_map = EpisodeMap(
            _get(template_dict, 'seasons', default={}),
            _get(template_dict, 'episode_ranges', default={}),
        )
        if not episode_map.valid:
            raise HTTPException(
                status_code=422,
                detail=f'Invalid season titles in Template "{template_name}"',
            )
        season_titles = episode_map.raw

        # Get extras
        extras = _get(template_dict, 'extras', default={})
        if not isinstance(extras, dict):
            raise HTTPException(
                status_code=422,
                detail=f'Invalid extras in Template "{template_name}"',
            )

        # Create NewTemplate with all indicated customization
        templates.append(NewTemplate(
            name=str(template_name),
            card_filename_format=_get(template_dict, 'filename_format'),
            episode_data_source=_parse_episode_data_source(template_dict),
            sync_specials=_get(template_dict, 'sync_specials', type_=bool),
            translations=_parse_translations(template_dict),
            font_id=font_id,
            card_type=_get(template_dict, 'card_type'),
            season_title_ranges=list(season_titles.keys()),
            season_title_values=list(season_titles.values()),
            hide_season_text=_get(template_dict, 'seasons', 'hide', type_=bool),
            episode_text_format=_get(template_dict, 'episode_text_format'),
            hide_episode_text=_get(template_dict, 'hide_episode_text', type_=bool),
            unwatched_style=_get(
                template_dict, 'unwatched_style',
                type_=preferences.standardize_style
            ), watched_style=_get(
                template_dict, 'watched_style',
                type_=preferences.standardize_style
            ),
            extra_keys=list(extras.keys()),
            extra_values=list(extras.values()),
        ))

    return templates