from datetime import datetime, timedelta
from typing import Callable, Optional

from pydantic import Field, PositiveInt

from app.schemas.base import Base

"""
Base classes
"""
class NewJob(Base):
    id: str = Field(description='Unique ID of the Job')
    function: Callable[..., None] = Field(description='Function this Job will run')
    seconds: PositiveInt = Field(description='How often (in seconds) to run this Job')
    description: str = Field(description='Description of the Job')
    internal: bool = Field(
        default=False,
        description='Whether this Job is internal and should not be exposed in API calls',
    )
    running: bool = Field(
        default=False,
        description='Whether this Job is currently running'
    )
    previous_start_time: Optional[datetime] = Field(
        default=None,
        description='When this Job was last started',
    )
    previous_end_time: Optional[datetime] = Field(
        default=None,
        description="When this Job's previous execution last finished",
    )

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
    frequency: PositiveInt = Field(description='How often (in seconds) the Task runs')
    next_run: str = Field(description='Next runtime for the Task')
    previous_duration: Optional[timedelta] = Field(default=None, description="How long this Job's previous execution took")
    running: bool = Field(description='Whether this Task is currently running')