from typing import Optional

from pydantic import constr # pylint: disable=no-name-in-module


EmbyID = Optional[constr(regex=r'^(\d+[:-][a-fA-F0-9]+,)*\d+[:-][a-fA-F0-9]+$')]
IMDbID =  Optional[constr(regex=r'^tt\d{4,}$')]
JellyfinID = Optional[constr(regex=r'^[a-fA-F0-9]+$')]
SonarrID = Optional[constr(regex=r'^(\d+[:-]\d+,)*\d+[:-]\d+$')]
TMDbID = Optional[int]
TVDbID = Optional[int]
TVRageID = Optional[int]
