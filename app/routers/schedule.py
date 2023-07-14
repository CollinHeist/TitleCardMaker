from datetime import datetime
from logging import Logger
from typing import Literal, Optional

from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from app.database.session import backup_database
from app.dependencies import get_scheduler
from app.internal.availability import get_latest_version
from app.internal.cards import (
    create_all_title_cards, refresh_all_remote_card_types
)
from app.internal.episodes import refresh_all_episode_data
from app.internal.series import (
    download_all_series_posters, load_all_media_servers, set_all_series_ids
)
from app.internal.sources import (
    download_all_source_images, download_all_series_logos
)
from app.internal.sync import sync_all
from app.internal.translate import translate_all_series
from app.schemas.schedule import NewJob, ScheduledTask, UpdateInterval

from modules.Debug import contextualize, log


# Do not allow tasks to be scheduled faster than this interval
MINIMUM_TASK_INTERVAL = 1 * 60 * 10 # 10 minutes

# Create sub router for all /schedule API requests
schedule_router = APIRouter(
    prefix='/schedule',
    tags=['Scheduler'],
)


# Job ID's for scheduled tasks
JOB_ADD_TRANSLATIONS: str = 'AddMissingTranslations'
JOB_CREATE_TITLE_CARDS: str = 'CreateTitleCards'
JOB_DOWNLOAD_SERIES_LOGOS: str = 'DownloadSeriesLogos'
JOB_DOWNLOAD_SERIES_POSTERS: str = 'DownloadSeriesPosters'
JOB_DOWNLOAD_SOURCE_IMAGES: str = 'DownloadSourceImages'
JOB_LOAD_MEDIA_SERVERS: str = 'LoadMediaServers'
JOB_REFRESH_EPISODE_DATA: str = 'RefreshEpisodeData'
JOB_SYNC_INTERFACES: str = 'SyncInterfaces'
JOB_BACKUP_DATABASE: str = 'BackupDatabase'
# Internal Job ID's
INTERNAL_JOB_CHECK_FOR_NEW_RELEASE: str = 'CheckForNewRelease'
INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES: str = 'RefreshRemoteCardTypes'
INTERNAL_JOB_SET_SERIES_IDS: str = 'SetSeriesIDs'

TaskID = Literal[
    JOB_REFRESH_EPISODE_DATA, JOB_SYNC_INTERFACES, JOB_DOWNLOAD_SOURCE_IMAGES,  # type: ignore
    JOB_CREATE_TITLE_CARDS, JOB_LOAD_MEDIA_SERVERS, JOB_ADD_TRANSLATIONS,       # type: ignore
    JOB_DOWNLOAD_SERIES_LOGOS, JOB_DOWNLOAD_SERIES_POSTERS, JOB_BACKUP_DATABASE,# type: ignore
    # Internal jobs
    INTERNAL_JOB_CHECK_FOR_NEW_RELEASE, INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES, # type: ignore
    INTERNAL_JOB_SET_SERIES_IDS,                                                # type: ignore
]

"""
Wrap all periodically called functions to set the runnin attributes when
the job is started and finished.
"""
# pylint: disable=missing-function-docstring,redefined-outer-name
def _wrap_before(job_id, *, log: Logger = log):
    log.info(f'Task[{job_id}] Started execution')
    BaseJobs[job_id].previous_start_time = datetime.now()
    BaseJobs[job_id].running = True

def _wrap_after(job_id, *, log: Logger = log):
    log.info(f'Task[{job_id}] Finished execution')
    BaseJobs[job_id].previous_end_time = datetime.now()
    BaseJobs[job_id].running = False

def wrapped_create_all_title_cards(log: Optional[Logger] = None):
    log = contextualize() if log is None else log
    _wrap_before(JOB_CREATE_TITLE_CARDS, log=log)
    create_all_title_cards(log=log)
    _wrap_after(JOB_CREATE_TITLE_CARDS, log=log)

def wrapped_download_all_series_logos(log: Optional[Logger] = None):
    log = contextualize() if log is None else log
    _wrap_before(JOB_DOWNLOAD_SERIES_LOGOS, log=log)
    download_all_series_logos(log=log)
    _wrap_after(JOB_DOWNLOAD_SERIES_LOGOS, log=log)

def wrapped_download_all_series_posters(log: Optional[Logger] = None):
    log = contextualize() if log is None else log
    _wrap_before(JOB_DOWNLOAD_SERIES_POSTERS, log=log)
    download_all_series_posters(log=log)
    _wrap_after(JOB_DOWNLOAD_SERIES_POSTERS, log=log)

def wrapped_download_source_images(log: Optional[Logger] = None):
    log = contextualize() if log is None else log
    _wrap_before(JOB_DOWNLOAD_SOURCE_IMAGES, log=log)
    download_all_source_images(log=log)
    _wrap_after(JOB_DOWNLOAD_SOURCE_IMAGES, log=log)

def wrapped_load_media_servers(log: Optional[Logger] = None):
    log = contextualize() if log is None else log
    _wrap_before(JOB_LOAD_MEDIA_SERVERS, log=log)
    load_all_media_servers(log=log)
    _wrap_after(JOB_LOAD_MEDIA_SERVERS, log=log)

