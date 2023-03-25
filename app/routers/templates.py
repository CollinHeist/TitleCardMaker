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
    if new_template.font_id is not None:
        if db.query(models.font.Font).filter_by(id=font_id).first() is None:
            raise HTTPException(
                status_code=404,
                detail=f'Font {font_id} not found',
            )

    # Validate season titles
    season_titles = join_lists(
        new_template.season_title_ranges,
        new_template.season_title_values,
        'season title ranges and values'
    )

    # Validate extras
    extras = join_lists(
        new_template.extra_keys,
        new_template.extra_values,
        'extra keys and values'
    )

    # Create dictionary, remove unnecessary keys
    template_dict = new_template.dict()
    for key in ('season_title_ranges', 'season_title_values', 'extra_keys',
                'extra_values'):
        template_dict.pop(key, None)

    template = models.template.Template(**template_dict)
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

    # Get the template being modified, raise 404 if DNE
    template = db.query(models.template.Template)\
        .filter_by(id=template_id).first()
    if template is None:
        raise HTTPException(
            status_code=404,
            detail=f'Template {template_id} not found',
        )

    # If a font ID was specified, verify it exists
    if update_template.font_id not in (None, UNSPECIFIED):
        font = db.query(models.font.Font)\
            .filter_by(id=update_template.font_id).first()
        if font is None:
            raise HTTPException(
                status_code=404,
                detail=f'Font {font_id} not found',
            )

    # Validate season titles and extras
    season_titles = join_lists(
        update_template.season_title_ranges,update_template.season_title_values,
        'season title ranges and names',
    )
    extras = join_lists(
        update_template.extra_keys, update_template.extra_values,
        'extra keys and values',
    )

    # Update if specified and new
    changed = False
    if season_titles != UNSPECIFIED and template.season_titles != season_titles:
        log.error(f'SETTING template.season_titles={season_titles}')
        template.season_titles = season_titles
        changed = True
    if extras != UNSPECIFIED and template.extras != extras:
        log.error(f'SETTING template.extras={extras}')
        template.extras = extras
        changed = True
    
    # Update each attribute of the object
    for attr, value in update_template.dict().items():
        # Skip intermediate keys 
        if attr in ('season_title_ranges', 'season_title_values',
                    'extra_keys', 'extra_values'):
            continue
        if value != UNSPECIFIED and getattr(template, attr) != value:
            setattr(template, attr, value)
            log.error(f'SETTING template.{attr}={getattr(template, attr)}')
            changed = True

    # If any values were changed, commit to database
    if changed:
        db.commit()

    return template


@template_router.delete('/{template_id}', status_code=204)
async def delete_template(
        template_id: int,
        db = Depends(get_database)) -> None:

    query = db.query(models.template.Template).filter_by(id=template_id)
    if query.first() is None:
        raise HTTPException(
            status_code=404,
            detail=f'Template {template_id} not found',
        )

    query.delete()
    db.commit()

    return None