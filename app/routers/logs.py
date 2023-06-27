from datetime import datetime
from typing import Any, Optional
from warnings import simplefilter

from re import IGNORECASE, compile as re_compile
from fastapi import APIRouter, Query
from fastapi_pagination import paginate
from fastapi_pagination.utils import FastAPIPaginationWarning

from app.database.session import Page
from app.schemas.logs import LogEntry, LogLevel

from modules.Debug import LOG_FILE

# Do not warn about SQL pagination, not used for log filtering
simplefilter('ignore', FastAPIPaginationWarning)

# Create sub router for all /logs API requests
log_router = APIRouter(
    prefix='/logs',
    tags=['Logs'],
)

"""
Regex to match logdata from a log entry.
"""
LOG_REGEX = re_compile(
    r'^\[(?P<level>[^]]+)\]\s+\[(?P<time>[^]]+)\]\s+\[(?P<context_id>[^]]+)\]\s+(?P<message>.*)$',
    IGNORECASE
)

from fastapi import Request
@log_router.get('/query', status_code=201)
def query_logs(
        level: LogLevel = Query(default='info'),
        after: Optional[datetime] = Query(default=None),
        before: Optional[datetime] = Query(default=None),
        context_id: Optional[str] = Query(default=None, min_length=1),
        contains: Optional[str] = Query(default=None, min_length=1),
    ) -> Page[LogEntry]:
    """
    Query all log entries for the given criteria.

    - level: Minimum log level. All messages of lower levels are removed.
    - after: Earliest date of logs to return. ISO 8601 format.
    - before: Latest date of logs to return. ISO 8601 format.
    - context_id: Comma separated list of contexts to filter by.
    - contains: Required substring. Case insensitive. 
    """

    # Read all associated log files from the rotated files
    logs = []
    for log_file in LOG_FILE.parent.glob(f'{LOG_FILE.name}*'):
        with log_file.open('r') as file_handle:
            logs.extend(file_handle.readlines())

    # Function to filter log results by
    level_no = {'debug': 0, 'info': 1, 'warning': 2, 'error': 3, 'critical': 4}
    contains = None if contains is  None else contains.lower()
    def meets_filters(data: dict[str, Any]) -> bool:
        # Level criteria
        if level_no[data['level']] < level_no[level]:
            return False
        
        # Context
        if context_id is not None and data['context_id'] not in context_id:
            return False
        
        # Before/After
        if ((before is not None and data['time'] > before)
            or (after is not None and data['time'] < after)):
            return False

        # Contains substring
        return contains is None or contains in data['message'].lower()

    # Convert raw logs to LogEntry objects/dicts
    log_entries, last_entry_is_valid = [], False
    for log_entry in logs:
        # Parse entry into data
        if (data_match := LOG_REGEX.match(log_entry)):
            data = data_match.groupdict()
            data['level'] = data['level'].lower()
            try:
                data['time'] = datetime.strptime(data['time'], '%m-%d-%y %H:%M:%S.%f')
            except Exception:
                continue
        # Cannot parse data, append content to last entry's message (if valid)
        else:
            if len(log_entries) > 0 and last_entry_is_valid:
                log_entries[-1]['message'] += f'\n{log_entry}'
            continue

        # Skip if doesn't meet filter criteria
        if not meets_filters(data):
            last_entry_is_valid = False
            continue

        last_entry_is_valid = True
        log_entries.append(data)

    return paginate(
        sorted(log_entries, key=lambda data: data['time'], reverse=True)
    )