from logging import Logger

from sqlalchemy import Boolean, Column, Integer, String, JSON
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import Mapped, object_session, relationship

from app.database.session import Base
from app.models.template import SyncTemplates, Template
from modules.Debug import log


class Sync(Base):
    """
    SQL Table that defines a Sync. This contains Sync requirements and
    exclusions, as well as relational objects to linked Templates and
    Series.
    """

    __tablename__ = 'sync'

    # Referencial arguments
    id = Column(Integer, primary_key=True, index=True)
    series = relationship('Series', back_populates='sync')
    _templates: Mapped[list[SyncTemplates]] = relationship(
        SyncTemplates,
        back_populates='sync',
        order_by=SyncTemplates.order,
        cascade='all, delete-orphan',
    )
    templates: AssociationProxy[list[Template]] = association_proxy(
        '_templates', 'template',
        creator=lambda st: st,
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


    @hybrid_method
    def assign_templates(self,
            templates: list[Template],
            *,
            log: Logger = log,
        ) -> None:
        """
        Assign the given Templates to this Sync. This updates the
        association table for Sync:Template relationships as needed.

        Args:
            templates: List of Templates to assign to this object. The
                provided order is used for the creation of the
                association table objects so that order is preserved
                within the relationship.
            log: Logger for all log messages.
        """

        # Reset existing assocations
        self.templates = []
        for index, template in enumerate(templates):
            existing = object_session(template).query(SyncTemplates)\
                .filter_by(sync_id=self.id,
                           template_id=template.id,
                           order=index)\
                .first()
            if existing:
                self.templates.append(existing)
            else:
                self.templates.append(SyncTemplates(
                    sync_id=self.id,
                    template_id=template.id,
                    order=index,
                ))

        log.debug(f'Sync[{self.id}].template_ids = {[t.id for t in templates]}')


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
