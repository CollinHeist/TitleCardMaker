from abc import ABC, abstractmethod

from yaml import safe_load

from modules.Debug import log

class YamlReader(ABC):
    """
    This abstract class describes some class that reads and parses YAML.
    """
    
    @abstractmethod
    def __init__(self, yaml: dict={}) -> None:
        """Initialization function of this class"""
        self._base_yaml = yaml


    def __getitem__(self, attributes):
        """
        Main way to get attribute values from YAML. If the given indices exist,
        then the value is returned, if not then None is returned.
        
        :param      attributes: Attributes to get of this YAML.
        
        :returns:   The value within YAML indicated by the given attributes, 
                    None if DNE.
        """

        # For multi-indexing
        if isinstance(attributes, tuple):
            if self._is_specified(*attributes):
                value = self._base_yaml
                for attrib in attributes:
                    value = value[attrib]

                return value
            return None

        return self._base_yaml.get(attributes, None)


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
            if current[attribute] == None:
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
        