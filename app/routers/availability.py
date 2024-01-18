from datetime import datetime, timedelta
from logging import Logger
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from requests import get as req_get
from sqlalchemy.orm import Session

from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.auth import get_current_user
from app.internal.availability import get_latest_version
from app import models
from app.models.preferences import Preferences
from app.models.template import OPERATIONS, ARGUMENT_KEYS
from app.schemas.availability import (
    AvailableFont, AvailableSeries, AvailableTemplate, TranslationLanguage
)
from app.schemas.card import (
    BuiltinCardType, CardTypeDescription, LocalCardType, RemoteCardType
)
from app.schemas.card_type import Extra
from app.schemas.preferences import StyleOption
from app.schemas.series import MediaServerLibrary
from app.schemas.sync import Tag

from modules.cards.available import LocalCards
from modules.Debug import log


# URL for user card types
USER_CARD_TYPE_URL = (
    'https://raw.githubusercontent.com/CollinHeist/TitleCardMaker-CardTypes/'
    'web-ui/cards.json'
)

# Extra variable overrides
VARIABLE_OVERRIDES = [
    Extra(
        name='Title Text Format', identifier='title_text_format',
        description='How to format title text',
        tooltip=(
            'Applies after all Font replacements, casing, etc. See '
            'documentation for full list of supported variables.'
        ),
    ), Extra(
        name='Season Text Format', identifier='season_text_format',
        description='How to format season text',
        tooltip=(
            'Applies after any season title ranges. See documentation for full '
            'list of supported variables.'
        ),
    ), Extra(
        name='Logo Filepath', identifier='logo_file',
        description='Logo file name or file name format string',
        tooltip=(
            'Override the specific logo file. This is relative to the Series '
            'source directory.'
        ),
    )
]


def _get_local_cards(preferences: Preferences) -> list[LocalCardType]:
    """
    Get the list of availably locally specified card types.

    Args:
        preferences: Global preferences.

    Returns:
        List of LocalCardType objects.
    """

    return [
        card_class.API_DETAILS
        for card_class in preferences.local_card_types.values()
    ]


_cache = {'content': [], 'expires': datetime.now()}
def _get_remote_cards(*, log: Logger = log) -> list[RemoteCardType]:
    """
    Get the list of available RemoteCardTypes. This will cache results
    for 30 minutes. If the available data is older than 30 minutes, the
    GitHub is re-queried.

    Args:
        log: Logger for all log messages.

    Returns:
        List of RemoteCardTypes.
    """

    # If the cached content has expired, request and update cache
    if _cache['expires'] <= datetime.now():
        log.debug(f'Refreshing cached RemoteCardTypes..')
        response = req_get(USER_CARD_TYPE_URL, timeout=30).json()
        _cache['content'] = response
        _cache['expires'] = datetime.now() + timedelta(hours=6)
    # Cache has not expired, use cached content
    else:
        response = _cache['content']

    return [RemoteCardType(**card) for card in response]


# Create sub router for all /connection API requests
availablility_router = APIRouter(
    prefix='/available',
    tags=['Availability'],
    dependencies=[Depends(get_current_user)],
)


@availablility_router.get('/version', status_code=200)
def get_latest_available_version(request: Request) -> Optional[str]:
    """
    Get the latest version number for TitleCardMaker.
    """

    return get_latest_version(log=request.state.log)


@availablility_router.get('/card-types', status_code=200, tags=['Title Cards'])
def get_all_available_card_types(
        request: Request,
        show_excluded: bool = Query(default=False),
        preferences: Preferences = Depends(get_preferences),
    ) -> list[CardTypeDescription]:
    """
    Get a list of all available card types (local and remote).

    - show_excluded: Whether to include globally excluded card types in
    the returned list.
    """

    # Get contextual logger
    log = request.state.log

    all_cards = LocalCards \
        + _get_local_cards(preferences) \
        + _get_remote_cards(log=log)
    if show_excluded:
        return all_cards

    return [
        card for card in all_cards
        if card.identifier not in preferences.excluded_card_types
    ]


@availablility_router.get('/card-types/builtin', status_code=200, tags=['Title Cards'])
def get_builtin_card_types() -> list[BuiltinCardType]:
    """
    Get all pre-built card types.
    """

    return LocalCards


