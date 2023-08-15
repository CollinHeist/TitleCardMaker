# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Literal, Union

from pydantic import BaseModel, constr, root_validator


# Default value to use for arguments in Update objects that accept None
UNSPECIFIED = '__unspecified_'

# String that can be used as key in a dictionary
DictKey = constr(regex=r'^[a-zA-Z]+[^ -]*$', min_length=1)

# Pydantic base class
class Base(BaseModel):
    class Config:
        orm_mode = True

# Base class for all "update" models
class UpdateBase(Base):
    @root_validator(skip_on_failure=True)
    def delete_unspecified_args(cls, values):
        delete_keys = [key for key, value in values.items() if value == UNSPECIFIED]
        for key in delete_keys:
            del values[key]

        return values

# Better "Color" class to support "transparent", required until Pydantic v2.0
BetterColor = Union[str, Literal['transparent']]

# Function to validate two equal length lists are provided
def validate_argument_lists_to_dict(
        values: dict,
        label: str,
        key0: str,
        key1: str,
        output_key: str,
        allow_empty_strings: bool = False,
    ) -> dict:
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
        allow_empty_strings: Whether '' is permitted in `values[key1]`.

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
        return values
    # Both unspecified
    if ((list0 == UNSPECIFIED and list1 == UNSPECIFIED)
        or (list0 == [UNSPECIFIED] and list1 == [UNSPECIFIED])):
        pass
    # Only one was provided
    elif isinstance(list0, list) ^ isinstance(list1, list):
        raise ValueError(f'{label} must both be lists or omitted')

    # Both provided as lists - filter out unspecified values
    BAD_VALS = (UNSPECIFIED,) if allow_empty_strings else (UNSPECIFIED, '')
    list0 = [in_ for in_ in list0 if in_ not in BAD_VALS]
    list1 = [out_ for out_ in list1 if out_ not in BAD_VALS]

    # Verify lists are equal lengths
    if (isinstance(list0, list) and isinstance(list1, list)
        and len(list0) != len(list1)):
        raise ValueError(f'{label} must be the same length')

    # Create dictionary of combined lists
    values[output_key] = {
        in_: out_ for in_, out_ in zip(list0, list1)
        if UNSPECIFIED not in (in_, out_)
    }

    return values
