from datetime import datetime
from functools import wraps
from logging import Logger
from typing import Callable, Literal, Optional

from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from app.database.session import backup_data
from app.dependencies import get_preferences, get_scheduler
from app.internal.auth import get_current_user
from app.internal.availability import get_latest_version
from app.internal.cards import (
    create_all_title_cards, refresh_all_remote_card_types, clean_database,
)
from app.internal.series import (
    download_all_series_posters, load_all_media_servers, set_all_series_ids
)
from app.internal.sources import download_all_series_logos
from app.internal.snapshot import snapshot_database
from app.internal.sync import sync_all
from app.models.preferences import Preferences
from app.schemas.schedule import (
    Days, Hours, Minutes, NewJob, ScheduledTask, UpdateSchedule
)

from modules.Debug import contextualize, log, tz


# Do not allow tasks to be scheduled faster than this interval
MINIMUM_TASK_INTERVAL = Minutes(10)


# Create sub router for all /schedule API requests
schedule_router = APIRouter(
    prefix='/schedule',
    tags=['Scheduler'],
    dependencies=[Depends(get_current_user)],
)

# Job ID's for scheduled tasks
JOB_CREATE_TITLE_CARDS = 'CreateTitleCards'
JOB_DOWNLOAD_SERIES_LOGOS = 'DownloadSeriesLogos'
JOB_DOWNLOAD_SERIES_POSTERS = 'DownloadSeriesPosters'
JOB_LOAD_MEDIA_SERVERS = 'LoadMediaServers'
JOB_SYNC_INTERFACES = 'SyncInterfaces'
JOB_BACKUP_DATABASE = 'BackupDatabase'
# Internal Job ID's
INTERNAL_JOB_CHECK_FOR_NEW_RELEASE = 'CheckForNewRelease'
INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES = 'RefreshRemoteCardTypes'
INTERNAL_JOB_SET_SERIES_IDS = 'SetSeriesIDs'
INTERNAL_JOB_CLEAN_DATABASE = 'CleanDatabase'
INTERNAL_JOB_SNAPSHOT_DATABASE = 'SnapshotDatabase'

TaskID = Literal[
    JOB_SYNC_INTERFACES, JOB_CREATE_TITLE_CARDS, JOB_LOAD_MEDIA_SERVERS,
    JOB_DOWNLOAD_SERIES_LOGOS, JOB_DOWNLOAD_SERIES_POSTERS, JOB_BACKUP_DATABASE,
    # Internal jobs
    INTERNAL_JOB_CHECK_FOR_NEW_RELEASE, INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES,
    INTERNAL_JOB_SET_SERIES_IDS, INTERNAL_JOB_CLEAN_DATABASE,
    INTERNAL_JOB_SNAPSHOT_DATABASE
]

"""
Wrap all periodically called functions to set the runnin attributes when
the job is started and finished.
"""
# pylint: disable=missing-function-docstring,redefined-outer-name
def wrap_scheduled_function(job_id: str) -> Callable[[Optional[Logger]], None]:
    def decorator(func: Callable[[Optional[Logger]], None]) -> Callable[[Optional[Logger]], None]:
        @wraps(func)
        def wrapper(log: Optional[Optional[Logger]] = None) -> None:
            log = log or contextualize()
            log.info(f'Task[{job_id}] Started Execution')
            if BaseJobs[job_id].running:
                log.info(f'Task[{job_id}] Finished execution - Task is already running')
                return None

            BaseJobs[job_id].previous_start_time = datetime.now()
            BaseJobs[job_id].running = True

            func(log=log)

            log.info(f'Task[{job_id}] Finished execution')
            BaseJobs[job_id].previous_end_time = datetime.now()
            BaseJobs[job_id].running = False
        return wrapper
    return decorator

@wrap_scheduled_function(JOB_CREATE_TITLE_CARDS)
def wrapped_create_all_title_cards(log: Optional[Logger] = None) -> None:
    create_all_title_cards(log=log)

@wrap_scheduled_function(JOB_DOWNLOAD_SERIES_LOGOS)
def wrapped_download_all_series_logos(log: Optional[Logger] = None) -> None:
    download_all_series_logos(log=log)

