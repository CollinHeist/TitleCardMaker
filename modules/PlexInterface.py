from pathlib import Path
from xml.etree.ElementTree import fromstring

from requests import get, put

from modules.Debug import *
from modules.Show import Show

class PlexInterface:
    """
    This class describes a plex interface.

    Get the plex token from: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
    """

    def __init__(self, url: str, x_plex_token: str) -> None:
        """
        Constructs a new instance.
        
        :param      url:            The url

        :param      x_plex_token:   The x plex token
        """

        # If any args are None, this interface is inactive
        if any(_ is None for _ in (url, x_plex_token)):
            self.__active = False
            self.base_url, self.base_params, self.library = None, None, None
            return

        self.__active = True
        url = url + ('' if url.endswith('/') else '/')
        self.base_url = url + 'library/'
        self.base_params = {'X-Plex-Token': x_plex_token}

        # Structre is {library_name: {full_title: ratingKey, ...}, ...}
        self.library = {}
        self.parse_plex_library()


    def __bool__(self) -> bool:
        """
        Get the truthiness of this object.

        :returns:   Whether this interface is active orn ot.
        """

        return self.__active


    def parse_plex_library(self) -> None:
        """
        Parse the associated plex library 
        """

        if not self:
            return
        
        url = self.base_url + 'sections'
        params = self.base_params

        # Attempt to query Plex, if it errors, the URL was probably wrong - set inactive
        try:
            response = get(url=url, params=params)
        except Exception as e:
            error(f'Cannot query Plex. Returned error: "{e}"')
            self.__active = False
            return None

        library_xml = fromstring(response.text)

        for library in library_xml.findall('Directory'):
            library_title = library.attrib['title']
            library_key = int(library.attrib['key'])

            # Make a new request for all contents of this library
            url = self.base_url + f'sections/{library_key}/all'
            params = self.base_params

            response = get(url=url, params=params)
            content_xml = fromstring(response.text)

            # Go through each element (series) of the library
            content_dict = {}
            for series in content_xml.findall('Directory'):
                # Skip content with any missing keys
                if any(_  not in series.attrib for _ in ('title', 'ratingKey', 'year')):
                    continue

                series_title = series.attrib['title']
                series_rating_key = int(series.attrib['ratingKey'])
                series_year = int(series.attrib['year'])

                # Construct full title for this series
                if f'({series_year})' in series_title:
                    full_title = series_title
                else:
                    full_title = f'{series_title} ({series_year})'

                content_dict.update({Show.strip_specials(full_title): series_rating_key})

            # Add this library to the object's dictionary
            self.library.update({library_title: content_dict})

        info(f'Found {len(self.library)} Plex libraries ({", ".join(self.library.keys())})')


    def refresh_metadata(self, library: str, full_title: str) -> None:
        """
        Refresh the given title's (if found in the specified library) metadata. This
        effectively forces new title cards to be pulled in.

        If the library or full title is not found, no content is refreshed.

        :param      library:    The name of the library where the content is. Must be
                                a valid library name (i.e. matching Plex).
        
        :param      full_title: The full name (title, year) of the content to refresh.
        """

        if not self:
            return

        # Match based on the stripped full title
        match_title = Show.strip_specials(full_title)

        # Invalid library - error and exit
        if library not in self.library:
            error(f'Library "{library}" was not found in Plex')
            return
        
        # Valid library, invalid title - error and exit
        if match_title not in self.library[library]:
            error(f'Series "{full_title}" was not found under library "{library}" in Plex')
            return

        # Get the plex ratingKey for this title, then PUT a metadata refresh
        rating_key = self.library[library][match_title]

        url = self.base_url + f'metadata/{rating_key}/refresh'
        put(url)

        info(f'Refreshed Plex metadata for "{full_title}"', 1)


        