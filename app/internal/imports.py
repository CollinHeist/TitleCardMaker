from logging import Logger
from pathlib import Path
from re import match, IGNORECASE
from typing import Any, Callable, Optional, Union

from fastapi import HTTPException
from ruamel.yaml import YAML
from sqlalchemy.orm import Session

from app.dependencies import (
    get_emby_interfaces, get_jellyfin_interfaces, get_plex_interfaces,
    get_sonarr_interfaces, get_tmdb_interfaces, refresh_imagemagick_interface
)
from app.internal.cards import (
    add_card_to_database, resolve_card_settings, validate_card_type_model
)
from app.internal.connection import add_connection, update_connection
from app import models
from app.models.connection import Connection
from app.models.preferences import Preferences
from app.schemas.base import UNSPECIFIED
from app.schemas.card import NewTitleCard
from app.schemas.connection import (
    NewEmbyConnection, NewJellyfinConnection, NewPlexConnection,
    NewSonarrConnection, NewTMDbConnection, UpdateEmby, UpdateJellyfin,
    UpdatePlex, UpdateSonarr, UpdateTMDb,
)
from app.schemas.font import NewNamedFont
from app.schemas.preferences import (
    CardExtension, EpisodeDataSource, UpdatePreferences
)
from app.schemas.series import NewSeries, NewTemplate, Series, Translation
from app.schemas.sync import (
    NewEmbySync, NewJellyfinSync, NewPlexSync, NewSonarrSync
)

from modules.Debug import log
from modules.EpisodeMap import EpisodeMap
from modules.PreferenceParser import PreferenceParser
from modules.SeriesInfo2 import SeriesInfo
from modules.TieredSettings import TieredSettings


# pylint: disable=unnecessary-lambda-assignment
Extension = lambda s: str(s) if s.startswith('.') else f'.{s}'
Percentage = lambda s: float(str(s).split('%', maxsplit=1)[0]) / 100.0
Width = lambda dims: int(str(dims).lower().split('x', maxsplit=1)[0])
Height = lambda dims: int(str(dims).lower().split('x')[1])
# pylint: enable=unnecessary-lambda-assignment


