from pathlib import Path
from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.dependencies import get_preferences
from app.schemas.base import UNSPECIFIED
from app.schemas.font import Font, NewFont, UpdateFont
import app.models as models
from modules.Debug import log

# Create sub router for all /fonts API requests
font_router = APIRouter(
    prefix='/fonts',
    tags=['Fonts']
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


@font_router.post('/new', status_code=201)
def create_font(
        new_font: NewFont = Body(...),
        db = Depends(get_database)) -> Font:
    """
    Create a new Font.

    - new_font: Font definition to create.
    """

    # Join replacements inputs/outputs
    replacements = join_lists(
        new_font.replacements_in, new_font.replacements_out,
        'character replacements', default={},
    )

    # Get dictionary, remove replacements in/outs
    font_dict = new_font.dict()
    for remove_key in ('replacements_in', 'replacements_out'):
        font_dict.pop(remove_key, None)

    # Add to database
    font = models.font.Font(replacements=replacements, **font_dict)
    db.add(font)
    db.commit()

    return font


@font_router.put('/{font_id}/file', status_code=200)
async def add_font_file(
        font_id: int,
        file: UploadFile,
        db = Depends(get_database),
        preferences = Depends(get_preferences)) -> Font:
    """
    Add a custom font file to the specified Font.

    - font_id: ID of the font to upload the font file to.
    - file: Font file to attach to the specified font.
    """

    font = db.query(models.font.Font).filter_by(id=font_id).first()
    if font is None:
        raise HTTPException(
            status_code=404,
            detail=f'Font {font_id} not found',
        )

    # Download file, raise 400 if contentless
    file_content = await file.read()
    if len(file_content) == 0:
        raise HTTPException(
            status_code=400,
            detail=f'Font file has no content',
        )

    # Write to file, update path in database.
    font_directory = preferences.asset_directory / 'fonts'
    file_path = font_directory / str(font.id) / file.filename
    file_path.parent.mkdir(exist_ok=True, parents=True)
    file_path.write_bytes(file_content)
    font.file_path = str(file_path)
    db.commit()

    return font


@font_router.delete('/{font_id}/file', status_code=200)
def delete_font_file(
        font_id: int,
        db = Depends(get_database)) -> Font:
    """
    Delete the font file associated with the given Font.

    - font_id: ID of the Font to delete the file of.
    """

    # Get existing font object, raise 404 if DNE
    font = db.query(models.font.Font).filter_by(id=font_id).first()
    if font is None:
        raise HTTPException(
            status_code=404,
            detail=f'Font {font_id} not found',
        )

    # Font has no file, return unmodified
    if font.file_path is None:
        return font

    # If file exists, delete
    if Path(font.file_path).exists():
        # Raise exception if unable to delete file
        try:
            Path(font.file_path).unlink()
        except Exception as e:
            log.exception(f'Error deleting {font.file_path}', e)
            raise HTTPException(
                status_code=500,
                detail=f'Error deleting font file - {e}',
            )

    # Reset file path, update database
    font.file_path = None
    db.commit()

    return font


@font_router.patch('/{font_id}', status_code=200)
def update_font(
        font_id: int,
        update_font: UpdateFont = Body(...),
        db = Depends(get_database)) -> Font:
    """
    Update the Font with the given ID. Only provided fields are updated.

    - font_id: ID of the Font to update.
    - update_font: UpdateFont containing fields to update.
    """

    # Get existing font object, raise 404 if DNE
    font = db.query(models.font.Font).filter_by(id=font_id).first()
    if font is None:
        raise HTTPException(
            status_code=404,
            detail=f'Font {font_id} not found',
        )

    # Update object
    changed = False

    # Update replacements
    replacements = join_lists(
        update_font.replacements_in, update_font.replacements_out,
        'character replacements'
    )
    if replacements != UNSPECIFIED and font.replacements != replacements:
        font.replacements = replacements
        changed = True

    # Update other attributes
    for attribute, value in update_font.dict().items():
        if attribute in ('replacements_in', 'replacements_out'):
            continue
        if value is not None and getattr(font, attribute) != value:
            setattr(font, attribute, value)
            changed = True

    # If object was changed, update DB
    if changed:
        db.commit()

    return font


@font_router.get('/all', status_code=200)
def get_all_fonts(
        db = Depends(get_database)) -> list[Font]:
    """
    Get all defined Fonts.
    """

    return db.query(models.font.Font).all()


@font_router.get('/{font_id}', status_code=200)
def get_font_by_id(
        font_id: int,
        db = Depends(get_database)) -> Font:
    """
    Get the Font with the given ID.

    - font_id: ID of the Font to retrieve.
    """

    font = db.query(models.font.Font).filter_by(id=font_id).first()
    if font is None:
        raise HTTPException(
            status_code=404,
            detail=f'Font {font_id} not found',
        )

    return font


@font_router.delete('/{font_id}', status_code=204)
def delete_font(
        font_id: int,
        db = Depends(get_database)) -> None:
    """
    Delete the Font with the given ID. This also deletes the font's
    font file if it exists.

    - font_id: ID of the Fync to delete
    """

    query = db.query(models.font.Font).filter_by(id=font_id)
    if query.first() is None:
        raise HTTPException(
            status_code=404,
            detail=f'Font {font_id} not found',
        )

    # If font file is specified (and exists), delete
    if (path := query.first().file_path) is not None:
        if (file := Path(path)).exists():
            try:
                file.unlink()
            except Exception as e:
                log.exception(f'Error deleting {file}', e)
                raise HTTPException(
                    status_code=500,
                    detail=f'Error deleting font file - {e}',
                )
        
    query.delete()
    db.commit()

    return None