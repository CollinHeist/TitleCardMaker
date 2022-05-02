class SeriesInfo:
    """
    This class encapsulates static information that is tied to a single Series.
    """

    """After how many characters to truncate the short name"""
    SHORT_WIDTH = 15

    """Mapping of illegal filename characters and their replacements"""
    __ILLEGAL_CHARACTERS = {
        '?': '!',
        '<': '',
        '>': '',
        ':':' -',
        '"': '',
        '/': '+',
        '\\': '+',
        '|': '',
        '*': '-',
    }

    __slots__ = ('year', 'name', 'full_name', 'short_name', 'match_name',
                 'full_match_name', 'legal_path', 'sonarr_id', 'tvdb_id',
                 'tmdb_id')
    

    def __init__(self, name: str, year: int) -> None:
        """
        Constructs a new instance.
        
        :param      name:  The name of the series.
        :param      year:  The air year of the series.
        """

        # Set year
        self.year = int(year)

        # Update all name attributes
        self.update_name(name)

        # Optional attributes
        self.sonarr_id = None
        self.tvdb_id = None
        self.tmdb_id = None


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return self.full_name


    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object."""

        ret = f'<SeriesInfo name={self.name}, year={self.year}'
        ret += '' if self.sonarr_id == None else f', sonarr_id={self.sonarr_id}'
        ret += '' if self.tvdb_id == None else f', tvdb_id={self.tvdb_id}'
        ret += '' if self.tmdb_id == None else f', tmdb_id={self.tmdb_id}'

        return f'{ret}>'


    def update_name(self, name: str) -> None:
        """
        Update all names for this series.
        
        :param      name:  The new name of the series info.
        """

        # If the given name already has the year, remove it
        if f'({self.year})' in str(name):
            self.name = name.rsplit(' (', 1)[0]
        else:
            self.name = str(name)

        # Set full name
        self.full_name = f'{self.name} ({self.year})'
        
        # Set short name
        if len(self.name) > self.SHORT_WIDTH:
            self.short_name = f'{self.name[:self.SHORT_WIDTH]}..'
        else:
            self.short_name = self.name
            
        # Set match names
        self.match_name = self.get_matching_title(self.name)
        self.full_match_name = self.get_matching_title(self.full_name)

        # Set folder-safe name
        translation = str.maketrans(self.__ILLEGAL_CHARACTERS)
        self.legal_path = self.full_name.translate(translation)


    def set_sonarr_id(self, sonarr_id: int) -> None:
        """
        Set the Sonarr ID for this series.
        
        :param      sonarr_id:  The Sonarr ID used for this series.
        """
        
        self.sonarr_id = int(sonarr_id)


    def set_tvdb_id(self, tvdb_id: int) -> None:
        """
        Set the TVDb ID for this series.
        
        :param      tvdb_id:  The TVDb ID for this series.
        """

        self.tvdb_id = int(tvdb_id)


    def set_tmdb_id(self, tmdb_id: int) -> None:
        """
        Set the TMDb ID for this series.
        
        :param      tmdb_id:    The TMDb ID for this series.
        """

        self.tmdb_id = int(tmdb_id)


    @staticmethod
    def get_matching_title(text: str) -> str:
        """
        Remove all non A-Z characters from the given title.
        
        :param      text:   The title to strip of special characters.
        
        :returns:   The input `text` with all non A-Z characters removed.
        """

        return ''.join(filter(str.isalnum, text)).lower()


    def matches(self, *names: tuple) -> bool:
        """
        Get whether any of the given names match this Series.
        
        :param      names:  The names to check
        
        :returns:   True if any of the given names match this series, False
                    otherwise.
        """

        matching_names = map(self.get_matching_title, names)

        return any(name == self.match_name for name in matching_names)
        