def parse_raw_yaml(yaml: str) -> dict[str, Any]:
    """
    Parse the raw YAML string into a Python dictionary (ordereddict).

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
        yaml_dict = YAML().load(yaml)
        return {} if yaml_dict is None else yaml_dict
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid and cannot be parsed',
        ) from exc


def _get(yaml_dict: dict[str, Any],
        *keys: tuple[str],
        type_: Optional[Callable[..., Any]] = None,
        default: Any = None,
    ) -> Any:
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
        HTTPException (422) if the indicated type conversion raises any
            Exceptions.
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
        try:
            return type_(value)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f'YAML is incorrectly typed - {e}',
            ) from e

    return value


def _parse_translations(
        yaml_dict: dict[str, Any],
        default: Any = None
    ) -> list[Translation]:
    """
    Parse translations from the given YAML.

    Args:
        yaml_dict: Dictionary of YAML to parse.
        default: Default value to return if no translations are defined.

    Returns:
        List of Translations defined by the given YAML.

    Raises:
        HTTPException (422) if the YAML is invalid and cannot be parsed.
    """

    # No translations, return default
    if (translations := yaml_dict.get('translation', None)) is None:
        return default

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

    # List of translations
    if isinstance(translations, list):
        return [
            _parse_single_translation(translation)
            for translation in translations
        ]

    # Singular translation
    if isinstance(translations, dict):
        return [_parse_single_translation(translations)]

    # Not list or dictionary, invalid translations
    raise HTTPException(
        status_code=422,
        detail=f'Invalid translations',
    )


def _parse_episode_data_source(
        yaml_dict: dict[str, Any]
    ) -> Optional[EpisodeDataSource]:
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
    except KeyError as e:
        raise HTTPException(
            status_code=422,
            detail=f'Invalid episode data source "{eds}"',
        ) from e


def _parse_filesize_limit(
        yaml_dict: dict[str, Any]
    ) -> str:
    """
    Parse the filesize limit from the given YAML.

    Args:
        yaml_dict: Dictionary of YAML to parse.

    Returns:
        The modified filesize limit. If the limit is not in the
        specified YAML, then UNSPECIFIED is returned.

    Raises:
        HTTPException (422): The limit values cannot be parsed.
    """

    if (not isinstance(yaml_dict, dict)
        or (limit := yaml_dict.get('filesize_limit', None)) is None):
        return UNSPECIFIED

    try:
        number, unit = limit.split(' ')
        modified_unit = {
            'b': 'Bytes', 'kb': 'Kilobytes', 'mb': 'Megabytes'
        }[unit.lower()]
        return f'{number} {modified_unit}'
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f'Invalid filesize limit',
        ) from exc


def _parse_filename_format(yaml_dict: dict[str, Any]) -> str:
    """
    Parse the card filename format from the given YAML. This converts
    any "old" filename variables (e.g. {season} or {episode}) into their
    new equivalents.

    Args:
        yaml_dict: Dictionary of YAML to parse.

    Returns:
        The parsed (and converted) filename format. If the format is not
        in the specified YAML, then UNSPECIFIED is returned.

    Raises:
        HTTPException (422) if the format cannot be parsed.
    """

    # If no YAML or no EDS indicated, return None
    if (not isinstance(yaml_dict, dict)
        or (filename_format := yaml_dict.get('filename_format')) is None):
        return UNSPECIFIED

    if not isinstance(filename_format, str):
        raise HTTPException(
            status_code=422,
            detail=f'Invalid filename format',
        )

    return filename_format\
        .replace('{name}', '{series_name}')\
        .replace('{full_name}', '{series_full_name}')\
        .replace('{season}', '{season_number}')\
        .replace('{season:02}', '{season_number:02}')\
        .replace('{episode}', '{episode_number}')\
        .replace('{episode:02}', '{episode_number:02}')\
        .replace('{abs_number}', '{absolute_number}')\
        .replace('{abs_number:02}', '{absolute_number:02}')


def _parse_season_folder_format(yaml_dict: dict[str, Any]) -> str:
    """
    Parse the season folder format from the given YAML. This converts
    any "old" variables (e.g. {season} or {episode}) into their new
    equivalents.

    Args:
        yaml_dict: Dictionary of YAML to parse.

    Returns:
        The parsed (and converted) season folder format. If the format
        is not in the specified YAML, then UNSPECIFIED is returned.

    Raises:
        HTTPException (422): The format cannot be parsed.
    """

    # If no YAML or no EDS indicated, return None
    if (not isinstance(yaml_dict, dict)
        or (folder_format := yaml_dict.get('season_folder_format')) is None):
        return UNSPECIFIED

    if not isinstance(folder_format, str):
        raise HTTPException(
            status_code=422,
            detail=f'Invalid season folder format',
        )

    return folder_format\
        .replace('{name}', '{series_name}')\
        .replace('{full_name}', '{series_full_name}')\
        .replace('{season}', '{season_number}')\
        .replace('{season:02}', '{season_number:02}')\
        .replace('{episode}', '{episode_number}')\
        .replace('{episode:02}', '{episode_number:02}')\
        .replace('{abs_number}', '{absolute_number}')\
        .replace('{abs_number:02}', '{absolute_number:02}')


def _remove_unspecifed_args(**dict_kwargs: dict) -> dict:
    """
    Remove unspecified arguments.

    Args:
        dict_kwargs: Any number of keyword arguments to parse.

    Returns:
        `dict_kwargs` where any keys whose corresponding value was equal
        to `UNSPECIFIED` are omitted.
    """

    return {
        key: value for key, value in dict_kwargs.items()
        if value != UNSPECIFIED
    }


def parse_preferences(
        preferences: Preferences,
        yaml_dict: dict,
        *,
        log: Logger = log,
    ) -> Preferences:
    """
    Modify the preferences for the given YAML.

    Args:
        preferences: Preferences to modify.
        yaml_dict: Dictionary of YAML attributes to parse.
        log: Logger for all log messages.

    Returns:
        Modified Preferences.

    Raises:
        HTTPException (422) if there are any YAML formatting errors.
        Pydantic ValidationError if an object cannot be created from the
            given YAML.
    """

    # Shorthand for an unspecified value
    unsp = UNSPECIFIED

    # Get options section
    options = _get(yaml_dict, 'options', default={})

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
            'emby': 'Emby', 'jellyfin': 'Jellyfin',
            'plex': 'Plex', 'tmdb': 'TMDb'
        }
        image_source_priority = [
            mapping[source]
            for source in isp.lower().replace(' ', '').split(',')
            if source in mapping
        ]

    # Parse episode data source
    episode_data_source = _parse_episode_data_source(options)
    if episode_data_source is None:
        episode_data_source = UNSPECIFIED

    # Create UpdatePreferenes object from the YAML
    update_preferences = UpdatePreferences(**_remove_unspecifed_args(
        source_directory=_get(options, 'source', default=unsp),
        card_width=_get(options, 'card_dimensions', type_=Width, default=unsp),
        card_height=_get(options, 'card_dimensions', type_=Height, default=unsp),
        card_filename_format=_parse_filename_format(options),
        card_extension=_get(options, 'card_extension', type_=Extension, default=unsp),
        image_source_priority=image_source_priority,
        episode_data_source=episode_data_source,
        season_folder_format=_parse_season_folder_format(options),
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
        ),
    ))

    preferences.update_values(log=log, **update_preferences.dict())
    refresh_imagemagick_interface()
    preferences.determine_imagemagick_prefix(log=log)

    return preferences


def parse_emby(
        db: Session,
        yaml_dict: dict,
        *,
        log: Logger = log,
    ) -> None:
    """
    Update the Emby connection details for the given YAML. This either
    modifies the first existing Emby Connection, if one exists, or
    creates a new Connection with the parsed details.

    Args:
        db: Database to query for an existing Connection to modify, or
            to add the new Connection to.
        yaml_dict: Dictionary of YAML attributes to parse.
        log: Logger for all log messages.

    Raises:
        HTTPException (422): There are any YAML formatting errors.
        ValidationError: The YAML cannot be parsed into valid Connection
            details.
    """

    # Skip if no section
    if not isinstance(yaml_dict, dict) or 'emby' not in yaml_dict:
        return None

    # Get emby options
    emby = _get(yaml_dict, 'emby', default={})

    # If there is an existing Connection, update instead of create
    existing = db.query(Connection).filter_by(interface_type='Emby').first()
    if existing:
        update_obj = UpdateEmby(**_remove_unspecifed_args(
            url=_get(emby, 'url', type_=str, default=UNSPECIFIED),
            api_key=_get(emby, 'api_key', default=UNSPECIFIED),
            username=_get(emby, 'username', type_=str, default=UNSPECIFIED),
            use_ssl=_get(emby, 'verify_ssl', type_=bool, default=UNSPECIFIED),
            filesize_limit=_parse_filesize_limit(emby),
        ))
        update_connection(
            db, existing.id, get_emby_interfaces(), update_obj, log=log,
        )

        return None

    # New Connection
    new_obj = NewEmbyConnection(
        url=_get(emby, 'url', type_=str),
        api_key=_get(emby, 'api_key', type_=str),
        use_ssl=_get(emby, 'verify_ssl', type_=bool, default=True),
        filesize_limit=_parse_filesize_limit(emby),
        username=_get(emby, 'username', type_=str, default=None),
    )
    add_connection(db, new_obj, get_emby_interfaces(), log=log)

    return None


def parse_jellyfin(
        db: Session,
        yaml_dict: dict,
        *,
        log: Logger = log,
    ) -> None:
    """
    Update the Jellyfin connection details for the given YAML. This
    either modifies the first existing Jellyfin Connection, if one
    exists, or creates a new Connection with the parsed details.

    Args:
        db: Database to query for an existing Connection to modify, or
            to add the new Connection to.
        yaml_dict: Dictionary of YAML attributes to parse.
        log: Logger for all log messages.

    Raises:
        HTTPException (422): There are any YAML formatting errors.
        ValidationError: The YAML cannot be parsed into valid Connection
            details.
    """

    # Skip if no section
    if not isinstance(yaml_dict, dict) or 'jellyfin' not in yaml_dict:
        return None

    # Get jellyfin options
    jellyfin = _get(yaml_dict, 'jellyfin', default={})

    # If there is an existing Jellyfin interface, update instead of create
    existing = db.query(Connection).filter_by(interface_type='Jellyfin').first()
    if existing:
        # Create Update object from these arguments
        update_obj = UpdateJellyfin(**_remove_unspecifed_args(
            url=_get(jellyfin, 'url', type_=str, default=UNSPECIFIED),
            api_key=_get(jellyfin, 'api_key', default=UNSPECIFIED),
            username=_get(jellyfin, 'username', type_=str, default=UNSPECIFIED),
            use_ssl=_get(jellyfin, 'verify_ssl', type_=bool, default=UNSPECIFIED),
            filesize_limit=_parse_filesize_limit(jellyfin),
        ))
        update_connection(
            db, existing.id, get_jellyfin_interfaces(), update_obj, log=log,
        )

        return None

    # New connection
    new_obj = NewJellyfinConnection(
        url=_get(jellyfin, 'url', type_=str),
        api_key=_get(jellyfin, 'api_key', type_=str),
        use_ssl=_get(jellyfin, 'verify_ssl', type_=bool, default=True),
        filesize_limit=_parse_filesize_limit(jellyfin),
        username=_get(jellyfin, 'username', type_=str, default=None),
    )
    add_connection(db, new_obj, get_jellyfin_interfaces(), log=log)

    return None


def parse_plex(
        db: Session,
        yaml_dict: dict,
        *,
        log: Logger = log,
    ) -> None:
    """
    Update the Plex connection details for the given YAML. This either
    modifies the first existing Plex Connection, if one exists, or
    creates a new Connection with the parsed details.

    Args:
        db: Database to query for an existing Connection to modify, or
            to add the new Connection to.
        yaml_dict: Dictionary of YAML attributes to parse.
        log: Logger for all log messages.

    Raises:
        HTTPException (422): There are any YAML formatting errors.
        ValidationError: The YAML cannot be parsed into valid Connection
            details.
    """

    # Skip if no section
    if not isinstance(yaml_dict, dict) or 'plex' not in yaml_dict:
        return None

    # Get jellyfin options
    plex = _get(yaml_dict, 'plex', default={})

    # If there is an existing Plex interface, update instead of create
    existing = db.query(Connection).filter_by(interface_type='Plex').first()
    if existing:
        # Create Update object from these arguments
        update_obj = UpdatePlex(**_remove_unspecifed_args(
            url=_get(plex, 'url', type_=str, default=UNSPECIFIED),
            api_key=_get(plex, 'token', default=UNSPECIFIED),
            use_ssl=_get(plex, 'verify_ssl', type_=bool, default=UNSPECIFIED),
            filesize_limit=_parse_filesize_limit(plex),
            integrate_with_pmm=_get(
                plex, 'integrate_with_pmm_overlays',
                type_=bool,
                default=UNSPECIFIED
            ),
        ))
        update_connection(
            db, existing.id, get_plex_interfaces(), update_obj, log=log,
        )

        return None

    # New connection
    new_obj = NewPlexConnection(
        url=_get(plex, 'url', type_=str),
        api_key=_get(plex, 'api_key', type_=str),
        use_ssl=_get(plex, 'verify_ssl', type_=bool, default=True),
        filesize_limit=_parse_filesize_limit(plex),
        integrate_with_pmm=_get(plex, 'integrate_with_pmm_overlays', type_=bool)
    )
    add_connection(db, new_obj, get_emby_interfaces(), log=log)

    return None


def parse_sonarr(
        db: Session,
        yaml_dict: dict,
        *,
        log: Logger = log,
    ) -> None:
    """
    Update the Sonarr connection details for the given YAML. This either
    modifies the first existing Sonarr Connection, if one exists, or
    creates a new Connection with the parsed details.

    Args:
        db: Database to query for an existing Connection to modify, or
            to add the new Connection to.
        yaml_dict: Dictionary of YAML attributes to parse.
        log: Logger for all log messages.

    Raises:
        HTTPException (422): There are any YAML formatting errors.
        ValidationError: The YAML cannot be parsed into valid Connection
            details.
    """

    # Skip if no section
    if not isinstance(yaml_dict, dict) or 'sonarr' not in yaml_dict:
        return None

    # Get sonarr options, format as list of servers
    sonarrs = _get(yaml_dict, 'sonarr', default={})
    if isinstance(sonarrs, dict):
        sonarrs = [sonarrs]

    all_existing = db.query(Connection).filter_by(interface_type='Emby').all()
    for id_, sonarr in enumerate(sonarr):
        # Existing Connection, update instead of create
        if id_ < len(all_existing):
            update_obj = UpdateSonarr(**_remove_unspecifed_args(
                url=_get(sonarr, 'url', type_=str, default=UNSPECIFIED),
                api_key=_get(sonarr, 'token', default=UNSPECIFIED),
                use_ssl=_get(sonarr, 'verify_ssl', type_=bool, default=UNSPECIFIED),
                downloaded_only=_get(
                    sonarr, 'downloaded_only', type_=bool, default=UNSPECIFIED
                ),
            ))
            update_connection(
                db, all_existing[id_].id, get_sonarr_interfaces(), update_obj,
                log=log,
            )

            return None

        # New connection
        new_obj = NewSonarrConnection(
            url=_get(sonarr, 'url', type_=str),
            api_key=_get(sonarr, 'api_key', type_=str),
            use_ssl=_get(sonarr, 'verify_ssl', type_=bool, default=True),
            downloaded_only=_get(sonarr, 'downloaded_only', type_=bool, default=True),
        )
        add_connection(db, new_obj, get_sonarr_interfaces(), log=log)

    return None


def parse_tmdb(
        db: Session,
        yaml_dict: dict,
        *,
        log: Logger = log,
    ) -> None:
    """
    Update the TMDb connection details for the given YAML. This either
    modifies the first existing TMDb Connection, if one exists, or
    creates a new Connection with the parsed details.

    Args:
        db: Database to query for an existing Connection to modify, or
            to add the new Connection to.
        yaml_dict: Dictionary of YAML attributes to parse.
        log: Logger for all log messages.

    Raises:
        HTTPException (422): There are any YAML formatting errors.
        ValidationError: The YAML cannot be parsed into valid Connection
            details.
    """

    # Skip if no section
    if not isinstance(yaml_dict, dict) or 'tmdb' not in yaml_dict:
        return None

    # Get tmdb options
    tmdb = _get(yaml_dict, 'tmdb', default={})

    SplitList = lambda s: str(s).lower().replace(' ', '').split(',')

    # If there is an existing Connection, update instead of create
    existing = db.query(Connection).filter_by(interface_type='TMDb').first()
    if existing:
        update_obj = UpdateTMDb(**_remove_unspecifed_args(
            api_key=_get(tmdb, 'api_key', default=UNSPECIFIED),
            minimum_dimensions=_get(
                tmdb, 'minimum_resolution', default=UNSPECIFIED
            ),
            skip_localized=_get(
                tmdb,
                'skip_localized_images',
                type_=bool, default=UNSPECIFIED,
            ), logo_language_priority=_get(
                tmdb,
                'logo_language_priority',
                type_=SplitList, default=UNSPECIFIED,
            ),
        ))
        update_connection(
            db, existing.id, get_tmdb_interfaces(), update_obj, log=log
        )

        return None

    # New Connection
    new_obj = NewTMDbConnection(
        api_key=_get(tmdb, 'api_key', type_=str),
        minimum_dimensions=_get(tmdb, 'minimum_resolution', default='0x0'),
        skip_localized=_get(
            tmdb, 'skip_localized_images', type_=bool, default=True
        ),
        logo_language_priority=_get(
            tmdb, 'logo_language_priority', type_=SplitList, default=['en']
        ),
    )
    add_connection(db, new_obj, get_tmdb_interfaces(), log=log)

    return None


def parse_syncs(
        db: Session,
        yaml_dict: dict[str, Any],
    ) -> list[Union[NewEmbySync, NewJellyfinSync, NewPlexSync, NewSonarrSync]]:
    """
    Create NewSync objects for all defined syncs in the given YAML.

    Args:
        db: Database to query for Templates (if indicated).
        yaml_dict: Dictionary of YAML attributes to parse.

    Returns:
        List of New*Sync objects corresponding to each indicated sync
        defined in the YAML.

    Raises:
        HTTPException (404): An indicated Template cannot be found in
            the database.
        HTTPException (422): YAML formatting errors.
        ValidationError: An New*Sync object cannot be created from the
            given YAML.
    """

    def _get_templates(sync: dict[str, Any]) -> list[int]:
        if 'add_template' not in sync:
            return []

        template = db.query(models.template.Template)\
            .filter_by(name=sync['add_template'])\
            .first()
        if template is None:
            raise HTTPException(
                status_code=404,
                detail=f'Template "{sync["add_template"]}" not found',
            )
        return [template.id]

    def _parse_media_server_sync(
            yaml_dict: dict[str, Any],
            connection: Connection,
            NewSyncClass: Union[NewEmbySync, NewJellyfinSync, NewPlexSync]
        ) -> Union[list[NewEmbySync], list[NewJellyfinSync], list[NewPlexSync]]:
        """
        Inner function to parse the Sync definition of a media server.

        Args:
            yaml_dict: Dictionary of YAML attributes to parse.
            connection: Connection to associate the imported Syncs with.
            NewSyncClass: Class to instantiate with the parsed arguments

        Returns:
            List of instantiated NewSyncClass objects for all Syncs
            defined in the given YAML.
        """

        # Create New*Sync object for each defined sync
        syncs = yaml_dict if isinstance(yaml_dict, list) else [yaml_dict]
        all_syncs = []
        for sync_id, sync in enumerate(syncs):
            # Skip invalid syncs, and those not being written to files
            if not isinstance(sync, dict) or 'file' not in sync:
                continue

            # Merge the first sync settings into this one
            TieredSettings(sync, syncs[0], sync)

            # Get excluded tags
            excluded_tags = [
                list(exclusion.values())[0] for exclusion in _get(
                    sync, 'exclusions', type_=list, default=[]
                ) if list(exclusion.keys())[0] == 'tag'
            ]

            # Add object to list
            all_syncs.append(NewSyncClass(**_remove_unspecifed_args(
                interface_id=connection.id,
                name=f'Imported {connection.name} Sync {sync_id+1}',
                templates=_get_templates(sync),
                required_tags=_get(sync, 'required_tags',type_=list,default=[]),
                excluded_tags=excluded_tags,
                required_libraries=_get(sync, 'libraries',type_=list,default=[])
            )))

        return all_syncs

    # Add Syncs for each defined section
    all_syncs = []
    if (emby := _get(yaml_dict, 'emby', 'sync')) is not None:
        connection = db.query(Connection)\
            .filter_by(interface_type='Emby')\
            .first()
        if connection:
            all_syncs += _parse_media_server_sync(emby, connection, NewEmbySync)
        else:
            log.warning(f'Cannot import Emby Syncs, no valid Connection')

    if (jellyfin := _get(yaml_dict, 'jellyfin', 'sync')) is not None:
        connection = db.query(Connection)\
            .filter_by(interface_type='Jellyfin')\
            .first()
        if connection:
            all_syncs += _parse_media_server_sync(
                jellyfin, connection, NewJellyfinSync
            )
        else:
            log.warning(f'Cannot import Jellyfin Syncs, no valid Connection')

    if (plex := _get(yaml_dict, 'plex', 'sync')) is not None:
        connection = db.query(Connection)\
            .filter_by(interface_type='Plex')\
            .first()
        if connection:
            all_syncs += _parse_media_server_sync(plex, connection, NewPlexSync)
        else:
            log.warning(f'Cannot import Plex Syncs, no valid Connection')

    sonarrs = _get(yaml_dict, 'sonarr')
    sonarrs = sonarrs if isinstance(sonarrs, list) else [sonarrs]
    all_existing = db.query(Connection).filter_by(interface_type='Sonarr').all()
    for id_, sonarr in enumerate(sonarrs):
        # No associated Connection to import into
        if id_ > len(all_existing):
            log.warning(f'Cannot import Sonarr syncs for Connection[{id_}] - '
                        f'no valid Connection')
            break
        existing = all_existing[id_]

        if (syncs := _get(sonarr, 'sync')) is not None:
            syncs = syncs if isinstance(syncs, list) else [syncs]
            for sync_id, sync in enumerate(syncs):
                # Skip invalid syncs, and those not being written to files
                if not isinstance(sync, dict) or 'file' not in sync:
                    continue

                # Merge the first sync settings into this one
                TieredSettings(sync, syncs[0], sync)

                # Get excluded tags
                excluded_tags = [
                    list(exclusion.values())[0] for exclusion in _get(
                        sync, 'exclusions', type_=list, default=[]
                    ) if list(exclusion.keys())[0] == 'tag'
                ]

                # Add object to list
                all_syncs.append(NewSonarrSync(**_remove_unspecifed_args(
                    interface_id=existing.id,
                    name=f'Imported {existing.name} Sync {sync_id+1}',
                    template_ids=_get_templates(sync),
                    required_tags=_get(sync, 'required_tags', type_=list, default=[]),
                    excluded_tags=excluded_tags,
                    required_series_type=_get(sync, 'series_type'),
                    downloaded_only=_get(sync, 'downloaded_only', type_=bool, default=False),
                    monitored_only=_get(sync, 'monitored_only', type_=bool, default=False),
                )))

    return all_syncs


def parse_fonts(yaml_dict: dict) -> list[tuple[NewNamedFont, Optional[Path]]]:
    """
    Create NewNamedFont objects for any defined fonts in the given
    YAML.

    Args:
        yaml_dict: Dictionary of YAML attributes to parse.

    Returns:
        List of tuples of each new Font object and the Path to the
        listed Font file for that Font.

    Raises:
        HTTPException (422) if there are any YAML formatting errors.
        Pydantic ValidationError if a NewTemplate object cannot be
            created from the given YAML.
    """

    # Return empty list if no header
    if 'fonts' not in yaml_dict:
        return []
    all_fonts = yaml_dict['fonts']

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

        # Create New Font with all indicated customization
        new_font = NewNamedFont(**_remove_unspecifed_args(
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
        fonts.append((new_font, _get(font_dict, 'file', type_=Path)))

    return fonts


def parse_templates(
        db: Session,
        preferences: Preferences,
        yaml_dict: dict[str, Any]
    ) -> list[NewTemplate]:
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

    # Return empty list if no header
    if 'templates' not in yaml_dict:
        return []
    all_templates = yaml_dict['templates']

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

        # Remove logo, as this is built-in
        extras.pop('logo', None)

        # Create NewTemplate with all indicated customization
        templates.append(NewTemplate(**_remove_unspecifed_args(
            name=str(template_name),
            card_filename_format=_get(template_dict, 'filename_format'),
            episode_data_source=_parse_episode_data_source(template_dict),
            sync_specials=_get(template_dict, 'sync_specials', type_=bool),
            translations=_parse_translations(template_dict, default=[]),
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
        )))

    return templates


def parse_series(
        db: Session,
        preferences: Preferences,
        yaml_dict: dict[str, Any],
        *,
        log: Logger = log,
    ) -> list[NewSeries]:
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
        log: Logger for all log messages.

    Returns:
        List of NewSeries that match any defined YAML series.

    Raises:
        HTTPException (404): An indicated Font or Template name cannot
            be found in the database.
        HTTPException (422): There are YAML formatting errors.
        ValidationError: NewSeries object cannot be created from the
            given YAML.
    """

    # Return empty list if no header
    if 'series' not in yaml_dict:
        return []
    all_series = yaml_dict['series']

    # If not a dictionary of series, return empty list
    if not isinstance(all_series, dict):
        return []

    # Parse library section
    yaml_libraries = _get(yaml_dict, 'libraries', type_=dict, default={})

    # Create NewSeries objects for all listed Series
    series = []
    for series_name, series_dict in all_series.items():
        # Skip if not a dictionary
        if not isinstance(series_dict, dict):
            raise HTTPException(
                status_code=422,
                detail=f'Invalid Series "{series_name}"',
            )

        # Finalize with PreferenceParser
        series_dict = PreferenceParser.finalize_show_yaml(
            _get(series_dict, 'name', type_=str, default=series_name),
            series_dict,
            {}, # Assign Templates, do not merge
            yaml_libraries,
            {}, # assign Fonts, do not merge
            raise_exc=True,
        )

        # If None, then finalization failed
        if series_dict is None:
            raise HTTPException(
                status_code=422,
                detail=f'Unable to finalize YAML for {series_name}',
            )
        log.debug(f'Finalized YAML {series_dict}')

        # Create SeriesInfo for this series - parsing name/year/ID's
        try:
            series_info = SeriesInfo(
                _get(series_dict, 'name', type_=str, default=series_name),
                _get(series_dict, 'year', type_=int, default=None),
                imdb_id=_get(series_dict, 'imdb_id', default=None),
                tmdb_id=_get(series_dict, 'tmdb_id', default=None),
                tvdb_id=_get(series_dict, 'tvdb_id', default=None),
                tvrage_id=_get(series_dict, 'tvrage_id', default=None),
            )
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=f'Series "{series_name}" is missing the required year',
            ) from e

        # Parse custom Font
        series_font = _get(series_dict, 'font', default={})
        font_id = None
        if not isinstance(series_font, (str, dict)):
            raise HTTPException(
                status_code=422,
                detail=f'Unrecognized Font in Series "{series_info}"',
            )
        if isinstance(series_font, str):
            # Get Font ID of this Font (if indicated)
            font = db.query(models.font.Font)\
                .filter_by(name=series_font).first()
            if font is None:
                raise HTTPException(
                    status_code=404,
                    detail=f'Font "{series_font}" not found',
                )
            font_id = font.id

        # Get the assigned template name ID
        series_template = _get(series_dict, 'template', default={})
        if isinstance(series_template, str):
            template_name = series_template
        elif isinstance(series_template, dict):
            template_name = _get(series_template, 'name', default='Unnamed')
        else:
            raise HTTPException(
                status_code=422,
                detail=f'Unrecognized Template in Series "{series_info}"',
            )

        # Look for Template with this name
        template_id: Optional[int] = db.query(models.template.Template.id)\
            .filter_by(name=template_name)\
            .first()
        if series_template and not template_id:
            raise HTTPException(
                status_code=404,
                detail=f'Template "{template_name}" not found',
            )

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

        # Assign library
        libraries = []
        if (library_name := _get(series_dict, 'library', 'name')):
            # No explicit server specification, use global enables
            if not (media_server := _get(series_dict, 'library', 'media_server')):
                if preferences.use_emby:
                    media_server = 'Emby'
                elif preferences.use_jellyfin:
                    media_server = 'Jellyfin'
                else:
                    media_server = 'Plex'

            # Get first Connection for this server type
            connection = db.query(models.connection.Connection)\
                .filter_by(interface_type=media_server.title())\
                .first()
            if connection:
                libraries.append({
                    'interface_id': connection.id,
                    'interface': connection.interface_type,
                    'name': library_name
                })
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f'Invalid library assignment in" {series_info}"'
                )

        # Create NewTemplate with all indicated customization
        series.append(NewSeries(**_remove_unspecifed_args(
            name=series_info.name,
            year=series_info.year,
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
            translations=_parse_translations(series_dict, default=None),
            template_id=template_id,
            font_id=font_id,
            font_color=_get(series_dict, 'font', 'color'),
            font_title_case=_get(series_dict, 'font', 'case'),
            font_size=_get(
                series_dict,
                'font', 'size',
                type_=Percentage
            ), font_kerning=_get(
                series_dict,
                'font', 'kerning',
                type_=Percentage
            ), font_stroke_width=_get(
                series_dict,
                'font', 'stroke_width',
                type_=Percentage
            ), font_interline_spacing=_get(
                series_dict,
                'font', 'interline_spacing',
                type_=int
            ), font_vertical_shift=_get(
                series_dict,
                'font', 'vertical_shift',
                type_=int
            ), directory=_get(series_dict, 'media_directory'),
            libraries=libraries,
            **series_info.ids,
            season_title_ranges=list(season_titles.keys()),
            season_title_values=list(season_titles.values()),
            hide_season_text=_get(series_dict, 'seasons', 'hide', type_=bool),
            episode_text_format=_get(series_dict, 'episode_text_format'),
            hide_episode_text=_get(series_dict, 'hide_episode_text', type_=bool),
            extra_keys=list(extras.keys()),
            extra_values=list(extras.values()),
        )))

    return series


