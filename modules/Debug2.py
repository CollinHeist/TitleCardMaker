from os import environ
from json import dumps
from pathlib import Path
import sys
from typing import TYPE_CHECKING

from better_exceptions import format_exception
from loguru import logger

if TYPE_CHECKING:
    from loguru import Record


"""Format for all datetime objects written to log files"""
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f %Z'

"""Base log file"""
LOG_FILE = Path(__file__).parent.parent / 'config' / 'logs' / 'log.jsonl'
if environ.get('TCM_IS_DOCKER', 'false').lower() == 'true':
    LOG_FILE = Path('/config/logs/log.jsonl')
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

"""
Logging filters and formatters
"""
SECRETS = set()
def redact_secrets(message: str) -> str:
    """Redact all secrets from the given message"""

    for secret in SECRETS:
        message = message.replace(secret, '********')

    return message


def secret_formatter(record: 'Record') -> str:
    """Formatter which also redacts secrets"""

    record['extra']['redacted_message'] = redact_secrets(record['message'])

    return (
        '[{time:YYYY-MM-DD at HH:mm:ss Z}] [{level}] [{extra[context_id]}] '
        '{extra[redacted_message]}'
    )


def reduced_serializer(record: 'Record') -> str:
    """Formatter which serializes a subset of the record"""

    exc = None
    if (record['exception']) is not None:
        exc = {
            'type': str(record['exception'].type),
            'value': str(record['exception'].value),
            'traceback': format_exception(*record['exception']),
        }

    record['extra']['serialized'] = dumps({
        'message': redact_secrets(record['message']),
        'context_id': record['extra'].get('context_id', None),
        'level': getattr(record.get('level', {}), 'name', 'UNSET'),
        # 'YYYY-MM-DD HH:mm:ss Z'),
        'time': record['time'].strftime(DATETIME_FORMAT),
        'execution': {
            'file': getattr(record.get('file', {}), 'path', None),
            'line': record.get('line', None),
        },
        'exception': exc,
    })
    return '{extra[serialized]}\n'


# Remove builtin logger to stderr
logger.remove()

logger_id = None
def set_primary_logger(level: str = 'INFO') -> int:
    if logger_id is not None:
        logger.remove(logger_id)
    handler_id = logger.add(
        sys.stdout,
        level=environ.get('TCM_LOG', level),
        # See https://github.com/Delgan/loguru/issues/150
        format='<level>[<bold>{level}</bold>] {message}</level>',
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )
    logger.level('DEBUG', color='<dim><white>')
    logger.level('INFO', color='<light-cyan>')
    logger.level('WARNING', color='<fg 237,112,46>')
    logger.level('ERROR', color='<yellow>')
    logger.level('CRITICAL', color='<red><bold>')
    return handler_id
logger_id = set_primary_logger()

logger.add(
    LOG_FILE,
    # Debug level for log file
    level='DEBUG',
    # Format messages
    format=reduced_serializer,
    # Rotate every 12 hours
    rotation='12h',
    # Keep logs for two weeks
    retention='2 weeks',
    # Zip log files
    # compression='zip',
    # Better exception printing
    backtrace=True,
    diagnose=True,
    # Serialize each log entry as JSON; !this is handled by the formatter!
    # See https://loguru.readthedocs.io/en/latest/resources/recipes.html
    # serialize=True,
    # Make log calls non-blocking
    enqueue=True,
)
