from typing import Literal, TypedDict, Union

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.models.template import SyncTemplates


SyncInterface = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr']
SonarrKwargs = TypedDict('SonarrKwargs',{
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
    interface: SyncInterface = Column(String, nullable=False)

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


    @hybrid_property
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
