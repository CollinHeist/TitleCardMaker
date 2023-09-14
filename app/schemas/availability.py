# pylint: disable=missing-class-docstring
from typing import Optional

from app.schemas.base import Base


class AvailableFont(Base):
    id: int
    name: str

class AvailableSeries(Base):
    id: int
    name: str
    year: int
    directory: Optional[str] = None

class AvailableTemplate(Base):
    id: int
    name: str
