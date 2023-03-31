from pathlib import Path
from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session

from app.dependencies import get_database
from app.dependencies import get_preferences
import app.models as models
# from app.schemas.font import Font, TitleCase, PreviewFont
from app.schemas.card import TitleCard, NewTitleCard, PreviewTitleCard
from modules.Debug import log
from modules.TitleCard import TitleCard as TitleCardCreator
 
def join_lists(keys: list[Any], vals: list[Any], desc: str,
        default: Any=None) -> Union[dict[str, Any], None]:

    if (keys is None) ^ (vals is None):
        raise HTTPException(
            status_code=400,
            detail=f'Provide same number of {desc}',
        )
    elif keys is not None and vals is not None:
        if len(keys) != len(vals):
            raise HTTPException(
                status_code=400,
                detail=f'Provide same number of {desc}',
            )
        else:
            return {key: val for key, val in zip(keys, vals) if len(key) > 0}

    return default


def priority_merge_v2(merge_base, *dicts):
    """
    Merges an arbitrary number of nested dictionaries, with the values of later dictionaries taking priority over earlier ones.
    If a key is present in multiple dictionaries with a non-None value, the value of the latest dictionary takes priority.
    If a key is present in multiple dictionaries with a value of None in the latest dictionary, the value of the first non-None dictionary takes priority.
    """

    for dict_ in dicts:
        # Skip non-dictionaries, cannot merge
        if not isinstance(dict_, dict):
            continue
        
        for key, value in dict_.items():
            # Skip underscored keys
            if key.startswith('_'):
                continue

            if key in merge_base:
                if isinstance(value, dict):
                    priority_merge_v2(merge_base[key], value)
                elif value is not None:
                    merge_base[key] = value
            else:
                if value is not None:
                    merge_base[key] = value


def create_font_dict(font) -> dict[str, Any]:
    return {
        f'font_{key}': value
        for key, value in font.__dict__.items()
        if not key.startswith('_')
    }

# Create sub router for all /connection API requests
card_router = APIRouter(
    prefix='/cards',
    tags=['Title Cards'],
)


@card_router.get('/{card_id}')
def get_title_card(
        card_id: int,
        db = Depends(get_database)) -> str:

    ...


@card_router.get('/series/{series_id}', status_code=200, tags=['Series'])
async def get_series_cards(
        series_id: int,
        db=Depends(get_database)) -> list[TitleCard]:
    """
    Get all title cards for the given series.

    - series_id: ID of the series to get the cards of.
    """

    return db.query(models.card.Card).filter_by(series_id=series_id).all()


@card_router.delete('/series/{series_id}', status_code=204, tags=['Series'])
async def delete_series_cards(
        series_id: int,
        db=Depends(get_database)) -> None:

    # TODO: Delete actual files

    db.query(models.card.Card).filter_by(series_id=series_id).delete()
    db.commit()

    return None




@card_router.get('/episode/{episode_id}', tags=['Episodes'])
def get_episode_card(
        episode_id: int,
        db=Depends(get_database)) -> int:

    card = db.query(models.card.Card).filter_by(episode_id=episode_id).first()
    if episode is None:
        raise HTTPException(status_code=404)

    ...