from logging import Logger, Formatter, getLogger, setLoggerClass, StreamHandler
from logging.handlers import TimedRotatingFileHandler
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

from pathlib import Path
from tqdm import tqdm

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

"""Log file"""
LOG_FILE = Path(__file__).parent.parent / 'logs' / 'maker.log'
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


class BetterExceptionLogger(Logger):
    """
    Logger class that overrides `Logger.exception` to log as
    `Logger.error`, and then print the traceback at the debug level.
    """

    def exception(self, msg: object, excpt: Exception, *args, **kwargs) -> None:
        super().error(msg, *args, **kwargs)
        super().debug(excpt, exc_info=True)
setLoggerClass(BetterExceptionLogger)


class LogHandler(StreamHandler):
    """Handler to integrate log messages with tqdm."""

    def emit(self, record):
        # Write after flushing buffer to integrate with tqdm
        try:
            tqdm.write(self.format(record))
            self.flush()
        except Exception:
            self.handleError(record)


# Formatter classes to handle exceptions
class ErrorFormatterColor(Formatter):
    """
    Formatter class to handle exception traceback printing with color.
    """

    def formatException(self, ei) -> str:
        return f'\x1b[1;30m[TRACEBACK] {super().formatException(ei)}\x1b[0m'


class ErrorFormatterNoColor(Formatter):
    """
    Formatter class to handle exception traceback printing without
    color.
    """

    def formatException(self, ei) -> str:
        return f'[TRACEBACK] {super().formatException(ei)}'


class LogFormatterColor(Formatter):
    """
    Formatter containing ErrorFormatterColor objects instantiated with
    different format strings for various colors depending on the log
    level.
    """

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
    """Colorless version of the `LogFormatterColor` class."""

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
