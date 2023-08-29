from logging import Logger
import sys
from importlib.util import spec_from_file_location, module_from_spec

from pathlib import Path
from requests import get

from modules.CleanPath import CleanPath
from modules.Debug import log
from modules.RemoteFile import RemoteFile

class RemoteCardType:
    """
    This class defines a remote CardType. This is an encapsulation of a
    CardType class that, rather than being defined locally, queries the
    Maker GitHub for Python classes to dynamically inject in the modules
    namespace.
    """

    """Base URL for all remote Card Type files to download"""
    URL_BASE = (
        'https://raw.githubusercontent.com/CollinHeist/'
        'TitleCardMaker-CardTypes/web-ui'
    )

    """Temporary directory all card types are written to"""
    TEMP_DIR = Path(__file__).parent / '.objects'

    __slots__ = ('card_class', 'valid')


    def __init__(self,
            remote: str,
            *,
            log: Logger = log,
        ) -> None:
        """
        Construct a new RemoteCardType. This downloads the source file
        at the specified location and loads it as a class in the global
        modules, under the interpreted class name. If the given remote
        specification is a file that exists, that file is loaded.

        Args:
            remote: URL to remote card to inject. Should omit repo base.
                Should be specified like `{username}/{class_name}`. Can
                also be a local filepath.
            log: (Keyword) Logger for all log messages.
        """

        # Get database of loaded assets/cards
        self.valid = True

        # If local file has been specified..
        if (file := CleanPath(remote).sanitize()).exists():
            # Get class name from file
            class_name = file.stem
            file_name = str(file.resolve())
        else:
            # Get username and class name from the remote specification
            username = remote.split('/')[0]
            class_name = remote.split('/')[-1]

            # Download and write the CardType class into a temporary file
            file_name = self.TEMP_DIR / f'{username}-{class_name}.py'
            url = f'{self.URL_BASE}/{remote}.py'

            # Make GET request for the contents of the specified value
            if (response := get(url, timeout=30)).status_code >= 400:
                log.error(f'Cannot identify remote Card Type "{remote}"')
                self.valid = False
                return None

            # Write remote file contents to temporary class file
            file_name.parent.mkdir(parents=True, exist_ok=True)
            with (file_name).open('wb') as fh:
                fh.write(response.content)

        # Import new file as module
        try:
            # Create module for newly loaded file
            spec = spec_from_file_location(class_name, file_name)
            module = module_from_spec(spec)
            sys.modules[class_name] = module
            spec.loader.exec_module(module)

            # Get class from module namespace
            self.card_class = module.__dict__[class_name]

            # Validate that each RemoteFile of this class loaded correctly
            for attribute_name in dir(self.card_class):
                attribute = getattr(self.card_class, attribute_name)
                if isinstance(attribute, RemoteFile):
                    self.valid &= attribute.valid

            # Add this url to the loaded database
            log.debug(f'Loaded RemoteCardType "{remote}"')
        except Exception as e:
            # Some error in loading, set object as invalid
            log.exception(f'Cannot load CardType "{remote}"', e)
            self.card_class = None
            self.valid = False

        return None