@availablility_router.get('/card-types/local', status_code=200, tags=['Title Cards'])
def get_local_card_types(
        preferences: Preferences = Depends(get_preferences),
    ) -> list[LocalCardType]:
    """
    Get all locally defined card types.
    """

    return _get_local_cards(preferences)


@availablility_router.get('/card-types/remote', status_code=200, tags=['Title Cards'])
def get_remote_card_types(request: Request) -> list[RemoteCardType]:
    """
    Get all available remote card types.
    """

    try:
        return _get_remote_cards(log=request.state.log)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Error encountered while getting remote card types'
        ) from e


@availablility_router.get('/extras')
def get_all_supported_extras(
        request: Request,
        show_excluded: bool = Query(default=False),
        preferences: Preferences = Depends(get_preferences),
    ) -> list[Extra]:
    """
    Get details of all the available Extras for local and remote card
    types.

    - show_excluded: Whether to include globally excluded card types in
    the returned list.
    """

    locals = [
        {'card_type': identifier} | extra.dict()
        for identifier, CardClass in preferences.local_card_types.items()
        if (show_excluded or identifier not in preferences.excluded_card_types)
        for extra in CardClass.API_DETAILS.supported_extras
    ]

    return [
        {'card_type': card_type.identifier} | extra.dict()
        for card_type in LocalCards + _get_remote_cards(log=request.state.log)
        if (show_excluded
            or card_type.identifier not in preferences.excluded_card_types)
        for extra in card_type.supported_extras
    ] + locals + VARIABLE_OVERRIDES


@availablility_router.get('/template-filters', status_code=200, tags=['Templates'])
def get_available_template_filters() -> dict[str, list[str]]:
    """
    Get all available Tempalte filter condition argument and operation
    values.
    """

    return {
        'arguments': list(ARGUMENT_KEYS),
        'operations': list(OPERATIONS),
    }


@availablility_router.get('/translations', status_code=200)
def get_available_tmdb_translations() -> list[TranslationLanguage]:
    """
    Get all supported translations from TMDb.
    """

    return [
        {'language_code': code, 'language': language}
        for code, language in sorted(
            TMDbInterface.LANGUAGES.items(), key=lambda kv: kv[1]
        )
    ]


@availablility_router.get('/logo-languages', status_code=200)
def get_available_tmdb_logo_languages() -> list[dict]:
    """
    Get the list of available TMDb logo languages.
    """

    return [
        {'name': label, 'value': language_code}
        for language_code, label in TMDbInterface.LANGUAGES.items()
    ]


@availablility_router.get('/libraries/emby', status_code=200, tags=['Emby'])
def get_emby_libraries(
        emby_interface: EmbyInterface = Depends(require_emby_interface),
    ) -> list[MediaServerLibrary]:
    """
    Get all available libraries for the given Emby interface.
    """

    return [
        MediaServerLibrary(
            media_server='Emby',
            interface_id=emby_interface._interface_id,
            name=library,
        ) for library in emby_interface.get_libraries()
    ]


@availablility_router.get('/libraries/emby', status_code=200, tags=['Jellyfin'])
def get_jellyfin_libraries(
        jellyfin_interface: JellyfinInterface = Depends(require_jellyfin_interface),
    ) -> list[MediaServerLibrary]:
    """
    Get all available libraries for the given Jellyfin interface.
    """

    return [
        MediaServerLibrary(
            media_server='Jellyfin',
            interface_id=jellyfin_interface._interface_id,
            name=library,
        ) for library in jellyfin_interface.get_libraries()
    ]


@availablility_router.get('/libraries/plex', status_code=200, tags=['Plex'])
def get_plex_libraries(
        plex_interface: PlexInterface = Depends(require_plex_interface),
    ) -> list[MediaServerLibrary]:
    """
    Get all available libraries for the given Plex interface.
    """

    return [
        MediaServerLibrary(
            media_server='Plex',
            interface_id=plex_interface._interface_id,
            name=library,
        ) for library in plex_interface.get_libraries()
    ]


@availablility_router.get('/libraries/all', status_code=200,
                          tags=['Emby', 'Jellyfin', 'Plex'])
