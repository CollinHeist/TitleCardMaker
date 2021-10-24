from requests import get

class SonarrInterface:
    def __init__(self, url: str, api_key: str) -> None:
        """
        Constructs a new instance.
        
        :param      url:      The url

        :param      api_key:  The api key
        """

        if not url.endswith(('api', 'api/')):
            raise ValueError(f'Sonarr URL must have /api endpoint')
        
        self._url_base = url + '' if url.endswith('/') else '/'
        self._param_base = {
            'apikey': api_key
        }


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
        Gets the episode title.
        
        :param      series_id:  The series identifier
        :type       series_id:  int
        
        :returns:   The episode title.
        :rtype:     str
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


    def get_episode_title(self, title: str, season: int, episode: int) -> str:
        """
        Gets the episode title.
        
        :param      title:    The title
        :type       title:    str
        :param      season:   The season
        :type       season:   int
        :param      episode:  The episode
        :type       episode:  int
        
        :returns:   The episode title.
        :rtype:     str
        """

        series_id = self._get_series_id(title)

        return self._get_episode_title_for_id(series_id, season, episode)
        

    def __get(self, url: str, params: dict) -> dict:
        """
        { function_description }
        
        :param      url:     The url
        :type       url:     str
        :param      params:  The parameters
        :type       params:  dict
        
        :returns:   { description_of_the_return_value }
        :rtype:     dict
        """

        return get(url=url, params=params).json()


        