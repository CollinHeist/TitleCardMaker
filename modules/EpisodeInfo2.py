from datetime import datetime
from logging import Logger
from typing import Optional, TypedDict, Union

from num2words import num2words
from plexapi.video import Episode as PlexEpisode
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Query
from titlecase import titlecase

from modules.Debug import log
from modules.DatabaseInfoContainer import DatabaseInfoContainer, InterfaceID
from modules.Title import Title


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

class WordSet(dict):
    """
    Dictionary subclass that contains keys for translated word-versions
    of numbers.

    >>> word_set = WordSet()
    >>> word_set.add_numeral('season_number', 4)
    >>> print(word_set)
    {'season_number_cardinal': 'four', 'season_number_ordinal': 'fourth'}
    >>> word_set.add_numeral('absolute_number', 2, 'es')
    {'season_number_cardinal': 'four',
     'season_number_ordinal': 'fourth',
     'absolute_number_cardinal_es': 'dos',
     'absolute_number_ordinal_es': 'segundo'}
    """

    def add_numeral(self,
            label: str,
            number: Optional[int],
            lang: Optional[str] = None,
        ) -> None:
        """
        Add the cardinal and ordinal versions of the given number under
        the given label.

        Args:
            label: Label key to add the converted number under.
            number: Number to wordify and add into this object.
            lang: Language to wordify the object into. Appended to any
                added keys.
        """

        # If value is None, do nothing
        if number is None:
            return None

        # If a specific language was indicated, use in conversion
        if lang:
            # Catch exceptions caused by an unsupported language
            try:
                cardinal = num2words(number, to='cardinal', lang=lang)
                self.update({
                    f'{label}_cardinal_{lang}': cardinal,
                    f'{label}_cardinal_{lang}_title': titlecase(cardinal),
                })
            except NotImplementedError:
                pass
            try:
                ordinal = num2words(number, to='ordinal', lang=lang)
                self.update({
                    f'{label}_ordinal_{lang}': ordinal,
                    f'{label}_ordinal_{lang}_title': titlecase(ordinal),
                })
            except NotImplementedError:
                pass
        # No language indicated, convert using base language
        else:
            cardinal = num2words(number, to='cardinal')
            ordinal = num2words(number, to='ordinal')
            self.update({
                f'{label}_cardinal': cardinal,
                f'{label}_cardinal_title': f'{titlecase(cardinal)}',
                f'{label}_ordinal': ordinal,
                f'{label}_ordinal_title': titlecase(ordinal),
            })

        return None


    def has_number(self, label: str, lang: Optional[str] = None) -> bool:
        """
        Whether this object has defined translations for the given label
        and language combination.

        Args:
            label: Label key of the converted numbers.
            lang: Language of the converted numbers.

        Returns:
            True if the cardinal and ordinal translations are defined
            for this label and language; False otherwise.
        """

        if lang:
            return (
                f'{label}_cardinal_{lang}' in self
                and f'{label}_ordinal_{lang}' in self
            )

        return f'{label}_cardinal' in self and f'{label}_ordinal' in self


class EpisodeInfo(DatabaseInfoContainer):
    """
    This class describes static information about an Episode, such as
    the season, episode, and absolute number, as well as the various IDs
    associated with it.
    """

    __slots__ = (
        'title', 'season_number', 'episode_number', 'absolute_number',
        'emby_id', 'imdb_id', 'jellyfin_id', 'tmdb_id', 'tvdb_id', 'tvrage_id',
        'airdate', '__languages', '__word_set',
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
            languages: list[str] = [],
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

        # Store default database ID's
        self.emby_id = InterfaceID(emby_id, type_=int, libraries=True)
        self.imdb_id = None
        self.jellyfin_id = InterfaceID(jellyfin_id, type_=str, libraries=True)
        self.tmdb_id = None
        self.tvdb_id = None
        self.tvrage_id = None

        # Update each ID
        self.set_imdb_id(imdb_id)
        self.set_tmdb_id(tmdb_id)
        self.set_tvdb_id(tvdb_id)
        self.set_tvrage_id(tvrage_id)

        # Add word variations for each of this episode's indices
        self.__languages = languages + [None]
        self.__word_set = WordSet()


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


    @property
    def word_set(self) -> WordSet[str, str]:
        """
        The WordSet for this object. This constructs the translations of
        the season, episode, and absolute numbers if not already
        present.
        """

        # Get fallback absolute number
        if self.absolute_number is None:
            absolute_episode = self.episode_number
        else:
            absolute_episode = self.absolute_number

        # Add words for the season, episode, absolute, and fallback abs numbers
        number_sets = (
            ('season_number', self.season_number),
            ('episode_number', self.episode_number),
            ('absolute_number', self.absolute_number),
            ('absolute_episode_number', absolute_episode),
        )

        for lang in self.__languages:
            for label, number in number_sets:
                if not self.__word_set.has_number(label, lang):
                    self.__word_set.add_numeral(label, number, lang=lang)

        return self.__word_set


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
        """Index key for this EpisodeInfo - i.e. s1e1"""

        return f's{self.season_number}e{self.episode_number}'


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
            **self.word_set,
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


    def filter_conditions(self,
            EpisodeModel: 'sqlachemy.Model', # type: ignore
        ) -> Query:
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
                f'^{self.emby_id}$', EpisodeModel.emby_id,
            ))
        if self.imdb_id is not None:
            id_conditions.append(EpisodeModel.imdb_id==self.imdb_id)
        if self.jellyfin_id:
            id_conditions.append(func.regex_match(
                f'^{self.jellyfin_id}$', EpisodeModel.jellyfin_id,
            ))
        if self.tmdb_id is not None:
            id_conditions.append(EpisodeModel.tmdb_id==self.tmdb_id)
        if self.tvdb_id is not None:
            id_conditions.append(EpisodeModel.tvdb_id==self.tvdb_id)
        if self.tvrage_id is not None:
            id_conditions.append(EpisodeModel.tvrage_id==self.tvrage_id)

        return or_(
            # Find by database ID
            or_(*id_conditions),
            # Find by index and title
            and_(
                EpisodeModel.season_number==self.season_number,
                EpisodeModel.episode_number==self.episode_number,
                EpisodeModel.title==self.title.full_title,
            ),
        )
