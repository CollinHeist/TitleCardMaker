from logging import (
    DEBUG, INFO, WARNING, ERROR, CRITICAL,
    Logger, Formatter, LoggerAdapter, getLogger, setLoggerClass, StreamHandler
)
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from random import choices as random_choices
from string import hexdigits
from typing import Optional

from tqdm import tqdm

def generate_context_id() -> str:
    return ''.join(random_choices(hexdigits, k=12)).lower()

"""Global tqdm arguments"""
TQDM_KWARGS = {
    # Progress bar format string
    'bar_format': ('{desc:.50s} {percentage:2.0f}%|{bar}| {n_fmt}/{total_fmt} '
                   '[{elapsed}]'),
    # Progress bars should disappear when finished
    'leave': False,
}

"""Log file"""
LOG_FILE = Path(__file__).parent.parent / 'logs' / 'maker.log'
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Logger class that overrides exception calls to log message as error, and then
# traceback as debug level of the exception only
class BetterExceptionLogger(Logger):
    def exception(self, msg: object, excpt: Exception, *args, **kwargs) -> None:
        super().error(msg, *args, **kwargs)
        super().debug(excpt, exc_info=True)
setLoggerClass(BetterExceptionLogger)

# StreamHandler to integrate log messages with TQDM
class LogHandler(StreamHandler):
    def emit(self, record):
        # Write after flushing buffer to integrate with tqdm
        try:
            tqdm.write(self.format(record))
            self.flush()
        except Exception:
            self.handleError(record)

# Formatter classes to handle exceptions
class ErrorFormatterColor(Formatter):
    def formatException(self, ei) -> str:
        return f'\x1b[1;30m[TRACEBACK] {super().formatException(ei)}\x1b[0m'

class ErrorFormatterNoColor(Formatter):
    def formatException(self, ei) -> str:
        return f'[TRACEBACK] {super().formatException(ei)}'

# Formatter class containing ErrorFormatterColor objects instantiated with
# different format strings for various colors depending on the log level
class LogFormatterColor(Formatter):
    """Color codes"""
    GRAY =     '\x1b[1;30m'
    CYAN =     '\033[96m'
    YELLOW =   '\x1b[33;20m'
    RED =      '\x1b[31;20m'
    BOLD_RED = '\x1b[31;1m'
    RESET =    '\x1b[0m'

    format_layout = '[%(levelname)s] %(message)s'

    LEVEL_FORMATS = {
        DEBUG:    ErrorFormatterColor(f'{GRAY}{format_layout}{RESET}'),
        INFO:     ErrorFormatterColor(f'{CYAN}{format_layout}{RESET}'),
        WARNING:  ErrorFormatterColor(f'{YELLOW}{format_layout}{RESET}'),
        ERROR:    ErrorFormatterColor(f'{RED}{format_layout}{RESET}'),
        CRITICAL: ErrorFormatterColor(f'{BOLD_RED}{format_layout}{RESET}'),
    }

    def format(self, record):
        return self.LEVEL_FORMATS[record.levelno].format(record)

class LogFormatterNoColor(Formatter):
    FORMATTER = ErrorFormatterNoColor('[%(levelname)s] %(message)s')

    def format(self, record):
        return self.FORMATTER.format(record)

# Create global logger
log = getLogger('tcm')
log.setLevel(DEBUG)

# Add TQDM handler and color formatter to the logger
handler = LogHandler()
handler.setFormatter(LogFormatterColor())
handler.setLevel(DEBUG)
log.addHandler(handler)

# Add rotating file handler to the logger
file_handler = TimedRotatingFileHandler(
    filename=LOG_FILE, when='midnight', backupCount=14,
)
file_handler.setFormatter(ErrorFormatterNoColor(
    '[%(levelname)s] [%(asctime)s.%(msecs)03d] %(message)s',
    '%m-%d-%y %H:%M:%S'
))
file_handler.setLevel(DEBUG)
log.addHandler(file_handler)

# Contextual logger which adds some context ID to all messages written with it
class ContextLogger(LoggerAdapter):
    def process(self, msg, kwargs):
        return f'[{self.extra["context_id"]}] {msg}', kwargs

# Helper function to easily create a ContextLogger
def contextualize(
        logger: Logger = log,
        context_id: Optional[str] = None
    ) -> ContextLogger:
    """
    Create a ContextLogger.

    Args:
        logger: Base Logger to initialize the ContextLogger with.
        context_id: Context ID to utilize for logging. If not provided,
            one is generated.
    """

    context_id = generate_context_id() if context_id is None else context_id

    return ContextLogger(logger, extra={'context_id': context_id})


def apply_no_color_formatter() -> None:
    """
    Modify the global logger object by replacing the colored Handler
    with an instance of the LogFormatterNoColor Handler class. Also set
    the log level to that of the removed handler.
    """

    # Get existing handler's log level, then delete
    log_level = log.handlers[0].level
    log.removeHandler(log.handlers[0])

    # Create colorless Handler with Colorless Formatter
    handler = LogHandler()
    handler.setFormatter(LogFormatterNoColor())
    handler.setLevel(log_level)

    # Add colorless handler in place of deleted one
    log.addHandler(handler)