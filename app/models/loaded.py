from pathlib import Path

from json import dumps, loads
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType

from app.database.session import Base

class Loaded(Base):
    __tablename__ = 'loaded'

    id = Column(Integer, primary_key=True)

    media_server = Column(String, nullable=False)
    series_id = Column(Integer, ForeignKey('series.id'))
    episode_id = Column(Integer, ForeignKey('episode.id'))
    card_id = Column(Integer, ForeignKey('card.id'))
    filesize = Column(Integer, ForeignKey('card.filesize'))