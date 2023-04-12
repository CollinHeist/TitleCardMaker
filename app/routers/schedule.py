from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, Body, Depends, Form, HTTPException

from app.dependencies import get_scheduler, get_preferences
import app.models as models
from app.routers.sync import sync_all
from app.schemas.base import Base, UNSPECIFIED
from app.schemas.schedule import ScheduledTask, UpdateInterval

from modules.Debug import log

def fake_refresh_episode_data():
    ...

def fake_create_title_cards():
    ...

# Job ID's for scheduled tasks
JOB_REFRESH_EPISODE_DATA: str = 'refresh episode data'
JOB_SYNC_INTERFACES: str = 'sync interfaces'
JOB_CREATE_TITLE_CARDS: str = 'create title cards'
JOBS = [
    {'id': JOB_REFRESH_EPISODE_DATA,
     'function': fake_refresh_episode_data,  # TODO populate with actual function call
     'interval': 60 * 60 * 6,  # 6 hours
    },
    {'id': JOB_SYNC_INTERFACES,
     'function': sync_all,
     'interval': 60 * 60 * 6, # 6 hours
    },
    {'id': JOB_CREATE_TITLE_CARDS,
     'function': fake_create_title_cards,
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


@schedule_router.get('/scheduled')
def get_scheduled_tasks(
        scheduler = Depends(get_scheduler)) -> list[ScheduledTask]:

    return [{
        'task_id': str(job.id),
        'frequency': job.trigger.interval.total_seconds(),
        'next_run': str(job.next_run_time),
    } for job in scheduler.get_jobs()]


@schedule_router.patch('update/{task_id}')
def update_scheduled_task(
        task_id: str,
        update_interval: UpdateInterval = Body(...),
        scheduler = Depends(get_scheduler)) -> ScheduledTask:
    """
    Reschedule the given Task with a new interval.

    - task_id: ID of the Task being rescheduled.
    - update_interval: UpdateInterval whose total interval is used to
      reschedule the given Task.
    """

    log.critical(f'{update_interval.dict()=}')
    # Verify job exists, raise 404 if DNE
    if (job := scheduler.get_job(task_id)) is None:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    # Reschedule with modified interval
    job = scheduler.reschedule_job(
        task_id,
        trigger='interval',
        **update_interval.dict()
    )
    
    return {
        'task_id': str(job.id),
        'frequency': job.trigger.interval.total_seconds(),
        'next_run': str(job.next_run_time),
    }