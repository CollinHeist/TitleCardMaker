from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.database.query import get_font
from app.dependencies import get_database, get_preferences
from app.internal.auth import get_current_user
from app.models.font import Font
from app.models.preferences import Preferences
from app.schemas.font import NamedFont, NewNamedFont, UpdateNamedFont


# Create sub router for all /fonts API requests
font_router = APIRouter(
    prefix='/fonts',
    tags=['Fonts'],
    dependencies=[Depends(get_current_user)],
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
    font = Font(**new_font.dict())
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
    font.file_name = file_path.name
    db.commit()

    return font


@font_router.delete('/{font_id}/file', status_code=200)
def delete_font_file(
        request: Request,
        font_id: int,
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

    # Font has no file, raise 404
    if font.file is None:
        raise HTTPException(
            status_code=404,
            detail=f'Font {font.name} has no file',
        )

    # Raise exception if unable to delete file
    try:
        font.file.unlink()
    except Exception as exc:
        log.exception(f'Error deleting {font.file}', exc)
        raise HTTPException(
            status_code=500,
            detail=f'Error deleting Font file - {exc}',
        ) from exc

    # Reset file path, update database
    font.file_name = None
    db.commit()

    return font


@font_router.patch('/{font_id}', status_code=200)
def update_font(
        request: Request,
        font_id: int,
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
        order: Literal['id', 'name'] = 'name',
        db: Session = Depends(get_database),
    ) -> list[NamedFont]:
    """
    Get all defined Fonts.
    """

    if order == 'id':
        return db.query(Font).all()

    return db.query(Font).order_by(Font.sort_name).all()


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
        request: Request,
        font_id: int,
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
            font_file.unlink(missing_ok=True)
            font_file.parent.rmdir()
        except Exception as exc:
            log.exception(f'Error deleting {font_file}', exc)
            raise HTTPException(
                status_code=500,
                detail=f'Error deleting font file - {exc}',
            ) from exc

    db.delete(font)
    db.commit()
