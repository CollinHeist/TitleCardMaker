from typing import Literal, Optional
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_preferences, get_emby_interface, get_plex_interface, get_sonarr_interface, get_tmdb_interface
from app.schemas.preferences import FilesizeUnit, Preferences, Style
from modules.Debug import log
from modules.EmbyInterface2 import EmbyInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface

SupportedConnection = Literal['emby', 'jellyfin', 'plex', 'sonarr', 'tmdb']

# Create sub router for all /connection API requests
connection_router = APIRouter(
    prefix='/connection',
)

@connection_router.get('/{connection}')
def get_connection_details(
        connection: SupportedConnection,
        db = Depends(get_database),
        preferences = Depends(get_preferences)) -> Preferences:

    ...


@connection_router.put('/{connection}/{status}', status_code=204)
def toggle_connection(
        connection: SupportedConnection,
        status: Literal['enable', 'disable'],
        preferences=Depends(get_preferences)) -> None:

    if connection == 'emby':
        preferences.use_emby = (status == 'enable')
    elif connection == 'jellyfin':
        preferences.use_jellyfin = (status == 'enable')
    elif connection == 'plex':
        preferences.use_plex = (status == 'enable')
    elif connection == 'sonarr':
        preferences.use_sonarr = (status == 'enable')
    elif connection == 'tmdb':
        preferences.use_tmdb = (status == 'enable')


@connection_router.patch('/emby', status_code=200)
