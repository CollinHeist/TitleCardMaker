from typing import Optional

from sqlalchemy import Boolean, Column, Integer, String, JSON
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship

from app.database.session import Base


class Connection(Base):
    """
    SQL Table that defines a connection to Emby, Jellyfin, Plex, or
    Sonarr. Not all types of connections care about or use all
    attributes.
    """

    __tablename__ = 'connection'

    id = Column(Integer, primary_key=True, index=True)

    series = relationship('Series', back_populates='data_source')
    syncs = relationship('Sync', back_populates='connection')
    templates = relationship('Template', back_populates='data_source')

    interface = Column(String, nullable=False)
    enabled = Column(Boolean, default=False, nullable=False)
    name = Column(String, nullable=False)

    url = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    use_ssl = Column(Boolean, default=True, nullable=False)

    username = Column(String, default=None)
    filesize_limit = Column(String, default='5 Megabytes')
    integrate_with_pmm = Column(Boolean, default=False, nullable=False)
    downloaded_only = Column(Boolean, default=True, nullable=False)
    libraries = Column(MutableList.as_mutable(JSON), default=[], nullable=False)


    @hybrid_property
    def log_str(self) -> str:
        """
        _summary_ # TODO populate

        Returns:
            _description_
        """

        return f'{self.interface}Connection[{self.id}]'


    @hybrid_property
    def filesize_limit_value(self) -> Optional[int]:
        """
        The filesize limit of this Connection - in Bytes.

        Returns:
            The filesize limit in Bytes, or None.
        """

        if self.filesize_limit is None:
            return None

        value, unit = self.filesize_limit.split(' ', maxsplit=1)

        return int(value) * {
            'bytes':     1,
            'kilobytes': 2**10,
            'megabytes': 2**20,
            'gigabytes': 2**30,
            'terabytes': 2**40,
        }[unit.lower()]


    @hybrid_property
    def interface_kwargs(self) -> dict:
        """
        The dictionary of keyword arguments required to initialize an
        Interface of this Connection's type. For example:

        >>> si = SonarrInterface(connection.interface_kwargs())

        Returns:
            Dictionary of keyword-arguments.
        """

        if self.interface in ('Emby', 'Jellyfin'):
            return {
                'interface_id': self.id,
                'url': self.url,
                'api_key': self.api_key,
                'use_ssl': self.use_ssl,
                'filesize_limit': self.filesize_limit_value,
                'username': self.username,
            }

        if self.interface == 'Plex':
            return {
                'interface_id': self.id,
                'url': self.url,
                'api_key': self.api_key,
                'use_ssl': self.use_ssl,
                'filesize_limit': self.filesize_limit_value,
                'integrate_with_pmm': self.integrate_with_pmm,
            }

        if self.interface == 'Sonarr':
            return {
                'interface_id': self.id,
                'url': self.url,
                'api_key': self.api_key,
                'use_ssl': self.use_ssl,
                'downloaded_only': self.downloaded_only,
                'libraries': self.libraries,   
            }
