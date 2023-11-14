from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.card import Card
    from app.models.connection import Connection
    from app.models.episode import Episode
    from app.models.series import Series


class Loaded(Base):
    """
    SQL Table that defines a Loaded asset. This contains which media
    server the asset was loaded into, the file size of the asset, as
    well as relational objects to the parent Series, Episode, and Card.
    """

    __tablename__ = 'loaded'

    # Referencial arguments
    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey('card.id'))
    episode_id: Mapped[int] = mapped_column(ForeignKey('episode.id'))
    interface_id: Mapped[int] = mapped_column(ForeignKey('connection.id'))
    series_id: Mapped[int] = mapped_column(ForeignKey('series.id'))

    card: Mapped[list['Card']] = relationship(
        back_populates='loaded',
        foreign_keys=[card_id]
    )
    connection: Mapped[list['Connection']] = relationship(back_populates='loaded')
    episode: Mapped[list['Episode']] = relationship(back_populates='loaded')
    series: Mapped[list['Series']] = relationship(back_populates='loaded')

    filesize: Mapped[int] = mapped_column(ForeignKey('card.filesize'))
    library_name: Mapped[str]


    def __repr__(self) -> str:
        return f'Loaded[{self.id}] Card[{self.card_id}] {self.filesize:,} bytes into "{self.library_name}"'


    @property
    def log_str(self) -> str:
        """
        Loggable string that defines this object (i.e. `__repr__`).
        """

        return f'Loaded[{self.id}] Card[{self.card_id}]'
