from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database.session import Base

class Loaded(Base):
    """
    SQL Table that defines a Loaded asset. This contains which media
    server the asset was loaded into, the file size of the asset, as
    well as relational objects to the parent Series, Episode, and Card.
    """

    __tablename__ = 'loaded'

    # Referencial arguments
    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey('series.id'))
    series = relationship('Series', back_populates='loaded')
    episode_id = Column(Integer, ForeignKey('episode.id'))
    episode = relationship('Episode', back_populates='loaded')
    card_id = Column(Integer, ForeignKey('card.id'))
    card = relationship('Card', back_populates='loaded', foreign_keys=[card_id])

    media_server = Column(String, nullable=False)
    filesize = Column(Integer, ForeignKey('card.filesize'))

    @hybrid_property
    def log_str(self) -> str:
        """
        Loggable string that defines this object (i.e. `__repr__`).
        """

        return f'Loaded[{self.id}] Card[{self.card_id}] in {self.media_server}'