from copy import deepcopy
from re import findall
from typing import Any

from modules.Debug import log

class Template:
    """
    This class describes a template. A Template is a fallback YAML
    object that can be "filled in" with values, or just outright contain
    them. Variable data is encoded in the form <<{key}>>. When applied
    to some series YAML dictionary, the template'd YAML is applied to
    the series, unless both have instances of the data, in which the
    series data takes priority.
    """

    """Maximum number of template application iterations"""
    MAX_TEMPLATE_DEPTH = 10


    def __init__(self, name: str, template: dict[str: str]) -> None:
        """
        Construct a new Template object with the given name, and with
        the given template dictionary. Keys of the form <<{key}>> are
        search for through this template.

        Args:
            name: The template name/identifier. For logging only.
            template: The template YAML to implement.
        """

        self.name = name
        self.valid = True

        # Validate template is dictionary
        if isinstance(template, dict):
            self.template = template
            self.keys = self.__identify_template_keys(self.template, set())
        else:
            log.error(f'Invalid template "{self.name}"')
            self.valid = False

        # Get validate/defaults
        if isinstance((defaults := template.get('defaults', {})), dict):
            self.defaults = defaults
        else:
            log.error(f'Invalid defaults for template "{self.name}"')
            self.valid = False


    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object."""

        return f'<Template {self.name=}, {self.keys=}, {self.template=}>'


    def __identify_template_keys(self, template: dict, keys: set) -> set:
        """
        Identify the required template keys to use this template. This
        looks for all unique values like "<<{key}>>". This is a
        recursive function, and searches through all sub-dictionaries of
        template.

        Args:
            template: The template dictionary to search through.
            keys: The existing keys identified, only used for recursion.

        Returns:
            Set of keys required by the given template.
        """

        for _, value in template.items():
            # If this attribute value is just a string, add keys to set
            if (isinstance(value, str)
                and (new_keys := findall(r'<<(.+?)>>', value))):
                keys.update(new_keys)
            # Recurse through this sub-attribute
            elif isinstance(value, dict):
                keys.update(self.__identify_template_keys(value, keys))
            # List of values, recurse through each item
            elif isinstance(value, list):
                for value_ in value:
                    keys.update(self.__identify_template_keys(value_, keys))

        return keys


    def __apply_value_to_key(self, template: dict, key: str, value: Any) -> None:
        """
        Apply the given value to all instances of the given key in the
        template. This looks for <<{key}>>, and puts value in place.
        This function is recursive, so if any values of template are
        dictionaries, those are applied as well. For example:

        >>> temp = {'year': <<year>>,
                    'b': {'b1': False,
                          'b2': 'Hey <<year>>'}}
        >>> __apply_value_to_key(temp, 'year', 1234)
        >>> temp
        {'year': 1234, 'b': {'b1': False, 'b2': 'Hey 1234'}}

        Args:
            template: The dictionary to modify any instances of 
                <<{key}>> within. Modified in-place.
            key: The key to search/replace for.
            value: The value to replace the key with.
        """

        for t_key, t_value in template.items():
            # If the templated value is JUST the replacement, just copy over
            if isinstance(t_value, str):
                if t_value == f'<<{key}>>':
                    template[t_key] = value
                else:
                    template[t_key] = t_value.replace(f'<<{key}>>', str(value))
            # Template'd value is dictionary, recurse
            elif isinstance(t_value, dict):
                self.__apply_value_to_key(template[t_key], key, value)
            # Template'd value is list, apply to each value individually
            elif isinstance(t_value, list):
                for index, sub_value in enumerate(t_value):
                    if isinstance(sub_value, str):
                        template[t_key][index] = sub_value.replace(f'<<{key}>>',
                                                                   str(value))
                    elif isinstance(sub_value, dict):
                        self.__apply_value_to_key(template[t_key][index], key,
                                                  value)


    @staticmethod
    def recurse_priority_union(base_yaml: dict,
            template_yaml: dict) -> None:
        """
        Construct the union of the two dictionaries, with all key/values
        of template_yaml being ADDED to the first, priority dictionary
        IF that specific key is not already present. This is a recurisve
        function that applies to any arbitrary set of nested
        dictionaries. For example:

        >>> base_yaml = {'a': 123, 'c': {'c1': False}}
        >>> t_yaml = {'a': 999, 'b': 234, 'c': {'c2': True}}
        >>> recurse_priority_union(base_yaml, t_yaml)
        >>> base_yaml
        {'a': 123, 'b': 234, 'c': {'c1': False, 'c2': True}}

        Args:
            base_yaml: The base - i.e. higher priority - YAML that forms
                the basis of the union of these dictionaries. Modified
                in-place.
            template_yaml: The templated - i.e. lower priority - YAML.
        """

        # Go through each key in template and add to priority YAML if not present
        for t_key, t_value in template_yaml.items():
            if isinstance(base_yaml, dict):
                if t_key in base_yaml:
                    if isinstance(t_value, dict):
                        # Both have this dictionary, recurse on keys of dictionary
                        Template.recurse_priority_union(
                            base_yaml[t_key], t_value
                        )
                else:
                    # Key is not present in base, carryover template value
                    base_yaml[t_key] = t_value


    def apply_to_series(self, series_info: 'SeriesInfo',
            series_yaml: dict[str, Any]) -> bool:
        """
        Apply this Template object to the given series YAML, modifying
        it to include the templated values. This function assumes that
        the given series YAML has a template attribute, and that it
        applies to this object

        Args:
            series_info: The info of the series. Used for built-in
                series data.
            series_yaml: The series YAML to modify. Must have 'template'
                key. Modified in-place.

        Returns:
            True if the given series contained all the required template
            variables for application, False if it did not.
        """

        # Evaluate built-in keys from series info
        builtin_data = {}
        if series_info is not None:
            builtin_data = {
                'title': series_info.name,
                'full_title': series_info.full_name,
                'clean_title': series_info.clean_name,
                'year': series_info.year,
            }

        # Add builtin-data to series YAML template
        series_yaml['template'] = builtin_data | series_yaml['template']

        # If not all required template keys are specified, warn and exit
        given_keys = set(series_yaml['template'].keys())
        default_keys = set(self.defaults.keys())
        if not (given_keys | default_keys).issuperset(self.keys):
            log.warning(f'Missing "{self.name}" template data for '
                        f'"{series_info}"')
            return False

        # Copy base template before modification
        modified_template = deepcopy(self.template)

        # Iteratively apply template until all keys are removed
        count, remaining_keys = 0, self.keys
        while remaining_keys and count < self.MAX_TEMPLATE_DEPTH:
            # Take given template values, fill in template object
            for key, value in series_yaml['template'].items():
                self.__apply_value_to_key(modified_template, key, value)

            # Fill any remaining template keys with default values
            for key, value in self.defaults.items():
                self.__apply_value_to_key(modified_template, key, value)

            # Identify any remaining keys after application
            remaining_keys=self.__identify_template_keys(modified_template,set())
            count += 1

        # Log and exit if failed to apply
        if count >= self.MAX_TEMPLATE_DEPTH:
            log.warning(f'Unable to apply template "{self.name}" to {series_info}')
            return False

        # Delete the template section from the series YAML
        del series_yaml['template']

        # Construct union of series and filled-in template YAML
        self.recurse_priority_union(series_yaml, modified_template)

        return True