from logging import Logger
from typing import Literal, Optional, TypedDict, Union, TYPE_CHECKING

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from app.database.session import Base
from app.models.template import SyncTemplates, Template
from modules.Debug import log

if TYPE_CHECKING:
    from app.models.connection import Connection
    from app.models.series import Series


SyncInterface = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr']
SonarrKwargs = TypedDict('SonarrKwargs', {
    'required_tags': list[str], 'excluded_tags': list[str],
    'monitored_only': bool, 'downloaded_only': bool,
    'required_series_type': str, 'excluded_series_type': str,
})
NonSonarrKwargs = TypedDict('NonSonarrKwargs', {
    'required_libraries': list[str], 'excluded_libraries': list[str],
    'required_tags': list[str], 'excluded_tags': list[str]
})

class Sync(Base):
    """
    SQL Table that defines a Sync. This contains Sync requirements and
    exclusions, as well as relational objects to linked Templates and
    Series.
    """

    __tablename__ = 'sync'

    # Referencial arguments
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interface_id: Mapped[int] = mapped_column(ForeignKey('connection.id'))

    connection: Mapped['Connection'] = relationship(back_populates='syncs')
    series: Mapped[list['Series']] = relationship(back_populates='sync')
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

    name: Mapped[str]
    interface: Mapped[SyncInterface] = mapped_column(String)

    required_tags: Mapped[list[str]] = mapped_column(JSON, default=[])
    required_libraries: Mapped[list[str]] = mapped_column(JSON, default=[])

    excluded_tags: Mapped[list[str]] = mapped_column(JSON, default=[])
    excluded_libraries: Mapped[list[str]] = mapped_column(JSON, default=[])

    downloaded_only: Mapped[bool] = mapped_column(default=False)
    monitored_only: Mapped[bool] = mapped_column(default=False)
    required_series_type: Mapped[Optional[str]]
    excluded_series_type: Mapped[Optional[str]]


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'Sync[{self.id}] {self.name}'


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


    @property
    def template_ids(self) -> list[int]:
        """
        ID's of any Templates associated with this Sync (rather than the
        ORM objects themselves).

        Returns:
            List of ID's for associated Templates.
        """

        return [template.id for template in self.templates]


    @property
    def sync_kwargs(self) -> Union[SonarrKwargs, NonSonarrKwargs]:
        """
        Keyword arguments for calling the Sync function of the Interface
        associated with this type of Sync - e.g. some implementation of
        `SyncInterface.get_all_series(**sync.sync_kwargs)`.

        Returns:
            Dictionary that can be unpacked in a call of the sync
            function.
        """

        if self.interface == 'Sonarr':
            return {
                'required_tags': self.required_tags,
                'excluded_tags': self.excluded_tags,
                'monitored_only': self.monitored_only,
                'downloaded_only': self.downloaded_only,
                'required_series_type': self.required_series_type,
                'excluded_series_type': self.excluded_series_type,
            }

        return {
            'required_libraries': self.required_libraries,
            'excluded_libraries': self.excluded_libraries,
            'required_tags': self.required_tags,
            'excluded_tags': self.excluded_tags,
        }
