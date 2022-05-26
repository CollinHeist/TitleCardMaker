import sys
from importlib.util import spec_from_file_location, module_from_spec

from pathlib import Path
from requests import get

from modules.Debug import log

class RemoteCardType:
    """
    This class defines a remote CardType. This is an encapsulation of a CardType
    class that, rather than being defined locally, queries the Maker GitHub for
    Python classes to dynamically inject in the modules namespace. These 
    """

    """Base URL for all remote Card Type files to download"""
    URL_BASE = ('https://raw.githubusercontent.com/CollinHeist/'
                'TitleCardMaker-CardTypes/master')

    """Temporary directory all card types are written to"""
    TEMP_DIR = Path(__file__).parent / '.objects'

    __slots__ = ('card_class', 'valid')


    def __init__(self, remote: str) -> None:
        """
        Construct a new RemoteCardType. This downloads the source file at the
        specified location and loads it as a class in the global modules, under
        the interpreted class name.
        
        :param      remote: URL to remote card to inject. Should omit repo base.
                            Should be specified like {username}/{class_name}.
        """

        # Make GET request for the contents of the specified value
        url = f'{self.URL_BASE}/{remote}.py'
        if (response := get(url)).status_code >= 400:
            log.error(f'Cannot identify remote Card Type "{remote}"')
            self.valid = False
            return None

        # Succesful request (i.e. file remotely exists)
        # Get username and class name from the git specification
        username = remote.split('/')[0]
        class_name = remote.split('/')[-1]  

        # Download and write the CardType class into a temporary file
        file_name = self.TEMP_DIR / f'{username}-{class_name}.py'
        file_name.parent.mkdir(parents=True, exist_ok=True)

        # Download file, import as module
        try:
            # Write remote file contents to temporary class
            with (file_name).open('wb') as fh:
                fh.write(response.content)
            log.debug(f'Wrote {class_name}.py to {file_name.resolve()}')

            # Create module for newly loaded file
            spec = spec_from_file_location(class_name, file_name)
            module = module_from_spec(spec)
            sys.modules[class_name] = module
            spec.loader.exec_module(module)

            # Get class from module namespace
            self.card_class = module.__dict__[class_name]
            log.info(f'Loaded Remote Card Type "{remote}"')
            self.valid = True
        except Exception as e:
            # Some error in loading, set object as invalid
            log.error(f'Cannot load Remote Card Type "{remote}", returned "{e}"')
            self.card_class = None
            self.valid = False

