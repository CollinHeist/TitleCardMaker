from abc import ABC, abstractmethod

from yaml import safe_load

from modules.Debug import log
from modules.RemoteCardType import RemoteCardType
from modules.TitleCard import TitleCard

class YamlReader:
    """This class describes an object capable of reading and parsing YAML."""
    
    
    def __init__(self, yaml: dict={}, *,
                 log_function: callable=log.error) -> None:
        """
        Initialize this object.

        Args:
            yaml: Base YAML to read.
            log_function: Function to call and log with for any YAML read
                failures. Defaults to log.error.
        """
        
        self._base_yaml = yaml
        self.valid = True
        self.__log = log_function


    def _get(self, *attributes, type_: type=None, default=None):
        """
        Get the value specified by the given attributes/sub-attributes of YAML,
        optionally converting to the given type. Log invalidity and return None
        if value is either unspecified or cannot be converted to the type.
        
        :param      attributes: Any number of nested attributes to get value of.
        :param      type_:      Optional callable (i.e.) type to call on
                                specified value before returning
        :param      default:    Default value to return if unspecified.
        
        :returns:   Value located at the given attribute specification, None
                    if DNE or cannot be typed.
        """

        # If the value is specified
        if self._is_specified(*attributes):
            value = self._base_yaml
            for attrib in attributes:
                value = value[attrib]

            # If no type conversion is indicated, just return value
            if type_ is None:
                return value

            try:
                # Attempt type conversion
                return type_(value)
            except Exception:
                # Type conversion failed, log, set invalid, return None
                attrib_string = '", "'.join(attributes)
                self.__log(f'Value of "{attrib_string}" is invalid')
                self.valid = False
                
                return default
        else:
            # No value specified, return None
            return default


    def _is_specified(self, *attributes) -> bool:
        """
        Determines whether the given attribute/sub-attribute has been manually 
        specified in the show's YAML.
        
        :param      attributes: Any number of attributes to check for. Each
                                subsequent argument is checked for as a sub-
                                attribute of the prior one.
        
        :returns:   True if ALL attributes are specified, False otherwise.
        """

        # Start on the top-level YAML
        current = self._base_yaml

        for attribute in attributes:
            # If this level isn't even a dictionary or the attribute DNE - False
            if not isinstance(current, dict) or attribute not in current:
                return False

            # If this level has sub-attributes, but is blank (None) - False
            if current[attribute] is None:
                return False

            # Move to the next level
            current = current[attribute]

        # All given attributes have been checked without exit, must be specified
        return True


    def _parse_card_type(self, card_type: str) -> None:
        """
        Read the card_type specification for this object. This first looks at
        the locally implemented types in the TitleCard class, then attempts to
        create a RemoteCardType from the specification. This can be either a
        local file to inject, or a GitHub-hosted remote file to download and
        inject. This updates the card_type, valid, and episode_text_format
        attributes of this object.
        
        :param      card_type:  The value of card_type to read/parse.
        """

        # If known card type, set right away, otherwise check remote repo
        if card_type in TitleCard.CARD_TYPES:
            self.card_class = TitleCard.CARD_TYPES[card_type]
        elif (remote_card_type := RemoteCardType(card_type)).valid:
            self.card_class = remote_card_type.card_class
        else:
            log.error(f'Invalid card type "{card_type}"')
            self.valid = False


    @staticmethod
    def _read_file(file: 'Path', *, critical: bool=False) -> dict:
        """
        Read the given file and return the contained YAML.

        Args:
            file: Path to the file to read.
            critical: Whether YAML read errors should result in a critical
                error and exit.
        
        Returns:
            Empty dictionary if the file DNE, otherwise the content of the file.
        """

        # If file does not exist, return blank dictionary
        if not file.exists():
            return {}

        # Open file and return contents
        with file.open('r', encoding='utf-8') as file_handle:
            try:
                return safe_load(file_handle)
            except Exception as e:
                # Log error, if critical then exit with error code
                if critical:
                    log.critical(f'Error reading "{file.resolve()}":\n{e}\n')
                    exit(1)
                else:
                    log.error(f'Error reading "{file.resolve()}":\n{e}\n')

        return {}
        