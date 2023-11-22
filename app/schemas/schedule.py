# pylint: disable=missing-class-docstring,missing-function-docstring,no-name-in-module
from datetime import datetime, timedelta
from typing import Callable, Optional

from pydantic import Field, PositiveInt # pylint: disable=no-name-in-module

from app.schemas.base import Base

"""
Base classes
"""
class NewJob(Base):
    id: str
    function: Callable[..., None]
    seconds: PositiveInt
    crontab: str
    description: str
    internal: bool = False
    running: bool = False
    previous_start_time: Optional[datetime] = None
    previous_end_time: Optional[datetime] = None

"""
Update classes
"""
class UpdateSchedule(Base):
    seconds: PositiveInt = 0
    minutes: PositiveInt = 0
    hours: PositiveInt = 0
    days: PositiveInt = 0
    weeks: PositiveInt = 0
    crontab: Optional[str] = '*/10 * * * *'

"""
Return classes
"""
class ScheduledTask(Base):
    id: str
    description: str
    frequency: Optional[PositiveInt] = None
    crontab: Optional[str] = None
    next_run: str
    previous_duration: Optional[timedelta] = None
    running: bool
