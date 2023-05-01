from typing import Any, Literal, Optional, Union

from apscheduler.events import EVENT_JOB_SUBMITTED, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from fastapi import APIRouter, Body, Depends, Form, HTTPException

from app.dependencies import get_scheduler, get_preferences
import app.models as models
from app.routers.cards import create_all_title_cards
from app.routers.episodes import refresh_all_episode_data
from app.routers.sync import sync_all
from app.schemas.base import Base, UNSPECIFIED
from app.schemas.schedule import NewJob, ScheduledTask, UpdateInterval

from modules.Debug import log

def fake_func():
    log.debug(f'Starting fake function')
    from time import sleep
    sleep(5)
    log.debug(f'Ending fake function')

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
        function=refresh_all_episode_data,
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
        function=create_all_title_cards,
        seconds=60 * 60 * 6,
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

# Add listener to update running status of jobs
def job_started_listener(event):
    log.debug(f'Task[{event.job_id}] Started execution')
    BaseJobs.get(event.job_id).running = True

def job_finished_listener(event):
    log.debug(f'Task[{event.job_id}] Finished execution')
    BaseJobs.get(event.job_id).running = False

get_scheduler().add_listener(job_started_listener, EVENT_JOB_SUBMITTED)
get_scheduler().add_listener(job_finished_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)


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
        running=BaseJobs.get(job.id).running,
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

    # If new interval is the same as old interval, skip
    new_interval = (
        update_interval.seconds
        + (update_interval.minutes * 60)
        + (update_interval.hours * 60 * 60)
        + (update_interval.days * 60 * 60 * 24)
        + (update_interval.weeks * 60 * 60 * 24 * 7)
    )
    if new_interval == job.trigger.interval.total_seconds():
        log.debug(f'Task[{job.id}] Not rescheduling, interval unchanged')
        return _scheduled_task_from_job(job)

    # Reschedule with modified interval
    job = scheduler.reschedule_job(
        task_id,
        trigger='interval',
        **update_interval.dict()
    )
    
    return _scheduled_task_from_job(job)


@schedule_router.post('/{task_id}', status_code=201)
def run_task(
        task_id: TaskID,
        scheduler = Depends(get_scheduler)) -> None:
    """
    Run the given Task immediately. This __does not__ reschedule or
    modify the Task's next scheduled run.

    - task_id: ID of the Task to run.
    """

    # Verify Task exists, raise 404 if DNE
    if (job := BaseJobs.get(task_id, None)) is None:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    # Run this Task's function
    job.function()

    return None