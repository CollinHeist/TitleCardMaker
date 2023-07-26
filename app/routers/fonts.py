from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.database.query import get_font
from app.dependencies import * # pylint: disable=wildcard-import,unused-wildcard-import
from app import models
from app.schemas.font import NamedFont, NewNamedFont, UpdateNamedFont
from app.schemas.preferences import Preferences


# Create sub router for all /fonts API requests
font_router = APIRouter(
    prefix='/fonts',
    tags=['Fonts']
)


@font_router.post('/new', status_code=201)
def create_font(
        new_font: NewNamedFont = Body(...),
        db: Session = Depends(get_database),
    ) -> NamedFont:
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
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> NamedFont:
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
        request: Request,
        db: Session = Depends(get_database),
    ) -> NamedFont:
    """
    Delete the font file associated with the given Font.

    - font_id: ID of the Font to delete the file of.
    """

    # Get contextual logger
    log = request.state.log

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
            ) from e

    # Reset file path, update database
    font.file = None
    db.commit()

    return font


@font_router.patch('/{font_id}', status_code=200)
def update_font(
        font_id: int,
        request: Request,
        update_font: UpdateNamedFont = Body(...),
        db: Session = Depends(get_database),
    ) -> NamedFont:
    """
    Update the Font with the given ID. Only provided fields are updated.

    - font_id: ID of the Font to update.
    - update_font: UpdateFont containing fields to update.
    """

    # Get contextual logger
    log = request.state.log

    # Get existing font object, raise 404 if DNE
    font = get_font(db, font_id, raise_exc=True)

    # Update other attributes
    changed = False
    for attribute, value in update_font.dict().items():
        if getattr(font, attribute) != value:
            setattr(font, attribute, value)
            changed = True
            log.debug(f'Font[{font_id}].{attribute} = {value}')

    # If object was changed, update DB
    if changed:
        db.commit()

    return font


@font_router.get('/all', status_code=200)
def get_all_fonts(
        order_by: Literal['id', 'name'] = 'name',
        db: Session = Depends(get_database),
    ) -> list[NamedFont]:
    """
    Get all defined Fonts.
    """

    if order_by == 'id':
        return db.query(models.font.Font).all()
    
    return db.query(models.font.Font).order_by(models.font.Font.name).all()


@font_router.get('/{font_id}', status_code=200)
def get_font_by_id(
        font_id: int,
        db: Session = Depends(get_database),
    ) -> NamedFont:
    """
    Get the Font with the given ID.

    - font_id: ID of the Font to retrieve.
    """

    return get_font(db, font_id, raise_exc=True)


@font_router.delete('/{font_id}', status_code=204)
def delete_font(
        font_id: int,
        request: Request,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Delete the Font with the given ID. This also deletes the font's
    font file if it exists.

    - font_id: ID of the Font to delete.
    """

    # Get contextual logger
    log = request.state.log

    # Get specified Font, raise 404 if DNE
    font = get_font(db, font_id, raise_exc=True)

    # If Font file is specified (and exists), delete
    if (font_file := font.file) is not None:
        try:
            Path(font_file).unlink(missing_ok=True)
        except Exception as e:
            log.exception(f'Error deleting {font_file}', e)
            raise HTTPException(
                status_code=500,
                detail=f'Error deleting font file - {e}',
            ) from e

    db.delete(font)
    db.commit()
