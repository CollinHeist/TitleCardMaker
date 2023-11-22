from datetime import datetime
from logging import Logger

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.session import Base
from modules.Debug import log


class Statistic(Base):
    """
    SQL Table that defines a Statistic. This is essentially a
    timestamped count of the database for chart generation.
    """

    __tablename__ = 'statistic'

    # Referencial arguments
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    timestamp: Mapped[datetime] = mapped_column(
        default=func.now(), # pylint: disable=not-callable
    )

    # Counts
    blueprints: Mapped[int] = mapped_column(default=0)
    cards: Mapped[int] = mapped_column(default=0)
    episodes: Mapped[int] = mapped_column(default=0)
    fonts: Mapped[int] = mapped_column(default=0)
    loaded: Mapped[int] = mapped_column(default=0)
    series: Mapped[int] = mapped_column(default=0)
    syncs: Mapped[int] = mapped_column(default=0)
    templates: Mapped[int] = mapped_column(default=0)
    users: Mapped[int] = mapped_column(default=0)

    # Non-Counts
    filesize: Mapped[int] = mapped_column(default=0)
    cards_created: Mapped[int] = mapped_column(default=0)
