from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_database

SupportedConnection = Literal['emby', 'plex', 'sonarr', 'tmdb']

connection_router = APIRouter(
    prefix='/connection',
    tags=['connection', 'plex', 'emby', 'tmdb', 'sonarr'],
)

@connection_router.get('/{connection}')
async def get_connection_details(
        connection: SupportedConnection,
        db: Session = Depends(get_database)) -> dict:
    
    pass

@connection_router.patch('/{connection}')
async def update_connection(
        connection: SupportedConnection,
        db: Session = Depends(get_database)) -> dict:
    
    pass