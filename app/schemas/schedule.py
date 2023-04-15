from typing import Any, Callable, Optional

from pydantic import Field, PositiveInt

from app.schemas.base import Base

"""
Base classes
"""
class NewJob(Base):
    id: str
    function: Callable[..., Any]
    seconds: int
    description: str

"""
Update classes
"""
class UpdateInterval(Base):
    seconds: PositiveInt = Field(default=0)
    minutes: PositiveInt = Field(default=0)
    hours: PositiveInt = Field(default=0)
    days: PositiveInt = Field(default=0)
    weeks: PositiveInt = Field(default=0)

"""
Return classes
"""
class ScheduledTask(Base):
    id: str = Field(description='Unique ID of the Task')
    description: str = Field(description='Description of the Task')
    frequency: int = Field(description='How often (in seconds) the Task runs')
    next_run: str = Field(description='Next runtime for the Task')