from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType

from app.database.session import Base

class Sync(Base):
    __tablename__ = 'sync'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    interface = Column(String, nullable=False)

    template_id = Column(Integer, ForeignKey('template.id'))

    required_tags = Column(JSON, default=[], nullable=False)
    required_libraries = Column(JSON, default=[], nullable=False)
    # required_tags = Column(MutableList.as_mutable(PickleType), default=[])
    # required_libraries = Column(MutableList.as_mutable(PickleType), default=[])

    excluded_tags = Column(JSON, default=[], nullable=False)
    excluded_libraries = Column(JSON, default=[], nullable=False)
    # excluded_tags = Column(MutableList.as_mutable(PickleType), default=[])
    # excluded_libraries = Column(MutableList.as_mutable(PickleType), default=[])

    downloaded_only = Column(Boolean, default=False)
    monitored_only = Column(Boolean, default=False)
    required_series_type = Column(String, default=None)
    excluded_series_type = Column(String, default=None)

    @hybrid_property
    def log_str(self) -> str:
        return f'Sync[{self.id}] {self.name}'