from typing import Any, Callable, Optional, Union

from fastapi import HTTPException
from ruamel.yaml import YAML

from app.dependencies import refresh_imagemagick_interface
from app.internal.connection import update_connection
import app.models as models
from app.schemas.base import UNSPECIFIED
from app.schemas.font import NewNamedFont
from app.schemas.preferences import (
    EpisodeDataSource, Preferences, UpdateEmby, UpdateJellyfin, UpdatePlex,
    UpdatePreferences, UpdateSonarr, UpdateTMDb
)
from app.schemas.series import NewSeries, NewTemplate, Translation
from app.schemas.sync import NewEmbySync, NewJellyfinSync, NewPlexSync, NewSonarrSync

from modules.Debug import log
from modules.EpisodeMap import EpisodeMap
from modules.SeriesInfo import SeriesInfo


Extension = lambda s: str(s) if s.startswith('.') else f'.{s}'
Percentage = lambda s: float(str(s).split('%')[0]) / 100.0
Width = lambda dims: int(str(dims).lower().split('x')[0])
Height = lambda dims: int(str(dims).lower().split('x')[1])


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
        type_: Optional[Callable[..., Any]] = None,
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

    # Iterate through this object one key-at-a-time
    value = yaml_dict
    for key in keys:
        # If the current value cannot be traversed, or the key is missing
        if not isinstance(value, dict) or key not in value:
            return default

        # Key is present, continue iteration
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


def _parse_filesize_limit(
        yaml_dict: dict[str, Any]
    ) -> Union[tuple[int, str], tuple[UNSPECIFIED, UNSPECIFIED]]:
    """
    Parse the filesize limit unit and number from the given YAML.

    Args:
        yaml_dict: Dictionary of YAML to parse.

    Returns:
        Tuple of the filesize number and unit. If the limit is not in
        the specified YAML, then a tuple of UNSPECIFIED is returned.

    Raises:
        HTTPException (422) if the limit values cannot be parsed.
    """

    if (not isinstance(yaml_dict, dict)
        or (limit := yaml_dict.get('filesize_limit', None)) is None):
        return UNSPECIFIED, UNSPECIFIED
    
    try:
        number, unit = limit.split(' ')
        return int(number), unit
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f'Invalid filesize limit',
        )


def parse_preferences(
        preferences: Preferences,
        yaml_dict: dict[str, Any]) -> Preferences:
    """
    Modify the preferences for the given YAML.

    Args:
        preferences: Preferences to modify.
        yaml_dict: Dictionary of YAML attributes to parse.

    Returns:
        Modified Preferences.

    Raises:
        HTTPException (422) if there are any YAML formatting errors.
        Pydantic ValidationError if an object cannot be created from the
            given YAML.
    """

    # Shorthand for an unspecified value
    unsp = UNSPECIFIED

    # Get each major section
    options = _get(yaml_dict, 'options', default={})
    imagemagick = _get(yaml_dict, 'imagemagick', default={})

    # Determine which media server to query default styles from
    if preferences.use_emby:
        media_server = 'emby'
    elif preferences.use_jellyfin:
        media_server = 'jellyfin'
    else:
        media_server = 'plex'

    # Parse image source priority
    image_source_priority = unsp
    if (isp := _get(options, 'image_source_priority')) is not None:
        mapping = {
            'emby': 'Emby', 'jellyfin': 'Jellyfin', 'plex': 'Plex', 'tmdb': 'TMDb'
        }
        image_source_priority = [
            mapping[source] 
            for source in isp.lower().replace(' ', '').split(',')
            if source in mapping
        ]

    # Create UpdatePreferenes object from the YAML
    update_preferences = UpdatePreferences(
        source_directory=_get(options, 'source', default=unsp),
        card_width=_get(options, 'card_dimensions', type_=Width, default=unsp),
        card_height=_get(options, 'card_dimensions', type_=Height, default=unsp),
        card_filename_format=_get(options, 'filename_format', default=unsp),
        card_extension=_get(options, 'card_extension', type_=Extension, default=unsp),
        image_source_priority=image_source_priority,
        episode_data_source=_parse_episode_data_source(options),
        # specials_folder_format=..., # New option
        season_folder_format=_get(options, 'season_folder_format', default=unsp),
        sync_specials=_get(options, 'sync_specials', type_=bool, default=unsp),
        default_card_type=_get(options, 'card_type', default=unsp),
        default_unwatched_style=_get(
            yaml_dict,
            media_server, 'unwatched_style',
            type_=str,
            default=unsp,
        ), default_watched_style=_get(
            yaml_dict,
            media_server, 'watched_style',
            type_=str,
            default=unsp,
        ), imagemagick_container=_get(imagemagick, 'container', default=unsp),
    )

    preferences.update_values(**update_preferences.dict())
    refresh_imagemagick_interface()
    preferences.determine_imagemagick_prefix()

    return preferences