@wrap_scheduled_function(JOB_DOWNLOAD_SERIES_POSTERS)
def wrapped_download_all_series_posters(log: Optional[Logger] = None) -> None:
    download_all_series_posters(log=log)

@wrap_scheduled_function(JOB_LOAD_MEDIA_SERVERS)
def wrapped_load_media_servers(log: Optional[Logger] = None) -> None:
    load_all_media_servers(log=log)

@wrap_scheduled_function(JOB_SYNC_INTERFACES)
def wrapped_sync_all(log: Optional[Logger] = None) -> None:
    sync_all(log=log)

@wrap_scheduled_function(INTERNAL_JOB_CHECK_FOR_NEW_RELEASE)
def wrapped_get_latest_version(log: Optional[Logger] = None) -> None:
    get_latest_version(log=log)

@wrap_scheduled_function(INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES)
def wrapped_refresh_all_remote_cards(log: Optional[Logger] = None) -> None:
    refresh_all_remote_card_types(log=log)

@wrap_scheduled_function(INTERNAL_JOB_SET_SERIES_IDS)
def wrapped_set_series_ids(log: Optional[Logger] = None) -> None:
    set_all_series_ids(log=log)

@wrap_scheduled_function(JOB_BACKUP_DATABASE)
def wrapped_backup_database(log: Optional[Logger] = None) -> None:
    backup_data(log=log)

@wrap_scheduled_function(INTERNAL_JOB_CLEAN_DATABASE)
def wrapped_clean_database(log: Optional[Logger] = None) -> None:
    clean_database(log=log)

def wrapped_snapshot_database(log: Optional[Logger] = None):
    log = log or contextualize()
    BaseJobs[INTERNAL_JOB_SNAPSHOT_DATABASE].previous_start_time =datetime.now()
    BaseJobs[INTERNAL_JOB_SNAPSHOT_DATABASE].running = True
    snapshot_database(log=log)
    BaseJobs[INTERNAL_JOB_SNAPSHOT_DATABASE].previous_end_time = datetime.now()
    BaseJobs[INTERNAL_JOB_SNAPSHOT_DATABASE].running = False
# pylint: enable=missing-function-docstring,redefined-outer-name

"""
Dictionary of Job ID's to NewJob objects that contain the default Job
attributes for all major functions.
"""
BaseJobs = {
    # Public jobs
    JOB_SYNC_INTERFACES: NewJob(
        id=JOB_SYNC_INTERFACES,
        function=wrapped_sync_all,
        seconds=Hours(6),
        crontab='0 */6 * * *',
        description='Run all defined Syncs, adding any new Series',
    ),
    JOB_CREATE_TITLE_CARDS: NewJob(
        id=JOB_CREATE_TITLE_CARDS,
        function=wrapped_create_all_title_cards,
        seconds=Hours(12),
        crontab='0 */12 * * *',
        description='Create all missing or outdated Title Cards',
    ),
    JOB_LOAD_MEDIA_SERVERS: NewJob(
        id=JOB_LOAD_MEDIA_SERVERS,
        function=wrapped_load_media_servers,
        seconds=Hours(4),
        crontab='0 */4 * * *',
        description='Load all Title Cards into Emby, Jellyfin, or Plex',
    ),
    JOB_DOWNLOAD_SERIES_LOGOS: NewJob(
        id=JOB_DOWNLOAD_SERIES_LOGOS,
        function=wrapped_download_all_series_logos,
        seconds=Days(1),
        crontab='0 0 */1 * *',
        description='Download Logos for all Series',
    ),
    JOB_DOWNLOAD_SERIES_POSTERS: NewJob(
        id=JOB_DOWNLOAD_SERIES_POSTERS,
        function=wrapped_download_all_series_posters,
        seconds=Days(1),
        crontab='0 0 */1 * *',
        description='Download Posters for all Series',
    ),
    JOB_BACKUP_DATABASE: NewJob(
        id=JOB_BACKUP_DATABASE,
        function=wrapped_backup_database,
        seconds=Days(1),
        crontab='0 0 */1 * *',
        description='Backup the database and global settings',
    ),
    # Internal (private) jobs
    INTERNAL_JOB_CHECK_FOR_NEW_RELEASE: NewJob(
        id=INTERNAL_JOB_CHECK_FOR_NEW_RELEASE,
        function=wrapped_get_latest_version,
        seconds=Days(1),
        crontab='0 0 */1 * *',
        description='Check for a new release',
        internal=True,
    ),
    INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES: NewJob(
        id=INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES,
        function=wrapped_refresh_all_remote_cards,
        seconds=Days(1),
        crontab='0 0 */1 * *',
        description='Refresh all non-built-in card types',
        internal=True,
    ),
    INTERNAL_JOB_SET_SERIES_IDS: NewJob(
        id=INTERNAL_JOB_SET_SERIES_IDS,
        function=wrapped_set_series_ids,
        seconds=Days(2),
        crontab='0 0 */2 * *',
        description='Set Series IDs',
        internal=True,
    ),
    INTERNAL_JOB_CLEAN_DATABASE: NewJob(
        id=INTERNAL_JOB_CLEAN_DATABASE,
        function=wrapped_clean_database,
        seconds=Days(2) + Hours(12),
        crontab='0 */3 * * *',
        description='Clean the database',
        internal=True,
    ),
    INTERNAL_JOB_SNAPSHOT_DATABASE: NewJob(
        id=INTERNAL_JOB_SNAPSHOT_DATABASE,
        function=wrapped_snapshot_database,
        seconds=Minutes(30),
        crontab='*/30 * * * *',
        description='Take a snapshot of the database',
        internal=True,
    ),
}


