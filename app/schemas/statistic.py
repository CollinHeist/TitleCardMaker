from pathlib import Path

from app.schemas.base import Base

class Statistic(Base):
    value: int
    value_text: str
    unit: str
    description: str

class CardCount(Statistic):
    unit: str = 'Cards'
    description: str = 'Number of managed title cards'

class SeriesCount(Statistic):
    unit: str = 'Series'
    description: str = 'Number of series within TCM'

class AssetSize(Statistic):
    description: str = 'Combined size of title cards created by TCM'