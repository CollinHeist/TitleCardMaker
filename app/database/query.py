from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

import app.models as models
from app.schemas.card import TitleCard
from app.schemas.episode import Episode
from app.schemas.font import NamedFont
from app.schemas.series import Series, Template
from app.schemas.sync import Sync
from modules.Debug import log


def _get_obj(
        db: Session,
        model: Any,
        model_name: str,
        object_id: int,
        raise_exc: bool = True
    ) -> Optional[Any]:
    """
    Get the Object from the Database with the given ID.

    Args:
        db: SQL Database to query for the given object.
        model: SQL model to filter the SQL Database Table by.
        model_name: Name of the Model for logging.
        object_id: ID of the Object to query for.
        raise_exc: Whether to raise 404 if the given object does not 
            exist. If False, then only an error message is logged.

    Returns:
        Object with the given ID. If one cannot be found and raise_exc
        is False, or if the given ID is None, then None is returned.

    Raises:
        HTTPException with a 404 status code if the Object cannot be
        found and raise_exc is True.
    """

    # No ID provided, return immediately
    if object_id is None:
        return None

    if (obj := db.query(model).filter_by(id=object_id).first()) is None:
        if raise_exc:
            raise HTTPException(
                status_code=404,
                detail=f'{model_name} {object_id} not found',
            )
        else:
            log.error(f'{model_name} {object_id} not found')
            return None

    return obj


def get_card(
        db: Session,
        card_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[TitleCard]:
    """
    Get the Card with the given ID from the given Database.

    See _get_obj docstring for all details.
    """

    return _get_obj(db, models.card.Card, 'Card', card_id, raise_exc)


def get_episode(
        db: Session,
        episode_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[Episode]:
    """
    Get the Episode with the given ID from the given Database.

    See _get_obj docstring for all details.
    """

    return _get_obj(db, models.episode.Episode, 'Episode', episode_id,raise_exc)


def get_font(
        db: Session,
        font_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[NamedFont]:
    """
    Get the Font with the given ID from the given Database.

    See _get_obj docstring for all details.
    """

    return _get_obj(db, models.font.Font, 'Font', font_id, raise_exc)


def get_series(
        db: Session,
        series_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[Series]:
    """
    Get the Series with the given ID from the given Database.

    See _get_obj docstring for all details.
    """

    return _get_obj(db, models.series.Series, 'Series', series_id, raise_exc)


def get_sync(
        db: Session,
        sync_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[Sync]:
    """
    Get the Sync with the given ID from the given Database.

    See _get_obj docstring for all details.
    """

    return _get_obj(db, models.sync.Sync, 'Sync', sync_id, raise_exc)


def get_template(
        db: Session,
        template_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[Template]:
    """
    Get the Template with the given ID from the given Database.

    See _get_obj docstring for all details.
    """

    return _get_obj(
        db, models.template.Template, 'Template', template_id, raise_exc
    )


def get_all_templates(
        db: Session,
        obj_dict: dict,
        *,
        raise_exc: bool = True,
    ) -> list[Template]:
    """
    Get all Templates defined in the given Dictionaries "template_ids"
    key. This removes the "template_ids" key from obj_dict.

    Args:
        db: Database to query for Templates by their ID's.
        obj_dict: Dictionary whose "template_ids" key to pop and parse
            for Template ID's.

    Returns:
        List of Template objects whose order and ID correspond to the
        indicated ID's.

    Raises:
        HTTPException (404) if any of the indicated Templates do not
        exist.
    """

    if not (template_ids := obj_dict.pop('template_ids', [])):
        return []

    return [
        get_template(db, template_id, raise_exc=raise_exc)
        for template_id in template_ids
    ]
