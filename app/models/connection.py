from typing import Literal, Optional, Union

from sqlalchemy import Boolean, Column, Integer, String, JSON
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship

from app.database.query import (
    EmbyInterface, JellyfinInterface, PlexInterface, SonarrInterface,
    TMDbInterface, get_interface
)
from app.database.session import Base
from app.schemas.connection import InterfaceType


SonarrLibraries = dict[Literal['interface_id', 'name', 'path'], Union[int, str]]


class Connection(Base):
    """
    SQL Table that defines a connection to Emby, Jellyfin, Plex, or
    Sonarr. Not all types of connections care about or use all
    attributes.
    """

    __tablename__ = 'connection'

    id = Column(Integer, primary_key=True, index=True)

    loaded = relationship('Loaded', back_populates='connection')
    series = relationship('Series', back_populates='data_source')
    syncs = relationship('Sync', back_populates='connection')
    templates = relationship('Template', back_populates='data_source')

    interface_type: InterfaceType = Column(String, nullable=False)
    enabled = Column(Boolean, default=False, nullable=False)
    name = Column(String, nullable=False)
    api_key = Column(String, nullable=False)

    url = Column(String, default=None, nullable=True)
    use_ssl = Column(Boolean, default=True, nullable=False)

    username = Column(String, default=None)
    filesize_limit = Column(String, default='5 Megabytes')
    integrate_with_pmm = Column(Boolean, default=False, nullable=False)
    downloaded_only = Column(Boolean, default=True, nullable=False)
    libraries: SonarrLibraries = Column(
        MutableList.as_mutable(JSON),
        default=[],
        nullable=False
    )

    minimum_dimensions = Column(String, default=None)
    skip_localized = Column(Boolean, default=True, nullable=False)
    logo_language_priority: list[str] = Column(
        MutableList.as_mutable(JSON),
        default=[],
        nullable=False
    )


    @hybrid_property
    def log_str(self) -> str:
        """
        Loggable string that defines this object (i.e. `__repr__`).
        """

        return f'{self.interface_type}Connection[{self.id}]'


    @hybrid_property
    def filesize_limit_value(self) -> Optional[int]:
        """
        The filesize limit of this Connection - in Bytes (or None).
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
    def minimum_width(self) -> Optional[int]:
        """
        The minimum width dimension of this Connection (in pixels).
        """

        if self.minimum_dimensions is None or self.interface_type != 'TMDb':
            return None

        return self.minimum_dimensions.split('x')[0]


    @hybrid_property
    def minimum_height(self) -> Optional[int]:
        """
        The minimum width dimension of this Connection (in pixels).
        """

        if self.minimum_dimensions is None or self.interface_type != 'TMDb':
            return None

        return self.minimum_dimensions.split('x')[1]


    @hybrid_property
    def interface_kwargs(self) -> dict:
        """
        The dictionary of keyword arguments required to initialize an
        Interface of this Connection's type. For example:

        >>> si = SonarrInterface(connection.interface_kwargs())

        Returns:
            Dictionary of keyword-arguments.
        """

        if self.interface_type in ('Emby', 'Jellyfin'):
            return {
                'interface_id': self.id,
                'url': self.url,
                'api_key': self.api_key,
                'use_ssl': self.use_ssl,
                'filesize_limit': self.filesize_limit_value,
                'username': self.username,
            }

        if self.interface_type == 'Plex':
            return {
                'interface_id': self.id,
                'url': self.url,
                'api_key': self.api_key,
                'use_ssl': self.use_ssl,
                'filesize_limit': self.filesize_limit_value,
                'integrate_with_pmm': self.integrate_with_pmm,
            }

        if self.interface_type == 'Sonarr':
            return {
                'interface_id': self.id,
                'url': self.url,
                'api_key': self.api_key,
                'use_ssl': self.use_ssl,
                'downloaded_only': self.downloaded_only,
                'libraries': self.libraries,   
            }


    @hybrid_property
    def interface(self) -> Union[EmbyInterface, JellyfinInterface,
                                 PlexInterface, SonarrInterface, TMDbInterface]:
        """
        Get the `Interface` object to actually communicate with this
        Connection's interface.
        """

        return get_interface(self.id)


    def determine_libraries(self,
            directory: str,
        ) -> list[tuple[int, str]]:
        """
        Determine the libraries of the series in the given directory.
        >>> connection.libraries = [
            {'interface_id': 2, 'name': 'TV', 'path': '/mnt/media/tv'},
            {'interface_id': 3, 'name': 'TV 4K', 'path': '/mnt/media/tv'},
            {'interface_id': 3, 'name': 'Anime', 'path': '/mnt/media/anime'},
        ]
        >>> connection.determine_libraries('/mnt/media/tv/Series (1999)')
        [(2, 'TV'), (3, 'TV 4K')]

        Args:
            directory: Directory whose library is being determined.

        Returns:
            List of tuples of the interface ID and the library names
            that are associated with the given directory.
        """

        return [
            (library['interface_id'], library['name'])
            for library in self.libraries
            if directory.startswith(library['path'])
        ]
