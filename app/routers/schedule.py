from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.dependencies import get_scheduler
from app.internal.availability import get_latest_version
from app.internal.cards import (
    create_all_title_cards, refresh_all_remote_card_types
)
from app.internal.episodes import refresh_all_episode_data
from app.internal.series import load_all_media_servers
from app.internal.sources import (
    download_all_source_images, download_all_series_logos
)
from app.internal.sync import sync_all
from app.internal.translate import translate_all_series
from app.schemas.schedule import NewJob, ScheduledTask, UpdateInterval

from modules.Debug import log


# Create sub router for all /schedule API requests
schedule_router = APIRouter(
    prefix='/schedule',
    tags=['Scheduler'],
)


# Job ID's for scheduled tasks
JOB_ADD_TRANSLATIONS: str = 'AddMissingTranslations'
JOB_CREATE_TITLE_CARDS: str = 'CreateTitleCards'
JOB_DOWNLOAD_SERIES_LOGOS: str = 'DownloadSeriesLogos'
JOB_DOWNLOAD_SOURCE_IMAGES: str = 'DownloadSourceImages'
JOB_LOAD_MEDIA_SERVERS: str = 'LoadMediaServers'
JOB_REFRESH_EPISODE_DATA: str = 'RefreshEpisodeData'
JOB_SYNC_INTERFACES: str = 'SyncInterfaces'
# Internal Job ID's
INTERNAL_JOB_CHECK_FOR_NEW_RELEASE: str = 'CheckForNewRelease'
INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES: str = 'RefreshRemoteCardTypes'

TaskID = Literal[
    JOB_REFRESH_EPISODE_DATA, JOB_SYNC_INTERFACES, JOB_DOWNLOAD_SOURCE_IMAGES,
    JOB_CREATE_TITLE_CARDS, JOB_LOAD_MEDIA_SERVERS, JOB_ADD_TRANSLATIONS,
    JOB_DOWNLOAD_SERIES_LOGOS,
]

"""
Wrap all periodically called functions to set the runnin attributes when
the job is started and finished.
"""
def _wrap_before(job_id):
    log.debug(f'Task[{job_id}] Started execution')
    BaseJobs[job_id].previous_start_time = datetime.now()
    BaseJobs[job_id].running = True

def _wrap_after(job_id):
    log.debug(f'Task[{job_id}] Finished execution')
    BaseJobs[job_id].previous_end_time = datetime.now()
    BaseJobs[job_id].running = False

def wrapped_create_all_title_cards():
    _wrap_before(JOB_CREATE_TITLE_CARDS)
    create_all_title_cards()
    _wrap_after(JOB_CREATE_TITLE_CARDS)

def wrapped_download_all_series_logos():
    _wrap_before(JOB_DOWNLOAD_SERIES_LOGOS)
    download_all_series_logos()
    _wrap_after(JOB_DOWNLOAD_SERIES_LOGOS)

def wrapped_download_source_images():
    _wrap_before(JOB_DOWNLOAD_SOURCE_IMAGES)
    download_all_source_images()
    _wrap_after(JOB_DOWNLOAD_SOURCE_IMAGES)

def wrapped_load_media_servers():
    _wrap_before(JOB_LOAD_MEDIA_SERVERS)
    load_all_media_servers()
    _wrap_after(JOB_LOAD_MEDIA_SERVERS)

def wrapped_refresh_all_episode_data():
    _wrap_before(JOB_REFRESH_EPISODE_DATA)
    refresh_all_episode_data()
    _wrap_after(JOB_REFRESH_EPISODE_DATA)

def wrapped_sync_all():
    _wrap_before(JOB_SYNC_INTERFACES)
    sync_all()
    _wrap_after(JOB_SYNC_INTERFACES)

def wrapped_translate_all_series():
    _wrap_before(JOB_ADD_TRANSLATIONS)
    translate_all_series()
    _wrap_after(JOB_ADD_TRANSLATIONS)

def wrapped_get_latest_version():
    _wrap_before(INTERNAL_JOB_CHECK_FOR_NEW_RELEASE)
    get_latest_version()
    _wrap_after(INTERNAL_JOB_CHECK_FOR_NEW_RELEASE)

def wrapped_refresh_all_remote_cards():
    _wrap_before(INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES)
    refresh_all_remote_card_types()
    _wrap_after(INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES)


