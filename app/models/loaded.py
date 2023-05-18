from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.session import Base

class Loaded(Base):
    __tablename__ = 'loaded'

    # Referencial arguments
    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey('series.id'))
    episode_id = Column(Integer, ForeignKey('episode.id'))
    card_id = Column(Integer, ForeignKey('card.id'))
    series = relationship('Series', back_populates='loaded')

    media_server = Column(String, nullable=False)
    filesize = Column(Integer, ForeignKey('card.filesize'))