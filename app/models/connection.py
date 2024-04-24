from typing import Literal, Optional, Union, TYPE_CHECKING

from sqlalchemy import String, JSON
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.schemas.connection import InterfaceType

if TYPE_CHECKING:
    from app.models.card import Card
    from app.models.loaded import Loaded
    from app.models.series import Series
    from app.models.sync import Sync
    from app.models.template import Template


SonarrLibraries = dict[Literal['interface_id', 'name', 'path'], Union[int, str]]


class Connection(Base):
    """
    SQL Table that defines a connection to Emby, Jellyfin, Plex, Sonarr,
    TMDb, or TVDb. Not all types of connections use all attributes.
    """

    __tablename__ = 'connection'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    cards: Mapped[list['Card']] = relationship(back_populates='connection')
    loaded: Mapped[list['Loaded']] = relationship(back_populates='connection')
    series: Mapped[list['Series']] = relationship(back_populates='data_source')
    syncs: Mapped[list['Sync']] = relationship(back_populates='connection')
    templates: Mapped[list['Template']] = relationship(back_populates='data_source')

    interface_type: Mapped[InterfaceType] = mapped_column(String)
    enabled: Mapped[bool] = mapped_column(default=False)
    name: Mapped[str]
    api_key: Mapped[str]

    url: Mapped[Optional[str]]
    use_ssl: Mapped[bool] = mapped_column(default=True)

    username: Mapped[Optional[str]]
    filesize_limit: Mapped[str] = mapped_column(default='5 Megabytes')
    integrate_with_pmm: Mapped[bool] = mapped_column(default=False)
    downloaded_only: Mapped[bool] = mapped_column(default=True)
    libraries: Mapped[list[SonarrLibraries]] = mapped_column(
        MutableList.as_mutable(JSON),
        default=[],
        nullable=False
    )

    minimum_dimensions: Mapped[Optional[str]]
    skip_localized: Mapped[bool] = mapped_column(default=True)
    logo_language_priority: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON),
        default=[],
        nullable=False
    )


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'{self.interface_type}Connection[{self.id}]'


    @property
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


    @property
    def minimum_width(self) -> Optional[int]:
        """
        The minimum width dimension of this Connection (in pixels).
        """

        if self.minimum_dimensions is None or self.interface_type != 'TMDb':
            return None

        return int(self.minimum_dimensions.split('x')[0])


    @property
    def minimum_height(self) -> Optional[int]:
        """
        The minimum width dimension of this Connection (in pixels).
        """

        if self.minimum_dimensions is None or self.interface_type != 'TMDb':
            return None

        return int(self.minimum_dimensions.split('x')[1])


    @property
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
                # PMM rebranded to Kometa; not worth Schema migration
                'integrate_with_kometa': self.integrate_with_pmm,
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

        if self.interface_type == 'TMDb':
            return {
                'api_key': self.api_key,
                'minimum_source_width': self.minimum_width,
                'minimum_source_height': self.minimum_height,
                'logo_language_priority': self.logo_language_priority,
            }

        return {}


    def determine_libraries(self, directory: str, /) -> list[tuple[int, str]]:
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


    def add_secrets(self, secret: set[str], /) -> None:
        """
        Add this Connection's secret details (the URL and API key) to
        the given set of secrets (for log redaction).

        Args:
            secret: Set of secrets to add to.
        """

        if self.url:
            secret.add(self.url)
        if self.api_key:
            secret.add(self.api_key)
