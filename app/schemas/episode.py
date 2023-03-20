from typing import Literal, Optional, Union

from app.schemas.base import Base

class Episode(Base):
    id: int
    series_id: int

    season_number: int
    episode_number: int
    absolute_number: Optional[int]

    title: str

    source_file: str
    destination: str