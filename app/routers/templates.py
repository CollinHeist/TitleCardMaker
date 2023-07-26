from typing import Literal

from fastapi import APIRouter, Body, Depends, Request
from fastapi_pagination import paginate
from sqlalchemy.orm import Session

from app.database.query import get_font, get_template
from app.database.session import Page
from app.dependencies import get_database
from app.internal.cards import refresh_remote_card_types
from app import models
from app.schemas.base import UNSPECIFIED
from app.schemas.series import NewTemplate, Template, UpdateTemplate


# Create sub router for all /templates API requests
template_router = APIRouter(
    prefix='/templates',
    tags=['Templates'],
)


@template_router.post('/new', status_code=201)
def create_template(
        request: Request,
        new_template: NewTemplate = Body(...),
        db: Session = Depends(get_database),
    ) -> Template:
    """
    Create a new Template. Any referenced font_id must exist.

    - new_template: Template definition to create.
    """

    # Validate font ID if provided
    get_font(db, new_template.font_id, raise_exc=True)

    template = models.template.Template(**new_template.dict())
    db.add(template)
    db.commit()

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=request.state.log)

    return template


@template_router.get('/all', status_code=200)
def get_all_templates(
        order_by: Literal['id', 'name'] = 'name',
        db: Session = Depends(get_database),
    ) -> Page[Template]:
    """
    Get all defined Templates.
    """

    query = db.query(models.template.Template)
    if order_by == 'id':
        return paginate(query.all())

    return paginate(query.order_by(models.template.Template.name).all())


@template_router.get('/{template_id}', status_code=200)
def get_template_by_id(
        template_id: int,
        db: Session = Depends(get_database),
    ) -> Template:
    """
    Get the Template with the given ID.

    - template_id: ID of the Template.
    """

    return get_template(db, template_id, raise_exc=True)


@template_router.patch('/{template_id}', status_code=200)
def update_template_(
        request: Request,
        template_id: int,
        update_template: UpdateTemplate = Body(...),
        db: Session = Depends(get_database),
    ) -> Template:
    """
    Update the Template with the given ID. Only provided fields are
    updated.

    - template_id: ID of the Template to update.
    - update_template: UpdateTemplate containing fields to update.
    """

    # Get contextual logger
    log = request.state.log

    # Query for Template, raise 404 if DNE
    template = get_template(db, template_id, raise_exc=True)

    # If a Font ID was specified, verify it exists
    get_font(db, getattr(update_template, 'font_id', None), raise_exc=True)

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

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=log)

    return template


@template_router.delete('/{template_id}', status_code=204)
def delete_template(
        template_id: int,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Delete the specified Template.

    - template_id: ID of the Template to delete.
    """

    # Query for Template, raise 404 if DNE
    get_template(db, template_id, raise_exc=True)

    # Delete Template, update database
    db.delete(get_template(db, template_id, raise_exc=True))
    db.commit()
