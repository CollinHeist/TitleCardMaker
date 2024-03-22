from importlib.util import spec_from_file_location, module_from_spec
from logging import Logger
import sys
from typing import Literal, Optional, Union

from pathlib import Path
from requests import get

from app.schemas.base import Base
from modules.BaseCardType import BaseCardType
from modules.CleanPath import CleanPath
from modules.Debug import log
from modules.RemoteFile import RemoteFile


class RemoteCardType:
    """
    This class defines a remote (or local) CardType. This is an
    encapsulation of a CardType class that, rather than being built-in,
    either queries the Maker GitHub for Python classes to dynamically
    inject in the modules namespace, or loads an arbitrary Python file.
    """

    """Base URL for all remote Card Type files to download"""
    URL_BASE = (
        'https://raw.githubusercontent.com/CollinHeist/'
        'TitleCardMaker-CardTypes/title-rework'
    )

    """Temporary directory all card types are written to"""
    TEMP_DIR = Path(__file__).parent / '.objects'


    __slots__ = ('card_class', 'valid', 'source')


    def __init__(self,
            /,
            identifier: Union[str, Path],
            *,
            log: Logger = log,
        ) -> None:
        """
        Construct a new RemoteCardType. This downloads the source file
        at the specified location and loads it as a class in the global
        modules, under the interpreted class name. If the given
        identifier specification is a file that exists, that file is
        loaded.

        Args:
            identifier: Local filepath to the card class or the URL to
                remote card to inject. If a remote class, it must be
                specified like `{username}/{class_name}`.
            log: Logger for all log messages.
        """

        # Get database of loaded assets/cards
        self.card_class: Optional[type[BaseCardType]] = None
        self.source: Literal['local', 'remote'] = 'remote'
        self.valid = True

        # If local file has been specified, get class name from the file
        if (file := CleanPath(identifier).sanitize()).exists():
            class_name = file.stem
            file_name = str(file.resolve())
            self.source = 'local'
        else:
            # Get username and class name from the identifier specification
            username = identifier.split('/')[0]
            class_name = identifier.split('/')[-1]

            # Download and write the CardType class into a temporary file
            file_name = self.TEMP_DIR / f'{username}-{class_name}.py'
            url = f'{self.URL_BASE}/{identifier}.py'

            # Make GET request for the contents of the specified value
            if (response := get(url, timeout=30)).status_code >= 400:
                log.error(f'Cannot identify Card Type "{identifier}"')
                self.valid = False
                return None

            # Write identifier file contents to temporary class file
            self.source = 'remote'
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
            self.card_class: type[BaseCardType] = module.__dict__[class_name]

            # Validate that each RemoteFile of this class loaded correctly
            for attribute_name in dir(self.card_class):
                attribute = getattr(self.card_class, attribute_name)
                if isinstance(attribute, RemoteFile):
                    self.valid &= attribute.valid

            # Validate UI requirements
            self.__validate_ui_requirements(identifier)

            # Add this url to the loaded database
            if self.valid:
                log.debug(f'Loaded RemoteCardType "{identifier}"')
        # Error looking for module under class name - likely bad naming
        except KeyError:
            log.exception(f'Cannot load CardType "{identifier}" - cannot '
                          f'identify Card class. Ensure there is a Class of '
                          f'the same name as the file itself.')
            self.valid = False
        # Some error in loading, set object as invalid
        except Exception:
            log.exception(f'Cannot load CardType "{identifier}"')
            self.valid = False

        return None


    def __validate_ui_requirements(self, identifier: str, /) -> None:
        """
        Validate this object's Card class UI requirements and update the
        object's validity.

        Args:
            identifier: Identifier of the Card class being validated.
        """

        # Validate the API implementation details are there
        if not issubclass(self.card_class, BaseCardType):
            log.error(f'CardType "{identifier}" must be is a subclass of '
                      f'modules.BaseCardType.BaseCardType')
            self.valid = False

        if not hasattr(self.card_class, 'CardModel'):
            log.error(f'CardType "{identifier}" is missing the required '
                      f'CardModel object')
            self.valid = False

        if (hasattr(self.card_class, 'CardModel')
            and not issubclass(self.card_class.CardModel, Base)):
            log.error(f'CardType "{identifier}" CardModel is invalid - must be '
                      f'a Pydantic model')
            self.valid = False
