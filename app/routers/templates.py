from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, Body, Depends, Form, HTTPException

from app.dependencies import get_database
from app.dependencies import get_preferences
import app.models as models
from app.routers.fonts import get_font
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


def get_template(db, template_id, *, raise_exc=True) -> Union[Template, None]:
    """
    Get the Template with the given ID from the given Database.

    Args:
        db: SQL Database to query for the given Template.
        template_id: ID of the Template to query for.
        raise_exc: Whether to raise 404 if the given Template does not 
            exist. If False, then only an error message is logged.

    Returns:
        Template with the given ID. If one cannot be found and raise_exc
        is False, then None is returned.

    Raises:
        HTTPException with a 404 status code if the Template cannot be
        found and raise_exc is True.
    """

    # No ID given, return None
    if template_id is None:
        return None

    template = db.query(models.template.Template)\
        .filter_by(id=template_id).first()
    if template is None:
        if raise_exc:
            raise HTTPException(
                status_code=404,
                detail=f'Template {template_id} not found',
            )
        else:
            log.error(f'Template {template_id} not found')
            return None

    return template


@template_router.post('/new', status_code=201)
def create_template(
        new_template: NewTemplate = Body(...),
        db = Depends(get_database)) -> Template:
    """
    Create a new Template. Any referenced font_id must exist.

    - new_template: Template definition to create.
    """

    # Validate font ID if provided
    if getattr(new_template, 'font_id', None) is not None:
        get_font(db, new_template.font_id, raise_exc=True)

    template = models.template.Template(**new_template.dict())
    db.add(template)
    db.commit()

    return template


@template_router.get('/all', status_code=200)
def get_all_templates(
        db = Depends(get_database)) -> list[Template]:
    """
    Get all defined Templates.
    """    

    return db.query(models.template.Template).all()


@template_router.get('/{template_id}', status_code=200)
def get_template(
        template_id: int,
        db = Depends(get_database)) -> Template:
    """
    Get the Template with the given ID.

    - template_id: ID of the Template.
    """

    return get_template(db, template_id, raise_exc=True)


@template_router.patch('/{template_id}')
def update_template(
        template_id: int,
        update_template: UpdateTemplate = Body(...),
        db = Depends(get_database)) -> Template:
    """
    Update the Template with the given ID. Only provided fields are
    updated.

    - template_id: ID of the Template to update.
    - update_template: UpdateTemplate containing fields to update.
    """
    log.critical(f'{update_template.dict()=}')
    # Query for template, raise 404 if DNE
    template = get_template(db, template_id, raise_exc=True)

    # If a font ID was specified, verify it exists
    if getattr(update_template, 'font_id', None) is not None:
        get_font(db, update_template.font_id, raise_exc=True)

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
def delete_template(
        template_id: int,
        db = Depends(get_database)) -> None:
    """
    Delete the given Template. This also deletes the reference to this
    Template on any associated Series of Episode entries.

    - template_id: ID of the Template to delete.
    """

    # Query for template, raise 404 if DNE
    template = get_template(db, template_id, raise_exc=True)

    # Delete template reference from any Series, Episode, or Sync
    for series in db.query(models.series.Series)\
            .filter_by(template_id=template_id).all():
        series.template_id = None
    for episode in db.query(models.episode.Episode)\
            .filter_by(template_id=template_id).all():
        episode.template_id = None
    for sync in db.query(models.sync.Sync)\
            .filter_by(template_id=template_id).all():
        sync.template_id = None

    # Delete Template, update database
    query.delete()
    db.commit()

    return None