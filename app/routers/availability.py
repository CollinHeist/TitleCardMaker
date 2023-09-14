from datetime import datetime, timedelta
from logging import Logger
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from requests import get as req_get
from sqlalchemy.orm import Session

from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.auth import get_current_user
from app.internal.availability import get_latest_version
from app import models
from app.models.template import OPERATIONS, ARGUMENT_KEYS
from app.schemas.availability import (
    AvailableFont, AvailableSeries, AvailableTemplate
)
from app.schemas.card import CardType, LocalCardType, RemoteCardType
from app.schemas.card_type import Extra
from app.schemas.preferences import (
    EpisodeDataSourceToggle, Preferences, StyleOption
)
from app.schemas.sync import Tag

from modules.cards.available import LocalCards
from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface


# URL for user card types
USER_CARD_TYPE_URL = (
    'https://raw.githubusercontent.com/CollinHeist/TitleCardMaker-CardTypes/'
    'web-ui/cards.json'
)


_cache = {'content': [], 'expires': datetime.now()}
def _get_remote_cards(*, log: Logger = log) -> list[RemoteCardType]:
    """
    Get the list of available RemoteCardTypes. This will cache results
    for 30 minutes. If the available data is older than 30 minutes, the
    GitHub is re-queried.

    Args:
        log: (Keyword) Logger for all log messages.

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
    ) -> list[CardType]:
    """
    Get a list of all available card types (local and remote).

    - show_excluded: Whether to include globally excluded card types in
    the returned list.
    """

    # Get contextual logger
    log = request.state.log

    all_cards = LocalCards + _get_remote_cards(log=log)
    if show_excluded:
        return all_cards

    return [
        card for card in LocalCards + _get_remote_cards(log=log)
        if card.identifier not in preferences.excluded_card_types
    ]


@availablility_router.get('/card-types/local', status_code=200, tags=['Title Cards'])
def get_local_card_types() -> list[LocalCardType]:
    """
    Get all locally defined card types.
    """

    return LocalCards


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

    return [
        {'card_type': card_type.identifier} | extra.dict()
        for card_type in LocalCards + _get_remote_cards(log=request.state.log)
        if (show_excluded
            or card_type.identifier not in preferences.excluded_card_types)
        for extra in card_type.supported_extras
    ]


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
def get_available_tmdb_translations() -> list[dict[str, str]]:
    """
    Get all supported translations from TMDb.
    """

    return [
        {'language_code': code, 'language': language}
        for code, language in sorted(
            TMDbInterface.LANGUAGES.items(), key=lambda kv: kv[1]
        )
    ]


@availablility_router.get('/episode-data-sources', status_code=200)
def get_available_episode_data_sources(
        preferences: Preferences = Depends(get_preferences),
    ) -> list[EpisodeDataSourceToggle]:
    """
    Get all available (enabled) Episode data sources.
    """

    return [
        {'name': source,
         'value': source,
         'selected': source == preferences.episode_data_source}
        for source in preferences.valid_episode_data_sources
    ]


@availablility_router.get('/image-source-priority', status_code=200)
def get_image_source_priority(
        preferences: Preferences = Depends(get_preferences),
    ) -> list[EpisodeDataSourceToggle]:
    """
    Get the global image source priority.
    """

    return [
        {
            'name': source,
            'value': source,
            'selected': (source in preferences.image_source_priority)
        }
        for source in (set(preferences.image_source_priority)
                       | set(preferences.valid_image_sources))
    ]


@availablility_router.get('/libraries', status_code=200,
                          tags=['Emby', 'Jellyfin', 'Plex'])
def get_server_libraries(
        emby_interfaces: InterfaceGroup[int, EmbyInterface] = Depends(get_all_emby_interfaces),
        jellyfin_interfaces: InterfaceGroup[int, JellyfinInterface] = Depends(get_all_jellyfin_interfaces),
        plex_interfaces: InterfaceGroup[int, PlexInterface] = Depends(get_all_plex_interfaces),
    ) -> list[MediaServerLibrary]:
    """
    Get all available TV libraries for all enabled interfaces.
    """

    libraries = []
    for interface_id, interface in emby_interfaces:
        libraries += [
            MediaServerLibrary(
                media_server='Emby',
                interface_id=interface_id,
                name=library
            ) for library in interface.get_libraries()
        ]
    for interface_id, interface in jellyfin_interfaces:
        libraries += [
            MediaServerLibrary(
                media_server='Jellyfin',
                interface_id=interface_id,
                name=library
            ) for library in interface.get_libraries()
        ]
    for interface_id, interface in plex_interfaces:
        libraries += [
            MediaServerLibrary(
                media_server='Plex',
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
    Get all the public usernames in Emby. Returns an empty list if
    Emby is disabled.
    """

    return emby_interface.get_usernames()


@availablility_router.get('/usernames/jellyfin', status_code=200, tags=['Jellyfin'])
def get_jellyfin_usernames(
        jellyfin_interface: JellyfinInterface = Depends(require_jellyfin_interface),
    ) -> list[str]:
    """
    Get all the public usernames in the specified Jellyfin interface.
    """

    return jellyfin_interface.get_usernames()


@availablility_router.get('/tags/sonarr', status_code=200, tags=['Sonarr'])
def get_sonarr_tags(
        sonarr_interface: SonarrInterface = Depends(require_sonarr_interface)
    ) -> list[Tag]:
    """
    Get all tags defined in the specified Sonarr interface.
    """

    return sonarr_interface.get_all_tags()


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
