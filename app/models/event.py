# pylint: disable=no-self-argument
from datetime import datetime
from typing import Literal, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import LoggingBase, logs_engine

LogLevel = Literal['Debug', 'Info', 'Warning', 'Error', 'Critical']

"""
The following SQL tables should not be a part of the primary SQL Base
Metadata. These tables should be part of a Blueprint SQL Metadata; as
these are only defined in the Blueprints SQL table.
"""
class Event(LoggingBase):
    """
    SQL table for all Log Events.  
    """

    __tablename__ = 'event'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    series_id: Mapped[Optional[int]] = mapped_column(default=None)
    episode_id: Mapped[Optional[int]] = mapped_column(default=None)

    context_id: Mapped[str]
    level: Mapped[LogLevel] = mapped_column(String)
    time: Mapped[datetime]
    message: Mapped[str]

LoggingBase.metadata.create_all(logs_engine)
