from fastapi import APIRouter, Depends
from sqlalchemy import func
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
        db: Session = Depends(get_database),
        preferences = Depends(get_preferences)) -> list[Statistic]:
    """
    Get all statistics.
    """
    
    series_count = db.query(models.series.Series).count()
    episode_count = db.query(models.episode.Episode).count()
    card_count = db.query(models.card.Card).count()

    # Get/format total asset size
    asset_size = db.query(models.card.Card)\
        .with_entities(func.sum(models.card.Card.filesize)).scalar()
    asset_size = 0 if asset_size is None else asset_size

    return [
        CardCount(value=card_count, value_text=f'{card_count:,}'),
        SeriesCount(value=series_count, value_text=f'{series_count:,}'),
        EpisodeCount(value=episode_count, value_text=f'{episode_count:,}'),
        AssetSize(
            value=asset_size,
            value_text=preferences.format_filesize(asset_size)[0],
            unit=preferences.format_filesize(asset_size)[1],
        ),
    ]


@statistics_router.get('/series-count', status_code=200)
def get_series_count(
        db: Session = Depends(get_database)) -> SeriesCount:
    """
    Get the statistics for the number of series.
    """

    count = db.query(models.series.Series).count()
    return SeriesCount(value=count, value_text=f'{count:,}')


@statistics_router.get('/series/{series_id}', status_code=200)
def get_series_statistics(
        series_id: int,
        db: Session = Depends(get_database),
        preferences = Depends(get_preferences)) -> list[Statistic]:
    
    episode_count = db.query(models.episode.Episode)\
        .filter_by(series_id=series_id).count()
    card_count = db.query(models.card.Card)\
        .filter_by(series_id=series_id).count()
    asset_size = db.query(models.card.Card)\
        .filter_by(series_id=series_id)\
        .with_entities(func.sum(models.card.Card.filesize)).scalar()
    asset_size = 0 if asset_size is None else asset_size
    
    return [
        CardCount(value=card_count, value_text=f'{card_count:,}'),
        EpisodeCount(value=episode_count, value_text=f'{episode_count:,}'),
        AssetSize(
            value=asset_size,
            value_text=preferences.format_filesize(asset_size)[0],
            unit=preferences.format_filesize(asset_size)[1],
        ),
    ]