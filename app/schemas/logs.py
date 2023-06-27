from datetime import datetime
from typing import Literal, Optional

from pydantic import Field

from app.schemas.base import Base


"""
Base classes
"""
LogLevel = Literal['debug', 'info', 'warning', 'error', 'critical']

"""
Creation classes
"""
...

"""
Update classes
"""
...

"""
Return classes
"""
class LogEntry(Base):
    level: LogLevel
    context_id: str
    time: datetime
    message: str