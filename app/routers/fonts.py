from pathlib import Path
from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, HTTPException, Query, UploadFile

from app.database.query import get_font
from app.dependencies import get_database
from app.dependencies import get_preferences
from app.schemas.base import UNSPECIFIED
from app.schemas.font import NamedFont, NewNamedFont, UpdateNamedFont
import app.models as models
from modules.Debug import log

# Create sub router for all /fonts API requests
font_router = APIRouter(
    prefix='/fonts',
    tags=['Fonts']
)


@font_router.post('/new', status_code=201)
def create_font(
        new_font: NewNamedFont = Body(...),
        db = Depends(get_database)) -> NamedFont:
    """
    Create a new Font.

    - new_font: Font definition to create.
    """

    # Add to database
    font = models.font.Font(**new_font.dict())
    db.add(font)
    db.commit()

    return font


@font_router.put('/{font_id}/file', status_code=200)
async def add_font_file(
        font_id: int,
        file: UploadFile,
        db = Depends(get_database),
        preferences = Depends(get_preferences)) -> NamedFont:
    """
    Add a custom font file to the specified Font.

    - font_id: ID of the font to upload the font file to.
    - file: Font file to attach to the specified font.
    """

    # Get existing font object, raise 404 if DNE
    font = get_font(db, font_id, raise_exc=True)

    # Download file, raise 400 if contentless
    file_content = await file.read()
    if len(file_content) == 0:
        raise HTTPException(
            status_code=400,
            detail=f'Font file has no content',
        )

    # Write to file
    font_directory = preferences.asset_directory / 'fonts'
    file_path = font_directory / str(font.id) / file.filename
    file_path.parent.mkdir(exist_ok=True, parents=True)
    file_path.write_bytes(file_content)

    # Update object and database
    font.file = str(file_path)
    db.commit()

    return font


@font_router.delete('/{font_id}/file', status_code=200)
def delete_font_file(
        font_id: int,
        db = Depends(get_database)) -> NamedFont:
    """
    Delete the font file associated with the given Font.

    - font_id: ID of the Font to delete the file of.
    """

    # Get existing font object, raise 404 if DNE
    font = get_font(db, font_id, raise_exc=True)

    # Font has no file, return unmodified
    if font.file is None:
        return font

    # If file exists, delete
    if Path(font.file).exists():
        # Raise exception if unable to delete file
        try:
            Path(font.file).unlink()
        except Exception as e:
            log.exception(f'Error deleting {font.file}', e)
            raise HTTPException(
                status_code=500,
                detail=f'Error deleting font file - {e}',
            )

    # Reset file path, update database
    font.file = None
    db.commit()

    return font


@font_router.patch('/{font_id}', status_code=200)
def update_font(
        font_id: int,
        update_font: UpdateNamedFont = Body(...),
        db = Depends(get_database)) -> NamedFont:
    """
    Update the Font with the given ID. Only provided fields are updated.

    - font_id: ID of the Font to update.
    - update_font: UpdateFont containing fields to update.
    """
    log.critical(f'{update_font.dict()=}')
    # Get existing font object, raise 404 if DNE
    font = get_font(db, font_id, raise_exc=True)

    # Update other attributes
    changed = False
    for attribute, value in update_font.dict().items():
        if getattr(font, attribute) != value:
            setattr(font, attribute, value)
            changed = True
            log.debug(f'SETTING font[{font_id}].{attribute} = {value}')

    # If object was changed, update DB
    if changed:
        db.commit()

    return font


@font_router.get('/all', status_code=200)
def get_all_fonts(
        db = Depends(get_database)) -> list[NamedFont]:
    """
    Get all defined Fonts.
    """

    return db.query(models.font.Font).all()


@font_router.get('/{font_id}', status_code=200)
def get_font_by_id(
        font_id: int,
        db = Depends(get_database)) -> NamedFont:
    """
    Get the Font with the given ID.

    - font_id: ID of the Font to retrieve.
    """

    return get_font(db, font_id, raise_exc=True)


@font_router.delete('/{font_id}', status_code=204)
def delete_font(
        font_id: int,
        db = Depends(get_database)) -> None:
    """
    Delete the Font with the given ID. This also deletes the font's
    font file if it exists, as well as removing any references to this
    font on any associated Template, Series, or Episode entries.

    - font_id: ID of the Font to delete.
    """

    query = db.query(models.font.Font).filter_by(id=font_id)
    if query.first() is None:
        raise HTTPException(
            status_code=404,
            detail=f'Font {font_id} not found',
        )

    # If font file is specified (and exists), delete
    if (path := query.first().file) is not None:
        if (file := Path(path)).exists():
            try:
                file.unlink()
            except Exception as e:
                log.exception(f'Error deleting {file}', e)
                raise HTTPException(
                    status_code=500,
                    detail=f'Error deleting font file - {e}',
                )
    
    # Delete font reference from any template, series, or episode
    for template in db.query(models.template.Template)\
            .filter_by(font_id=font_id).all():
        template.font_id = None
    for series in db.query(models.series.Series)\
            .filter_by(font_id=font_id).all():
        series.font_id = None
    for episode in db.query(models.episode.Episode)\
            .filter_by(font_id=font_id).all():
        episode.font_id = None
        
    query.delete()
    db.commit()

    return None