"""
Dictionary of Job ID's to NewJob objects that contain the default Job
attributes for all major functions.
"""
BaseJobs = {
    # Public jobs
    JOB_REFRESH_EPISODE_DATA: NewJob(
        id=JOB_REFRESH_EPISODE_DATA,
        function=wrapped_refresh_all_episode_data,
        seconds=60 * 60 * 6,
        description='Look for new episodes and update all existing episodes',
    ), JOB_SYNC_INTERFACES: NewJob(
        id=JOB_SYNC_INTERFACES,
        function=wrapped_sync_all,
        seconds=60 * 60 * 6,
        description='Run all defined Syncs, adding any new Series',
    ), JOB_DOWNLOAD_SOURCE_IMAGES: NewJob(
        id=JOB_DOWNLOAD_SOURCE_IMAGES,
        function=wrapped_download_source_images,
        seconds=60 * 60 * 4,
        description='Download source images for Title Cards',
    ), JOB_CREATE_TITLE_CARDS: NewJob(
        id=JOB_CREATE_TITLE_CARDS,
        function=wrapped_create_all_title_cards,
        seconds=60 * 60 * 6,
        description='Create all missing or updated Title Cards',
    ), JOB_LOAD_MEDIA_SERVERS: NewJob(
        id=JOB_LOAD_MEDIA_SERVERS,
        function=wrapped_load_media_servers,
        seconds=60 * 60 * 4,
        description='Load all Title Cards into Emby, Jellyfin, or Plex',
    ), JOB_ADD_TRANSLATIONS: NewJob(
        id=JOB_ADD_TRANSLATIONS,
        function=wrapped_translate_all_series,
        seconds=60 * 60 * 4,
        description='Search for and add all missing Episode translations',
    ), JOB_DOWNLOAD_SERIES_LOGOS: NewJob(
        id=JOB_DOWNLOAD_SERIES_LOGOS,
        function=wrapped_download_all_series_logos,
        seconds=60 * 60 * 24,
        description='Download Logos for all Series',
    ),
    # Internal (private) jobs
    INTERNAL_JOB_CHECK_FOR_NEW_RELEASE: NewJob(
        id=INTERNAL_JOB_CHECK_FOR_NEW_RELEASE,
        function=wrapped_get_latest_version,
        seconds=60 * 60 * 12,
        description='Check for a new release of TitleCardMaker',
        internal=True,
    ), INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES: NewJob(
        id=INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES,
        function=wrapped_refresh_all_remote_cards,
        seconds=60 * 60 * 24,
        description='Refresh all RemoteCardType files',
        internal=True,
    ),
}


# Initialize scheduler with starting jobs
def initialize_scheduler() -> None:
    scheduler = get_scheduler()
    for job in BaseJobs.values():
        # If Job is not already scheduled, add
        if scheduler.get_job(job.id) is None:
        # if True:
            scheduler.add_job(
                job.function,
                'interval',
                seconds=job.seconds,
                id=job.id,
                replace_existing=True,
            )
initialize_scheduler()


def _scheduled_task_from_job(job: 'apscheduler.jobs.Job') -> ScheduledTask:
    """
    Create a ScheduledTask object for the given apscheduler.job.

    Args:
        job: APScheduler Job object to create a ScheduledTask of.

    Returns:
        ScheduledTask describing the given Job.
    """

    base_job = BaseJobs.get(job.id)
    previous_duration = None
    if (base_job.previous_start_time is not None
        and base_job.previous_end_time is not None):
        previous_duration = \
            base_job.previous_end_time - base_job.previous_start_time

    return ScheduledTask(
        id=str(job.id),
        frequency=job.trigger.interval.total_seconds(),
        next_run=str(job.next_run_time),
        description=base_job.description,
        previous_duration=previous_duration,
        running=base_job.running,
    )


@schedule_router.get('/scheduled', status_code=200)
def get_scheduled_tasks(
        show_internal: bool = Query(default=False),
        scheduler = Depends(get_scheduler)) -> list[ScheduledTask]:
    """
    Get scheduling details for all defined Tasks.

    - show_internal: Whether to show internal tasks.
    """

    return [
        _scheduled_task_from_job(job)
        for job in scheduler.get_jobs()
        if job.id in BaseJobs and (show_internal or not BaseJobs[job.id].internal)
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


@schedule_router.post('/{task_id}', status_code=200)
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

    return _scheduled_task_from_job(scheduler.get_job(task_id))