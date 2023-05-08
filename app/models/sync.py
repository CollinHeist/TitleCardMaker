from pathlib import Path

from json import dumps, loads
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType

from app.database.session import Base

class Sync(Base):
    __tablename__ = 'sync'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    interface = Column(String, nullable=False)

    template_id = Column(Integer, ForeignKey('template.id'))

    required_tags = Column(MutableList.as_mutable(PickleType), default=[])
    required_libraries = Column(MutableList.as_mutable(PickleType), default=[])

    excluded_tags = Column(MutableList.as_mutable(PickleType), default=[])
    excluded_libraries = Column(MutableList.as_mutable(PickleType), default=[])

    downloaded_only = Column(Boolean, default=False)
    monitored_only = Column(Boolean, default=False)
    required_series_type = Column(String, default=None)
    excluded_series_type = Column(String, default=None)

    @hybrid_property
    def log_str(self) -> str:
        return f'Sync[{self.id}] {self.name}'