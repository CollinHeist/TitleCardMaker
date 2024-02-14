from datetime import datetime
from typing import Optional, TypedDict
from warnings import simplefilter

from fastapi import APIRouter, Depends, Query
from fastapi_pagination import paginate
from fastapi_pagination.utils import FastAPIPaginationWarning
from json import loads

from app.database.session import Page
from app.internal.auth import get_current_user
from app.schemas.logs import LogEntry, LogLevel

from modules.Debug import log, DATETIME_FORMAT, LOG_FILE

# Do not warn about SQL pagination, not used for log filtering
simplefilter('ignore', FastAPIPaginationWarning)

# pylint: disable=missing-class-docstring
class ExecutionDetails(TypedDict):
    file: str
    line: int

class ExceptionDetails(TypedDict):
    type: str
    value: str
    traceback: str

class RawLogData(TypedDict):
    message: str
    context_id: str
    level: LogLevel
    time: datetime
    execution: ExecutionDetails
    exception: Optional[ExceptionDetails]
# pylint: enable=missing-class-docstring

# Create sub router for all /logs API requests
log_router = APIRouter(
    prefix='/logs',
    tags=['Logs'],
    dependencies=[Depends(get_current_user)],
)

_LEVEL_NUMBERS: dict[LogLevel, int] = {
    'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4
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

    # Read all associated log files from the rotated files
    logs: list[RawLogData] = []

    # Only read the active log file
    if shallow:
        with LOG_FILE.open('r') as file_handle:
            logs.extend(list(map(loads, file_handle.readlines())))
    # Read all log files
    else:
        for log_file in LOG_FILE.parent.glob(f'{LOG_FILE.stem}*{LOG_FILE.suffix}'):
            with log_file.open('r') as file_handle:
                logs.extend(list(map(loads, file_handle.readlines())))

    # Function to filter log results by
    contains = None if contains is None else contains.lower().split('|')
    def meets_filters(data: RawLogData) -> bool:
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
