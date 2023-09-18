# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Optional

from pydantic import constr # pylint: disable=no-name-in-module


Hexstring = constr(regex=r'^[a-fA-F0-9]+$')

EmbyID = Optional[Hexstring]
IMDbID =  Optional[constr(regex=r'^tt\d{4,}$')]
JellyfinID = Optional[Hexstring]
SonarrID = Optional[constr(regex=r'^\d+-\d+$')]
TMDbID = Optional[int]
TVDbID = Optional[int]
TVRageID = Optional[int]
