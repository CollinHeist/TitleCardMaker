from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.session import Base

class Loaded(Base):
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