def parse_emby(
        preferences: Preferences,
        yaml_dict: dict[str, Any]) -> Preferences:
    """
    Update the Emby connection preferences for the given YAML.

    Args:
        preferences: Preferences whose connection details are being
            modified.
        yaml_dict: Dictionary of YAML attributes to parse.
    
    Returns:
        Modified Preferences object. If no changes are made, the object
        is returned unmodified.

    Raises:
        HTTPException (422) if there are any YAML formatting errors.
        Pydantic ValidationError if an UpdateEmby object cannot be 
            created from the given YAML.
    """

    # Get each major section
    emby = _get(yaml_dict, 'emby', default={})

    # Get filesize limit
    limit_number, limit_unit = _parse_filesize_limit(emby)

    update_emby = UpdateEmby(
        url=_get(emby, 'url', type_=str, default=UNSPECIFIED),
        api_key=_get(emby, 'api_key', default=UNSPECIFIED),
        username=_get(emby, 'username', type_=str, default=UNSPECIFIED),
        use_ssl=_get(emby, 'verify_ssl', type_=bool, default=UNSPECIFIED),
        filesize_limit_number=limit_number,
        filesize_limit_unit=limit_unit,
    )

    return update_connection(preferences, update_emby, 'emby')


def parse_jellyfin(
        preferences: Preferences,
        yaml_dict: dict[str, Any]) -> Preferences:
    """
    Update the Jellyfin connection preferences for the given YAML.

    Args:
        preferences: Preferences whose connection details are being
            modified.
        yaml_dict: Dictionary of YAML attributes to parse.
    
    Returns:
        Modified Preferences object. If no changes are made, the object
        is returned unmodified.

    Raises:
        HTTPException (422) if there are any YAML formatting errors.
        Pydantic ValidationError if an UpdateJellyfin object cannot be 
            created from the given YAML.
    """

    # Get each major section
    jellyfin = _get(yaml_dict, 'jellyfin', default={})

    # Get filesize limit
    limit_number, limit_unit = _parse_filesize_limit(jellyfin)

    update_emby = UpdateJellyfin(
        url=_get(jellyfin, 'url', type_=str, default=UNSPECIFIED),
        api_key=_get(jellyfin, 'api_key', default=UNSPECIFIED),
        username=_get(jellyfin, 'username', type_=str, default=UNSPECIFIED),
        use_ssl=_get(jellyfin, 'verify_ssl', type_=bool, default=UNSPECIFIED),
        filesize_limit_number=limit_number,
        filesize_limit_unit=limit_unit,
    )

    return update_connection(preferences, update_emby, 'jellyfin')


def parse_plex(
        preferences: Preferences,
        yaml_dict: dict[str, Any]) -> Preferences:
    """
    Update the Plex connection preferences for the given YAML.

    Args:
        preferences: Preferences whose connection details are being
            modified.
        yaml_dict: Dictionary of YAML attributes to parse.
    
    Returns:
        Modified Preferences object. If no changes are made, the object
        is returned unmodified.

    Raises:
        HTTPException (422) if there are any YAML formatting errors.
        Pydantic ValidationError if an UpdatePlex object cannot be
            created from the given YAML.
    """

    # Get each major section
    plex = _get(yaml_dict, 'plex', default={})

    # Get filesize limit
    limit_number, limit_unit = _parse_filesize_limit(plex)

    update_plex = UpdatePlex(
        url=_get(plex, 'url', type_=str, default=UNSPECIFIED),
        token=_get(plex, 'token', default=UNSPECIFIED),
        use_ssl=_get(plex, 'verify_ssl', type_=bool, default=UNSPECIFIED),
        integrate_with_pmm=_get(
            plex,
            'integrate_with_pmm_overlays',
            type_=bool, default=UNSPECIFIED,
        ), filesize_limit_number=limit_number,
        filesize_limit_unit=limit_unit,
    )

    return update_connection(preferences, update_plex, 'plex')


