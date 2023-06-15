from modules.Debug import log

class StyleSet:
    """
    Set of watched and unwatched styles. 
    """

    """Default spoil type for all episodes without explicit watch statuses"""
    DEFAULT_SPOIL_TYPE = 'spoiled'

    """Mapping of style values to spoil types for Episode objects"""
    SPOIL_TYPE_STYLE_MAP = {
        'art':                      'art',
        'art blur':                 'art blur',
        'art blur grayscale':       'art blur grayscale',
        'art grayscale':            'art grayscale',
      # 'art unique':               # INVALID COMBINATION
        'blur':                     'blur',
        'blur grayscale':           'blur grayscale',
        'blur unique':              'blur',
        'blur grayscale unique':    'blur grayscale',
        'grayscale':                'grayscale',
        'grayscale unique':         'grayscale',
        'unique':                   'spoiled',
    }

    __slots__ = ('__kwargs', 'valid', 'watched', 'unwatched')


    def __init__(self,
            watched: str = 'unique',
            unwatched: str = 'unique') -> None:
        """
        Initialize this object with the given watched/unwatched styles.
        Also updates the validity of this object.

        Args:
            watched: Watched style. Defaults to 'unique'.
            unwatched: Unwatched style. Defaults to 'unique'.
        """

        # Start as valid
        self.__kwargs = {'watched': watched, 'unwatched': unwatched}
        self.valid = True

        # Parse each style
        self.update_watched_style(watched)
        self.update_unwatched_style(unwatched)


    def __repr__(self) -> str:
        """Return an unambigious string representation of the object."""

        return f'<StyleSet {self.watched=}, {self.unwatched=}>'


    def __copy__(self) -> 'StyleSet':
        """Copy this objects' styles into a new StyleSet object."""

        return StyleSet(**self.__kwargs)


    @staticmethod
    def __standardize(style: str) -> str:
        """
        Standardize the given style string so that "unique blur", "blur
        unique" evaluate to the same style.

        Args:
            style: Style string (from YAML) being standardized.

        Returns:
            Standardized value. This is lowercase with spaces removed,
            and sorted alphabetically.
        """

        return ' '.join(sorted(str(style).lower().strip().split(' ')))


    def update_watched_style(self, style: str) -> None:
        """
        Set the watched style for this set.

        Args:
            style: Style to set.
        """

        if (value := self.__standardize(style)) in self.SPOIL_TYPE_STYLE_MAP:
            self.watched = value
        else:
            log.error(f'Invalid style "{style}"')
            self.valid = False


    def update_unwatched_style(self, style: str) -> None:
        """
        Set the unwatched style for this set.

        Args:
            style: Style to set.
        """

        if (value := self.__standardize(style)) in self.SPOIL_TYPE_STYLE_MAP:
            self.unwatched = value
        else:
            log.error(f'Invalid style "{style}"')
            self.valid = False


    @property
    def watched_style_is_art(self) -> bool:
        return 'art' in self.watched

    @property
    def unwatched_style_is_art(self) -> bool:
        return 'art' in self.unwatched


    def effective_style_is_art(self, watch_status: bool) -> bool:
        return 'art' in (self.watched if watch_status else self.unwatched)

    def effective_style_is_blur(self, watch_status: bool) -> bool:
        return 'blur' in (self.watched if watch_status else self.unwatched)

    def effective_style_is_grayscale(self, watch_status: bool) -> bool:
        return 'grayscale' in (self.watched if watch_status else self.unwatched)

    def effective_style_is_unique(self, watch_status: bool) -> bool:
        return 'unqiue' == (self.watched if watch_status else self.unwatched)

    def effective_spoil_type(self, watch_status: bool) -> str:
        return self.SPOIL_TYPE_STYLE_MAP[
            self.watched if watch_status else self.unwatched
        ]