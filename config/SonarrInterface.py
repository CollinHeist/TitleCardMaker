from datetime import datetime
from re import match
from pathlib import Path
from requests import get

from Debug import *

class SonarrInterface:
    """
    This class describes a Sonarr interface. The primary purpose of this
    class is to get episode titles based on season and episode counts. This
    is the alternative to making API requests to TheMovieDatabase.
    """

    """Datetime format string for airDateUtc field in Sonarr API requests"""
    AIRDATE_FORMAT: str = '%Y-%m-%dT%H:%M:%SZ'

    def __init__(self, url: str, api_key: str) -> None:
        """
        Constructs a new instance.
        
        :param      url:        The base url of Sonarr.

        :param      api_key:    The api key for requesting data to/from
                                Sonarr.
        """

        # If unspecified, create an inactive object
        if url is None or api_key is None:
            self._active = False
            self._url_base = None
            self._param_base = None
            return

        # Add /api/ endpoint if not provided
        if not url.endswith('api') and not url.endswith('api/'):
            url += 'api/' if url.endswith('/') else '/api/'
        
        self._active = True
        self._url_base = url + ('' if url.endswith('/') else '/')
        self._param_base = {'apikey': api_key}


    def _if_active(func):
        """
        Decorator for methods of this class that instantly returns
        if this instance's `_active` attribute is False.
        """

        def __wrapped_func(*args, **kwargs):
            if args[0]._active:
                return func(*args, **kwargs)
            else:
                return

        return __wrapped_func


    def _get_series_id(self, title: str, year: int) -> int:
        """
        Gets the series ID used by Sonarr to identify this show.
        
        :param      title:  The title of the show in question. Should
                            not include year.
        
        :returns:   The series ID as used by this object's instance of
                    Sonarr.
        """

        # Get only text from this title..
        title = self.__text_only(title)

        # Construct GET arguments
        url = f'{self._url_base}series/'
        params = self._param_base

        # Query Sonarr to get JSON of all series in the library
        all_series = self.__get(url, params)

        # Go through each series
        for show in all_series:
            # Skip shows with a year mismatch, prevents parsing titles (slower)
            if int(show['year']) != year:
                continue

            # Year match, verify the given title matches main/alternate titles
            current_title = self.__text_only(show['title'])
            alternate_titles = [self.__text_only(_['title']) for _ in show['alternateTitles']]

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
            f'Cannot find Season {season}, Episode {episode} of seriesId={series_id}'
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
            # Unaired episodes (such as specials) won't have airDateUtc key
            if 'airDateUtc' in episode:
                # Verify this episode has already aired
                air_datetime = datetime.strptime(episode['airDateUtc'], self.AIRDATE_FORMAT)
                if air_datetime > datetime.now():
                    continue

            # Skip episodes whose titles aren't in Sonarr yet (to avoid naming them TBA.. )
            if episode['title'] == 'TBA':
                continue

            episode_info.append({
                'season_number':    int(episode['seasonNumber']),
                'episode_number':   int(episode['episodeNumber']),
                'title':            episode['title'],
            })

        return episode_info


    @_if_active
    def get_episode_title(self, title: str, year: int, season: int,
                          episode: int) -> str:
        """
        Gets the episode title.
        
        :param      title:      The title of the requested show. 

        :param      season:     The season number whose title is requested.

        :param      episode:    The episode number whose title is requested.
        
        :returns:   The episode title.
        """

        series_id = self._get_series_id(title, year)

        return self._get_episode_title_for_id(series_id, season, episode)


    @_if_active
    def get_all_episodes_for_series(self, title: str, year: int) -> list:
        """
        Gets all episode info for the given series title from Sonarr. The
        returned info is season/episode number and title for each episode.

        Only episodes that have already aired are returned.
        
        :param      title:  The title of the requested show.
        
        :returns:   List of dictionaries of episode data.
        """

        series_id = self._get_series_id(title, year)

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


    def __text_only(self, text: str) -> str:
        """
        Get only the A-Z characters from the given text string.
        
        :param      text:   The text to process.
        
        :returns:   String with all non a-z A-Z characters removed.
        """

        return ''.join(filter(lambda c: match('[a-zA-Z]', c), text))
        