from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse

from app.routers.connection import connection_router
from app.routers.fonts import font_router
from app.routers.series import series_router
from app.routers.statistics import statistics_router
from app.routers.sync import sync_router

# Create sub router for all API requests
api_router = APIRouter(
    prefix='/api',
)

# Include sub-routers
api_router.include_router(connection_router)
api_router.include_router(font_router)
api_router.include_router(settings_router)
api_router.include_router(sync_router)
