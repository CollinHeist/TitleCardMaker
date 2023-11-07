from pathlib import Path

from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from app.database.session import Base


class Card(Base):
    """
    SQL Table that defines a Title Card. This contains all the details
    used in the Card creation, as well as relational objects to the
    associated Series, Episode, and Loaded instances.
    """

    __tablename__ = 'card'

    # Referencial arguments
    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey('series.id'))
    episode_id = Column(Integer, ForeignKey('episode.id'))
    series = relationship('Series', back_populates='cards')
    episode = relationship('Episode', back_populates='cards')
    loaded = relationship(
        'Loaded',
        back_populates='card',
        foreign_keys='Loaded.card_id',
    )

    card_file = Column(String, nullable=False)
    filesize = Column(Integer)

    card_type = Column(String, nullable=False)
    model_json = Column(MutableDict.as_mutable(JSON), default={}, nullable=False)


    @hybrid_property
    def log_str(self) -> str:
        """
        Loggable string that defines this object (i.e. `__repr__`).
        """

        return f'Card[{self.id}] "{self.card_file}"'
    

    @hybrid_property
    def exists(self) -> bool:
        """Whether the Card file for this object exists."""

        return Path(self.card_file).exists()


    @hybrid_property
    def exists(self) -> bool:
        """Whether this Card file exists."""

        return Path(self.card_file).exists()
