from typing import Any

class TieredSettings:
    """
    
    """

    def __init__(self,  
            merge_base: dict[str, Any],
            *dicts: tuple[dict[str, Any]]) -> None:
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
            if dict_ is None: continue

            # Iterate through all items of the dictionary being merged
            for key, value in dict_.items():
                # Skip underscored keys
                if key.startswith('_'):
                    continue

                # Non-None values get merged in
                if value is not None:
                    merge_base[key] = value


    @staticmethod
    def new_settings(*dicts: tuple[dict[str, Any]]) -> dict[str, Any]:
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
    def resolve_singular_setting(*values: Any) -> Any:
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