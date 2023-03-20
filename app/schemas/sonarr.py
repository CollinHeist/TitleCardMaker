from typing import Literal, Optional, Union

from app.schemas.base import Base

class Tag(Base):
    id: int
    label: str