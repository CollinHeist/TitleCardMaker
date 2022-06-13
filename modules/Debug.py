from logging import Formatter, getLogger, StreamHandler
from logging.handlers import TimedRotatingFileHandler
from logging import NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL

from pathlib import Path
from tqdm import tqdm

"""TQDM bar format string"""
TQDM_KWARGS = {
    'bar_format': ('{desc} {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} '
                   '[{elapsed}, {rate_fmt}{postfix}]'),
    'leave': False,
}

"""Log file"""
LOG_FILE = Path(__file__).parent.parent / 'logs' / 'maker.log'
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

class LogHandler(StreamHandler):
    """Handler subclass to integrate logging messages with TQDM"""

    def __init__(self, level=NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            tqdm.write(self.format(record))
            self.flush()
        except Exception:
            self.handleError(record)
            

class LogFormatterColor(Formatter):
    """Custom Formatter for logging integration, uses color"""

    """Color codes"""
    GRAY =     '\x1b[1;30m'
    CYAN =     '\033[96m'
    YELLOW =   '\x1b[33;20m'
    RED =      '\x1b[31;20m'
    BOLD_RED = '\x1b[31;1m'
    RESET =    '\x1b[0m'

    format_layout = '[%(levelname)s] %(message)s'

    LEVEL_FORMATS = {
        DEBUG: f'{GRAY}{format_layout}{RESET}',
        INFO: f'{CYAN}{format_layout}{RESET}',
        WARNING: f'{YELLOW}{format_layout}{RESET}',
        ERROR: f'{RED}{format_layout}{RESET}',
        CRITICAL: f'{BOLD_RED}{format_layout}{RESET}',
    }

    def format(self, record):
        format_string = self.LEVEL_FORMATS[record.levelno]
        formatter_obj = Formatter(format_string)

        return formatter_obj.format(record)


class LogFormatterNoColor(Formatter):
    """Custom Formatter for logging integration, does not use color"""

    format_layout = '[%(levelname)s] %(message)s'

    LEVEL_FORMATS = {
        DEBUG: f'{format_layout}',
        INFO: f'{format_layout}',
        WARNING: f'{format_layout}',
        ERROR: f'{format_layout}',
        CRITICAL: f'{format_layout}',
    }

    def format(self, record):
        format_string = self.LEVEL_FORMATS[record.levelno]
        formatter_obj = Formatter(format_string)

        return formatter_obj.format(record)

# Create global logger
log = getLogger('TitleCardMaker')
log.setLevel(DEBUG)

# Add TQDM handler and color formatter to the logger
handler = LogHandler()
handler.setFormatter(LogFormatterColor())
handler.setLevel(DEBUG)
log.addHandler(handler)

# Add rotating file handler to the logger
file_handler = TimedRotatingFileHandler(
    filename=LOG_FILE, when='H', interval=6, backupCount=8
)
file_handler.setFormatter(Formatter(
    '[%(levelname)s] [%(asctime)s] %(message)s',
    '%y-%m-%d %H:%M:%S'
))
file_handler.setLevel(DEBUG)
log.addHandler(file_handler)

def apply_no_color_formatter(log_object: 'Logger') -> None:
    """
    Modify the given logger object, removing the colored Handler, adding an
    instance of the colorless one.
    
    :param      log_object: The log object to modify.
    """

    # Create colorless Formatter
    handler = LogHandler()
    handler.setFormatter(LogFormatterNoColor())

    # Delete existing Handler, add new one
    log.removeHandler(log.handlers[0])
    log.addHandler(handler)