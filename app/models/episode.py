from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey

class Episode(BaseModel):
    __tablename__ = 'episode'

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey('series.id'))

    season_number = Column(Integer)
    episode_number = Column(Integer)
    absolute_number = Column(Integer, nullable=True)

    source_file = Column(String)
    destination = Column(String)