from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, Body, Depends, Form, HTTPException

from app.dependencies import get_database, get_scheduler, get_preferences
import app.models as models
from app.schemas.base import Base, UNSPECIFIED

from modules.Debug import log

# Job ID's for scheduled tasks
JOB_REFRESH_EPISODE_DATA: str = 'refresh episode data'
JOB_SYNC_INTERFACES: str = 'sync interfaces'
JOB_CREATE_TITLE_CARDS: str = 'create title cards'
JOBS = [
    {'id': JOB_REFRESH_EPISODE_DATA,
     'function': ...,  # TODO populate with actual function call
     'interval': 60 * 60 * 6,  # 6 hours
    },
    {'id': JOB_SYNC_INTERFACES,
     'function': ...,
     'interval': 60 * 60 * 6, # 6 hours
    },
    {'id': JOB_CREATE_TITLE_CARDS,
     'function': ...,
     'interval': 60 * 60 * 6, # 6 hours
    },
]

# Create sub router for all /schedule API requests
schedule_router = APIRouter(
    prefix='/schedule',
    tags=['Schedule'],
)

# Initialize scheduler with starting events
def initialize_scheduler() -> None:
    scheduler = get_scheduler()
    for job in JOBS:
        if scheduler.get_job(job['id']) is None:
            scheduler.add_job(
                job['function'],
                'interval',
                seconds=job['interval'],
                id=job['id'],
                replace_existing=True,
            )
initialize_scheduler()

...