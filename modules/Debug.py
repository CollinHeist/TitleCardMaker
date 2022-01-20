CYAN = '\033[96m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[00m'

def info(text: str, level: int=0) -> None:
    """
    Output some text as information.
    
    :param      text:  The text to log at info level.
    """

    indent = '  ' * level
    print(f'{indent}{CYAN}[INFO] {text}{RESET}')


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