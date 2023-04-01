from pydantic import Field

from app.schemas.base import Base

class ScheduledTask(Base):
    id: str
    # description: str
    frequency: str
    next_run: str