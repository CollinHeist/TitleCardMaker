from logging import Logger
from os import environ

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy import MetaData
from sqlalchemy.orm import Session

from app.database.session import engine
from app.dependencies import get_database, get_preferences
from app.models.preferences import Preferences
from app.routers.auth import auth_router
from app.routers.availability import availablility_router
from app.routers.blueprint import blueprint_router
from app.routers.cards import card_router
from app.routers.connection import connection_router
from app.routers.episodes import episodes_router
from app.routers.fonts import font_router
from app.routers.imports import import_router
from app.routers.logs import log_router
from app.routers.proxy import proxy_router
from app.routers.schedule import initialize_scheduler, schedule_router
from app.routers.series import series_router
from app.routers.settings import settings_router
from app.routers.sources import source_router
from app.routers.statistics import statistics_router
from app.routers.sync import sync_router
from app.routers.templates import template_router
from app.routers.translate import translation_router
from app.routers.webhooks import webhook_router

# Create sub router for all API requests
api_router = APIRouter(prefix='/api')

# Include sub-routers
api_router.include_router(auth_router)
api_router.include_router(availablility_router)
api_router.include_router(blueprint_router)
api_router.include_router(card_router)
api_router.include_router(connection_router)
api_router.include_router(episodes_router)
api_router.include_router(font_router)
api_router.include_router(import_router)
api_router.include_router(log_router)
api_router.include_router(proxy_router)
api_router.include_router(schedule_router)
api_router.include_router(series_router)
api_router.include_router(settings_router)
api_router.include_router(statistics_router)
api_router.include_router(source_router)
api_router.include_router(sync_router)
api_router.include_router(template_router)
api_router.include_router(translation_router)
api_router.include_router(webhook_router)

@api_router.get('/healthcheck')
def health_check(
        request: Request,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Check the health of the TCM server by attempting to perform a dummy
    database operation; raising an HTTPException (500) if a connection
    cannot be established.
    """

    try:
        db.execute(text('SELECT 1'))
    except Exception as exc:
        request.state.log.exception(f'Health check failed - {exc}')
        raise HTTPException(
            status_code=500,
            detail=f'Database returned some error - {exc}'
        ) from exc


@api_router.post('/reset')
def reset_database(
        request: Request,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Reset the entire database and system state. This DOES NOT clear any
    files, and requires the appropriate environment variable to be set
    in order to function.

    Intended only for testing setup and teardown.
    """

    log: Logger = request.state.log

    if environ.get('TCM_TESTING', 'false') == 'TRUE':
        # Delete all tables in the database in reverse order so children
        # are removed before parents
        metadata = MetaData()
        metadata.reflect(bind=engine)
        for table in reversed(metadata.sorted_tables):
            # Do not delete the version table so migrations aren't triggered
            if table.name == 'alembic_version':
                continue
            log.info(f'Deleting SQL Table "{table.name}"')
            db.execute(table.delete())
        db.commit()

        # Reset the global preferences
        preferences.reset(log=log)

        # Re-initialize the scheduler
        initialize_scheduler(override=True)
    else:
        raise HTTPException(
            status_code=401,
            detail='Unauthorized',
        )
