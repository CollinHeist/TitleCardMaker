from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, Body, Depends, Form, HTTPException

from app.dependencies import get_database
from app.dependencies import get_preferences
import app.models as models
from app.schemas.base import Base, UNSPECIFIED
from app.schemas.preferences import EpisodeDataSource, Style
from app.schemas.series import NewTemplate, Template, UpdateTemplate

from modules.Debug import log

# Create sub router for all /templates API requests
template_router = APIRouter(
    prefix='/templates',
    tags=['Templates'],
)

def join_lists(keys: list[Any], vals: list[Any], desc: str,
        default: Any=None) -> Union[dict[str, Any], None]:

    is_null = lambda v: (v is None) or (v == UNSPECIFIED)

    if is_null(keys) ^ is_null(vals):
        raise HTTPException(
            status_code=400,
            detail=f'Provide same number of {desc}',
        )
    elif not is_null(keys) and not is_null(vals):
        if len(keys) != len(vals):
            raise HTTPException(
                status_code=400,
                detail=f'Provide same number of {desc}',
            )
        else:
            return {key: val for key, val in zip(keys, vals) if len(key) > 0}

    return UNSPECIFIED if keys == UNSPECIFIED else default


@template_router.post('/new', status_code=201)
def create_template(
        new_template: NewTemplate = Body(...),
        db = Depends(get_database)) -> Template:

    # Validate font ID if provided
    if getattr(new_template, 'font_id', None) is not None:
        if db.query(models.font.Font).filter_by(id=font_id).first() is None:
            raise HTTPException(
                status_code=404,
                detail=f'Font {font_id} not found',
            )

    template = models.template.Template(**new_template.dict())
    db.add(template)
    db.commit()

    return template


@template_router.get('/all', status_code=200)
async def get_all_templates(
        db = Depends(get_database)) -> list[Template]:

    return db.query(models.template.Template).all()


@template_router.get('/{template_id}', status_code=200)
async def get_template(
        template_id: int,
        db = Depends(get_database)) -> Template:
    """
    Get the Template with the given ID.

    - template_id: ID of the Template.
    """

    template = db.query(models.template.Template)\
        .filter_by(id=template_id).first()
    if template is None:
        raise HTTPException(
            status_code=404,
            detail=f'Template {template_id} not found',
        )

    return template


@template_router.patch('/{template_id}')
async def update_template(
        template_id: int,
        update_template: UpdateTemplate = Body(...),
        db = Depends(get_database)) -> Template:
    log.critical(f'{update_template.dict()=}')
    # Get the template being modified, raise 404 if DNE
    template = db.query(models.template.Template)\
        .filter_by(id=template_id).first()
    if template is None:
        raise HTTPException(
            status_code=404,
            detail=f'Template {template_id} not found',
        )

    # If a font ID was specified, verify it exists
    if getattr(update_template, 'font_id', None) is not None:
        font = db.query(models.font.Font)\
            .filter_by(id=update_template.font_id).first()
        if font is None:
            raise HTTPException(
                status_code=404,
                detail=f'Font {font_id} not found',
            )

    # Update each attribute of the object
    changed = False
    for attr, value in update_template.dict().items():
        if value != UNSPECIFIED and getattr(template, attr) != value:
            setattr(template, attr, value)
            log.debug(f'SETTING template[{template_id}].{attr} = {value}')
            changed = True

    # If any values were changed, commit to database
    if changed:
        db.commit()

    return template


@template_router.delete('/{template_id}', status_code=204)
async def delete_template(
        template_id: int,
        db = Depends(get_database)) -> None:
    """
    Delete the given template. This also deletes the reference to this
    template on any associated Series of Episode entries.

    - template_id: ID of the template to delete.
    """

    # Query for template, raise 404 if DNE
    query = db.query(models.template.Template).filter_by(id=template_id)
    if query.first() is None:
        raise HTTPException(
            status_code=404,
            detail=f'Template {template_id} not found',
        )

    # Delete template reference from any series or episode
    for series in db.query(models.series.Series)\
        .filter_by(template_id=template_id).all():
        series.template_id = None
    for episode in db.query(models.episode.Episode)\
        .filter_by(template_id=template_id).all():
        episode.template_id = None

    query.delete()
    db.commit()

    return None