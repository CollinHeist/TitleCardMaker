from typing import Literal, Optional, TypeVar, Union, overload

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.session import Base
from app.dependencies import (
    EmbyInterface, EmbyInterfaces, JellyfinInterface, JellyfinInterfaces,
    PlexInterface, PlexInterfaces, SonarrInterface, SonarrInterfaces,
    TMDbInterface, TMDbInterfaces,
)
from app.models.blueprint import Blueprint
from app.models.card import Card
from app.models.connection import Connection
from app.models.episode import Episode
from app.models.font import Font
from app.models.series import Series
from app.models.sync import Sync
from app.models.template import Template

from modules.Debug import log

_ObjectType = TypeVar('_ObjectType', bound=Base)


def _get_obj(
        db: Session,
        model: _ObjectType,
        model_name: str,
        object_id: int,
        raise_exc: bool = True
    ) -> Optional[_ObjectType]:
    """
    Get the Object from the database with the given ID.

    Args:
        db: SQL database to query for the given object.
        model: SQL model to filter the SQL database Table by.
        model_name: Name of the Model for logging.
        object_id: ID of the Object to query for.
        raise_exc: Whether to raise 404 if the given object does not
            exist. If False, then only an error message is logged.

    Returns:
        Object with the given ID. If one cannot be found and `raise_exc`
        is False, None is returned. None is also returned if `object_id`
        is None.

    Raises:
        HTTPException (404): The Object cannot be found and `raise_exc`
            is True.
    """

    # No ID provided, return immediately
    if object_id is None:
        return None

    # Query for object, raise or return None if not found
    if (obj := db.query(model).filter_by(id=object_id).first()) is None:
        # Object not found and raising exception, raise
        if raise_exc:
            raise HTTPException(
                status_code=404,
                detail=f'{model_name} {object_id} not found',
            )

        log.error(f'{model_name} {object_id} not found')
        return None

    # Object found, return it
    return obj


@overload
def get_blueprint(
        db: Session, blueprint_id: int, *, raise_exc: Literal[True] = True
    ) -> Blueprint:
    ...

def get_blueprint(
        db: Session,
        blueprint_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[Blueprint]:
    """
    Get the Blueprint with the given ID from the given Database.

    See `_get_obj` for all details.
    """

    return _get_obj(db, Blueprint, 'Blueprint', blueprint_id, raise_exc)


@overload
def get_card(
        db: Session, card_id: int, *, raise_exc: Literal[True] = True,
    ) -> Card:
    ...

def get_card(
        db: Session,
        card_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[Card]:
    """
    Get the Card with the given ID from the given Database.

    See `_get_obj` for all details.
    """

    return _get_obj(db, Card, 'Card', card_id, raise_exc)


@overload
def get_connection(
        db: Session, connection_id: int, *, raise_exc: Literal[True] = True,
    ) -> Connection:
    ...

def get_connection(
        db: Session,
        connection_id: int,
        /,
        *,
        raise_exc: bool = True,
    ) -> Optional[Connection]:
    """
    Get the Connection with the given ID from the given Database.

    See `_get_obj` for all details.
    """

    return _get_obj(db, Connection, 'Connection', connection_id, raise_exc)


@overload
def get_episode(
        db: Session, episode_id: int, *, raise_exc: Literal[True] = True,
    ) -> Episode:
    ...

def get_episode(
        db: Session,
        episode_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[Episode]:
    """
    Get the Episode with the given ID from the given Database.

    See `_get_obj` for all details.
    """

    return _get_obj(db, Episode, 'Episode', episode_id, raise_exc)


@overload
def get_font(
        db: Session, font_id: int, *, raise_exc: Literal[True] = True,
    ) -> Font:
    ...

def get_font(
        db: Session,
        font_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[Font]:
    """
    Get the Font with the given ID from the given Database.

    See `_get_obj` docstring for all details.
    """

    return _get_obj(db, Font, 'Font', font_id, raise_exc)


@overload
def get_series(
        db: Session, series_id: int, *, raise_exc: Literal[True] = True,
    ) -> Series:
    ...

def get_series(
        db: Session,
        series_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[Series]:
    """
    Get the Series with the given ID from the given Database.

    See `_get_obj` for all details.
    """

    return _get_obj(db, Series, 'Series', series_id, raise_exc)


@overload
def get_sync(
        db: Session, sync_id: int, *, raise_exc: Literal[True] = True,
    ) -> Sync:
    ...

def get_sync(
        db: Session,
        sync_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[Sync]:
    """
    Get the Sync with the given ID from the given Database.

    See `_get_obj` for all details.
    """

    return _get_obj(db, Sync, 'Sync', sync_id, raise_exc)


@overload
def get_template(
        db: Session, template_id: int, *, raise_exc: Literal[True] = True,
    ) -> Template:
    ...

def get_template(
        db: Session,
        template_id: int,
        *,
        raise_exc: bool = True
    ) -> Optional[Template]:
    """
    Get the Template with the given ID from the given Database.

    See `_get_obj` for all details.
    """

    return _get_obj(db, Template, 'Template', template_id, raise_exc)


@overload
def get_all_templates(
        db: Session, obj_dict: dict, *, raise_exc: Literal[True] = True,
    ) -> list[Template]:
    ...


def get_all_templates(
        db: Session,
        obj_dict: dict,
        *,
        raise_exc: bool = True,
    ) -> Optional[list[Template]]:
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
        HTTPException (404): Any of the indicated Templates do not exist
            and `raise_exc` is True.
    """

    if not (template_ids := obj_dict.pop('template_ids', [])):
        return []

    return [
        get_template(db, template_id, raise_exc=raise_exc)
        for template_id in template_ids
    ]


@overload
def get_interface(
        interface_id: int, *, raise_exc: Literal[True] = True,
    ) -> Union[EmbyInterface, JellyfinInterface, PlexInterface, SonarrInterface,
               TMDbInterface]:
    ...

def get_interface(
        interface_id: int,
        *,
        raise_exc: bool = True,
    ) -> Optional[Union[EmbyInterface, JellyfinInterface, PlexInterface,
                        SonarrInterface, TMDbInterface]]:
    """
    Get the `Interface` to communicate with the service with the given
    ID. This searches all the global `InterfaceGroup` for each service.

    Args:
        interface_id: ID of the Interface to return.
        raise_exc: Whether to raise an `HTTPException` if there is no
            Interface with this ID.

    Returns:
        `Interface` with the given ID, or None (if `raise_exc` is False).
    """

    # Look for interface under each type
    interface = None
    if not interface and interface_id in EmbyInterfaces:
        interface = EmbyInterfaces[interface_id]

    if not interface and interface_id in JellyfinInterfaces:
        interface = JellyfinInterfaces[interface_id]

    if not interface and interface_id in PlexInterfaces:
        interface = PlexInterfaces[interface_id]

    if not interface and interface_id in SonarrInterfaces:
        interface = SonarrInterfaces[interface_id]

    if not interface and interface_id in TMDbInterfaces:
        interface = TMDbInterfaces[interface_id]

    # If defined (and activated), return
    if interface:
        return interface

    # Not defined / activated, raise or return None
    if raise_exc:
        raise HTTPException(
            status_code=404,
            detail=(
                f'No Connection with {interface_id} - Connection might be '
                f'disabled or invalid'
            )
        )

    return None