def get_server_libraries(
        emby_interfaces: InterfaceGroup[int, EmbyInterface] = Depends(get_emby_interfaces),
        jellyfin_interfaces: InterfaceGroup[int, JellyfinInterface] = Depends(get_jellyfin_interfaces),
        plex_interfaces: InterfaceGroup[int, PlexInterface] = Depends(get_plex_interfaces),
    ) -> list[MediaServerLibrary]:
    """
    Get all available libraries for all enabled interfaces.
    """

    libraries = []
    for interface_id, interface in emby_interfaces:
        libraries += [
            MediaServerLibrary(
                interface='Emby',
                interface_id=interface_id,
                name=library
            ) for library in interface.get_libraries()
        ]
    for interface_id, interface in jellyfin_interfaces:
        libraries += [
            MediaServerLibrary(
                interface='Jellyfin',
                interface_id=interface_id,
                name=library
            ) for library in interface.get_libraries()
        ]
    for interface_id, interface in plex_interfaces:
        libraries += [
            MediaServerLibrary(
                interface='Plex',
                interface_id=interface_id,
                name=library
            ) for library in interface.get_libraries()
        ]

    return libraries


@availablility_router.get('/usernames/emby', status_code=200, tags=['Emby'])
def get_emby_usernames(
        emby_interface: EmbyInterface = Depends(require_emby_interface),
    ) -> list[str]:
    """
    Get all the public usernames in Emby.
    """

    return emby_interface.get_usernames()


@availablility_router.get('/usernames/jellyfin', status_code=200, tags=['Jellyfin'])
def get_jellyfin_usernames(
        jellyfin_interface: EmbyInterface = Depends(require_jellyfin_interface),
    ) -> list[str]:
    """
    Get all the public usernames in Jellyfin.
    """

    return jellyfin_interface.get_usernames()


@availablility_router.get('/tags/sonarr', status_code=200, tags=['Sonarr'])
def get_sonarr_tags(
        sonarr_interfaces: InterfaceGroup[int, SonarrInterface] = Depends(get_sonarr_interfaces)
    ) -> list[Tag]:
    """
    Get all tags defined in all Sonarr interfaces.
    """

    tags = []
    for interface_id, interface in sonarr_interfaces:
        tags += [
            tag | {'interface_id': interface_id}
            for tag in interface.get_all_tags()
        ]

    return tags


@availablility_router.get('/fonts', status_code=200, tags=['Fonts'])
def get_available_fonts(
        db: Session = Depends(get_database),
    ) -> list[AvailableFont]:
    """
    Get all the available Font base data.
    """

    return db.query(models.font.Font).order_by(models.font.Font.sort_name).all()


@availablility_router.get('/series', status_code=200, tags=['Series'])
def get_available_series(
        db: Session = Depends(get_database),
    ) -> list[AvailableSeries]:
    """
    Get all the available Series base data.
    """

    return db.query(models.series.Series)\
        .order_by(models.series.Series.sort_name)\
        .order_by(models.series.Series.year)\
        .all()


@availablility_router.get('/templates', status_code=200, tags=['Templates'])
def get_available_templates(
        db: Session = Depends(get_database),
    ) -> list[AvailableTemplate]:
    """
    Get the names of all the available Templates.
    """

    return db.query(models.template.Template)\
        .order_by(models.template.Template.name)\
        .all()


@availablility_router.get('/styles', status_code=200)
def get_available_styles() -> list[StyleOption]:
    """
    Get all supported Styles.
    """

    return [
        {'name': 'Art', 'value': 'art', 'style_type': 'art'},
        {'name': 'Blurred Art', 'value': 'art blur', 'style_type': 'art'},
        {'name': 'Grayscale Art', 'value': 'art grayscale',
         'style_type': 'art'},
        {'name': 'Blurred Grayscale Art', 'value': 'art blur grayscale',
         'style_type': 'art'},
        {'name': 'Unique', 'value': 'unique', 'style_type': 'unique'},
        {'name': 'Blurred Unique', 'value': 'blur unique',
         'style_type': 'unique'},
        {'name': 'Grayscale Unique', 'value': 'grayscale unique',
         'style_type': 'unique'},
        {'name': 'Blurred Grayscale Unique', 'value': 'blur grayscale unique',
         'style_type': 'unique'},
    ]