# Initialize scheduler with starting jobs
def initialize_scheduler(override: bool = False) -> None:
    """
    Initialize the Scheduler by creating any Jobs in BaseJobs that do
    not already exist.
    """

    scheduler: BackgroundScheduler = get_scheduler()
    preferences: Preferences = get_preferences()

    # Schedule all defined Jobs
    changed = False
    for job in BaseJobs.values():
        # If Job is not already scheduled, add
        if override or scheduler.get_job(job.id) is None:
            if preferences.advanced_scheduling:
                changed = True
                # Store crontab in Preferences
                preferences.task_crontabs[job.id] = job.crontab
                scheduler.add_job(
                    job.function,
                    CronTrigger.from_crontab(job.crontab),
                    id=job.id,
                    replace_existing=True,
                    misfire_grace_time=60 * 10,
                )
            else:
                scheduler.add_job(
                    job.function,
                    'interval',
                    seconds=job.seconds,
                    id=job.id,
                    replace_existing=True,
                    misfire_grace_time=60 * 10,
                )

    if changed:
        preferences.commit()


def _scheduled_task_from_job(job: Job,) -> ScheduledTask:
    """
    Create a ScheduledTask object for the given apscheduler.job.

    Args:
        job: APScheduler Job object to create a ScheduledTask of.

    Returns:
        ScheduledTask describing the given Job.
    """

    # Calculate previous Task duration if possible
    base_job = BaseJobs.get(job.id)
    previous_duration = None
    if (base_job.previous_start_time is not None
        and base_job.previous_end_time is not None):
        previous_duration = \
            base_job.previous_end_time - base_job.previous_start_time

    # Get the frequency string or crontab
    frequency, crontab = None, None
    if (preferences := get_preferences()).advanced_scheduling:
        crontab = preferences.task_crontabs.get(job.id, base_job.crontab)
    else:
        try:
            frequency = job.trigger.interval.total_seconds()
        except AttributeError:
            # Using basic scheduling, but job was created in advanced mode
            crontab = preferences.task_crontabs.get(job.id, base_job.crontab)

    return ScheduledTask(
        id=str(job.id),
        frequency=frequency,
        crontab=crontab,
        next_run=str(job.next_run_time),
        description=base_job.description,
        previous_duration=previous_duration,
        running=base_job.running,
    )


