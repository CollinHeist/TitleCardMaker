from typing import Optional, TypeVar


_Setting = TypeVar('_Setting')


class TieredSettings:
    """
    Class defining some multi-tiered Setting dictionaries. All methods
    and functions relate to finding the highest-priority non-None value
    of any number of dictionaries.

    For example:
    >>> settings = TieredSettings.new_settings(
        {'a': 123, 'b': 234, 'c': None},
        {'a': None, 'b': 999, 'c': None},
        {'a': None, 'b': None, 'c': 'test'}
    )
    >>> print(settings)
    {'a': 123, 'b': 999, 'c': 'test'}
    """

    def __init__(self,
            merge_base: dict,
            *dicts: dict[str, _Setting],
        ) -> None:
        """
        Initialize a new TieredSettings object. This merges the given
        dictionaries into the given merge_base dictionary.

        Args:
            base: Dictionary to modify in-place with the highest
                priority settings.
            dicts: Any number of dictionaries to merge into base.
                Dictionaries are provided in increasing priority.
        """

        self.base = merge_base

        # Merge each provided dictionary (in order)
        for dict_ in dicts:
            # Skip non-Dictionaries
            if dict_ is None:
                continue

            # Iterate through all items of the dictionary being merged
            for key, value in dict_.items():
                # Skip underscored keys
                if key.startswith('_'):
                    continue

                # Non-None values get merged in
                if value is not None:
                    merge_base[key] = value


    @staticmethod
    def new_settings(*dicts: dict[str, _Setting]) -> dict[str, _Setting]:
        """
        Resolve the TieredSettings for the given dictionaries, and
        return the created base.

        Args:
            dicts: Any number of dictionaries to merge into the newly
                created base. Dictionaries are provided in increasing
                priority.

        Returns:
            New dictionary base with the merged settings.
        """

        # Create new base, merge into
        base = {}
        TieredSettings(base, *dicts)

        # Return modified base
        return base


    @staticmethod
    def filter(settings: dict[str, _Setting]) -> dict[str, _Setting]:
        """
        Filter the given settings dictionary any remove any key-value
        pairs whose value is None.

        Args:
            settings: Input dictionary to filter.

        Returns:
            Dictionary identical to `settings` but with all None values
            removed.
        """

        return {
            key: value for key, value in settings.items() if value is not None
        }


    @staticmethod
    def resolve_singular_setting(*values: Optional[_Setting]) -> _Setting:
        """
        Get the highest priority (non-None) value of the given values.

        Args:
            values: Any number of values to evaluate. Values are
                provided in increasing priority.

        Returns:
            The last non-None value of the provided values. None is
            returned if no non-None values are available.
        """

        return next(
            (item for item in reversed(values) if item is not None),
            None
        )
