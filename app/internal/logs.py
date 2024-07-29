from datetime import datetime, timedelta
from json import JSONDecodeError, loads
from pathlib import Path
from typing import Optional, TypedDict

from app.schemas.logs import LogLevel

from modules.Debug import log, LOG_FILE # noqa: F401


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
                try:
                    logs.append(loads(line) | {'file': LOG_FILE})
                except JSONDecodeError:
                    pass
    # Read all log files
    else:
        for log_file in LOG_FILE.parent.glob(f'{LOG_FILE.stem}*{LOG_FILE.suffix}'):
            # Skip files last modified before the minimum "after" time or
            # after the maximum "before" time minus one day since a log
            # file is cycled after at most 1 days
            log_mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if ((after and after > log_mod_time)
                or (before and before < log_mod_time - timedelta(days=1))):
                continue

            # Add file contents to the list
            with log_file.open('r') as file_handle:
                for line in file_handle.readlines():
                    try:
                        logs.append(loads(line) | {'file': log_file})
                    except JSONDecodeError:
                        pass

    return logs
