from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi_pagination import paginate
from sqlalchemy.orm import Session
from app.database.query import get_series

from app.database.session import Page
from app.dependencies import *
from app.internal.blueprint import generate_series_blueprint, query_series_blueprints
from app.schemas.blueprint import Blueprint, RemoteBlueprint


# Create sub router for all /blueprints API requests
blueprint_router = APIRouter(
    prefix='/blueprints',
    tags=['Blueprints'],
)


@blueprint_router.get('/{series_id}/export', status_code=200)
def export_series_blueprint(
        series_id: int,
        include_global_defaults: bool = Query(default=True),
        include_episode_overrides: bool = Query(default=True),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> Blueprint:
    """
    Generate the Blueprint for the given Series. This Blueprint can be
    imported to completely recreate a Series' (and all associated
    Episodes') configuration. 

    - series_id: ID of the Series to export the Blueprint of.
    - include_global_defaults: Whether to write global settings if the
    Series has no corresponding override, primarily for the card type.
    - include_episode_overrides: Whether to include Episode-level
    overrides in the exported Blueprint. If True, then any Episode Font
    and Template assignments are also included.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return generate_series_blueprint(
        series, include_global_defaults, include_episode_overrides, preferences,
    )


@blueprint_router.get('/{series_id}/files', status_code=200)
def export_series_blueprint_files(
        series_id: int,
        include_episode_overrides: bool = Query(default=True),
        db: Session = Depends(get_database),
    ) -> list[str]:
    """
    Get the URI's to the associated Blueprint's Font files so they can
    be downloaded.

    - series_id: ID of the Series to export the Blueprint of.
    - include_episode_overrides: Whether to include Episode-level
    overrides. If True, then any Episode Font are also included.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get all Episodes if indicates
    episodes = series.episodes if include_episode_overrides else []

    # Get all Templates
    templates = list(set(
        template for obj in [series] + episodes for template in obj.templates
    ))

    return [
        f'/assets/fonts/{font.id}/{Path(font.file).name}'
        for font in set(obj.font for obj in [series] + episodes + templates
                        if obj.font)
    ]


@blueprint_router.get('/{series_id}/query', status_code=200)
def query_series_blueprints_(
        request: Request,
        series_id: int,
        db: Session = Depends(get_database),
    ) -> list[RemoteBlueprint]:
    """
    
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    return query_series_blueprints(series, log=request.state.log)


@blueprint_router.put('/{series_id}/import/{blueprint_id}', status_code=200)
def import_series_blueprint_by_id(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> None:

    ...