def parse_tmdb(
        preferences: Preferences,
        yaml_dict: dict[str, Any]) -> Preferences:
    """
    Update the TMDb connection preferences for the given YAML.

    Args:
        preferences: Preferences whose connection details are being
            modified.
        yaml_dict: Dictionary of YAML attributes to parse.
    
    Returns:
        Modified Preferences object. If no changes are made, the object
        is returned unmodified.

    Raises:
        HTTPException (422) if there are any YAML formatting errors.
        Pydantic ValidationError if an UpdateTMDb object cannot be
            created from the given YAML.
    """

    # Get each major section
    tmdb = _get(yaml_dict, 'tmdb', default={})

    SplitList = lambda s: str(s).lower().replace(' ', '').split(',')

    update_tmdb = UpdateTMDb(
        api_key=_get(tmdb, 'api_key', default=UNSPECIFIED),
        minimum_width=_get(
            tmdb,
            'minimum_resolution',
            type_=Width, default=UNSPECIFIED,
        ), minimum_height=_get(
            tmdb,
            'minimum_resolution',
            type_=Height, default=UNSPECIFIED,
        ), skip_localized=_get(
            tmdb,
            'skip_localized_images',
            type_=bool, default=UNSPECIFIED,
        ), logo_language_priority=_get(
            tmdb,
            'logo_language_priority',
            type_=SplitList, default=UNSPECIFIED,
        ),
    )

    return update_connection(preferences, update_tmdb, 'tmdb')


def parse_sonarr(
        preferences: Preferences,
        yaml_dict: dict[str, Any]) -> Preferences:
    """
    Update the Sonarr connection preferences for the given YAML.

    Args:
        preferences: Preferences whose connection details are being
            modified.
        yaml_dict: Dictionary of YAML attributes to parse.
    
    Returns:
        Modified Preferences object. If no changes are made, the object
        is returned unmodified.

    Raises:
        HTTPException (422) if there are any YAML formatting errors.
        Pydantic ValidationError if an UpdateSonarr object cannot be
            created from the given YAML.
    """

    # Get each major section
    sonarr = _get(yaml_dict, 'sonarr', default={})

    update_sonarr = UpdateSonarr(
        url=_get(sonarr, 'url', default=UNSPECIFIED),
        api_key=_get(sonarr, 'api_key', default=UNSPECIFIED),
        use_ssl=_get(sonarr, 'verify_ssl', default=UNSPECIFIED),
    )

    return update_connection(preferences, update_sonarr, 'sonarr')


def parse_syncs(
        yaml_dict: dict[str, Any]
    ) -> Union[list[NewEmbySync], list[NewJellyfinSync], list[NewPlexSync],
               list[NewSonarrSync]]:
    """
    
    """

    ...


