from fastapi import APIRouter

from app.routers.availability import availablility_router
from app.routers.cards import card_router
from app.routers.connection import connection_router
from app.routers.episodes import episodes_router
from app.routers.fonts import font_router
from app.routers.imports import import_router
from app.routers.schedule import schedule_router
from app.routers.series import series_router
from app.routers.settings import settings_router
from app.routers.sources import source_router
from app.routers.statistics import statistics_router
from app.routers.sync import sync_router
from app.routers.templates import template_router
from app.routers.translate import translation_router

# Create sub router for all API requests
api_router = APIRouter(prefix='/api')

# Include sub-routers
api_router.include_router(availablility_router)
api_router.include_router(card_router)
api_router.include_router(connection_router)
api_router.include_router(episodes_router)
api_router.include_router(font_router)
api_router.include_router(import_router)
api_router.include_router(schedule_router)
api_router.include_router(series_router)
api_router.include_router(settings_router)
api_router.include_router(statistics_router)
api_router.include_router(source_router)
api_router.include_router(sync_router)
api_router.include_router(template_router)
api_router.include_router(translation_router)