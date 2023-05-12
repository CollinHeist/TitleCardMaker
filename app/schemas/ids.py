from typing import Optional

from pydantic import constr, PositiveInt

EmbyID = Optional[PositiveInt]
IMDbID =  Optional[constr(regex=r'^tt\d{4,}$')]
JellyfinID = Optional[PositiveInt]
SonarrID = Optional[constr(regex=r'^\d+-\d+$')]
TMDbID = Optional[PositiveInt]
TVDbID = Optional[PositiveInt]
TVRageID = Optional[PositiveInt]