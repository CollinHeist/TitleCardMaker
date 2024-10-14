from typing import Optional, Union

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_preferences
from app.models.episode import Episode
from app.models.font import Font
from app.models.series import Series
from app.schemas.availability import AvailableFont
from app.schemas.font import NamedFont
from modules.Debug import Logger, log


def get_effective_fonts(
        series: Series,
        episode: Optional[Episode] = None,
    ) -> Union[tuple[NamedFont, None], tuple[None, NamedFont]]:
    """
    Get the effective Series and Episode Fonts for the given Series and
    optional Episode. This evaluates the Episode Font overrides Series
    Font.

    Args:
        series: Series whose Font is being evaluated.
        episode: Episode whose Font is being evaluated.

    Returns:
        Tuple of the Series and Episode Font objects (or None). If an
        Episode is provided AND that Episode has a Font definition, then
        the Series Font is always None, and the Episode Font is
        returned. Otherwise the Series Font is returned, and the Episode
        Font is always None.
    """

    # No Episode OR Episode has no Font, return Series Font and None
    if episode is None or not episode.font:
        return series.font, None

    # Episode defines Font, return None and Episode Font
    return None, episode.font


def get_available_fonts(db: Session) -> list[AvailableFont]:
    """
    Get a list of all available Font information.

    Args:
        db: SQL database to query for the given object.

    Returns:
        List of dictionaries with the keys `id` and `name` for all
        defined Fonts.
    """

    return [
        {'id': font.id, 'name': font.name}
        for font in db.query(Font).order_by(Font.name).all()
    ]


def delete_font_files(font: Font, *, log: Logger = log) -> None:
    """
    Delete all files in the folder associated with the given Font. This
    is a recursive operation, deleting ANY files in the subfolder - not
    just those assigned to the Font itself.

    Args:
        font: Font whose files are being deleted.
        log: Logger for all log messages.

    Raises:
        HTTPException (500): Some error occurred while deleting a file
            or folder in the directory.
    """

    # If this Font's directory does not exist, exit
    font_dir = get_preferences().asset_directory / 'fonts' / str(font.id)
    if not font_dir.exists():
        return None

    # Delete all files in the directory
    for file in font_dir.iterdir():
        try:
            if file.is_file():
                file.unlink(missing_ok=True)
                log.debug(f'Deleted "fonts/{font.id}/{file.name}"')
            else:
                file.rmdir()
        except OSError as exc:
            log.exception(f'Error deleting "{file}"')
            raise HTTPException(
                status_code=500,
                detail='Error deleting Font file(s)',
            ) from exc

    return None 
