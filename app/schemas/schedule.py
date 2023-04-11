from typing import Any, Optional

from pydantic import Field

from app.schemas.base import Base

class UpdateInterval(Base):
    seconds: int = Field(default=0, min=0)
    minutes: int = Field(default=0, min=0)
    hours: int = Field(default=0, min=0)
    days: int = Field(default=0, min=0)
    weeks: int = Field(default=0, min=0)

class ScheduledTask(Base):
    task_id: str
    # description: str
    frequency: int
    next_run: str