def import_cards(
        db: Session,
        series: Series,
        directory: Optional[Path],
        image_extension: CardExtension,
        force_reload: bool,
        *,
        log: Logger = log,
    ) -> None:
    """
    Import any existing Title Cards for the given Series. This finds
    card files by filename, and makes the assumption that each file
    exactly matches the Episode's currently specified config.

    Args:
        db: Database to query for existing Cards.
        series: Series whose Cards are being imported.
        directory: Directory to search for Cards to import. If omitted,
            then the Series default card directory is used.
        image_extension: Extension of images to search for.
        force_reload: Whether to replace any existing Card entries for
            Episodes identified while importing.
        log: Logger for all log messages.
    """

    # If explicit directory was not provided, use Series default
    if directory is None:
        directory = series.card_directory

    # Glob directory for images to import
    all_images = list(directory.glob(f'**/*{image_extension}'))

    # No images to import, return
    if len(all_images) == 0:
        log.debug(f'No Cards identified within "{directory}" to import')
        return None

    # For each image, identify associated Episode
    for image in all_images:
        if (groups := match(r'.*s(\d+).*e(\d+)', image.name, IGNORECASE)):
            season_number, episode_number = map(int, groups.groups())
        else:
            log.warning(f'Cannot identify index of {image.resolve()} - skipping')
            continue

        # Find associated Episode
        episode = db.query(models.episode.Episode).filter(
            models.episode.Episode.series_id==series.id,
            models.episode.Episode.season_number==season_number,
            models.episode.Episode.episode_number==episode_number,
        ).first()

        # No associated Episode, skip
        if episode is None:
            log.warning(f'{series.log_str} No associated Episode for '
                        f'{image.resolve()} - skipping')
            continue

        # Episode has an existing Card, skip if not forced
        # TODO evaluate w/ multi-conn
        if episode.cards and not force_reload:
            log.debug(f'{series.log_str} {episode.log_str} has an associated Card - skipping')
            continue

        # Episode has card, delete if reloading
        # TODO evaluate w/ force-reload and multi-conn
        if episode.cards and force_reload:
            for card in episode.cards:
                log.debug(f'{card.log_str} deleting record')
                db.query(models.card.Card).filter_by(id=card.id).delete()
                log.debug(f'{series.log_str} {episode.log_str} has associated '
                          f'Card - reloading')

        # Get finalized Card settings for this Episode, override card file
        try:
            # TODO eval w/ library?
            card_settings = resolve_card_settings(episode, log=log)
        except HTTPException as e:
            log.exception(f'{series.log_str} {episode.log_str} Cannot import '
                          f'Card - settings are invalid {e}', e)
            continue

        # Get a validated card class, and card type Pydantic model
        _, CardTypeModel = validate_card_type_model(card_settings, log=log)

        # Card is valid, create and add to Database
        card_settings['card_file'] = image
        title_card = NewTitleCard(
            **card_settings,
            series_id=series.id,
            episode_id=episode.id,
        )

        # TODO revise w/ multi-conn
        card = add_card_to_database(db, title_card, card_settings['card_file'])
        log.debug(f'{series.log_str} {episode.log_str} Imported {image.resolve()}')

    return None
