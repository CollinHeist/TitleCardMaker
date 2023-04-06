from pydantic import Field

from app.schemas.base import Base

class ScheduledTask(Base):
    id: str
    # description: str
    frequency: int
    next_run: str