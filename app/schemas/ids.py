# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Optional

from pydantic import constr # pylint: disable=no-name-in-module


EmbyID = constr(regex=r'^(\d+[:-](.+)[:-][a-fA-F0-9]+,)*\d+[:-](.+)[:-][a-fA-F0-9]+$|^$')
IMDbID =  Optional[constr(regex=r'^tt\d{4,}$')]
JellyfinID = constr(regex=r'^(\d+[:-](.+)[:-][a-fA-F0-9]+,)*\d+[:-](.+)[:-][a-fA-F0-9]+$|^$')
SonarrID = constr(regex=r'^(\d+[:-]\d+,)*\d+[:-]\d+$|^$')
TMDbID = Optional[int]
TVDbID = Optional[int]
TVRageID = Optional[int]
