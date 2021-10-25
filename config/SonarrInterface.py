from datetime import datetime
from requests import get

class SonarrInterface:

    AIRDATE_FORMAT: str = '%Y-%m-%dT%H:%M:%SZ'

    def __init__(self, url: str, api_key: str) -> None:
        """
        Constructs a new instance.
        
        :param      url:        The base API url of Sonarr. Must end in
                                /api/ endpoint.

        :param      api_key:    The api key for requesting data to/from
                                Sonarr.
        """

        if not url.endswith(('api', 'api/')):
            raise ValueError(f'Sonarr URL must have /api endpoint')
        
        self._url_base = url + ('' if url.endswith('/') else '/')
        self._param_base = {'apikey': api_key}


    def _get_series_id(self, title: str) -> int:
        """
        Gets the series identifier.
        
        :param      title:  The title
        :type       title:  str
        
        :returns:   The series identifier.
        :rtype:     id
        """

        # Construct GET arguments
        url = f'{self._url_base}series/'
        params = self._param_base

        # Query Sonarr to get JSON of all series in the library
        all_series = self.__get(url, params)

        # Go through each series
        for show in all_series:
            current_title = show['title']
            alternate_titles = [_['title'] for _ in show['alternateTitles']]

            # If the provided title matches the given title/alt. title, return it'd id
            if title == current_title or title in alternate_titles:
                return int(show['id'])

        raise ValueError(f'Cannot find series "{title}" in Sonarr')


    def _get_episode_title_for_id(self, series_id: int, season: int,
                                  episode: int) -> str:

        """
        Gets the episode title for a given series ID and season/episode
        number.
        
        :param      series_id:  The series identifier
        
        :returns:   The episode title.
        """

        # Construct GET arguments
        url = f'{self._url_base}episode/'
        params = self._param_base
        params.update(seriesId=series_id)

        # Query Sonarr to get JSON of all episodes for this series id
        all_episodes = self.__get(url, params)

        # Go through each episode
        for episode in all_episodes:
            curr_season_number = int(episode['seasonNumber'])
            curr_episode_number = int(episode['episodeNumber'])

            if season == curr_season_number and episode == curr_season_number:
                return episode['title']

        raise ValueError(
            f'Cannot find Season {season}, '
            f'Episode {episode} of seriesId={series_id}'
        )


    def _get_all_episode_data_for_id(self, series_id: int) -> list:
        """
        Gets all episode data for identifier. Only returns episodes that have
        aired already.
        
        :param      series_id:  The series identifier
        
        :returns:   All episode data for the given series id. Only entries
                    that have ALREADY aired are returned.
        """

        # Construct GET arguments
        url = f'{self._url_base}episode/'
        params = self._param_base
        params.update(seriesId=series_id)

        # Query Sonarr to get JSON of all episodes for this series id
        all_episodes = self.__get(url, params)

        # Go through each episode and get its season/episode number, and title
        episode_info = []
        for episode in all_episodes:
            # Verify this episode has already aired
            air_datetime = datetime.strptime(episode['airDateUtc'], self.AIRDATE_FORMAT)
            if air_datetime > datetime.now():
                continue

            episode_info.append({
                'season_number':    int(episode['seasonNumber']),
                'episode_number':   int(episode['episodeNumber']),
                'title':            episode['title'],
            })

        return episode_info


    def get_episode_title(self, title: str, season: int, episode: int) -> str:
        """
        Gets the episode title.
        
        :param      title:      The title of the requested show. 

        :param      season:     The season number whose title is requested.

        :param      episode:    The episode number whose title is requested.
        
        :returns:   The episode title.
        """

        series_id = self._get_series_id(title)

        return self._get_episode_title_for_id(series_id, season, episode)


    def get_all_episodes_for_series(self, title: str) -> list:
        """
        Gets all episode info for the given series title from Sonarr. The
        returned info is season/episode number and title for each episode.

        Only episodes that have already aired are returned.
        
        :param      title:  The title of the requested show.
        
        :returns:   List of dictionaries of episode data.
        """

        series_id = self._get_series_id(title)

        return self._get_all_episode_data_for_id(series_id)
        

    def __get(self, url: str, params: dict) -> dict:
        """
        Wrapper for getting the JSON return of the specified GET request.
        
        :param      url:    URL to pass to GET.

        :param      params: Parameters to pass to GET.
        
        :returns:   Dict made from the JSON return of the specified
                    GET request.
        """

        return get(url=url, params=params).json()


        