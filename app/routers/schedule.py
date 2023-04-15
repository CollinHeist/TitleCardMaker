from typing import Any, Literal, Optional, Union

from fastapi import APIRouter, Body, Depends, Form, HTTPException

from app.dependencies import get_scheduler, get_preferences
import app.models as models
from app.routers.sync import sync_all
from app.schemas.base import Base, UNSPECIFIED
from app.schemas.schedule import NewJob, ScheduledTask, UpdateInterval

from modules.Debug import log

def fake_func():
    ...

# Create sub router for all /schedule API requests
schedule_router = APIRouter(
    prefix='/schedule',
    tags=['Scheduler'],
)


# Job ID's for scheduled tasks
JOB_REFRESH_EPISODE_DATA: str = 'RefreshEpisodeData'
JOB_SYNC_INTERFACES: str = 'SyncInterfaces'
JOB_DOWNLOAD_SOURCE_IMAGES: str = 'DownloadSourceImages'
JOB_CREATE_TITLE_CARDS: str = 'CreateTitleCards'
JOB_LOAD_MEDIA_SERVERS: str = 'LoadMediaServers'

TaskID = Literal[
    JOB_REFRESH_EPISODE_DATA, JOB_SYNC_INTERFACES, JOB_DOWNLOAD_SOURCE_IMAGES,
    JOB_CREATE_TITLE_CARDS, JOB_LOAD_MEDIA_SERVERS
]

BaseJobs = {
    # TODO populate with actual function calls
    JOB_REFRESH_EPISODE_DATA: NewJob(
        id=JOB_REFRESH_EPISODE_DATA,
        function=fake_func,
        seconds=60 * 60 * 6,
        description='Look for new episodes and update all existing episodes',
    ), JOB_SYNC_INTERFACES: NewJob(
        id=JOB_SYNC_INTERFACES,
        function=sync_all,
        seconds=60 * 60 * 6,
        description='Run all defined Syncs, adding any new Series',
    ), JOB_DOWNLOAD_SOURCE_IMAGES: NewJob(
        id=JOB_DOWNLOAD_SOURCE_IMAGES,
        function=fake_func,
        seconds=60 * 60 * 4,
        description='Download source images for Title Cards',
    ), JOB_CREATE_TITLE_CARDS: NewJob(
        id=JOB_CREATE_TITLE_CARDS,
        function=fake_func,
        seconds=60 * 60 * 4,
        description='Create all missing or updated Title Cards',
    ), JOB_LOAD_MEDIA_SERVERS: NewJob(
        id=JOB_LOAD_MEDIA_SERVERS,
        function=fake_func,
        seconds=60 * 60 * 4,
        description='Load all Title Cards into Emby, Jellyfin, or Plex',
    ),
}

# Initialize scheduler with starting jobs
def initialize_scheduler() -> None:
    scheduler = get_scheduler()
    for job in BaseJobs.values():
        if scheduler.get_job(job.id) is None:
            scheduler.add_job(
                job.function,
                'interval',
                seconds=job.seconds,
                id=job.id,
                replace_existing=True,
            )
initialize_scheduler()


def _scheduled_task_from_job(job) -> ScheduledTask:
    """
    Create a ScheduledTask object for the given apscheduler.job.

    Args:
        job: APScheduler Job object to create a ScheduledTask of.

    Returns:
        ScheduledTask describing the given Job.
    """

    return ScheduledTask(
        id=str(job.id),
        frequency=job.trigger.interval.total_seconds(),
        next_run=str(job.next_run_time),
        description=BaseJobs.get(job.id).description,
    )


@schedule_router.get('/scheduled', status_code=200)
def get_scheduled_tasks(
        scheduler = Depends(get_scheduler)) -> list[ScheduledTask]:
    """
    Get scheduling details for all defined Tasks.
    """

    return [
        _scheduled_task_from_job(job)
        for job in scheduler.get_jobs()
        if job.id in BaseJobs
    ]


@schedule_router.get('/{task_id}', status_code=200)
def get_scheduled_task(
        task_id: TaskID,
        scheduler = Depends(get_scheduler)) -> ScheduledTask:
    """
    Get the schedule details for the indicated Task.

    - task_id: ID of the Task to get the details of.
    """

    if (job := scheduler.get_job(task_id)) is None:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    return _scheduled_task_from_job(job)


@schedule_router.patch('/update/{task_id}', status_code=200)
def reschedule_task(
        task_id: TaskID,
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
    
    return _scheduled_task_from_job(job)