from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.models.template import SyncTemplates


class Sync(Base):
    """
    SQL Table that defines a Sync. This contains Sync requirements and
    exclusions, as well as relational objects to linked Templates and
    Series.
    """

    __tablename__ = 'sync'

    # Referencial arguments
    id = Column(Integer, primary_key=True, index=True)
    connection = relationship('Connection', back_populates='syncs')
    interface_id = Column(Integer, ForeignKey('connection.id'))
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
        """
        ID's of any Templates associated with this Sync (rather than the
        ORM objects themselves).

        Returns:
            List of ID's for associated Templates.
        """

        return [template.id for template in self.templates]


    @hybrid_property
    def log_str(self) -> str:
        """
        Loggable string that defines this object (i.e. `__repr__`).
        """

        return f'Sync[{self.id}] {self.name}'
