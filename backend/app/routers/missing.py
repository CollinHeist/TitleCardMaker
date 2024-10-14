from fastapi import APIRouter, Depends
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import not_
from sqlalchemy.orm import Session

from app.database.session import Page
from app.dependencies import get_database, get_preferences
from app.internal.auth import get_current_user
from app.models.card import Card as CardModel
from app.models.episode import Episode as EpisodeModel
from app.models.preferences import Preferences
from app.models.series import Series as SeriesModel
from app.schemas.episode import Episode
from app.schemas.series import Series


# Create sub router for all /fonts API requests
missing_router = APIRouter(
    prefix='/missing',
    tags=['Missing'],
    dependencies=[Depends(get_current_user)],
)


@missing_router.get('/cards')
def get_missing_cards(
        db: Session = Depends(get_database),
    ) -> Page[Episode]:
    """Get all the Episodes that do not have any associated Cards."""

    return paginate(
        db.query(EpisodeModel)\
            .filter(not_(EpisodeModel.id.in_(
                db.query(CardModel.episode_id).distinct()
            )))
    )


@missing_router.get('/logos')
def get_missing_logos(
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> list[Series]:
    """Get all Series which do not have an associated logo."""

    # Get all source subfolders
    source_directory = preferences.source_directory
    directories = set(source_directory.glob('*'))

    # Get set of series names with no logos
    missing_logos = [
        directory.name.rsplit(' ', maxsplit=1)[0]
        for directory in
        # Find directories which do not have a logo file
        directories - set(
            folder.parent for folder in source_directory.glob('*/logo.png')
        )
        if ' ' in directory.name
    ]

    return [
        series
        for series in db.query(SeriesModel)\
            .filter(SeriesModel.name.in_(missing_logos))\
            .all()
        if not (source_directory / series.path_safe_name / 'logo.png').exists()
    ]
