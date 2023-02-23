from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.models.series import Series
from app.models.episode import Episode

series_router = APIRouter(
    prefix='/series',
    tags=['series', 'shows'],
    dependencies=[],#[Depends(get_database)],
    responses={404: {'description': 'series not found'}},
)

@series_router.post('/new')
async def add_new_series(
        name: str,
        year: int,
        template: Optional[str],
        plex_library_name: Optional[str],
        emby_library_name: Optional[str],
        db: Session = Depends(get_database)) -> dict:
    
    pass


@series_router.get('/{series_id}')
async def get_series_config(
        series_id: int,
        db: Session = Depends(get_database)) -> Series:
    
    pass


@series_router.patch('/{series_id}')
async def update_series_config(
        series_id: int,
        # Update args
        db: Session = Depends(get_database)) -> Series:
    
    pass


@series_router.get('/{series_id}/episodes')
async def get_all_episodes(
        series_id: int,
        db: Session = Depends(get_database)) -> list[Episode]:
    
    pass


@series_router.get('/{series_id}/poster')
async def get_series_poster(
        series_id: int,
        db: Session = Depends(get_database)) -> str:
    
    pass


@series_router.patch('/{series_id}/poster')
async def update_series_poster(
        series_id: int,
        db: Session = Depends(get_database)) -> str:
    
    pass