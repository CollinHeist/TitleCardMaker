from datetime import datetime
from logging import Logger
from typing import TYPE_CHECKING, Optional, TypedDict, Union

from plexapi.video import Episode as PlexEpisode
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Query

from modules.Debug import log
from modules.DatabaseInfoContainer import DatabaseInfoContainer, InterfaceID
from modules.Title import Title

if TYPE_CHECKING:
    from app.models.episode import Episode

# pylint: disable=missing-class-docstring
class UserData(TypedDict):
    Played: Optional[bool]

class EmbyProviderIDs(TypedDict):
    Imdb: Optional[str]
    Tmdb: Optional[int]
    Tvdb: Optional[int]
    TvRage: Optional[int]

class EmbyEpisodeDict(TypedDict):
    Name: str
    ParentIndexNumber: int
    IndexNumber: int
    Id: int
    ProviderIds: EmbyProviderIDs
    PremiereDate: str
    UserData: UserData

class EpisodeDatabaseIDs(TypedDict):
    emby_id: int
    imdb_id: str
    jellyfin_id: str
    tmdb_id: int
    tvdb_id: int
    tvrage_id: int

class EpisodeCharacteristics(TypedDict, total=False):
    season_number: int
    episode_number: int
    absolute_number: Optional[int]
    absolute_episode_number: int
    airdate: Optional[datetime]

class EpisodeIndices(TypedDict):
    season_number: int
    episode_number: int
    absolute_number: Optional[int]
# pylint: enable=missing-class-docstring


