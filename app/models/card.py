from pathlib import Path
from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.connection import Connection
    from app.models.episode import Episode
    from app.models.loaded import Loaded
    from app.models.series import Series


class Card(Base):
    """
    SQL Table that defines a Title Card. This contains all the details
    used in the Card creation, as well as relational objects to the
    associated Series, Episode, and Loaded instances.
    """

    __tablename__ = 'card'

    # Referencial arguments
    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True
    )
    interface_id: Mapped[Optional[int]] = mapped_column(ForeignKey('connection.id'))
    series_id: Mapped[int] = mapped_column(ForeignKey('series.id'))
    episode_id: Mapped[int] = mapped_column(ForeignKey('episode.id'))

    connection: Mapped['Connection'] = relationship(back_populates='cards')
    series: Mapped['Series'] = relationship(back_populates='cards')
    episode: Mapped['Episode'] = relationship(back_populates='cards')
    loaded: Mapped['Loaded'] = relationship(
        back_populates='card',
        foreign_keys='Loaded.card_id',
    )

    card_file: Mapped[str]
    filesize: Mapped[int]
    library_name: Mapped[Optional[str]]

    card_type: Mapped[str]
    model_json: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON), default={})


    @property
    def log_str(self) -> str:
        """
        Loggable string that defines this object (i.e. `__repr__`).
        """

        return f'Card[{self.id}] "{self.card_file}"'


    @property
    def exists(self) -> bool:
        """Whether the Card file for this object exists."""

        return Path(self.card_file).exists()
