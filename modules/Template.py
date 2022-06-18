from copy import deepcopy
from re import findall

from modules.Debug import log

class Template:
    """
    This class describes a template. A Template is a fallback YAML object that
    can be "filled in" with values, or just outright contain them. Variable data
    is encoded in the form <<{key}>>. When applied to some series YAML
    dictionary, the template'd YAML is applied to the series, unless both have
    instances of the data, in which the series data takes priority.
    """

    def __init__(self, name: str, template: dict) -> None:
        """
        Construct a new Template object with the given name, and with the given
        template dictionary. Keys of the form <<{key}>> are search for through
        this template.
        
        :param      name:       The template name/identifier. For logging only.
        :param      template:   The template YAML to implement.
        """

        self.name = name
        self.__template = template
        self.__keys = self.__identify_template_keys(self.__template, set())


    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object."""

        return f'<Template {self.name=}, {self.__keys=}, {self.__template=}>'


    def __identify_template_keys(self, template: dict, keys: set) -> set:
        """
        Identify the required template keys to use this template. This looks for
        all unique values like "<<{key}>>". This is a recursive function, and
        searches through all sub-dictionaries of template.
        
        :param      template:   The template dictionary to search through.
        :param      keys:       The existing keys identified, only used for
                                recursion.
        
        :returns:   Set of keys required by the given template.
        """

        for _, value in template.items():
            # If this attribute value is just a string, add keys to set
            if (isinstance(value, str)
                and (new_keys := findall(r'<<(.+?)>>', value))):
                keys.update(new_keys)
            elif isinstance(value, dict):
                # Recurse through this sub-attribute
                keys.update(self.__identify_template_keys(value, keys))

        return keys


    def __apply_value_to_key(self, template: dict, key: str, value) -> None:
        """
        Apply the given value to all instances of the given key in the template.
        This looks for <<{key}>>, and puts value in place. This function is
        recursive, so if any values of template are dictionaries, those are
        applied as well. For example:

        >>> temp = {'year': <<year>>, 'b': {'b1': False, 'b2': 'Hey <<year>>'}}
        >>> __apply_value_to_key(temp, 'year', 1234)
        >>> temp
        {'year': 1234, 'b': 'b1': False, 'b2': 'Hey 1234'}
        
        :param      template:   The dictionary to modify any instances of
                                <<{key}>> within. Modified in-place.
        :param      key:        The key to search/replace for.
        :param      value:      The value to replace the key with.
        """

        for t_key, t_value in template.items():
            # log.info(f'template[{t_key}]={t_value}, {type(t_value)=}')
            if isinstance(t_value, str):
                # If the templated value is JUST the replacement, just copy over
                if t_value == f'<<{key}>>':
                    template[t_key] = value
                else:
                    template[t_key] = t_value.replace(f'<<{key}>>', str(value))
            elif isinstance(t_value, dict):
                # Template'd value is dictionary, recurse
                self.__apply_value_to_key(template[t_key], key, value)


    def __recurse_priority_union(self, base_yaml: dict,
                                 template_yaml: dict) -> None:
        """
        Construct the union of the two dictionaries, with all key/values of
        template_yaml being ADDED to the first, priority dictionary IF that
        specific key is not already present. This is a recurisve function that
        applies to any arbitrary set of nested dictionaries. For example:

        >>> base_yaml = {'a': 123, 'c': {'c1': False}}
        >>> t_yaml = {'a': 999, 'b': 234, 'c': {'c2': True}}
        >>> __recurse_priority_union(base_yaml, )
        >>> base_yaml
        {'a': 123, 'b': 234, 'c': {'c1': False, 'c2': True}}
        
        :param      base_yaml:      The base - i.e. higher priority - YAML that 
                                    forms the basis of the union of these
                                    dictionaries. Modified in-place.
        :param      template_yaml:  The templated - i.e. lower priority - YAML.
        """

        # Go through each key in template and add to priority YAML if not present
        for t_key, t_value in template_yaml.items():
            if t_key in base_yaml:
                if isinstance(t_value, dict):
                    # Both have this dictionary, recurse on keys of dictionary
                    self.__recurse_priority_union(base_yaml[t_key], t_value)
            else:
                # Key is not present in base, carryover template value
                base_yaml[t_key] = t_value


    def apply_to_series(self, series_name: str, series_yaml: dict) -> bool:
        """
        Apply this Template object to the given series YAML, modifying it
        to include the templated values. This function assumes that the given
        series YAML has a template attribute, and that it applies to this object
        
        :param      series_name:    The name of the series being modified.
        :param      series_yaml:    The series YAML to modify. Must have
                                    'template' key. Modified in-place.

        :returns:   True if the given series contained all the required template
                    variables for application, False if it did not.
        """
        
        # If not all required template keys are specified, warn and exit
        if not set(series_yaml['template'].keys()).issuperset(self.__keys):
            log.warning(f'Missing template data for "{series_name}"')
            return False

        # Take given template values, fill in template object
        modified_template = deepcopy(self.__template)
        for key, value in series_yaml['template'].items():
            self.__apply_value_to_key(modified_template, key, value)

        # Delete the template section from the series YAML
        del series_yaml['template']

        # Construct union of series and filled-in template YAML
        self.__recurse_priority_union(series_yaml, modified_template)

        return True

