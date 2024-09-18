from datetime import timedelta
from functools import partial
from os import environ
from json import dumps
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import better_exceptions
from fastapi import WebSocket
from loguru import logger
from loguru._file_sink import Rotation as LoguruRotation
from loguru._string_parsers import parse_size

if TYPE_CHECKING:
    from loguru import Record


"""Format for all datetime objects written to log files"""
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f %Z'

"""Base log file"""
LOG_FILE = Path(__file__).parent.parent / 'config' / 'logs' / 'log.jsonl'
if environ.get('TCM_IS_DOCKER', 'false').lower() == 'true':
    LOG_FILE = Path('/config/logs/log.jsonl')
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

"""Websocket connections to send log messages to"""
ACTIVE_WEBSOCKETS: set[WebSocket] = set()

"""Do not limit the length of exception tracebacks"""
better_exceptions.MAX_LENGTH = None

"""
Logging filters and formatters
"""
SECRETS: set[str] = set()
def redact_secrets(message: str) -> str:
    """Redact all secrets from the given message."""

    # Redact the longest secrets first so that substrings of secrets are
    # not leaked - e.g. {'ABC', 'ABCDEF'} would redact 'ABC' and then
    # leave 'DEF' exposed
    for secret in sorted(SECRETS, key=len, reverse=True):
        message = message.replace(secret, '[REDACTED]')

    return message


def reduced_serializer(record: 'Record') -> str:
    """Formatter which serializes a subset of the record."""

    exc = None
    if record['exception'] is not None:
        # Grab the ExceptionFormatter from the logger directly, rather
        # than using the better- exceptions formatter, so that extended
        # traceback stacks are properly displayed; handler[2]
        # corresponds to the file handler
        tb = logger._core.handlers[2]._exception_formatter.format_exception(
            *record['exception']
        )
        exc = {
            'type': str(record['exception'].type),
            'value': str(record['exception'].value),
            'traceback': redact_secrets(''.join(tb)),
        }

    record['extra']['serialized'] = dumps({
        'message': record['message'],
        'context_id': record['extra'].get('context_id', None),
        'level': getattr(record.get('level', {}), 'name', 'UNSET'),
        'time': record['time'].strftime(DATETIME_FORMAT),
        'execution': {
            'file': getattr(record.get('file', {}), 'path', None),
            'line': record.get('line', None),
        },
        'exception': exc,
    })
    return '{extra[serialized]}\n'


"""
Define a custom rotation function to combine a rotation of timing (12h)
and file size (24 MB).
"""
# Loguru's implementation of a timed file rotator
# TimedRotation = LoguruRotation.RotationTime( timedelta(hours=12))
TimedRotation = LoguruRotation.RotationTime(
    partial(LoguruRotation.forward_interval, interval=timedelta(hours=12))
)
SizeRotation = partial(
    LoguruRotation.rotation_size, size_limit=parse_size('9.9 MB')
)
def rotation_policy(message: str, file: Path) -> bool:
    return SizeRotation(message, file) or TimedRotation(message, file)

"""
Send log messages over all active WebSockets for real-time logs to the
UI.
"""
async def websocket_logger(message: str) -> None:
    for connection in ACTIVE_WEBSOCKETS:
        try:
            await connection.send_text(message)
        except Exception:
            pass

handlers = [
    # WARNING: The sys.stdout print WILL NOT have secrets redacted
    dict(
        sink=sys.stdout,
        level=environ.get('TCM_LOG_STDOUT', environ.get('TCM_LOG', 'INFO')),
        format='<level>[<bold>{level}</bold>] {message}</level>',
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=True,
    ),
    dict(
        sink=LOG_FILE,
        level=environ.get('TCM_LOG_FILE', 'TRACE'),
        format=reduced_serializer,
        # Rotate every 12 hours or 24.9 MB
        rotation=rotation_policy,
        # Keep logs for two weeks
        retention=environ.get('TCM_LOG_RETENTION', '7 days'),
        # Better exception printing
        colorize=False,
        backtrace=True,
        diagnose=True,
        # Do not serialize each log entry as JSON as this is handled by the
        # formatter! See
        # https://loguru.readthedocs.io/en/latest/resources/recipes.html
        # serialize=True,
        # Make log calls non-blocking
        enqueue=True,
    ),
    # Uncomment to capture SQLAlchemy logging
    # dict(
    #     sink='sqlalchemy.engine',
    #     level='DEBUG',
    # ),
    # Asyncronous websocket handler - must be removed if executing in an
    # environment w/o an event loop
    dict(
        sink=websocket_logger,
        level='INFO',
        format='{message}',
        colorize=False,
        backtrace=False,
        enqueue=environ.get('TCM_V1', 'False') == 'False',
    ),
]
levels = [
    dict(name='TRACE', color='<dim><fg #6d6d6d>'),
    dict(name='DEBUG', color='<dim><white>'),
    dict(name='INFO', color='<light-cyan>'),
    dict(name='WARNING', color='<yellow>'),
    dict(name='ERROR', color='<fg 237,112,46>'),
    dict(name='CRITICAL', color='<red><bold>'),
]

try:
    logger.configure(handlers=handlers, levels=levels)
except ValueError:
    # Remove the async handler if executing without an event loop
    handlers.pop(-1)
    logger.configure(handlers=handlers, levels=levels)

# Automatically redact all messages
logger = logger.patch(
    lambda record: record.update(message=redact_secrets(record['message']))
)

import http.client
def httpclient_logging_patch():
    """Enable HTTPConnection debug logging to the logging framework"""

    def httpclient_log(*args):
        if len(args) == 0 or args[0] == 'header:':
            return
        if args[0] == 'send:':
            logger.debug(f'SEND : ' + ' '.join(args[1:]))
        else:
            logger.info(f'{args[0].upper()} : ' + ' '.join(args[1:]))

    # mask the print() built-in in the http.client module to use
    # logging instead
    http.client.print = httpclient_log
    # enable debugging
    http.client.HTTPConnection.debuglevel = 1
# httpclient_logging_patch()
