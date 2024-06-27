from os import environ
from json import dumps
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import better_exceptions
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

better_exceptions.MAX_LENGTH = None

"""
Logging filters and formatters
"""
SECRETS = set()
def redact_secrets(message: str) -> str:
    """Redact all secrets from the given message"""

    for secret in SECRETS:
        message = message.replace(secret, '[REDACTED]')

    return message


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
        'message': record['message'],
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
# logger.remove()

logger.configure(
    handlers=[
        dict(
            sink=sys.stdout,
            level=environ.get('TCM_LOG', 'INFO'),
            format='<level>[<bold>{level}</bold>] {message}</level>',
            colorize=True,
            backtrace=True,
            diagnose=True,
            enqueue=True,
        ),
        dict(
            sink=LOG_FILE,
            level='TRACE',
            format=reduced_serializer,
            # Rotate every 12 hours
            rotation='12h',
            # Keep logs for two weeks
            retention='7 days',
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
        ),
        # dict(
        #     sink='sqlalchemy.engine',
        #     level='DEBUG',
        # ),
    ],
    levels=[
        dict(name='TRACE', color='<dim><fg #6d6d6d>'),
        dict(name='DEBUG', color='<dim><white>'),
        dict(name='INFO', color='<light-cyan>'),
        dict(name='WARNING', color='<yellow>'),
        dict(name='ERROR', color='<fg 237,112,46>'),
        dict(name='CRITICAL', color='<red><bold>'),
    ],
)

# Automatically redact all messages
logger = logger.patch(
    lambda record: record.update(message=redact_secrets(record['message']))
)