@schedule_router.post('/type/toggle', status_code=201)
def toggle_schedule_type(
        request: Request,
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Toggle the global scheduling between basic and advanced. Basic
    scheduling mode using standard intervals, while advanced scheduling
    uses Cron schedule expressions.
    """

    # Get contextual logger
    log = request.state.log

    # Toggle scheduling method
    if preferences.advanced_scheduling:
        log.info('Disabling advanced Task scheduling')
    else:
        log.info('Enabling advanced Task scheduling')
    preferences.advanced_scheduling = not preferences.advanced_scheduling
    preferences.commit()

    # Reset Scheduler
    initialize_scheduler(override=True)


@schedule_router.get('/scheduled', status_code=200)
def get_scheduled_tasks(
        show_internal: bool = Query(default=False),
        preferences: Preferences = Depends(get_preferences),
        scheduler: BackgroundScheduler = Depends(get_scheduler),
    ) -> list[ScheduledTask]:
    """
    Get scheduling details for all defined Tasks.

    - show_internal: Whether to show internal tasks.
    """

    show_internal |= preferences.advanced_scheduling

    return [
        _scheduled_task_from_job(job)
        for job in scheduler.get_jobs()
        if job.id in BaseJobs and (show_internal or not BaseJobs[job.id].internal)
    ]


@schedule_router.get('/{task_id}', status_code=200)
def get_scheduled_task(
        task_id: TaskID,
        scheduler: BackgroundScheduler = Depends(get_scheduler),
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


@schedule_router.put('/update/{task_id}', status_code=200)
def reschedule_task(
        request: Request,
        task_id: TaskID,
        update_schedule: UpdateSchedule = Body(...),
        preferences: Preferences = Depends(get_preferences),
        scheduler: BackgroundScheduler = Depends(get_scheduler),
    ) -> ScheduledTask:
    """
    Reschedule the given Task with a new interval.

    - task_id: ID of the Task being rescheduled.
    - update_schedule: New interval/schedule to reschedule this Task.
    """

    # Get contextual logger
    log = request.state.log # pylint: disable=redefined-outer-name

    # Verify job exists, raise 404 if DNE
    if (job := scheduler.get_job(task_id)) is None:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    # Advanced scheduling
    if preferences.advanced_scheduling:
        # Interval unchanged skip
        if update_schedule.crontab == BaseJobs.get(task_id).crontab:
            log.debug(f'Task[{job.id}] Not rescheduling, interval unchanged')
            return _scheduled_task_from_job(job)

        # Verify schedule is valid
        try:
            new_trigger = CronTrigger.from_crontab(update_schedule.crontab)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=f'Invalid Cron schedule',
            ) from exc

        # Reschedule with modified interval
        log.debug(f'Task[{job.id}] rescheduling to "{update_schedule.crontab}"')
        BaseJobs[task_id].crontab = update_schedule.crontab
        job = scheduler.reschedule_job(task_id, trigger=new_trigger)

        # Write are updated crontab to preferences, commit
        preferences.task_crontabs[task_id] = update_schedule.crontab
        preferences.commit()
    # Basic scheduling
    else:
        # If new interval is the same as old interval, skip
        new_interval = (
            update_schedule.seconds
            + (update_schedule.minutes * 60)
            + (update_schedule.hours * 60 * 60)
            + (update_schedule.days * 60 * 60 * 24)
            + (update_schedule.weeks * 60 * 60 * 24 * 7)
        )
        if new_interval == job.trigger.interval.total_seconds():
            log.debug(f'Task[{job.id}] Not rescheduling, interval unchanged')
            return _scheduled_task_from_job(job)

        # Ensure interval is not below minimum
        if new_interval < MINIMUM_TASK_INTERVAL:
            log.warning(f'Task[{job.id}] Cannot schedule Task more frequently '
                        f'than 10 minutes')
            update_schedule.minutes = 10

        # Reschedule with modified interval
        update_dict = update_schedule.dict()
        update_dict.pop('crontab', None) # Remove crontab arg
        log.debug(f'Task[{job.id}] rescheduled via {update_dict}')
        job = scheduler.reschedule_job(
            task_id,
            trigger='interval',
            **update_dict,
        )

    return _scheduled_task_from_job(job)


@schedule_router.post('/{task_id}', status_code=200)
def run_task(
        request: Request,
        task_id: TaskID,
        scheduler: BackgroundScheduler = Depends(get_scheduler),
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
