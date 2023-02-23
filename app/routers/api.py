from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse

from app.routers.connection import connection_router
from app.routers.series import series_router

api_router = APIRouter(
    prefix='/api',
)

@api_router.post('/create-card')
async def create_card(
        source_file: UploadFile,
        # TODO other params
        ) -> FileResponse:

    pass

api_router.include_router(connection_router)
api_router.include_router(series_router)