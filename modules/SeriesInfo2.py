from re import match, compile as re_compile
from typing import Iterable, Optional, Union

from plexapi.video import Show as PlexShow
from sqlalchemy import and_, literal, or_
from sqlalchemy.orm import Query

from modules.CleanPath import CleanPath
from modules.DatabaseInfoContainer import DatabaseInfoContainer, InterfaceID


class SeriesInfo(DatabaseInfoContainer):
    """
    This class encapsulates static information that is tied to a single
    Series.
    """

    """Regex to match name + year from given full name"""
    __FULL_NAME_REGEX = re_compile(r'^(.*?)\s+\((\d{4})\)$')

    __slots__ = (
        'name', 'year', 'emby_id', 'imdb_id', 'jellyfin_id', 'sonarr_id',
        'tmdb_id', 'tvdb_id', 'tvrage_id', 'match_titles', 'full_name',
        'match_name', 'full_match_name', 'clean_name', 'full_clean_name',
    )


    def __init__(self,
            name: str,
            year: Optional[int] = None,
            *,
            emby_id: Optional[int] = None,
            imdb_id: Optional[str] = None,
            jellyfin_id: Optional[str] = None,
            sonarr_id: Optional[str]  =None,
            tmdb_id: Optional[int] = None,
            tvdb_id: Optional[int] = None,
            tvrage_id: Optional[int] = None,
            match_titles: Optional[bool] = True,
        ) -> None:
        """
        Create a SeriesInfo object that defines a series described by
        all of  these attributes.

        Args:
            name: Name of the series. Can be just the name, or a full
                name of the series and year like "name (year)".
            year: Year of the series. Can be omitted if a year is
                provided from the name.
            emby_id: Emby ID of the series.
            imdb_id: IMDb ID of the series.
            jellyfin_id: Jellyfin ID of the series.
            sonarr_id: Sonarr ID of the series.
            tmdb_id: TMDb ID of the series.
            tvdb_id: TVDb ID of the series.
            tvrage_id: TVRage ID of the series.
            match_titles: Whether to match titles when comparing
                episodes for this series.

        Raises:
            ValueError: If no year is provided or one cannot be
                determined.
        """

        # Parse arguments into attributes
        self.name = name
        self.year = year
        self.emby_id = InterfaceID(emby_id, type_=str)
        self.imdb_id = None
        self.jellyfin_id = InterfaceID(jellyfin_id, type_=str)
        self.sonarr_id = InterfaceID(sonarr_id, type_=int)
        self.tmdb_id = None
        self.tvdb_id = None
        self.tvrage_id = None
        self.match_titles = match_titles

        self.set_imdb_id(imdb_id)
        self.set_tmdb_id(tmdb_id)
        self.set_tvdb_id(tvdb_id)
        self.set_tvrage_id(tvrage_id)

        # If no year was specified, parse from name as "name (year)"
        if (self.year is None
            and (group := match(self.__FULL_NAME_REGEX,self.name)) is not None):
            self.name = group.group(1)
            self.year = int(group.group(2))

        # If year still isn't specified, error
        if self.year is None:
            raise ValueError(f'Year not provided')

        self.year = int(self.year)
        self.update_name(self.name)


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        ret = '<SeriesInfo'
        for attr in self.__slots__:
            ret += f' {attr}={getattr(self, attr)!r}'

        return f'{ret}>'


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return self.full_name


    @staticmethod
    def from_series_infos(
            primary: 'SeriesInfo',
            *series_infos: tuple['SeriesInfo'],
        ) -> 'SeriesInfo':
        """
        Construct a SeriesInfo object from all the given objects. This
        takes `primary` as the base info (name, year, etc.), and then
        adds the IDs from the other infos.

        Args:
            primary: Base info.
            series_infos: Any number of infos whose IDs to utilize in
                the construction of the resulting SeriesInfo object.
                IDs are taken in priority sequentially.

        Returns:
            SeriesInfo object with the name/year of `primary`, but the
            combined IDs of all infos. 
        """

        series_info = SeriesInfo(
            primary.name, primary.year, emby_id=primary.emby_id,
            imdb_id=primary.imdb_id, jellyfin_id=primary.jellyfin_id,
            sonarr_id=primary.sonarr_id, tmdb_id=primary.tmdb_id,
            tvdb_id=primary.tvdb_id, tvrage_id=primary.tvrage_id,
            match_titles=primary.match_titles,
        )

        for info in series_infos:
            series_info.copy_ids(info)

        return SeriesInfo


    @staticmethod
    def from_plex_show(plex_show: PlexShow) -> 'SeriesInfo':
        """
        Create a SeriesInfo object from a plexapi Show object.

        Args:
            plex_show: Show to create an object from. Any available
                GUID's are utilized.

        Returns:
            SeriesInfo object encapsulating the given show.
        """

        # Create SeriesInfo for this show
        series_info = SeriesInfo(plex_show.title, plex_show.year)

        # Add any GUIDs as database ID's
        for guid in plex_show.guids:
            if 'imdb://' in guid.id:
                series_info.set_imdb_id(guid.id[len('imdb://'):])
            elif 'tmdb://' in guid.id:
                series_info.set_tmdb_id(int(guid.id[len('tmdb://'):]))
            elif 'tvdb://' in guid.id:
                series_info.set_tvdb_id(int(guid.id[len('tvdb://'):]))

        return series_info


    @property
    def characteristics(self) -> dict[str, Union[str, int]]:
        """Characteristics of this info to be used in Card creation."""

        return {
            'series_name': self.name,
            'series_year': self.year,
        }


    @property
    def ids(self) -> dict[str, Union[str, int]]:
        """Dictionary of IDs for this object."""

        return {
            'emby_id': str(self.emby_id),
            'imdb_id': self.imdb_id,
            'jellyfin_id': str(self.jellyfin_id),
            'sonarr_id': str(self.sonarr_id),
            'tmdb_id': self.tmdb_id,
            'tvdb_id': self.tvdb_id,
            'tvrage_id': self.tvrage_id,
        }


    def update_name(self, name: str) -> None:
        """
        Update all names for this series.

        Args:
            name: The new name of the series info.
        """

        # If the given name already has the year, remove it
        name = str(name)
        if (group := match(rf'^(.*?)\s+\({self.year}\)$', name)) is not None:
            self.name = group.group(1)
        else:
            self.name = name

        # Set full name
        self.full_name = f'{self.name} ({self.year})'

        # Set match names
        self.match_name = self.get_matching_title(self.name)
        self.full_match_name = self.get_matching_title(self.full_name)

        # Set folder-safe name
        self.clean_name = CleanPath.sanitize_name(self.name)
        self.full_clean_name =  CleanPath.sanitize_name(self.full_name)


    def set_emby_id(self, emby_id: int, interface_id: int) -> None:
        """Set this object's Emby ID - see `_update_attribute()`."""

        self._update_attribute('emby_id', emby_id, interface_id=interface_id)


    def set_imdb_id(self, imdb_id: str) -> None:
        """Set this object's IMDb ID - see `_update_attribute()`."""

        self._update_attribute('imdb_id', imdb_id, type_=str)


    def set_jellyfin_id(self, jellyfin_id: str, interface_id: int) -> None:
        """Set this object's Jellyfin ID - see `_update_attribute()`."""

        self._update_attribute(
            'jellyfin_id', jellyfin_id, interface_id=interface_id
        )


    def set_sonarr_id(self, sonarr_id: int, interface_id: int) -> None:
        """Set this object's Sonarr ID - see `_update_attribute()`."""

        self._update_attribute(
            'sonarr_id', sonarr_id, interface_id=interface_id
        )


    def set_tmdb_id(self, tmdb_id: int) -> None:
        """Set this object's TMDb ID - see `_update_attribute()`."""

        self._update_attribute('tmdb_id', tmdb_id, type_=int)


    def set_tvdb_id(self, tvdb_id: int) -> None:
        """Set this object's TVDb ID - see `_update_attribute()`."""

        self._update_attribute('tvdb_id', tvdb_id, type_=int)


    def set_tvrage_id(self, tvrage_id: int) -> None:
        """Set this object's TVRage ID - see `_update_attribute()`."""

        self._update_attribute('tvrage_id', tvrage_id, type_=int)


    @staticmethod
    def get_matching_title(text: str) -> str:
        """
        Remove all non A-Z characters from the given title.

        Args:
            text: The title to strip of special characters.

        Returns:
            The input `text` with all non A-Z characters removed.
        """

        return ''.join(filter(str.isalnum, text)).lower()


    def matches(self, *names: tuple[str]) -> bool:
        """
        Get whether any of the given names match this Series.

        Args:
            names: The names to check

        Returns:
            True if any of the given names match this series, False
            otherwise.
        """

        matching_names = map(self.get_matching_title, names)

        return any(name == self.match_name for name in matching_names)


    def filter_conditions(self,
            SeriesModel: 'sqlachemy.Model' # type: ignore
        ) -> Query:
        """
        Get the SQLAlchemy Query condition for this object.

        Args:
            SeriesModel: Series model to utilize for Query conditions.

        Returns:
            Query condition for this object. This includes an OR for any
            (non-None) database ID matches as well as a year+name match.
        """

        # Conditions to filter by database ID
        id_conditions = []
        if self.emby_id and hasattr(SeriesModel, 'emby_id'):
            id_str = str(self.emby_id)
            id_conditions.append(SeriesModel.emby_id.contains(id_str))
            id_conditions.append(literal(id_str).contains(SeriesModel.emby_id))
        if self.imdb_id is not None:
            id_conditions.append(SeriesModel.imdb_id==self.imdb_id)
        if self.jellyfin_id and hasattr(SeriesModel, 'jellyfin_id'):
            id_str = str(self.jellyfin_id)
            id_conditions.append(SeriesModel.jellyfin_id.contains(id_str))
            id_conditions.append(literal(id_str).contains(SeriesModel.jellyfin_id))
            id_conditions.append(SeriesModel.jellyfin_id==self.jellyfin_id)
        if self.sonarr_id and hasattr(SeriesModel, 'sonarr_id'):
            id_str = str(self.sonarr_id)
            id_conditions.append(SeriesModel.sonarr_id.contains(id_str))
            id_conditions.append(literal(id_str).contains(SeriesModel.sonarr_id))
        if self.tmdb_id is not None:
            id_conditions.append(SeriesModel.tmdb_id==self.tmdb_id)
        if self.tvdb_id is not None:
            id_conditions.append(SeriesModel.tvdb_id==self.tvdb_id)
        if self.tvrage_id is not None:
            id_conditions.append(SeriesModel.tvrage_id==self.tvrage_id)

        return or_(
            # Find by database ID
            or_(*id_conditions),
            # Find by title and year
            and_(SeriesModel.name==self.name, SeriesModel.year==self.year),
        )
