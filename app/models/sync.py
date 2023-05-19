from sqlalchemy import Boolean, Column, Integer, String, JSON
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.models.template import SyncTemplates

class Sync(Base):
    __tablename__ = 'sync'

    # Referencial arguments
    id = Column(Integer, primary_key=True, index=True)
    series = relationship('Series', back_populates='sync')
    templates = relationship(
        'Template',
        secondary=SyncTemplates.__table__,
        back_populates='syncs'
    )

    name = Column(String, nullable=False)
    interface = Column(String, nullable=False)

    required_tags = Column(JSON, default=[], nullable=False)
    required_libraries = Column(JSON, default=[], nullable=False)

    excluded_tags = Column(JSON, default=[], nullable=False)
    excluded_libraries = Column(JSON, default=[], nullable=False)

    downloaded_only = Column(Boolean, default=False)
    monitored_only = Column(Boolean, default=False)
    required_series_type = Column(String, default=None)
    excluded_series_type = Column(String, default=None)

    @hybrid_property
    def template_ids(self) -> list[int]:
        return [template.id for template in self.templates]

    @hybrid_property
    def log_str(self) -> str:
        return f'Sync[{self.id}] {self.name}'