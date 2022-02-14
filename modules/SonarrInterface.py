from datetime import datetime
from pathlib import Path
from pickle import dump, load, HIGHEST_PROTOCOL

from modules.Debug import *
from modules.Show import Show
from modules.Title import Title
from modules.WebInterface import WebInterface

class SonarrInterface(WebInterface):
    """
    This class describes a Sonarr interface, which is a type of WebInterface.
    The primary purpose of this class is to get episode titles for series
    entries.
    """

    """Datetime format string for airDateUtc field in Sonarr API requests"""
    __AIRDATE_FORMAT: str = '%Y-%m-%dT%H:%M:%SZ'

    """Path to the map of sonarr titles to ID's"""
    __ID_MAP: Path = Path(__file__).parent / '.objects' / 'sonarr_id_map.pkl'

    def __init__(self, url: str, api_key: str) -> None:
        """
        Constructs a new instance of an interface to Sonarr.
        
        :param      url:        The base url of Sonarr.
        :param      api_key:    The api key for requesting data to/from Sonarr.
        """

        # Initialize parent WebInterface 
        super().__init__()

        # Create objects directory if it does not exist
        self.__ID_MAP.parent.mkdir(parents=True, exist_ok=True)

        # Attempt to read existing ID map
        if self.__ID_MAP.exists():
            with self.__ID_MAP.open('rb') as file_handle:
                self.__id_map = load(file_handle)
        else:
            self.__id_map = {}

        # Add /api/ endpoint if not provided
        if not url.endswith('api') and not url.endswith('api/'):
            url += 'api/' if url.endswith('/') else '/api/'
        self._url_base = url + ('' if url.endswith('/') else '/')

        # Base parameters for sending requests to Sonarr
        self._param_base = {'apikey': api_key}


    def __add_id_to_map(self, full_title: str, id_: int) -> None:
        """
        Add the given ID to the object's map. Also write this updated map object
        to the file.
        
        :param      full_title: The full title of the entry to map.
        :param      id_:        The ID of the entry to store.
        """

        self.__id_map[full_title] = int(id_)

        with self.__ID_MAP.open('wb') as file_handle:
            dump(self.__id_map, file_handle, HIGHEST_PROTOCOL)


    def _get_series_id(self, title: str, year: int) -> int:
        """
        Gets the series ID used by Sonarr to identify this show.
        
        :param      title:  The title of the series.
        
        :returns:   The series ID as used by Sonarr, None if the series was
                    not found.
        """

        # Get titles to operate with
        full_title = f'{title} ({year})'
        match_title = Show.strip_specials(title)

        # If already mapped, return
        if full_title in self.__id_map:
            return self.__id_map[full_title]

        # Construct GET arguments
        url = f'{self._url_base}series/'
        params = self._param_base

        # Query Sonarr to get JSON of all series in the library
        all_series = self._get(url, params)

        # Go through each series
        for show in all_series:
            # Skip shows with a year mismatch, prevents parsing titles (slower)
            if int(show['year']) != year:
                continue

            # Year matches, verify the given title matches main/alternate titles
            current_title = Show.strip_specials(show['title'])
            alternate_titles = [
                Show.strip_specials(_['title']) for _ in show['alternateTitles']
            ]

            if match_title == current_title or match_title in alternate_titles:
                id_ = int(show['id'])
                self.__add_id_to_map(full_title, id_)

                return id_

        return None


    def get_absolute_episode_number(self, title: str, year: int,
                                    season_number: int,
                                    episode_number: int) -> int:
        """
        Gets the absolute episode number of the given entry.
        
        :param      title:          The title of the series.
        :param      year:           The year of the series.
        :param      season_number:  The season number of the entry.
        :param      episode_number: The episode number of the entry.
        
        :returns:   The absolute episode number. None if not found, or if the
                    entry does not have an absolute number.
        """

        # Get the ID for this series
        series_id = self._get_series_id(title, year)

        # If not found, skip
        if not series_id:
            error(f'Cannot find series "{title} ({year})" in Sonarr')
            return None

        # Get all episodes, and match by season+episode number
        for episode in self._get_all_episode_data_for_id(series_id):
            season_match = (episode['season_number'] == season_number)
            episode_match = (episode['episode_number'] == episode_number)

            if season_match and episode_match and 'abs_number' in episode:
                return episode['abs_number']

        return None


    def list_all_series_id(self) -> None:
        """List all the series ID's of all shows used by Sonarr. """

        # Construct GET arguments
        url = f'{self._url_base}series/'
        params = self._param_base
        
        # Query Sonarr to get JSON of all series in the library
        all_series = self._get(url, params)

        if 'error' in all_series:
            error(f'Sonarr returned error "{all_series["error"]}"')
            return None

        # Go through each series
        for show in all_series:
            main_title = show['title']
            alt_titles = [_['title'] for _ in show['alternateTitles']]

            padding = len(f'{show["id"]} : ')
            titles = f'\n{" " * padding}'.join([main_title] + alt_titles)
            print(f'{show["id"]} : {titles}')


    def _get_episode_title_for_id(self, series_id: int, season: int,
                                  episode: int) -> Title:
        """
        Gets the episode title for a given series ID and season/episode number.
        
        :param      series_id:  The series identifier
        
        :returns:   The episode title.
        """

        # Construct GET arguments
        url = f'{self._url_base}episode/'
        params = self._param_base
        params.update(seriesId=series_id)

        # Query Sonarr to get JSON of all episodes for this series id
        all_episodes = self._get(url, params)

        # Go through each episode
        for episode in all_episodes:
            curr_season_number = int(episode['seasonNumber'])
            curr_episode_number = int(episode['episodeNumber'])

            if season == curr_season_number and episode == curr_season_number:
                return Title(episode['title'])

        raise ValueError(
            f'Cannot find Season {season}, Episode {episode} of '
            f'seriesId={series_id}'
        )


    def _get_all_episode_data_for_id(self, series_id: int) -> list:
        """
        Gets all episode data for identifier. Only returns episodes that have
        aired already.
        
        :param      series_id:  The series identifier.
        
        :returns:   All episode data for the given series id. Only entries that
                    have ALREADY aired (or do not air) are returned.
        """

        # Construct GET arguments
        url = f'{self._url_base}episode/'
        params = self._param_base
        params.update(seriesId=series_id)

        # Query Sonarr to get JSON of all episodes for this series id
        all_episodes = self._get(url, params)

        # Go through each episode and get its season/episode number, and title
        episode_info = []
        for episode in all_episodes:
            # Unaired episodes (such as specials) won't have airDateUtc key
            if 'airDateUtc' in episode:
                # Verify this episode has already aired, skip if not
                air_datetime = datetime.strptime(
                    episode['airDateUtc'],
                    self.__AIRDATE_FORMAT
                )
                if air_datetime > datetime.now():
                    continue

            # Skip episodes whose titles aren't in Sonarr yet to avoid
            # placeholder names
            if episode['title'].lower() == 'tba':
                continue

            new_info = {
                'season_number':    int(episode['seasonNumber']),
                'episode_number':   int(episode['episodeNumber']),
                'title':            Title(episode['title']),
                # 'filename':         Path(episode['episodeFile']['path']).stem,
            }

            # Non-cannon episodes don't have an absolute number
            if 'absoluteEpisodeNumber' in episode:
                new_info['abs_number'] = int(episode['absoluteEpisodeNumber'])

            episode_info.append(new_info)

        return episode_info


    def get_episode_title(self, title: str, year: int, season: int,
                          episode: int) -> Title:
        """
        Gets the episode title of the requested entry.
        
        :param      title:      The title of the requested series.
        :param      year:       The year of the requested series.
        :param      season:     The season number of the entry.
        :param      episode:    The episode number of the entry.
        
        :returns:   The episode title.
        """

        series_id = self._get_series_id(title, year)

        return self._get_episode_title_for_id(series_id, season, episode)


    def get_all_episodes_for_series(self, title: str, year: int) -> list:
        """
        Gets all episode info for the given series title from Sonarr. The
        returned info is season/episode number and title for each episode.

        Only episodes that have already aired are returned.
        
        :param      title:  The title of the series.
        :param      year:   The year of the series.
        
        :returns:   List of dictionaries of episode data.
        """

        series_id = self._get_series_id(title, year)

        if series_id == None:
            error(f'Series "{title} ({year})" not found in Sonarr')
            return []

        return self._get_all_episode_data_for_id(series_id)


    #TODO immplement
    # def get_episode_filename(self, title: str, year: int, season_number: int,
    #                          episode_number: int) -> str:

    #     """
    #     { item_description }
    #     """

    #     if not self:
    #         return None

    #     # Get the ID for this series
    #     series_id = self._get_series_id(title, year)

    #     # Construct GET arguments
    #     url = f'{self._url_base}series/'
    #     params = self._param_base

    #     # Query Sonarr to get all series in the library
    #     all_series = self._get(url, params)

    #     # Match by ID, get the top-level series folder
    #     series_folder = None
    #     for show in all_series:
    #         if show['id'] == series_id:
    #             series_folder = Path(show['path']).name
    #             break

    #     # If no top-level series folder (for some reason..), exit
    #     if not series_folder:
    #         return None

    #     # Construct GET arguments for this specific episode
    #     url = f'{self._url_base}episode/'
    #     params = self._param_base
    #     params['seriesId'] = series_id

    #     # Query for all episodes of this show
    #     all_episodes = self._get(url, params)

    #     # Find this season/episode number
    #     for episode in all_episodes:
    #         if (int(episode['seasonNumber']) == season_number
    #             and int(episode['episodeNumber']) == episode_number):
    #             # If episode found, check if file exists and get that filename
    #             if episode['hasFile']:
    #                 full_path = episode['episodeFile']['relativePath']
    #                 filename = full_path[:full_path.rfind('.')]

    #                 return str(series_folder / Path(filename))

    #     return None


    @staticmethod
    def manually_specify_id(title: str, year: int, id_: int) -> None:
        """
        Manually override the Sonarr ID for the given full title.

        :param      title:  The title of the series.
        :param      year:   The year of the series.
        :param      id_:    The Sonarr ID for this series.
        """

        SonarrInterface('', '').__add_id_to_map(f'{title} ({year})', id_)
        info(f'Specified ID {id_} for "{title} ({year})"')
        


        