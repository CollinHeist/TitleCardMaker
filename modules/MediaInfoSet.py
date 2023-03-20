from typing import Any

from tinydb import where, Query

from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo
from modules.PersistentDatabase import PersistentDatabase
from modules.SeriesInfo import SeriesInfo

class MediaInfoSet:
    """
    This class describes a set of media info; notably SeriesInfo and EpisodeInfo
    objects. This object can be viewed as an interface to creating and getting
    these objects, so that database ID's can be preserved between instances of
    Show and Episode objects.

    This class keeps a PersistentDatabase of Series ID's, but a volatile one of
    EpisodeInfo objects that is created and updated in RAM at runtime.
    """


    def __init__(self) -> None:
        """
        Construct a new instance of the MediaInfoSet. This creates empty
        dictionaries that map various identifiers (like names or ID's) to Info
        objects.
        """

        # Database of full names and database ID's
        self.series_info_db = PersistentDatabase('series_infos.json')

        # Dictionary mapping various database keys to EpisodeInfo objects
        self.episode_info: dict[str, EpisodeInfo] = {}


    @staticmethod
    def __test_id_match(db_value: Any, search_value: Any) -> bool:
        """
        Determine whether the given ID's match for filtering.

        Args:
            db_value: Existing value from the ID database.
            search_value: New value to potentially store in the ID database.

        Returns:
            True if the row indicated by these ID's should be included (NOT
            filtered out); False if the row should be excluded (filted out).
        """

        # None indicates unquerable, do not filter out
        if db_value is None or search_value is None: return True
        # Both values are populated, filter on equality
        return db_value == search_value


    def __series_info_condition(self, full_name: str, emby_id: str,
            imdb_id: str, jellyfin_id: str, sonarr_id: int, tmdb_id: int,
            tvdb_id: int, tvrage_id: int) -> Query:
        """
        Get the Query condition associated with the given SeriesInfo attributes.

        Args:
            All SeriesInfo arguments.

        Returns:
            Query that filters the SeriesInfo database for any matching series
            indicated by the given arguments.
        """

        return (
            (where('full_name') == full_name) &
            Query().emby_id.test(self.__test_id_match, emby_id) &
            Query().imdb_id.test(self.__test_id_match, imdb_id) &
            Query().jellyfin_id.test(self.__test_id_match, jellyfin_id) &
            Query().sonarr_id.test(self.__test_id_match, sonarr_id) &
            Query().tmdb_id.test(self.__test_id_match, tmdb_id) &
            Query().tvdb_id.test(self.__test_id_match, tvdb_id) &
            Query().tvrage_id.test(self.__test_id_match, tvrage_id)
        )


    def get_series_info(self, name: str=None, year: int=None, *,
            emby_id: str=None,
            imdb_id: str=None,
            jellyfin_id: str=None,
            sonarr_id: int=None,
            tmdb_id: int=None,
            tvdb_id: int=None,
            tvrage_id: int=None,
            match_titles: bool=True) -> SeriesInfo:
        """
        Get the SeriesInfo object indicated by the given attributes.
        This looks for an existing object mapped under any of the given
        details; if none exists, a new SeriesInfo object is created with
        the given details.

        Args:
            name: The name of the series. Optional if the associated 
                object already exists.
            year: The year of the series. Optional if the associated 
                object already exists.
            *_id: Optional database ID's.

        Returns:
            The SeriesInfo object indicated by the given attributes.
        """

        # Get condition to search for this series in the database
        full_name = SeriesInfo(name, year).full_name
        condition = self.__series_info_condition(
            full_name, emby_id, imdb_id, jellyfin_id, sonarr_id, tmdb_id,
            tvdb_id, tvrage_id
        )

        # Series doesn't exist, create new info, insert into database, return
        if not (info := self.series_info_db.search(condition)):
            series_info = SeriesInfo(
                name, year, emby_id=emby_id, imdb_id=imdb_id,
                jellyfin_id=jellyfin_id, sonarr_id=sonarr_id, tmdb_id=tmdb_id,
                tvdb_id=tvdb_id, tvrage_id=tvrage_id, match_titles=match_titles
            )

            self.series_info_db.insert({
                'full_name': full_name, 'emby_id': emby_id, 'imdb_id': imdb_id,
                'jellyfin_id': jellyfin_id, 'sonarr_id': sonarr_id,
                'tmdb_id': tmdb_id, 'tvdb_id': tvdb_id, 'tvrage_id': tvrage_id, 
            })

            return series_info
        
        # Info for this series already exists
        # Check if multiple matches were returned (somehow)
        if len(info) > 1:
            log.warning(f'Multiple matches for existing SeriesInfo: {info}')
        info = info[0]

        # Update database only with ID's that are more accurate
        update_data = {}
        if info['emby_id'] is None and emby_id is not None:
            update_data |= {'emby_id': emby_id}
        if info['imdb_id'] is None and imdb_id is not None:
            update_data |= {'imdb_id': imdb_id}
        if info['jellyfin_id'] is None and jellyfin_id is not None:
            update_data |= {'jellyfin_id': jellyfin_id}
        if info['sonarr_id'] is None and sonarr_id is not None:
            update_data |= {'sonarr_id': sonarr_id}
        if info['tmdb_id'] is None and tmdb_id is not None:
            update_data |= {'tmdb_id': tmdb_id}
        if info['tvdb_id'] is None and tvdb_id is not None:
            update_data |= {'tvdb_id': tvdb_id}
        if info['tvrage_id'] is None and tvrage_id is not None:
            update_data |= {'tvrage_id': tvrage_id}
            
        # Update database, re-query for finalized data
        if update_data:
            log.debug(f'Updating SeriesInfo database.. {update_data=}')
            self.series_info_db.upsert(update_data, condition)
            info = self.series_info_db.get(condition)

        # Return SeriesInfo created from finalized data
        return SeriesInfo(
            name, year,
            emby_id=info['emby_id'],
            imdb_id=info['imdb_id'],
            jellyfin_id=info['jellyfin_id'],
            sonarr_id=info['sonarr_id'],
            tmdb_id=info['tmdb_id'],
            tvdb_id=info['tvdb_id'],
            tvrage_id=info['tvrage_id'],
            match_titles=match_titles,
        )


    def __set_series_id(self, id_type: str, series_info: SeriesInfo,
            id_: Any) -> None:
        """
        Set the series ID within this object's database and on the given
        SeriesInfo object.

        Args:
            id_type: Descriptive string of the ID type being set - e.g.
                'emby', 'imdb', etc.
            series_info: SeriesInfo object to update the ID of.
            id_: Associated ID to store.
        """

        # If the ID is invalid, skip
        existing = getattr(series_info, f'{id_type}_id')
        if id_ is None or id_ == 0 or existing is not None or existing == id_:
            return None

        # Update series info object with the given ID
        getattr(series_info, f'set_{id_type}_id')(id_)

        # Update database
        self.series_info_db.upsert({
                'full_name': series_info.full_name,
                'emby_id': series_info.emby_id,
                'imdb_id': series_info.imdb_id,
                'jellyfin_id': series_info.jellyfin_id,
                'sonarr_id': series_info.sonarr_id,
                'tmdb_id': series_info.tmdb_id,
                'tvdb_id': series_info.tvdb_id,
                'tvrage_id': series_info.tvrage_id, 
            },
            self.__series_info_condition(
                series_info.full_name, series_info.emby_id, series_info.imdb_id,
                series_info.jellyfin_id, series_info.sonarr_id,
                series_info.tmdb_id, series_info.tvdb_id, series_info.tvrage_id
            )
        )


    def set_emby_id(self, series_info: SeriesInfo, id_: str) -> None:
        self.__set_series_id('emby', series_info, id_)

    def set_imdb_id(self, series_info: SeriesInfo, id_: str) -> None:
        self.__set_series_id('imdb', series_info, id_)

    def set_jellyfin_id(self, series_info: SeriesInfo, id_: str) -> None:
        self.__set_series_id('jellyfin', series_info, id_)

    def set_sonarr_id(self, series_info: SeriesInfo, id_: str) -> None:
        self.__set_series_id('sonarr', series_info, id_)

    def set_tmdb_id(self, series_info: SeriesInfo, id_: str) -> None:
        self.__set_series_id('tmdb', series_info, id_)

    def set_tvdb_id(self, series_info: SeriesInfo, id_: str) -> None:
        self.__set_series_id('tvdb', series_info, id_)

    def set_tvrage_id(self, series_info: SeriesInfo, id_: str) -> None:
        self.__set_series_id('tvrage', series_info, id_)


    @staticmethod
    def __get_episode_info_storage_keys(series_info: SeriesInfo, season_number,
            episode_number, emby_id, imdb_id, jellyfin_id, tmdb_id, tvdb_id,
            tvrage_id) -> list[str]:
        """
        Get the keys to update within the EpisodeInfo map for the given data.

        Args:
            All arguments are EpisodeInfo data.

        Returns:
            List of storage keys for the episode_info map. Only keys where the
            associated data is non-None are returned.
        """

        new_keys = [
            f'title:{series_info.full_name}:{season_number}:{episode_number}'
        ]
        new_keys += [] if emby_id is None else [f'emby:{emby_id}']
        new_keys += [] if imdb_id is None else [f'imdb:{imdb_id}']
        new_keys += [] if jellyfin_id is None else [f'jellyfin:{jellyfin_id}']
        new_keys += [] if tmdb_id is None else [f'tmdb:{tmdb_id}']
        new_keys += [] if tvdb_id is None else [f'tvdb:{tvdb_id}']
        new_keys += [] if tvrage_id is None else [f'tvrage:{tvrage_id}']

        return new_keys


    def get_episode_info(self, series_info: SeriesInfo, title: str,
            season_number: int, episode_number: int, abs_number: int=None, *,
            emby_id: str=None, imdb_id: str=None, jellyfin_id: str=None,
            tmdb_id: int=None, tvdb_id: int=None, tvrage_id: int=None,
            airdate: 'datetime'=None, title_match: bool=True,
            **queried_kwargs: dict) -> EpisodeInfo:
        """
        Get the EpisodeInfo object indicated by the given attributes.

        Args:
            series_info: Parent SeriesInfo object for the EpisodeInfo object.
            title: The title of the episode.
            season_number: Season number of the episode.
            episode_number: Episode number of the episode.
            abs_number: Optional absolute number of the episode.
            emby_id: (Keyword only) Optional Emby ID.
            imdb_id: (Keyword only) Optional IMDb ID.
            jellyfin_id: (Keyword only) Optional Jellyfin ID.
            tmdb_id: (Keyword only) Optional TMDb ID.
            tvdb_id: (Keyword only) Optional TVDb ID.
            tvrage_id: (Keyword only) Optional TVRage ID.
            airdate: (Keyword only) Optional airdate of the episode
            queried_kwargs: Any queried_{interface} keyword arguments.

        Returns:
            The EpisodeInfo object indicated by the given attributes. This
            object is updated with any provided database ID's, the airdate, or
            queried keywords. The object is either new (if no matching entry)
            was found; or an updated existing object (if match was found).
        """

        # Get keys to update the EpisodeInfo map with
        update_keys = self.__get_episode_info_storage_keys(
            series_info, season_number, episode_number, emby_id, imdb_id,
            jellyfin_id, tmdb_id, tvdb_id, tvrage_id
        )
        index_key = update_keys[0]

        # Query by TVDb -> IMDb -> TMDb -> Emby -> TVRage -> Index+?Title
        if tvdb_id and (info := self.episode_info.get(f'tvdb:{tvdb_id}')):
            pass
        elif imdb_id and (info := self.episode_info.get(f'imdb:{imdb_id}')):
            pass
        elif jellyfin_id and (info := self.episode_info.get(f'jellyfin:{jellyfin_id}')):
            pass
        elif tmdb_id and (info := self.episode_info.get(f'tmdb:{tmdb_id}')):
            pass
        elif emby_id and (info := self.episode_info.get(f'emby:{emby_id}')):
            pass
        elif tvrage_id and (info := self.episode_info.get(f'tvrage:{tvrage_id}')):
            pass
        elif ((info := self.episode_info.get(index_key))
            and (not title_match
                 or (title_match and info.title.matches(title)))):
            pass
        # No existing EpisodeInfo, create new one
        else:
            info = EpisodeInfo(
                title, season_number, episode_number, abs_number,
                emby_id=emby_id, imdb_id=imdb_id, jellyfin_id=jellyfin_id,
                tmdb_id=tmdb_id, tvdb_id=tvdb_id, tvrage_id=tvrage_id,
                airdate=airdate, **queried_kwargs,
            )

            # Create new entries in EpisodeInfo map
            self.episode_info.update(dict.fromkeys(update_keys, info))
            return info
        
        # Update existing EpisodeInfo object
        info.set_emby_id(emby_id)
        info.set_imdb_id(imdb_id)
        info.set_jellyfin_id(jellyfin_id)
        info.set_tmdb_id(tmdb_id)
        info.set_tvdb_id(tvdb_id)
        info.set_tvrage_id(tvrage_id)
        info.set_airdate(airdate)
        info.update_queried_statuses(**queried_kwargs)

        # Update map with any keys
        self.episode_info.update(dict.fromkeys(update_keys, info))
        return info