from typing import Any, Literal, Optional, Union

from fastapi import (
    APIRouter, BackgroundTasks, Body, Depends, Form, HTTPException, UploadFile
)
from pydantic.error_wrappers import ValidationError
from sqlalchemy import or_

from app.database.query import get_font, get_template
from app.dependencies import (
    get_database, get_preferences, get_emby_interface, get_jellyfin_interface,
    get_plex_interface, get_sonarr_interface, get_tmdb_interface
)
from app.internal.imports import parse_raw_yaml, parse_templates
import app.models as models
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import Preferences
from app.schemas.series import Series, Template

from modules.Debug import log


import_router = APIRouter(
    prefix='/import',
    tags=['Import'],
)


@import_router.post('/preferences')
def import_preferences_yaml(
        yaml: str = Body(...),
        preferences = Depends(get_preferences)) -> Preferences:
    """
    
    """

    ...


@import_router.post('/template')
def import_template_yaml(
        yaml: str = Body(...),
        db = Depends(get_database),
        preferences = Depends(get_preferences)) -> list[Template]:
    """
    Import Templates defined in the given YAML.

    - yaml: YAML string to parse and import
    """

    # Parse raw YAML into dictionary
    yaml_dict = parse_raw_yaml(yaml)
    if len(yaml_dict) == 0:
        return []

    # Create NewTemplate objects from the YAML dictionary
    try:
        new_templates = parse_templates(db, preferences, yaml_dict)
    except ValidationError as e:
        log.exception(f'Invalid YAML', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {e}'
        )

    # Add each defined Template to the database
    templates = []
    for new_template in new_templates:
        template = models.template.Template(**new_template.dict())
        db.add(template)
        templates.append(template)
    db.commit()

    return templates


@import_router.post('/series')
def import_series_yaml(
        yaml: str = Body(...),
        db = Depends(get_database),
        preferences = Depends(get_preferences)) -> list[Series]:
    """
    
    """

    ...