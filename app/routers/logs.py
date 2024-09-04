from datetime import datetime
from logging import Logger
from typing import Optional
from warnings import simplefilter

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request
)
from fastapi.responses import FileResponse
from fastapi_pagination import paginate
from fastapi_pagination.utils import FastAPIPaginationWarning

from app.database.session import Page
from app.dependencies import get_preferences
from app.internal.auth import get_current_user
from app.internal.logs import RawLogData, read_log_files
from app.models.preferences import Preferences
from app.schemas.logs import LogEntry, LogInternalServerError, LogLevel

from modules.Debug import log, DATETIME_FORMAT, LOG_FILE
from modules.TemporaryZip import TemporaryZip # noqa: F401


# Do not warn about SQL pagination, not used for log filtering
simplefilter('ignore', FastAPIPaginationWarning)


# Create sub router for all /logs API requests
log_router = APIRouter(
    prefix='/logs',
    tags=['Logs'],
    dependencies=[Depends(get_current_user)],
)

# Map of log level names to numbers for relative comparison
_LEVEL_NUMBERS: dict[LogLevel, int] = {
    'TRACE': -1, 'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4
}


@log_router.get('/query')
def query_logs(
        level: LogLevel = Query(default='DEBUG'),
        after: Optional[datetime] = Query(default=None),
        before: Optional[datetime] = Query(default=None),
        context_id: Optional[str] = Query(default=None, min_length=1),
        contains: Optional[str] = Query(default=None, min_length=1),
        shallow: bool = Query(default=True),
    ) -> Page[LogEntry]:
    """
    Query all log entries for the given criteria.

    - level: Minimum log level. All messages of lower levels are removed.
    - after: Earliest date of logs to return. ISO 8601 format.
    - before: Latest date of logs to return. ISO 8601 format.
    - context_id: Comma separated list of contexts to filter by.
    - contains: Required substring. Case insensitive.
    - shallow: Whether to only do a "shallow" query, which will only
    evaluate the most recent (active) log file.
    """

    logs = read_log_files(after=after, before=before, shallow=shallow)

    # Function to filter log results by
    contains = None if contains is None else contains.lower().split('|')
    def meets_filters(data: RawLogData) -> bool:
        # return (
        #     _LEVEL_NUMBERS[data['level']] >= _LEVEL_NUMBERS[level]
        #     and (
        #         data['context_id'] is None
        #         or context_id is None
        #         or data['context_id'] in context_id
        #     )
        #     and (before is None or data['time'] <= before)
        #     and (after is None or data['time'] >= after)
        #     and (
        #         contains is None
        #         or any(cont in data['message'].lower() for cont in contains)
        #     )
        # )
        # Level criteria
        if _LEVEL_NUMBERS[data['level']] < _LEVEL_NUMBERS[level]:
            return False

        # Context
        if (data['context_id'] is not None and context_id is not None
            and data['context_id'] not in context_id):
            return False

        # Before/After
        if ((before is not None and data['time'] > before)
            or (after is not None and data['time'] < after)):
            return False

        # Contains substring
        return (
            contains is None
            or any(cont in data['message'].lower() for cont in contains)
        )

    # Convert raw logs to LogEntry objects/dicts
    log_entries = []
    for data in logs:
        # Parse entry into data
        if not isinstance(data['time'], datetime):
            try:
                data['time'] = datetime.strptime(data['time'], DATETIME_FORMAT)
            except ValueError:
                continue

        # Skip if doesn't meet filter criteria
        if not meets_filters(data):
            continue

        log_entries.append(data)

    return paginate(
        sorted(log_entries, key=lambda data: data['time'], reverse=True)
    )


@log_router.get('/files')
def get_log_files() -> list[str]:
    """
    Get a list of the log files. This returns the log URLs - i.e. /logs
    prefixed.
    """

    return [
        str(file).replace(str(LOG_FILE.parent.resolve()), '/logs')
        for file in LOG_FILE.parent.glob(f'{LOG_FILE.stem}*{LOG_FILE.suffix}')
    ]


@log_router.get('/files/{filename}/zip')
def get_zipped_log_file(
        background_tasks: BackgroundTasks,
        request: Request,
        filename: str,
        preferences: Preferences = Depends(get_preferences),
    ) -> FileResponse:
    """
    Zip the log file with the given name and return it's contents.

    - filename: Name of the file to zip.
    """

    log: Logger = request.state.log

    # Find associated log file, raise 404 if DNE
    if not (file := LOG_FILE.parent / filename).exists():
        raise HTTPException(
            status_code=404,
            detail='The specified log file does not exist',
        )

    # Add log file to a temporary directory
    tzip = TemporaryZip(preferences.TEMPORARY_DIRECTORY, background_tasks)
    tzip.add_file(file, 'log.jsonl', log=log)

    return FileResponse(tzip.zip(log=log))


@log_router.get('/errors')
def get_internal_server_errors(
        after: Optional[datetime] = Query(default=None),
        before: Optional[datetime] = Query(default=None),
        shallow: bool = Query(default=False),
    ) -> list[LogInternalServerError]:
    """
    Get a list of all internal server errors listed in the log files.

    - after: Earliest date of logs to return. ISO 8601 format.
    - before: Latest date of logs to return. ISO 8601 format.
    - shallow: Whether to only do a "shallow" query, which will only
    evaluate the most recent (active) log file.
    """

    def has_valid_dt(time: datetime) -> bool:
        try:
            datetime.strptime(time, DATETIME_FORMAT)
            return True
        except:
            return False

    return sorted(
        [
            LogInternalServerError(
                context_id=log['context_id'],
                time=(
                    log['time']
                    if isinstance(log['time'], datetime) else
                    datetime.strptime(log['time'], DATETIME_FORMAT)
                ),
                # message=log['message'],
                file=log['file'].name,
            )
            for log in read_log_files(after=after, before=before, shallow=shallow)
            if (
                log['message'].startswith('Internal Server Error')
                and has_valid_dt(log['time'])
            )
        ],
        key=lambda log: log.time,
        reverse=True,
    )
