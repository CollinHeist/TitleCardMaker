from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import PositiveFloat, PositiveInt
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.query import get_series
from app.dependencies import get_database, get_preferences
from app.internal.auth import get_current_user
from app.models.card import Card
from app.models.episode import Episode
from app.models.font import Font
from app.models.loaded import Loaded
from app.models.preferences import Preferences
from app.models.series import Series
from app.models.snapshot import Snapshot as SnapshotModel
from app.models.sync import Sync
from app.models.template import Template
from app.schemas.statistic import (
    Snapshot, Statistic, CardCount, EpisodeCount, AssetSize
)


statistics_router = APIRouter(
    prefix='/statistics',
    tags=['Statistics'],
    dependencies=[Depends(get_current_user)],
)


@statistics_router.get('/')
def get_all_statistics(
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> list[Statistic]:
    """Get all statistics."""

    # Count objects
    card_count = db.query(Card).count()
    episode_count = db.query(Episode).count()
    font_count = db.query(Font).count()
    loaded_count = db.query(Loaded).count()
    series_count = db.query(Series).count()
    monitored_count = db.query(Series).filter_by(monitored=True).count()
    unmonitored_count = db.query(Series).filter_by(monitored=False).count()
    sync_count = db.query(Sync).count()
    template_count = db.query(Template).count()

    # Get and format total asset size | pylint: disable=not-callable
    asset_size = db.query(Card)\
        .with_entities(func.sum(Card.filesize))\
        .scalar()
    asset_size = 0 if asset_size is None else asset_size
    formatted_filesize = preferences.format_filesize(asset_size)

    return [
        Statistic(
            value=card_count, value_text=f'{card_count:,}', unit='Cards',
            description='Number of Title Cards',
        ),
        Statistic(
            value=series_count, value_text=f'{series_count:,}', unit='Series',
            description='Number of Series',
        ),
        Statistic(
            value=monitored_count, value_text=f'{monitored_count:,}',
            unit='Monitored',
            description='Number of Monitored Series',
        ),
        Statistic(
            value=unmonitored_count, value_text=f'{unmonitored_count:,}',
            unit='Unmonitored',
            description='Number of Unmonitored Series',
        ),
        Statistic(
            value=episode_count, value_text=f'{episode_count:,}',
            unit='Episodes',
            description='Number of Episodes',
        ),
        Statistic(
            value=asset_size, value_text=formatted_filesize[0],
            unit=formatted_filesize[1],
            description='File size of all Title Cards',
        ),
        Statistic(
            value=font_count, value_text=f'{font_count:,}', unit='Fonts',
            description='Number of Named Fonts',
        ),
        Statistic(
            value=template_count, value_text=f'{template_count:,}',
            unit='Templates', description='Number of Templates',
        ),
        Statistic(
            value=sync_count, value_text=f'{sync_count:,}', unit='Syncs',
            description='Number of Syncs',
        ),
        Statistic(
            value=loaded_count, value_text=f'{loaded_count:,}',
            unit='Loaded Cards', description='Number of loaded Title Cards',
        )
    ]


@statistics_router.get('/series/{series_id}')
def get_series_statistics(
        series_id: int,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> list[Statistic]:
    """
    Get the statistics for the given Series.

    - series_id: ID of the Series to get the statistics of.
    """

    # Verify Series exists
    get_series(db, series_id, raise_exc=True)

    # Count the Episodes, Cards, and total asset size | pylint: disable=not-callable
    episode_count = db.query(Episode).filter_by(series_id=series_id).count()
    card_count = db.query(Card).filter_by(series_id=series_id).count()
    asset_size = (db.query(Card)\
        .filter_by(series_id=series_id)\
        .with_entities(func.sum(Card.filesize))\
        .scalar()) or 0

    return [
        CardCount(value=card_count, value_text=f'{card_count:,}'),
        EpisodeCount(value=episode_count, value_text=f'{episode_count:,}'),
        AssetSize(
            value=asset_size,
            value_text=preferences.format_filesize(asset_size)[0],
            unit=preferences.format_filesize(asset_size)[1],
        ),
    ]


@statistics_router.get('/snapshots')
def get_snapshots(
        previous_days: float = Query(default=14, ge=0.0),
        previous_hours: float = Query(default=0, ge=0.0),
        slice_: PositiveInt = Query(alias='slice', default=1),
        db: Session = Depends(get_database),
    ) -> list[Snapshot]:
    """
    Get the database Snapshots from the given number of days in the past.

    - previous_days: How many days of past snapshots to return. Added to
    previous hours.
    - previous_hours: How many hours of past snapshots to return. Added
    to previous days.
    - slice: How to "slice" the return - e.g. `1` would be every
    Snapshot, `2` would be every other, etc.
    """

    previous = datetime.now() \
        - timedelta(days=previous_days, hours=previous_hours)

    return db.query(SnapshotModel)\
        .filter(SnapshotModel.timestamp > previous)\
        .all()[::slice_]
