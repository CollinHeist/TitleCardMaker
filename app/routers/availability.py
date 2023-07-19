from datetime import datetime, timedelta
from logging import Logger
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from requests import get as req_get
from sqlalchemy.orm import Session

from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app.internal.availability import get_latest_version
from app import models
from app.models.template import OPERATIONS, ARGUMENT_KEYS
from app.schemas.card import CardType, LocalCardType, RemoteCardType
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
        log.debug(f'Refreshing cached RemoteCardTypes')
        response = req_get(USER_CARD_TYPE_URL, timeout=10).json()
        _cache['content'] = response
        _cache['expires'] = datetime.now() + timedelta(minutes=30)
    # Cache has not expired, use cached content
    else:
        response = _cache['content']

    return [RemoteCardType(**card) for card in response]


# Create sub router for all /connection API requests
availablility_router = APIRouter(
    prefix='/available',
    tags=['Availability'],
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
        preferences: Preferences = Depends(get_preferences)
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


@availablility_router.get('/libraries/{media_server}', status_code=200,
                          tags=['Emby', 'Jellyfin', 'Plex'])
def get_server_libraries(
        media_server: Literal['emby', 'jellyfin', 'plex'],
        preferences: Preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
        plex_interface: Optional[PlexInterface] = Depends(get_plex_interface),
    ) -> list[str]:
    """
    Get all available TV library names on the given media server.

    - media_server: Which media server to get the library names of.
    """

    if media_server == 'emby':
        if preferences.use_emby and emby_interface:
            return emby_interface.get_libraries()
        return []
    if media_server == 'jellyfin':
        if preferences.use_jellyfin and jellyfin_interface:
            return jellyfin_interface.get_libraries()
        return []
    if media_server == 'plex':
        if preferences.use_plex and plex_interface:
            return plex_interface.get_libraries()
        return []

    raise HTTPException(
        status_code=400,
        detail=f'Cannot get libraries for the "{media_server}" media server'
    )


@availablility_router.get('/usernames/emby', status_code=200, tags=['Emby'])
def get_emby_usernames(
        preferences: Preferences = Depends(get_preferences),
        emby_interface: Optional[EmbyInterface] = Depends(get_emby_interface),
    ) -> list[str]:
    """
    Get all the public usernames in Emby. Returns an empty list if
    Emby is disabled.
    """

    if preferences.use_emby and emby_interface:
        return emby_interface.get_usernames()

    return []


@availablility_router.get('/usernames/jellyfin', status_code=200, tags=['Jellyfin'])
def get_jellyfin_usernames(
        preferences: Preferences = Depends(get_preferences),
        jellyfin_interface: Optional[JellyfinInterface] = Depends(get_jellyfin_interface),
    ) -> list[str]:
    """
    Get all the public usernames in Jellyfin. Returns an empty list if
    Jellyfin is disabled.
    """

    if preferences.use_jellyfin and jellyfin_interface:
        return jellyfin_interface.get_usernames()

    return []


@availablility_router.get('/tags/sonarr', status_code=200, tags=['Sonarr'])
def get_sonarr_tags(
        preferences: Preferences = Depends(get_preferences),
        sonarr_interface: Optional[SonarrInterface] = Depends(get_sonarr_interface)
    ) -> list[Tag]:
    """
    Get all tags defined in Sonarr.
    """

    if preferences.use_sonarr and sonarr_interface:
        return sonarr_interface.get_all_tags()

    return []


@availablility_router.get('/fonts', status_code=200, tags=['Fonts'])
def get_available_fonts(db: Session = Depends(get_database)) -> list[str]:
    """
    Get the names of all the available Fonts.
    """

    return [font.name for font in db.query(models.font.Font).all()]


@availablility_router.get('/templates', status_code=200, tags=['Templates'])
def get_available_templates(db: Session = Depends(get_database)) -> list[str]:
    """
    Get the names of all the available Templates.
    """

    return [
        template.name for template in db.query(models.template.Template).all()
    ]


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
