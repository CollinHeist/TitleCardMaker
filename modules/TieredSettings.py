from typing import Any

class TieredSettings:

    def __init__(self,  
            merge_base: dict[str, Any],
            *dicts: tuple[dict[str, Any]]) -> None:
        """

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