def wrapped_refresh_all_episode_data(log: Optional[Logger] = None):
    log = contextualize() if log is None else log
    _wrap_before(JOB_REFRESH_EPISODE_DATA, log=log)
    refresh_all_episode_data(log=log)
    _wrap_after(JOB_REFRESH_EPISODE_DATA, log=log)

def wrapped_sync_all(log: Optional[Logger] = None):
    log = contextualize() if log is None else log
    _wrap_before(JOB_SYNC_INTERFACES, log=log)
    sync_all(log=log)
    _wrap_after(JOB_SYNC_INTERFACES, log=log)

def wrapped_translate_all_series(log: Optional[Logger] = None):
    log = contextualize() if log is None else log
    _wrap_before(JOB_ADD_TRANSLATIONS, log=log)
    translate_all_series(log=log)
    _wrap_after(JOB_ADD_TRANSLATIONS, log=log)

def wrapped_get_latest_version(log: Optional[Logger] = None):
    log = contextualize() if log is None else log
    _wrap_before(INTERNAL_JOB_CHECK_FOR_NEW_RELEASE, log=log)
    get_latest_version(log=log)
    _wrap_after(INTERNAL_JOB_CHECK_FOR_NEW_RELEASE, log=log)

def wrapped_refresh_all_remote_cards(log: Optional[Logger] = None):
    log = contextualize() if log is None else log
    _wrap_before(INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES, log=log)
    refresh_all_remote_card_types(log=log)
    _wrap_after(INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES, log=log)

def wrapped_set_series_ids(log: Optional[Logger] = None):
    log = contextualize() if log is None else log
    _wrap_before(INTERNAL_JOB_SET_SERIES_IDS, log=log)
    set_all_series_ids(log=log)
    _wrap_after(INTERNAL_JOB_SET_SERIES_IDS, log=log)

def wrapped_backup_database(log: Optional[Logger] = None):
    log = log or contextualize()
    _wrap_before(JOB_BACKUP_DATABASE, log=log)
    backup_database(log=log)
    _wrap_after(JOB_BACKUP_DATABASE, log=log)
# pylint: enable=missing-function-docstring,redefined-outer-name

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
    ), JOB_DOWNLOAD_SERIES_POSTERS: NewJob(
        id=JOB_DOWNLOAD_SERIES_POSTERS,
        function=wrapped_download_all_series_posters,
        seconds=60 * 60 * 24,
        description='Download Posters for all Series',
    ), JOB_BACKUP_DATABASE: NewJob(
        id=JOB_BACKUP_DATABASE,
        function=wrapped_backup_database,
        seconds=60 * 60 * 24,
        description='Backup the primary database',
    ),
    # Internal (private) jobs
    INTERNAL_JOB_CHECK_FOR_NEW_RELEASE: NewJob(
        id=INTERNAL_JOB_CHECK_FOR_NEW_RELEASE,
        function=wrapped_get_latest_version,
        seconds=60 * 60 * 24,
        description='Check for a new release of TitleCardMaker',
        internal=True,
    ), INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES: NewJob(
        id=INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES,
        function=wrapped_refresh_all_remote_cards,
        seconds=60 * 60 * 24,
        description='Refresh all RemoteCardType files',
        internal=True,
    ), INTERNAL_JOB_SET_SERIES_IDS: NewJob(
        id=INTERNAL_JOB_SET_SERIES_IDS,
        function=wrapped_set_series_ids,
        seconds=60 * 60 * 24,
        description='Set Series IDs',
        internal=True,
    )
}


# Initialize scheduler with starting jobs
def initialize_scheduler() -> None:
    """
    Initialize the Scheduler by creating any Jobs in BaseJobs that do
    not already exist.
    """

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
                misfire_grace_time=60 * 10,
            )


def _scheduled_task_from_job(job: Job) -> ScheduledTask:
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
        scheduler: BackgroundScheduler = Depends(get_scheduler)
    ) -> list[ScheduledTask]:
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
        scheduler: BackgroundScheduler = Depends(get_scheduler)
    ) -> ScheduledTask:
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
        request: Request,
        task_id: TaskID,
        update_interval: UpdateInterval = Body(...),
        scheduler: BackgroundScheduler = Depends(get_scheduler)
    ) -> ScheduledTask:
    """
    Reschedule the given Task with a new interval.

    - task_id: ID of the Task being rescheduled.
    - update_interval: UpdateInterval whose total interval is used to
      reschedule the given Task.
    """

    # Get contextual logger
    log = request.state.log # pylint: disable=redefined-outer-name

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

    # Ensure interval is not below minimum
    if new_interval < MINIMUM_TASK_INTERVAL:
        log.warning(f'Task[{job.id}] Cannot schedule task more frequently than '
                    f'10 minutes')
        update_interval.minutes = 10

    # Reschedule with modified interval
    log.debug(f'Task[{job.id}] rescheduled via {update_interval.dict()}')
    job = scheduler.reschedule_job(
        task_id,
        trigger='interval',
        **update_interval.dict(),
    )

    return _scheduled_task_from_job(job)


@schedule_router.post('/{task_id}', status_code=200)
def run_task(
        task_id: TaskID,
        request: Request,
        scheduler: BackgroundScheduler = Depends(get_scheduler)
    ) -> ScheduledTask:
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
    job.function(request.state.log)

    return _scheduled_task_from_job(scheduler.get_job(task_id))
