from pydantic import BaseModel
from sqlalchemy import Column, Integer, String

class Series(BaseModel):
    __tablename__ = 'series'

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)
    year = Column(Integer)