def parse_fonts(
        yaml_dict: dict[str, Any]) -> list[NewNamedFont]:
    """
    Create NewNamedFont objects for any defined fonts in the given
    YAML.

    Args:
        yaml_dict: Dictionary of YAML attributes to parse.

    Returns:
        List of NewTemplates that match any defined YAML templates.

    Raises:
        HTTPException (422) if there are any YAML formatting errors.
        Pydantic ValidationError if a NewTemplate object cannot be 
            created from the given YAML.
    """

    # If fonts header was included, get those
    if 'fonts' in yaml_dict:
        all_fonts = yaml_dict['fonts']
    else:
        all_fonts = yaml_dict

    # If not a dictionary of fonts, return empty list
    if not isinstance(all_fonts, dict):
        return []

    # Create NewNamedFont objects for all listed fonts
    fonts = []
    for font_name, font_dict in all_fonts.items():
        # Skip if not a dictionary
        if not isinstance(font_dict, dict):
            raise HTTPException(
                status_code=422,
                detail=f'Invalid Font "{font_name}"',
            )

        # Get replacements
        replacements = _get(font_dict, 'replacements', default={})
        if not isinstance(replacements, dict):
            raise HTTPException(
                status_code=422,
                detail=f'Invalid replacements in Font "{font_name}"',
            )

        # Create NewTemplate with all indicated customization
        fonts.append(NewNamedFont(
            name=str(font_name),
            color=_get(font_dict, 'color'),
            title_case=_get(font_dict, 'case'),
            size=_get(font_dict, 'size', default=1.0, type_=Percentage),
            kerning=_get(font_dict, 'kerning', default=1.0, type_=Percentage),
            stroke_width=_get(font_dict, 'stroke_width', default=1.0, type_=Percentage),
            interline_spacing=_get(font_dict, 'interline_spacing', default=0, type_=int),
            vertical_shift=_get(font_dict, 'vertical_shift', default=0, type_=int),
            delete_missing=_get(font_dict, 'delete_missing', default=True, type_=bool),
            replacements_in=list(replacements.keys()),
            replacements_out=list(replacements.values()),
        ))

    return fonts


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
        HTTPException (404) if an indicated Font name cannot be found in
            the database.
        HTTPException (422) if there are any YAML formatting errors.
        Pydantic ValidationError if a NewTemplate object cannot be 
            created from the given YAML.
    """

    # If templates header was included, get those
    if 'templates' in yaml_dict:
        all_templates = yaml_dict['templates']
    else:
        all_templates = yaml_dict

    # If not a dictionary of templates, return empty list
    if not isinstance(all_templates, dict):
        return []

    # Create NewTemplate objects for all listed templates
    templates = []
    for template_name, template_dict in all_templates.items():
        # Skip if not a dictionary
        if not isinstance(template_dict, dict):
            raise HTTPException(
                status_code=422,
                detail=f'Invalid Template "{template_name}"',
            )

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


def parse_series(
        db: 'Database',
        preferences: Preferences,
        yaml_dict: dict[str, Any],
        default_library: Optional[str] = None) -> list[NewSeries]:
    """
    Create NewSeries objects for any defined series in the given YAML.

    Args:
        db: Database to query for custom Fonts and Templates if
            indicated by any series.
        preferences: Preferences to standardize styles and query for
            the default media server.
        yaml_dict: Dictionary of YAML attributes to parse.
        default_library: Optional default Library name to apply to the
            Series if one is not manually specified within YAML.

    Returns:
        List of NewSeries that match any defined YAML series.

    Raises:
        HTTPException (404) if an indicated Font or Template name cannot
            be found in the database.
        HTTPException (422) if there are any YAML formatting errors.
        Pydantic ValidationError if a NewSeries object cannot be 
            created from the given YAML.
    """

    # If series header was included, get those
    if 'series' in yaml_dict:
        all_series = yaml_dict['series']
    else:
        all_series = yaml_dict

    # If not a dictionary of series, return empty list
    if not isinstance(all_series, dict):
        return []
    
    # Determine which media server to assume libraries are for
    if preferences.use_emby:
        library_type = 'emby_library_name'
    elif preferences.use_jellyfin:
        library_type = 'jellyfin_library_name'
    else:
        library_type = 'plex_library_name'

    # Create NewSeries objects for all listed templates
    series = []
    for series_name, series_dict in all_series.items():
        # Skip if not a dictionary
        if not isinstance(series_dict, dict):
            raise HTTPException(
                status_code=422,
                detail=f'Invalid Series "{series_name}"',
            )

        # Create SeriesInfo for this series - parsing name/year/ID's
        series_info = SeriesInfo(
            _get(series_dict, 'name', type_=str, default=series_name),
            _get(series_dict, 'year', type_=int, default=None),
            emby_id=_get(series_dict, 'emby_id', default=None),
            imdb_id=_get(series_dict, 'imdb_id', default=None),
            jellyfin_id=_get(series_dict, 'jellyfin_id', default=None),
            sonarr_id=_get(series_dict, 'sonarr_id', default=None),
            tmdb_id=_get(series_dict, 'tmdb_id', default=None),
            tvdb_id=_get(series_dict, 'tvdb_id', default=None),
            tvrage_id=_get(series_dict, 'tvrage_id', default=None),
        )

        # Parse custom Font
        series_font = _get(series_dict, 'font', default={})
        font_id = None
        if not isinstance(series_font, (str, dict)):
            raise HTTPException(
                status_code=422,
                detail=f'Unrecognized Font in Series "{series_info}"',
            )
        elif isinstance(series_font, str):
            # Get Font ID of this Font (if indicated)
            font = db.query(models.font.Font)\
                .filter_by(name=series_font).first()
            if font is None:
                raise HTTPException(
                    status_code=404,
                    detail=f'Font "{series_font}" not found',
                )
            font_id = font.id

        # Parse template
        template_id = None
        if 'template' in series_dict:
            # Get template name for querying
            series_template = series_dict['template']
            if isinstance(series_template, str):
                template_name = series_template
            elif isinstance(series_template, dict) and 'name' in series_template:
                template_name = series_template['name']
            else:
                raise HTTPException(
                    status_code=422,
                    detail=f'Unrecognized Template in Series "{series_info}"',
                )
            
            # Get Template ID
            template = db.query(models.template.Template)\
                .filter_by(name=template_name).first()
            if template is None:
                raise HTTPException(
                    status_code=404,
                    detail=f'Template "{template_name}" not found',
                )
            template_id = template.id

        # Get season titles via episode_ranges or seasons
        episode_map = EpisodeMap(
            _get(series_dict, 'seasons', default={}),
            _get(series_dict, 'episode_ranges', default={}),
        )
        if not episode_map.valid:
            raise HTTPException(
                status_code=422,
                detail=f'Invalid season titles in Series "{series_info}"',
            )
        season_titles = episode_map.raw

        # Get extras
        extras = _get(series_dict, 'extras', default={})
        if not isinstance(extras, dict):
            raise HTTPException(
                status_code=422,
                detail=f'Invalid extras in Series "{series_info}"',
            )
        # Remove basic logo as this is now built-in
        extras = {
            k: v
            for k, v in extras.items()
            if k != 'logo' and not str(v).endswith('logo.png')
        }
        
        # Use default library if a manual one was not specified
        if (library := _get(series_dict, 'library')) is None:
            library = default_library

        # Create NewTemplate with all indicated customization
        series.append(NewSeries(
            name=series_info.name,
            year=series_info.year,
            template_id=template_id,
            sync_specials=_get(series_dict, 'sync_specials', type_=bool),
            card_filename_format=_get(series_dict, 'filename_format'),
            episode_data_source=_parse_episode_data_source(series_dict),
            match_titles=_get(series_dict, 'refresh_titles', default=True),
            card_type=_get(series_dict, 'card_type'),
            unwatched_style=_get(
                series_dict,
                'unwatched_style',
                type_=preferences.standardize_style
            ), watched_style=_get(
                series_dict,
                'watched_style',
                type_=preferences.standardize_style
            ),
            translations=_parse_translations(series_dict),
            font_id=font_id,
            font_color=_get(series_dict, 'font', 'color'),
            font_title_case=_get(series_dict, 'font', 'case'),
            size=_get(
                series_dict,
                'font', 'size',
                default=1.0, type_=Percentage
            ), kerning=_get(
                series_dict,
                'font', 'kerning',
                default=1.0, type_=Percentage
            ), stroke_width=_get(
                series_dict,
                'font', 'stroke_width',
                default=1.0, type_=Percentage
            ), interline_spacing=_get(
                series_dict,
                'font', 'interline_spacing',
                default=0, type_=int
            ), vertical_shift=_get(
                series_dict,
                'font', 'vertical_shift',
                default=0, type_=int
            ), directory=_get(series_dict, 'media_directory'),
            **{library_type: library},
            **series_info.ids,
            season_title_ranges=list(season_titles.keys()),
            season_title_values=list(season_titles.values()),
            hide_season_text=_get(series_dict, 'seasons', 'hide', type_=bool),
            episode_text_format=_get(series_dict, 'episode_text_format'),
            hide_episode_text=_get(series_dict, 'hide_episode_text', type_=bool),
            extra_keys=list(extras.keys()),
            extra_values=list(extras.values()),
        ))

    return series