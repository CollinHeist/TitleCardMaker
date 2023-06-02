from typing import Optional

from pydantic import constr, PositiveInt

Hexstring = constr(regex=r'^[a-fA-F0-9]+$')

EmbyID = Optional[Hexstring]
IMDbID =  Optional[constr(regex=r'^tt\d{4,}$')]
JellyfinID = Optional[Hexstring]
SonarrID = Optional[constr(regex=r'^\d+-\d+$')]
TMDbID = Optional[PositiveInt]
TVDbID = Optional[PositiveInt]
TVRageID = Optional[PositiveInt]