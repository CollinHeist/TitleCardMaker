from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.routers.api import api_router

TEMPLATE_DIRECTORY = Path(__file__).parent / 'templates'
TEMPLATES = Jinja2Templates(directory=str(TEMPLATE_DIRECTORY))

description = """
Backend API for the TitleCardMaker.
"""

tags_metadata = [
    {'name': 'series',
     'description': 'Operations relating to series'},
    {'name': 'settings',
     'description': 'Settings related to how TCM operates'},
]

app = FastAPI(
    title='TitleCardMaker',
    description=description,
    version='0.0.1',
    contact={
        'name': 'Collin Heist',
        'url': 'https://github.com/CollinHeist/',
    },
    openapi_tags=tags_metadata
)

@app.get('/')
def goto_home_page(
        request: Request,
        db: Session = Depends(get_database)) -> dict:

    return TEMPLATES.TemplateResponse(
        'main.html',
        {'request': request}
    )


@app.get('/settings')
def goto_settings_page(
        request: Request,
        db: Session = Depends(get_database)) -> dict:

    return TEMPLATES.TemplateResponse(
        'settings.html',
        {'request': request}
    )


@app.get('/series/{series_id}')
def goto_series_page(
        request: Request,
        series_id: int,
        db: Session = Depends(get_database)) -> dict:

    return TEMPLATES.TemplateResponse(
        'series.html',
        {'request': request}
    )


@app.get('/connections')
def goto_connections_page(
        request: Request,
        db: Session = Depends(get_database)) -> dict:

    return TEMPLATES.TemplateResponse(
        'connections.html',
        {'request': request}
    )


@app.get('/sync')
def goto_sync_page(
        request: Request,
        db: Session = Depends(get_database)) -> dict:

    return TEMPLATES.TemplateResponse(
        'sync.html',
        {'request': request}
    )


@app.get('/import')
def goto_import_page(
        request: Request,
        db: Session = Depends(get_database)) -> dict:

    return TEMPLATES.TemplateResponse(
        'import.html',
        {'request': request}
    )


app.include_router(api_router)