class EpisodeInfo(DatabaseInfoContainer):
    """
    This class describes static information about an Episode, such as
    the season, episode, and absolute number, as well as the various IDs
    associated with it.
    """

    __slots__ = (
        'title', 'season_number', 'episode_number', 'absolute_number',
        'emby_id', 'imdb_id', 'jellyfin_id', 'tmdb_id', 'tvdb_id', 'tvrage_id',
        'airdate',
    )


    def __init__(self,
            title: Union[str, Title],
            season_number: int,
            episode_number: int,
            absolute_number: Optional[int] = None,
            *,
            emby_id: Optional[int] = None,
            imdb_id: Optional[str] = None,
            jellyfin_id: Optional[str] = None,
            tmdb_id: Optional[int] = None,
            tvdb_id: Optional[int] = None,
            tvrage_id: Optional[int] = None,
            airdate: Optional[datetime] = None,
        ) -> None:
        """
        Initialize this object with the given title, indices, database
        ID's, airdate.
        """

        # Ensure title is Title object
        if isinstance(title, Title):
            self.title = title
        else:
            self.title = Title(title)

        # Store arguments as attributes
        self.season_number = int(season_number)
        self.episode_number = int(episode_number)
        self.absolute_number = None if absolute_number is None else int(absolute_number)
        self.airdate = airdate

        self.emby_id = InterfaceID(emby_id, type_=int, libraries=True)
        self.imdb_id: Optional[str] = None
        self.jellyfin_id = InterfaceID(jellyfin_id, type_=str, libraries=True)
        self.tmdb_id: Optional[str] = None
        self.tvdb_id: Optional[int] = None
        self.tvrage_id: Optional[int] = None

        self.set_imdb_id(imdb_id)
        self.set_tmdb_id(tmdb_id)
        self.set_tvdb_id(tvdb_id)
        self.set_tvrage_id(tvrage_id)


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        attributes = ', '.join(f'{attr}={getattr(self, attr)!r}'
            for attr in self.__slots__
            if not attr.startswith('__')
        )

        return f'<EpisodeInfo {attributes}>'


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'S{self.season_number:02}E{self.episode_number:02}'


    def __eq__(self, other: 'EpisodeInfo') -> bool:
        """
        Returns whether the given EpisodeInfo object corresponds to the
        same entry (has the same season and episode index).

        Args:
            other: EpisodeInfo object to compare.

        Returns:
            True if the season and episode number of the two objects
            match,  False otherwise.
        """

        # Verify the comparison is another EpisodeInfo object
        if not isinstance(other, EpisodeInfo):
            raise TypeError(
                f'Can only compare equality between EpisodeInfo objects'
            )

        # ID matches are immediate equality
        for id_attr in ('emby_id', 'imdb_id', 'jellyfin_id', 'tmdb_id',
                        'tvdb_id', 'tvrage_id'):
            if (getattr(self, id_attr) is not None
                and getattr(self, id_attr) == getattr(other, id_attr)):
                return True

        # Require title match
        return (
            self.season_number == other.season_number
            and self.episode_number == other.episode_number
            and self.title.matches(other.title)
        )


    @staticmethod
    def from_emby_info(
            info: EmbyEpisodeDict,
            interface_id: int,
            library_name: str,
        ) -> 'EpisodeInfo':
        """
        Create an EpisodeInfo object from the given emby episode data.

        Args:
            info: Dictionary of episode info.
            interface_id: ID of the Emby interface whose data is being
                parsed.
            library_name: Name of the library associated with this
                Series.

        Returns:
            EpisodeInfo object defining the given data.
        """

        # Parse airdate
        airdate = None
        try:
            airdate = datetime.strptime(
                info['PremiereDate'], '%Y-%m-%dT%H:%M:%S.%f000000Z'
            )
        except Exception as e:
            log.exception(f'Cannot parse airdate', e)
            log.debug(f'Episode data: {info}')

        return EpisodeInfo(
            info['Name'],
            info['ParentIndexNumber'],
            info['IndexNumber'],
            emby_id=f'{interface_id}:{library_name}:{info["Id"]}',
            imdb_id=info['ProviderIds'].get('Imdb'),
            tmdb_id=info['ProviderIds'].get('Tmdb'),
            tvdb_id=info['ProviderIds'].get('Tvdb'),
            tvrage_id=info['ProviderIds'].get('TvRage'),
            airdate=airdate,
        )


    @staticmethod
    def from_jellyfin_info(
            info: EmbyEpisodeDict,
            interface_id: int,
            library_name: str,
            *,
            log: Logger = log,
        ) -> 'EpisodeInfo':
        """
        Create an EpisodeInfo object from the given Jellyfin episode
        data.

        Args:
            info: Dictionary of episode info.
            interface_id: ID of the Jellyfin interface whose data is
                being parsed.
            library_name: Name of the library associated with this
                Series.
            log: Logger for all log messages.

        Returns:
            EpisodeInfo object defining the given data.
        """

        # Parse airdate
        airdate = None
        if 'PremiereDate' in info:
            try:
                airdate = datetime.strptime(
                    info['PremiereDate'], '%Y-%m-%dT%H:%M:%S.%f000000Z'
                )
            except Exception as e:
                log.debug(f'Cannot parse airdate {e} - {info=}')

        return EpisodeInfo(
            info['Name'],
            info['ParentIndexNumber'],
            info['IndexNumber'],
            imdb_id=info['ProviderIds'].get('Imdb'),
            jellyfin_id=f'{interface_id}:{library_name}:{info["Id"]}',
            tmdb_id=info['ProviderIds'].get('Tmdb'),
            tvdb_id=info['ProviderIds'].get('Tvdb'),
            tvrage_id=info['ProviderIds'].get('TvRage'),
            airdate=airdate,
        )


    @staticmethod
    def from_plex_episode(plex_episode: PlexEpisode) -> 'EpisodeInfo':
        """
        Create an EpisodeInfo object from a `plexapi.video.Episode`
        object.

        Args:
            plex_episode: Episode to create an object from. Any
                available GUID's are utilized.

        Returns:
            EpisodeInfo object encapsulating the given Episode.
        """

        # Create EpisodeInfo for this Episode
        episode_info = EpisodeInfo(
            plex_episode.title, plex_episode.parentIndex, plex_episode.index,
            airdate=plex_episode.originallyAvailableAt
        )

        # Add any GUIDs as database ID's
        for guid in plex_episode.guids:
            if 'imdb://' in guid.id:
                episode_info.set_imdb_id(guid.id[len('imdb://'):])
            elif 'tmdb://' in guid.id:
                episode_info.set_tmdb_id(int(guid.id[len('tmdb://'):]))
            elif 'tvdb://' in guid.id:
                episode_info.set_tvdb_id(int(guid.id[len('tvdb://'):]))

        return episode_info


    @property
    def key(self) -> str:
        """Key for this episode - i.e. s1e1"""

        return f's{self.season_number}e{self.episode_number}'


    @property
    def index_str(self) -> str:
        """Index string for this episode - i.e. S01E01"""

        return f'S{self.season_number:02}E{self.episode_number:02}'


    @property
    def has_all_ids(self) -> bool:
        """Whether this object has all ID's defined"""

        return all(self.ids.values())


    @property
    def ids(self) -> EpisodeDatabaseIDs:
        """This object's ID's (as a dictionary)"""

        return {
            'emby_id': str(self.emby_id),
            'imdb_id': self.imdb_id,
            'jellyfin_id': str(self.jellyfin_id),
            'tmdb_id': self.tmdb_id,
            'tvdb_id': self.tvdb_id,
            'tvrage_id': self.tvrage_id,
        }


    @property
    def characteristics(self) -> EpisodeCharacteristics:
        """
        Get the characteristics of this object for formatting.

        Returns:
            Dictionary of characteristics that define this object. Keys
            are the indices of the episode in numeric, cardinal, and
            ordinal form.
        """

        if self.absolute_number is None:
            effective_absolute = self.episode_number
        else:
            effective_absolute = self.absolute_number

        return {
            'season_number': self.season_number,
            'episode_number': self.episode_number,
            'absolute_number': self.absolute_number,
            'absolute_episode_number': effective_absolute,
            'airdate': self.airdate,
        }


    @property
    def indices(self) -> EpisodeIndices:
        """This object's season/episode indices (as a dictionary)"""

        return {
            'season_number': self.season_number,
            'episode_number': self.episode_number,
            'absolute_number': self.absolute_number,
        }


    def set_emby_id(self,
            emby_id: int,
            interface_id: int,
            library_name: str,
        ) -> None:
        """Set the Emby ID of this object. See `_update_attribute()`."""

        self._update_attribute(
            'emby_id', emby_id,
            interface_id=interface_id, library_name=library_name,
        )


    def set_imdb_id(self, imdb_id: str) -> None:
        """Set the IMDb ID of this object. See `_update_attribute()`."""

        self._update_attribute('imdb_id', imdb_id, str)


    def set_jellyfin_id(self,
            jellyfin_id: str,
            interface_id: int,
            library_name: str,
        ) -> None:
        """Set the Jellyfin ID of this object. See `_update_attribute()`."""

        self._update_attribute(
            'jellyfin_id', jellyfin_id,
            interface_id=interface_id, library_name=library_name,
        )


    def set_tmdb_id(self, tmdb_id) -> None:
        """Set the TMDb ID of this object. See `_update_attribute()`."""

        self._update_attribute('tmdb_id', tmdb_id, int)


    def set_tvdb_id(self, tvdb_id) -> None:
        """Set the TVDb ID of this object. See `_update_attribute()`."""

        self._update_attribute('tvdb_id', tvdb_id, int)


    def set_tvrage_id(self, tvrage_id) -> None:
        """Set the TVRage ID of this object. See `_update_attribute()`."""

        self._update_attribute('tvrage_id', tvrage_id, int)


    def set_airdate(self, airdate: datetime) -> None:
        """Set the airdate of this object. See `_update_attribute()`."""

        self._update_attribute('airdate', airdate)


    def filter_conditions(self, EpisodeModel: 'Episode') -> Query:
        """
        Get the SQLAlchemy Query condition for this object.

        Args:
            EpisodeModel: Episode model to utilize for Query conditions.

        Returns:
            Query condition for this object. This includes an OR for any
            (non-None) database ID matches as well as an index and title
            match.
        """

        # Conditions to filter by database ID
        id_conditions = []
        if self.emby_id:
            id_conditions.append(func.regex_match(
                f'(?:^|\D){self.emby_id}(?!\d)', EpisodeModel.emby_id,
            ))
        if self.imdb_id is not None:
            id_conditions.append(EpisodeModel.imdb_id==self.imdb_id)
        if self.jellyfin_id:
            id_conditions.append(func.regex_match(
                f'(?:^|\D){self.jellyfin_id}(?!\d)', EpisodeModel.jellyfin_id,
            ))
        if self.tmdb_id is not None:
            id_conditions.append(EpisodeModel.tmdb_id==self.tmdb_id)
        if self.tvdb_id is not None:
            id_conditions.append(EpisodeModel.tvdb_id==self.tvdb_id)
        if self.tvrage_id is not None:
            id_conditions.append(EpisodeModel.tvrage_id==self.tvrage_id)

        # If >1 ID condition is present, require any two ID match to
        # prevent failed matches caused by single ID collision
        conditions = []
        if len(id_conditions) >= 2:
            for i, condition in enumerate(id_conditions):
                for j in range(i + 1, len(id_conditions)):
                    conditions.append(and_(condition, id_conditions[j]))
        else:
            conditions = id_conditions

        return or_(
            # Find by database ID
            or_(*conditions),
            # Find by index and title
            and_(
                EpisodeModel.season_number==self.season_number,
                EpisodeModel.episode_number==self.episode_number,
                EpisodeModel.title==self.title.full_title,
            ),
        )
