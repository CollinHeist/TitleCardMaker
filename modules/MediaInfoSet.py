from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo
from modules.SeriesInfo import SeriesInfo

class MediaInfoSet:
    """
    This class describes a set of Info, notably SeriesInfo and EpisodeInfo,
    objects. This object can be viewed as an interface to creating and getting
    these objects, so that database ID's can be preserved between instances of
    Show objects (as variations are created for archiving purposes).
    """


    def __init__(self) -> None:
        """
        Construct a new instance of the MediaInfoSet. This creates empty
        dictionaries that map various identifiers (like names or ID's) to Info
        objects.
        """

        # Containers for SeriesInfo objects
        # Full Name -> SeriesInfo
        self.series_names = {}
        # IMDb ID -> SeriesInfo
        self.series_imdb_ids = {}
        # Sonarr ID -> SeriesInfo
        self.series_sonarr_ids = {}
        # TVDb ID -> SeriesInfo
        self.series_tvdb_ids = {}
        # TMDb ID -> SeriesInfo
        self.series_tmdb_ids = {}

        # Containers for EpisodeInfo objects
        # SeriesInfo -> index key -> EpisodeInfo
        self.episode_indices = {}
        # TVDb ID -> EpisodeInfo
        self.episode_tvdb_ids = {}
        # IMDb ID -> EpisodeInfo
        self.episode_imdb_ids = {}
        # TMDb ID -> EpisodeInfo
        self.episode_tmdb_ids = {}


    def get_series_info(self, name: str=None, year: int=None, *,
                        imdb_id: str=None, sonarr_id: int=None,
                        tmdb_id: int=None, tvdb_id: int=None) -> SeriesInfo:
        """
        Get the SeriesInfo object indicated by the given attributes. This looks
        for an existing object mapped under any of the given details; if none
        exists, a new SeriesInfo object is created with the given details.
        
        Args:
            name: The name of the series. Optional if the associated object
                already exists.
            year: The year of the series. Optional if the associated object
                already exists.
            imdb_id: Optional IMDb ID.
            sonarr_id: Optional Sonarr ID.
            tmdb_id: Optional TMDb ID.
            tvdb_id: Optional TVDb ID.
        
        Returns:
            The SeriesInfo object indicated by the given attributes.
        """

        # Inner function to set all ID's of the given SeriesInfo object
        def set_ids(info_obj):
            info_obj.set_imdb_id(imdb_id)
            info_obj.set_sonarr_id(sonarr_id)
            info_obj.set_tmdb_id(tmdb_id)
            info_obj.set_tvdb_id(tvdb_id)

            return info_obj

        # Get by name, then ID's
        if (name is not None and year is not None
            and (info := self.series_names.get(f'{name} ({year})'))):
            return set_ids(info)
        if imdb_id is not None and (info := self.series_imdb_ids.get(imdb_id)):
            return set_ids(info)
        if (sonarr_id is not None
            and (info := self.series_sonarr_ids.get(sonarr_id))):
            return set_ids(info)
        if tmdb_id is not None and (info := self.series_tmdb_ids.get(tmdb_id)):
            return set_ids(info)
        if tvdb_id is not None and (info := self.series_tvdb_ids.get(tvdb_id)):
            return set_ids(info)

        # This SeriesInfo doesn't exist in the set, verify name and year present
        series_info = SeriesInfo(
            name,
            year,
            imdb_id=imdb_id,
            sonarr_id=sonarr_id,
            tmdb_id=tmdb_id,
            tvdb_id=tvdb_id,
        )

        # Add object to sets
        self.series_names[f'{name} ({year})'] = series_info
        if imdb_id is not None:
            self.series_imdb_ids[imdb_id] = series_info
        if sonarr_id is not None:
            self.series_sonarr_ids[sonarr_id] = series_info
        if imdb_id is not None:
            self.series_tmdb_ids[tmdb_id] = series_info
        if imdb_id is not None:
            self.series_tvdb_ids[tvdb_id] = series_info

        return series_info


    def __set_episode_imdb_id(self, episode_info: EpisodeInfo,
                              imdb_id: str) -> None:
        """
        Set the IMDb ID of the given EpisodeInfo object. This also updates
        the IMDb ID map of this info set.
        
        Args:
            episode_info: The EpisodeInfo to set the ID of.
            imdb_id: The IMDb ID.
        """

        if imdb_id is None:
            return None

        episode_info.set_imdb_id(imdb_id)
        self.episode_imdb_ids[imdb_id] = episode_info


    def __set_episode_tvdb_id(self, episode_info: EpisodeInfo,
                              tvdb_id: str) -> None:
        """
        Set the TVDb ID of the given EpisodeInfo object. This also updates
        the TVDb ID map of this info set.
        
        Args:
            episode_info: The EpisodeInfo to set the ID of.
            tvdb_id: The TVDb ID.
        """

        if tvdb_id is None:
            return None

        episode_info.set_tvdb_id(tvdb_id)
        self.episode_tvdb_ids[tvdb_id] = episode_info


    def __set_episode_tmdb_id(self, episode_info: EpisodeInfo,
                              tmdb_id: str) -> None:
        """
        Set the TMDb ID of the given EpisodeInfo object. This also updates
        the TMDb ID map of this info set.
        
        Args:
            episode_info: The EpisodeInfo to set the ID of.
            tmdb_id: The TMDb ID.
        """

        if tmdb_id is None:
            return None

        episode_info.set_tmdb_id(tmdb_id)
        self.episode_tmdb_ids[tmdb_id] = episode_info


    def get_episode_info(self, series_info: SeriesInfo=None,
                         title: 'Title'=None, season_number: int=None,
                         episode_number: int=None,  abs_number: int=None, *,
                         imdb_id: str=None, tvdb_id: int=None, tmdb_id:int=None,
                         title_match: bool=True, 
                         **queried_kwargs: dict) -> EpisodeInfo:
        """
        Get the EpisodeInfo object indicated by the given attributes. This looks
        for an existing object mapped under any of the given details; if none
        exists, a new EpisodeInfo object is created with the given details.
        
        Args:
            series_info: SeriesInfo object the EpisodeInfo object might be
                indexed under.
            title: The Title of the episode. Optional if associated object
                already exists. Optional if associated object already exists
            season_number: Season number of the episode. Optional if associated
                object already exists
            episode_number: Episode number of the episode. Optional if
                associated object already exists
            abs_number: Optional absolute number of the episode.
            imdb_id: Optional IMDb ID.
            tvdb_id: Optional TVDb ID.
            tmdb_id: Optional TMDb ID.
            kwargs: Any keyword arguments to pass to the initialization of the
                EpisodeInfo object, if indicated.
        
        Returns:
            The EpisodeInfo object indicated by the given attributes. None if an
            object does not exist and cannot be created due to an index conflict
        """

        def set_ids(info_obj):
            self.__set_episode_imdb_id(info_obj, imdb_id)
            self.__set_episode_tvdb_id(info_obj, tvdb_id)
            self.__set_episode_tmdb_id(info_obj, tmdb_id)
            info_obj.update_queried_statuses(**queried_kwargs)
            return info_obj

        # Check under TVDb ID, then IMDb, and finally index
        if tvdb_id is not None and (info := self.episode_tvdb_ids.get(tvdb_id)):
            return set_ids(info)
        if imdb_id is not None and (info := self.episode_imdb_ids.get(imdb_id)):
            return set_ids(info)
        if tmdb_id is not None and (info := self.episode_tmdb_ids.get(tmdb_id)):
            return set_ids(info)
        if (season_number is not None and episode_number is not None
            and series_info is not None):
            key = f'{season_number}-{episode_number}'
            if (info := self.episode_indices.get(series_info, {}).get(key)):
                if not title_match or (title_match and info.title.matches(title)):
                    return set_ids(info)
                else:
                    log.debug(f'Index match on {series_info} {key}, but title '
                              f'mismatch ({info.title}) vs ({title})')
                    return EpisodeInfo(title, season_number, episode_number,
                                       abs_number, imdb_id=imdb_id,
                                       tvdb_id=tvdb_id, tmdb_id=tmdb_id,
                                       **queried_kwargs)

        # This EpisodeInfo doesn't exist in the set, create new object
        episode_info = EpisodeInfo(
            title, season_number, episode_number, abs_number, imdb_id=imdb_id,
            tvdb_id=tvdb_id, tmdb_id=tmdb_id, **queried_kwargs,
        )

        # Add object to indices set
        key = f'{season_number}-{episode_number}'
        if series_info in self.episode_indices:
            self.episode_indices[series_info][key] = episode_info
        else:
            self.episode_indices[series_info] = {key: episode_info}

        # Add object to ID sets
        self.__set_episode_imdb_id(episode_info, imdb_id)
        self.__set_episode_tvdb_id(episode_info, tvdb_id)
        self.__set_episode_tmdb_id(episode_info, tmdb_id)

        return episode_info


    def update_series_name(self, series_info: SeriesInfo, name: str) -> None:
        """
        Update the name of the associated SeriesInfo object. This also updates
        the mapping in this object's set.
        
        Args:
            series_info: The SeriesInfo object being updated.
            name:New name of the associated series.
        """

        # Update name of the object itself
        old_key = series_info.full_name
        series_info.update_name(name)

        # Add object under new key within set
        self.series_names[f'{name} ({series_info.year})'] = series_info

        # Delete old key
        try:
            del self.series_names[old_key]
        except KeyError:
            pass