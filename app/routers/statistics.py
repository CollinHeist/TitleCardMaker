from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_preferences
import app.models as models
from app.schemas.statistic import Statistic, CardCount, EpisodeCount, SeriesCount, AssetSize

statistics_router = APIRouter(
    prefix='/statistics',
    tags=['Statistics'],
)

@statistics_router.get('/', status_code=200)
def get_all_statistics(
        db = Depends(get_database)) -> list[Statistic]:
    
    series_count = db.query(models.series.Series).count()
    episode_count = db.query(models.episode.Episode).count()
    card_count = db.query(models.card.Card).count()

    return [
        CardCount(value=card_count, value_text=f'{card_count:,}'),
        SeriesCount(value=series_count, value_text=f'{series_count:,}'),
        EpisodeCount(value=episode_count, value_text=f'{episode_count:,}'),
        AssetSize(value=102.4231, value_text='85.42', unit='Gigabytes'),
    ]


@statistics_router.get('/series-count', status_code=200)
def get_series_count(
        db = Depends(get_database)) -> SeriesCount:

    count = db.query(models.series.Series).count()
    return SeriesCount(value=count, value_text=f'{count:,}')


@statistics_router.get('/series/{series_id}', status_code=200)
def get_series_statistics(
        series_id: int,
        db = Depends(get_database)) -> list[Statistic]:
    
    episode_count = db.query(models.episode.Episode)\
        .filter_by(series_id=series_id)\
        .count()
    card_count = db.query(models.card.Card)\
        .filter_by(series_id=series_id)\
        .count()
    
    return [
        CardCount(value=card_count, value_text=f'{card_count:,}'),
        EpisodeCount(value=episode_count, value_text=f'{episode_count:,}'),
        AssetSize(value=102.4231, value_text='102.42', unit='Gigabytes')
    ]