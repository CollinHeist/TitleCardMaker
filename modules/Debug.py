CYAN = '\033[96m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[00m'
from logging import Formatter, Handler, getLogger
from logging import NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
from tqdm import tqdm

def info(text: str, level: int=0) -> None:
class LogHandler(Handler):
    def __init__(self, level=NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            tqdm.write(self.format(record))
            self.flush()
        except Exception:
            self.handleError(record)
            

class LogFormatter(Formatter):
    """
    Output some text as information.
    
    :param      text:  The text to log at info level.
    """

    indent = '  ' * level
    print(f'{indent}{CYAN}[INFO] {text}{RESET}')
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

# Create global logger
log = getLogger('TitleCardMaker')
log.setLevel(DEBUG)

# Add TQDM handler and color formatter to the logger
handler = LogHandler()
handler.setFormatter(LogFormatter())
log.addHandler(handler)

def warn(text: str, level: int=0) -> None:
    """
    Output some text as a warning.
    
    :param      text:  The text
    """
    
    indent = '  ' * level
    print(f'{indent}{YELLOW}[WARNING] {text}{RESET}')


def error(text: str, level: int=0) -> None:
    """
    Output some text as an error.
    
    :param      text:  The text
    """

    indent = '  ' * level
    print(f'{indent}{RED}[ERROR] {text}{RESET}')