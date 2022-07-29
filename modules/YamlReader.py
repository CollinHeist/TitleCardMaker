from abc import ABC, abstractmethod

from yaml import safe_load

from modules.Debug import log

class YamlReader(ABC):
    """
    This abstract class describes some class that reads and parses YAML.
    """
    
    @abstractmethod
    def __init__(self, yaml: dict={}, *,
                 log_function: callable=log.error) -> None:
        """Initialization function of this class"""
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


    @staticmethod
    def _read_file(file: 'Path') -> dict:
        """
        Read the given file and return the contained YAML.
        
        :param      file:   Path to the file to read.
        
        :returns:   Empty dictionary if the file DNE, otherwise the content of
                    the file.
        """

        # If file does not exist, return blank dictionary
        if not file.exists():
            return {}

        with file.open('r', encoding='utf-8') as file_handle:
            try:
                return safe_load(file_handle)
            except Exception as e:
                log.critical(f'Error reading "{file.resolve()}":\n{e}\n')
                exit(1)

        return {}
        