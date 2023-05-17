from fastapi import APIRouter, Body, Depends

from app.database.query import get_font, get_template
from app.dependencies import get_database
import app.models as models
from app.schemas.base import UNSPECIFIED
from app.schemas.series import NewTemplate, Template, UpdateTemplate

from modules.Debug import log


# Create sub router for all /templates API requests
template_router = APIRouter(
    prefix='/templates',
    tags=['Templates'],
)


@template_router.post('/new', status_code=201)
def create_template(
        new_template: NewTemplate = Body(...),
        db = Depends(get_database)) -> Template:
    """
    Create a new Template. Any referenced font_id must exist.

    - new_template: Template definition to create.
    """

    # Validate font ID if provided
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
def get_template_by_id(
        template_id: int,
        db = Depends(get_database)) -> Template:
    """
    Get the Template with the given ID.

    - template_id: ID of the Template.
    """

    return get_template(db, template_id, raise_exc=True)


@template_router.patch('/{template_id}', status_code=200)
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
    # Query for Template, raise 404 if DNE
    template = get_template(db, template_id, raise_exc=True)

    # If a Font ID was specified, verify it exists
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

    # Query for Template, raise 404 if DNE
    template = get_template(db, template_id, raise_exc=True)

    # Delete Template reference from any Series, Episode, or Sync
    for series in db.query(models.series.Series)\
            .filter_by(template_id=template_id).all():
        series.template_id = None
        log.debug(f'Unlinked {template.log_str} from {series.log_str}')
    for episode in db.query(models.episode.Episode)\
            .filter_by(template_id=template_id).all():
        episode.template_id = None
        log.debug(f'Unlinked {episode.log_str} from {series.log_str}')
    for sync in db.query(models.sync.Sync)\
            .filter_by(template_id=template_id).all():
        sync.template_id = None
        log.debug(f'Unlinked {sync.log_str} from {series.log_str}')

    # Delete Template, update database
    db.delete(template)
    db.commit()

    return None