# pylint: disable=missing-class-docstring,missing-function-docstring
from datetime import datetime, timedelta
from typing import Callable, Optional

from pydantic import constr, PositiveInt

from app.schemas.base import Base

"""
Base classes
"""
CronExpression = constr(strip_whitespace=True, regex=r'^([^ ]+\s+){4}([^ ]+)$')

class NewJob(Base):
    id: str
    function: Callable[..., None]
    seconds: PositiveInt
    crontab: CronExpression
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
    crontab: Optional[CronExpression] = '*/10 * * * *'

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
