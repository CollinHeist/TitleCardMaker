CYAN = '\033[96m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[00m'

def info(text: str) -> None:
    """
    { function_description }
    
    :param      text:  The text
    :type       text:  str
    
    :returns:   { description_of_the_return_value }
    :rtype:     None
    """

    print(f'{CYAN}[INFO] {text}{RESET}')


def warn(text: str) -> None:
    """
    { function_description }
    
    :param      text:  The text
    :type       text:  str
    
    :returns:   { description_of_the_return_value }
    :rtype:     None
    """
    
    print(f'{YELLOW}[WARNING] {text}{RESET}')


def error(text: str) -> None:
    """
    { function_description }
    
    :param      text:  The text
    :type       text:  str
    
    :returns:   { description_of_the_return_value }
    :rtype:     None
    """
    
    print(f'{RED}[ERROR] {text}{RESET}')