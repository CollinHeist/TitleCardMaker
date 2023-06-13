from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, root_validator
from pydantic.color import Color

from modules.Debug import log

# Default value to use for arguments in Update objects that accept None
UNSPECIFIED = '__unspecified_'

# Pydantic base class
class Base(BaseModel):
    class Config:
        orm_mode = True

# Base class for all "update" models
class UpdateBase(Base):
    @root_validator
    def delete_unspecified_args(cls, values):
        delete_keys = [key for key, value in values.items() if value == UNSPECIFIED]
        for key in delete_keys:
            del values[key]

        return values
    
# Better "Color" class to support "transparent"
BetterColor = Union[Color, Literal['transparent']]

# Function to validate two equal length lists are provided
def validate_argument_lists_to_dict(
        values: dict[str, Any],
        label: str,
        key0: str,
        key1: str,
        output_key: str) -> dict[str, Any]:
    """
    Validation function to join two paired lists into a dictionary.

    Args:
        values: Dictionary to get the value lists from.
        label: Name of the values being validated. For logging only.
        key0: The key within values which contains the list of keys to
            use as the output dictionary keys. Paired to key1.
        key1: The key within values which contains thel ist of values to
            use as the output ditionary values. Pared to key0.
        output_key: Output key to store the paired dictionary within
            values.

    Returns:
        Modified values dictionary with the merged dictionary added
        under the output key. If only one key is provided, the 
        unmodified dictionary is returned.

    Raises:
        ValueError if only one set of the provided values is a list, or
            if the two lists are not the equal length.
    """

    # Get values for these keys
    list0 = values.get(key0)
    list1 = values.get(key1)

    # If both keys omitted, exit after removing them
    if key0 not in values and key1 not in values:
        values.pop(key0, None)
        values.pop(key1, None)
        return values

    values.pop(key0, None)
    values.pop(key1, None)

    # Both specified as None, set output to None
    if list0 is None and list1 is None:
        values[output_key] = None
    # Both unspecified
    elif ((list0 == UNSPECIFIED and list1 == UNSPECIFIED)
        or (list0 == [UNSPECIFIED] and list1 == [UNSPECIFIED])):
        pass
    # Only one was provided
    elif isinstance(list0, list) ^ isinstance(list1, list):
        raise ValueError(f'{label} must both be lists or omitted')
    # Both provided as lists
    else:
        # Filter out unspecified values
        list0 = [in_ for in_ in list0 if in_ not in (UNSPECIFIED, '')]
        list1 = [out_ for out_ in list1 if out_ not in (UNSPECIFIED, '')]
        # Verify lists are equal lengths
        if (isinstance(list0, list) and isinstance(list1, list)
            and len(list0) != len(list1)):
            raise ValueError(f'{label} must be the same length')
        # Create dictionary of combined lists
        else:
            values[output_key] = {
                in_: out_ for in_, out_ in zip(list0, list1)
                if in_ != UNSPECIFIED and out_ != UNSPECIFIED
            }

    return values