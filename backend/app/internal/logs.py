from datetime import datetime, timedelta
from json import JSONDecodeError, loads
from pathlib import Path
from typing import Optional, TypedDict

from app.schemas.logs import LogLevel

from modules.Debug import (
    log,
    DATETIME_FORMAT,
    DATETIME_FORMAT_NO_TZ,
    LOG_FILE
)


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
    file: Path
# pylint: enable=missing-class-docstring

"""
Caching of JSON-parsed log data so that older log files are not parsed
unnecessarily (as their contents should not change).
"""
_LOG_DATA: dict[Path, list[RawLogData]] = {}


def parse_line(line: str, file: Path) -> Optional[RawLogData]:
    """
    Parse the raw log line into a dictionary of log data.

    Args:
        line: Line to parse.
        file: File which contained the given line.

    Returns:
        Log data parsed from the given line, None if there is some error
        in the parsing.
    """

    # Decode line as JSON
    try:
        line_data = loads(line) | {'file': file}
    except JSONDecodeError:
        return None

    try:
        line_data['time'] = datetime.strptime(line_data['time'],DATETIME_FORMAT)
        return line_data
    except ValueError:
        pass

    try:
        # If there are two spaces then there is likely a TZ which cannot
        # be parsed - remove from string and try again
        if len(line_data['time'].split()) == 3:
            new_time = ' '.join(line_data['time'].split()[:-1])
            line_data['time'] = datetime.strptime(new_time,DATETIME_FORMAT_NO_TZ)
        else:
            line_data['time'] = datetime.strptime(
                line_data['time'],
                DATETIME_FORMAT_NO_TZ
            )
        return line_data
    except ValueError:
        return None


def read_log_files(
        *,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
        shallow: bool = True,
    ) -> list[RawLogData]:
    """
    Read all raw log data from all files.

    Args:
        after: Earliest date of logs to return.
        before: Latest date of logs to return.
        shallow: Whether to only do a "shallow" query, which will only
            evaluate the most recent (active) log file.
    """

    # Read all associated log files from the rotated files
    logs: list[RawLogData] = []

    # Only read the active log file
    if shallow:
        with LOG_FILE.open('r') as file_handle:
            for line in file_handle.readlines():
                if (line_data := parse_line(line, file=LOG_FILE)):
                    logs.append(line_data)

        return logs

    # Read every log file
    for log_file in LOG_FILE.parent.glob(f'{LOG_FILE.stem}*{LOG_FILE.suffix}'):
        # Skip files last modified before the minimum "after" time or
        # after the maximum "before" time minus one day since a log
        # file is cycled after at most 1 days
        log_mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
        if ((after and after > log_mod_time)
            or (before and before < log_mod_time - timedelta(days=1))):
            continue

        # Check cache for this file
        if log_file in _LOG_DATA:
            logs += _LOG_DATA[log_file]
            continue

        # File is not cached - parse directly
        file_data: list[RawLogData] = []
        with log_file.open('r') as file_handle:
            for line in file_handle.readlines():
                if (line_data := parse_line(line, file=log_file)):
                    file_data.append(line_data)

        # Add to cache IF not the active log file since the active log
        # is constantly updated
        if log_file.name != LOG_FILE.name:
            _LOG_DATA[log_file] = file_data
        logs += file_data

    return logs
