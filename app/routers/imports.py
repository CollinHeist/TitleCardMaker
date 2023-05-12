from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic.error_wrappers import ValidationError

from app.dependencies import get_database, get_preferences
from app.internal.imports import parse_fonts, parse_raw_yaml, parse_templates
import app.models as models
from app.schemas.font import NamedFont
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


@import_router.post('/fonts')
def import_fonts_yaml(
        yaml: str = Body(...),
        db = Depends(get_database)) -> list[NamedFont]:
    """
    Import all Fonts defined in the given YAML.

    - yaml: YAML string to parse and import
    """

    # Parse raw YAML into dictionary
    yaml_dict = parse_raw_yaml(yaml)
    if len(yaml_dict) == 0:
        return []
    
    # Create NewNamedFont objects from the YAML dictionary
    try:
        new_fonts = parse_fonts(yaml_dict)
    except ValidationError as e:
        log.exception(f'Invalid YAML', e)
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {e}'
        )

    # Add each defined Font to the database
    fonts = []
    for new_font in new_fonts:
        font = models.font.Font(**new_font.dict())
        db.add(font)
        fonts.append(font)
    db.commit()

    return fonts


@import_router.post('/templates')
def import_template_yaml(
        yaml: str = Body(...),
        db = Depends(get_database),
        preferences = Depends(get_preferences)) -> list[Template]:
    """
    Import all Templates defined in the given YAML.

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