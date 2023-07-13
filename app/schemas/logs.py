# pylint: disable=missing-class-docstring,missing-function-docstring
from datetime import datetime
from typing import Literal

from app.schemas.base import Base


"""
Base classes
"""
LogLevel = Literal['debug', 'info', 'warning', 'error', 'critical']


"""
Return classes
"""
class LogEntry(Base):
    level: LogLevel
    context_id: str
    time: datetime
    message: str
