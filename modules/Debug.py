from datetime import datetime
from logging import Logger
from os import environ
from pathlib import Path
from random import choices as random_choices
from string import hexdigits
from typing import Optional

from pytz import timezone, UnknownTimeZoneError

from modules.Debug2 import DATETIME_FORMAT, logger as log

"""Custom Exception classes"""
# pylint: disable=missing-class-docstring,multiple-statements
class InvalidCardSettings(Exception): ...
class InvalidFormatString(InvalidCardSettings): ...
class MissingSourceImage(InvalidCardSettings): ...
# pylint: enable=missing-class-docstring,multiple-statements


__all__ = (
    'log', 'generate_context_id', 'contextualize', 'DATETIME_FORMAT',
    'IS_DOCKER', 'TQDM_KWARGS', 'InvalidCardSettings', 'InvalidFormatString',
    'MissingSourceImage',
)


"""Global tqdm arguments"""
TQDM_KWARGS = {
    # Progress bar format string
    'bar_format': ('{desc:.50s} {percentage:2.0f}%|{bar}| {n_fmt}/{total_fmt} '
                   '[{elapsed}]'),
    # Progress bars should disappear when finished
    'leave': False,
    # Progress bars can not be used if no TTY is present
    'disable': None,
}


def generate_context_id() -> str:
    """
    Generate a unique pseudo-random "unique" ID.
    
    Returns:
        6 character string of pseudo-random hexadecimal chacters.
    """

    return ''.join(random_choices(hexdigits, k=6)).lower()


def contextualize(
        logger: Logger = log,
        context_id: Optional[str] = None
    ) -> Logger:
    """
    Create a contextualized Logger.

    Args:
        logger: Base Logger to initialize the ContextLogger with.
        context_id: Context ID to utilize for logging. If not provided,
            one is generated.
    """

    return logger.bind(context_id=context_id or generate_context_id())


"""Whether this is being executed inside a Docker container"""
IS_DOCKER = environ.get('TCM_IS_DOCKER', 'false').lower() == 'true'

"""Base log file"""
LOG_FILE = Path(__file__).parent.parent / 'config' / 'logs' / 'log.jsonl'
if IS_DOCKER:
    LOG_FILE = Path('/config/logs/log.jsonl')
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


# Get local timezone
try:
    tz = datetime.now().astimezone().tzinfo
except Exception:
    tz = timezone('UTC')
if environ.get('TZ', None) is not None:
    try:
        tz = timezone(environ.get('TZ'))
    except UnknownTimeZoneError:
        print(f'Invalid timezone (TZ) environment variable')
