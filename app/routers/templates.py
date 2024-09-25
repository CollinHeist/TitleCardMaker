from typing import Literal

from fastapi import APIRouter, Body, Depends, Request
from fastapi_pagination import paginate
from sqlalchemy.orm import Session

from app.database.query import get_font, get_template
from app.database.session import Page
from app.dependencies import get_database, get_preferences
from app.internal.auth import get_current_user
from app.internal.cards import refresh_remote_card_types
from app.models.preferences import Preferences
from app.models.template import Template as TemplateModel
from app.schemas.base import UNSPECIFIED
from app.schemas.series import NewTemplate, Template, UpdateTemplate
from modules.Debug import Logger, log


# Create sub router for all /templates API requests
template_router = APIRouter(
    prefix='/templates',
    tags=['Templates'],
    dependencies=[Depends(get_current_user)],
)


@template_router.post('/new')
def create_template(
        request: Request,
        new_template: NewTemplate = Body(...),
        db: Session = Depends(get_database),
    ) -> Template:
    """
    Create a new Template. Any referenced font_id must exist.

    - new_template: Template definition to create.
    """

    # Validate Font ID if provided
    get_font(db, new_template.font_id, raise_exc=True)

    template = TemplateModel(**new_template.dict())
    db.add(template)
    db.commit()

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=request.state.log)

    return template


@template_router.get('/all')
def get_all_templates(
        order: Literal['id', 'name'] = 'name',
        db: Session = Depends(get_database),
    ) -> Page[Template]:
    """
    Get all defined Templates.

    - order: How to order the returned Templates.
    """

    query = db.query(TemplateModel)
    if order == 'id':
        return paginate(query.all())

    return paginate(query.order_by(TemplateModel.sort_name).all())


@template_router.get('/{template_id}')
def get_template_by_id(
        template_id: int,
        db: Session = Depends(get_database),
    ) -> Template:
    """
    Get the Template with the given ID.

    - template_id: ID of the Template.
    """

    return get_template(db, template_id, raise_exc=True)


@template_router.patch('/{template_id}')
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
    log: Logger = request.state.log

    # Query for Template, raise 404 if DNE
    template = get_template(db, template_id, raise_exc=True)

    # If a Font ID was specified, verify it exists
    get_font(db, getattr(update_template, 'font_id', None), raise_exc=True)

    # Update each attribute of the object
    changed = False
    for attr, value in update_template.dict().items():
        if value != UNSPECIFIED and getattr(template, attr) != value:
            setattr(template, attr, value)
            log.debug(f'Template[{template_id}].{attr} = {value}')
            changed = True

    # If any values were changed, commit to database
    if changed:
        db.commit()

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=log)

    return template


@template_router.delete('/{template_id}')
def delete_template(
        template_id: int,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Delete the specified Template.

    - template_id: ID of the Template to delete.
    """

    # Query for Template, raise 404 if DNE
    get_template(db, template_id, raise_exc=True)

    # Delete from global template list, if present
    if template_id in preferences.default_templates:
        preferences.default_templates = [
            tid for tid in preferences.default_templates if tid != template_id
        ]
        preferences.commit()

    # Delete Template from database
    db.delete(get_template(db, template_id, raise_exc=True))
    db.commit()
