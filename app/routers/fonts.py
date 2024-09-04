from logging import Logger
from string import printable, punctuation, whitespace
from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session
from unidecode import unidecode

from app.database.query import get_font
from app.dependencies import get_database, get_preferences
from app.internal.auth import get_current_user
from app.models.font import Font
from app.models.preferences import Preferences
from app.schemas.font import (
    FontAnalysis,
    NamedFont,
    NewNamedFont,
    UpdateNamedFont
)
from modules.FontValidator2 import FontValidator


"""Common character replacements to try when querying replacements"""
COMMON_REPLACEMENTS = {
    '`': "'",
    '’': "'",
    '&': 'and',
    '–': '-',
    '…': '...',
    'ø': 'o',
    'Ø': 'O',
}


# Create sub router for all /fonts API requests
font_router = APIRouter(
    prefix='/fonts',
    tags=['Fonts'],
    dependencies=[Depends(get_current_user)],
)


@font_router.post('/new')
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


@font_router.put('/{font_id}/file')
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
    if not file_content:
        raise HTTPException(
            status_code=400,
            detail='Font file is invalid',
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


@font_router.delete('/{font_id}/file')
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
    log: Logger = request.state.log

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
        log.exception(f'Error deleting {font.file}')
        raise HTTPException(
            status_code=400,
            detail=f'Error deleting Font file - {exc}',
        ) from exc

    # Reset file path, update database
    font.file_name = None
    db.commit()

    return font


@font_router.patch('/{font_id}')
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
    log: Logger = request.state.log

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


@font_router.get('/all')
def get_all_fonts(
        order: Literal['id', 'name'] = 'name',
        db: Session = Depends(get_database),
    ) -> list[NamedFont]:
    """Get all defined Fonts."""

    return db.query(Font)\
        .order_by(Font.id if order == 'id' else Font.sort_name)\
        .all()


@font_router.get('/{font_id}')
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
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Delete the Font with the given ID. This also deletes the font's
    font file if it exists.

    - font_id: ID of the Font to delete.
    """

    # Get contextual logger
    log: Logger = request.state.log

    # Get specified Font, raise 404 if DNE
    font = get_font(db, font_id, raise_exc=True)

    # Delete from global setting if indicated
    if font_id in preferences.default_fonts.values():
        preferences.default_fonts = {
            card_type: id_
            for card_type, id_ in preferences.default_fonts.items()
            if id_ != font_id
        }
        log.debug(f'{preferences.default_fonts = }')

    # If Font file is specified (and exists), delete
    font_dir = preferences.asset_directory / 'fonts' / str(font_id)
    if font_dir.exists():
        for file in font_dir.iterdir():
            try:
                if file.is_file():
                    file.unlink(missing_ok=True)
                else:
                    file.rmdir()
            except OSError as exc:
                log.exception(f'Error deleting "{file}"')
                raise HTTPException(
                    status_code=500,
                    detail='Error deleting Font file(s)',
                ) from exc

    db.delete(font)
    db.commit()
    preferences.commit()


@font_router.get('/{font_id}/analysis')
def get_suggested_font_replacements(
        request: Request,
        font_id: int,
        db: Session = Depends(get_database),
    ) -> FontAnalysis:
    """
    Analyze the Font file associated with the Font with the given ID and
    determine a suggested set of character replacements, along with a
    list of which characters have no suitable replacements. This looks
    at the leters of all associated Episodes that use this Font (through
    Series, Templates, etc.), as well as the standard alphanumberic
    set of English characters and punctuation.

    - font_id: ID of the Font to analyze. If this Font does not have a
    custom Font file, then no analysis is performed.
    """

    # Get contextual logger
    log: Logger = request.state.log

    # Get Font with this ID, raise 404 if DNE
    font = get_font(db, font_id, raise_exc=True)

    # Font has no custom file, make no suggestions
    if font.file_name is None:
        return FontAnalysis()

    # Get any titles associated with this Font - look at Episodes using this
    # Font; translated titles of Episodes using this Font; Episodes of Series
    # using this Font; translated titles of Episodes of Series using this Font;
    # Episodes using a Template using this Font; translated titles of Episodes
    # using a Template using this Font; Episodes of Series using a Template
    # using this Font; and translated titles of Episodes of Series using a
    # Template using this Font
    titles = set(episode.title for episode in font.episodes) \
        | set(translation for episode in font.episodes
                          for key, translation in episode.translations.items()
                          if key == 'preferred_title') \
        | set(episode.title for series in font.series
                            for episode in series.episodes) \
        | set(translation for series in font.series
                          for episode in series.episodes
                          for key, translation in episode.translations.items()
                          if key == 'preferred_title') \
        | set(episode.title for template in font.templates
                            for episode in template.episodes) \
        | set(translation for template in font.templates
                          for episode in template.episodes
                          for key, translation in episode.translations.items()
                          if key == 'preferred_title') \
        | set(episode.title for template in font.templates
                            for series in template.series
                            for episode in series.episodes) \
        | set(translation for template in font.templates
                          for series in template.series
                          for episode in series.episodes
                          for key, translation in episode.translations.items()
                          if key == 'preferred_title')

    # Get all (non-whitespace) letters in these titles, add base printables
    title_letters = set(''.join(titles).lower()) | set(''.join(titles).upper())
    letters = (title_letters | set(printable)) - set(whitespace)

    # Query FontValidator for this Font
    validator = FontValidator(font.file)
    missing = validator.get_missing_characters(letters)
    if missing:
        log.debug(f'Identified missing characters: {" ".join(missing)}')

    # Attempt to find replacements for all missing characters
    bad, replacements = [], {}
    for char in missing:
        # Remove any unicode non-spacing combining marks - e.g. é -> ´e -> e
        replacement = unidecode(char, errors='preserve')

        # See if there is a common replacement for this
        if (replacement in missing
            and char in COMMON_REPLACEMENTS
            and all(c not in missing for c in COMMON_REPLACEMENTS[char])):
            replacement = COMMON_REPLACEMENTS[char]

        # If this replacement is missing, try the other case-equivalent
        if replacement in missing and replacement.lower() not in missing:
            replacement = replacement.lower()
        if replacement in missing and replacement.upper() not in missing:
            replacement = replacement.upper()

        # If replacement is still missing, suggest deletion if character is
        # punctuation
        if replacement in missing and char in punctuation:
            replacement = ''

        # If the replacement is defined, add to replacements set
        if replacement not in missing:
            replacements[char] = replacement
        else:
            bad.append(char)

    return FontAnalysis(
        replacements=replacements,
        missing=bad,
    )
