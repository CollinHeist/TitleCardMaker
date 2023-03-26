from typing import Literal, Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_preferences, get_emby_interface,\
    get_jellyfin_interface, get_plex_interface, get_sonarr_interface
import app.models as models
from app.schemas.card import CardType, LocalCardType, RemoteCardType
from app.schemas.preferences import EpisodeDataSourceToggle, ImageSourceToggle,\
    MediaServer, StyleOption
from app.schemas.sonarr import Tag
from modules.cards.available import LocalCards
from modules.Debug import log

# Create sub router for all /connection API requests
availablility_router = APIRouter(
    prefix='/available',
    tags=['Availibility'],
)

@availablility_router.get('/card-types', tags=['Title Cards'])
def get_all_available_card_types(
        preferences=Depends(get_preferences)) -> list[CardType]:

    ...
     
    return LocalCards


@availablility_router.get('/card-types/local', tags=['Title Cards'])
def get_local_card_types(
        preferences=Depends(get_preferences)) -> list[LocalCardType]:
    """
    Get all locally defined card types.
    """
    
    return LocalCards


@availablility_router.get('/card-types/remote', tags=['Title Cards'])
def get_remote_card_types(
        preferences=Depends(get_preferences)) -> list[RemoteCardType]:
    
    ...


@availablility_router.get('/episode-data-sources')
def get_available_episode_data_sources(
        preferences=Depends(get_preferences)) -> list[EpisodeDataSourceToggle]:
    
    return [
        {'name': source,
         'value': source,
         'selected': source == preferences.episode_data_source}
        for source in preferences.valid_episode_data_sources
    ]


@availablility_router.get('/image-source-priority',
                          response_model=list[ImageSourceToggle])
def get_image_source_priority(
        preferences=Depends(get_preferences)) -> list[EpisodeDataSourceToggle]:
    
    return [
        {'name': source,
         'value': source,
         'selected': (source in preferences.image_source_priority)}
        for source in (set(preferences.image_source_priority)
                       | set(preferences.valid_image_sources))
    ]


# @availablility_router.get('/media-servers')
# def get_available_media_servers(
#         preferences=Depends(get_preferences)) -> list[MediaServer]:
    
#     return preferences.enabled_media_servers


@availablility_router.get('/libraries/{media_server}')
def get_server_libraries(
        media_server: Literal['emby', 'jellyfin', 'plex'],
        preferences = Depends(get_preferences),
        emby_interface = Depends(get_emby_interface),
        jellyfin_interface = Depends(get_jellyfin_interface),
        plex_interface = Depends(get_plex_interface)) -> list[str]:
    """
    Get all available TV library names on the given media server.

    - media_server: Which media server to get the library names of.
    """
    
    if media_server == 'emby':
        if preferences.use_emby:
            return emby_interface.get_libraries()
        return []
    elif media_server == 'jellyfin':
        if preferences.use_jellyfin:
            return jellyfin_interface.get_libraries()
        return []
    elif media_server == 'plex':
        if preferences.use_plex:
            return plex_interface.get_libraries()
        return []
    
    raise HTTPException(
        status_code=400,
        detail=f'Cannot get libraries for the "{media_server}" media server'
    )


@availablility_router.get('/usernames/emby', tags=['Emby'])
def get_emby_usernames(
        preferences=Depends(get_preferences),
        emby_interface = Depends(get_emby_interface)) -> list[str]:
    """
    Get all the public usernames in Emby. Returns an empty list if
    Emby is disabled.
    """

    if preferences.use_emby and emby_interface:
        return emby_interface.get_usernames()

    return []


@availablility_router.get('/usernames/jellyfin', tags=['Jellyfin'])
def get_jellyfin_usernames(
        preferences = Depends(get_preferences),
        jellyfin_interface = Depends(get_jellyfin_interface)) -> list[str]:
    """
    Get all the public usernames in Jellyfin. Returns an empty list if
    Jellyfin is disabled.
    """

    if preferences.use_jellyfin and jellyfin_interface:
        return jellyfin_interface.get_usernames()

    return []


@availablility_router.get('/tags/sonarr', tags=['Sonarr'])
def get_sonarr_tags(
        preferences=Depends(get_preferences),
        sonarr_interface = Depends(get_sonarr_interface)) -> list[Tag]:
    """
    Get all tags defined in Sonarr.
    """

    if preferences.use_sonarr and sonarr_interface:
        return sonarr_interface.get_all_tags()

    return []


@availablility_router.get('/fonts', tags=['Fonts'])
def get_available_fonts(db=Depends(get_database)) -> list[str]:
    """
    Get the names of all the available Fonts.
    """

    return [font.name for font in db.query(models.font.Font).all()]


@availablility_router.get('/templates', tags=['Templates'])
def get_available_templates(db=Depends(get_database)) -> list[str]:
    """
    Get the names of all the available Templates.
    """

    return [
        template.name for template in db.query(models.template.Template).all()
    ]


@availablility_router.get('/styles')
def get_available_styles() -> list[StyleOption]:
    return [
        {'name': 'Art', 'value': 'art', 'style_type': 'art'},
        {'name': 'Blurred Art', 'value': 'art blur', 'style_type': 'art'},
        {'name': 'Grayscale Art', 'value': 'art grayscale', 'style_type': 'art'},
        {'name': 'Blurred Grayscale Art', 'value': 'art blur grayscale', 'style_type': 'art'},
        {'name': 'Unique', 'value': 'unique', 'style_type': 'unique'},
        {'name': 'Blurred Unique', 'value': 'blur unique', 'style_type': 'unique'},
        {'name': 'Grayscale Unique', 'value': 'grayscale unique', 'style_type': 'unique'},
        {'name': 'Blurred Grayscale Unique', 'value': 'blur grayscale unique', 'style_type': 'unique'},
    ]