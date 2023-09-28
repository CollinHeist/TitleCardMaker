# pylint: disable=missing-class-docstring,missing-function-docstring
from app.schemas.base import Base


class Statistic(Base):
    value: int
    value_text: str
    unit: str
    description: str

class SeriesCount(Statistic):
    unit: str = 'Series'
    description: str = 'Number of series within TCM'

class EpisodeCount(Statistic):
    unit: str = 'Episodes'
    description: str = 'Number of episodes'
    value_text: str = '{value:,}'

class CardCount(Statistic):
    unit: str = 'Cards'
    description: str = 'Number of managed title cards'

class AssetSize(Statistic):
    description: str = 'Combined size of title cards created by TCM'
