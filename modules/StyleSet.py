from modules.Debug import log

class StyleSet:
    """
    Set of watched and unwatched styles. 
    """

    """Mapping of style values to spoil types for Episode objects"""
    SPOIL_TYPE_STYLE_MAP = {
        'art':                      'art',
        'art blur':                 'art blur',
        'art blur grayscale':       'art blur grayscale',
        'art grayscale':            'art grayscale',
       #'art unique':               # INVALID COMBINATION
        'blur':                     'blur',
        'blur grayscale':           'blur grayscale',
        'blur unique':              'blur',
        'blur grayscale unique':    'blur grayscale',
        'grayscale':                'grayscale',
        'grayscale unique':         'grayscale',
        'unique':                   'spoiled',
    }

    __slots__ = ('valid', 'watched', 'unwatched')


    def __init__(self, watched: str='unique', unwatched: str='unique') -> None:
        """
        Initialize this object with the given watched/unwatched styles. Also
        updates the validity of this object.

        Args:
            watched: Watched style. Defaults to 'unique'.
            unwatched: Unwatched style. Defaults to 'unique'.
        """

        # Start as valid
        self.valid = True

        # Function to standardize style strings
        standardize=lambda s:' '.join(sorted(str(s).lower().strip().split(' ')))

        # Parse the watched style
        if (value := standardize(watched)) in self.SPOIL_TYPE_STYLE_MAP:
            self.watched = self.SPOIL_TYPE_STYLE_MAP[value]
        else:
            log.error(f'Invalid style "{watched}"')
            self.valid = False

        # Parse the unwatched style
        if (value := standardize(unwatched)) in self.SPOIL_TYPE_STYLE_MAP:
            self.unwatched = self.SPOIL_TYPE_STYLE_MAP[value]
        else:
            log.error(f'Invalid style "{unwatched}"')
            self.valid = False

        # Unique styles should be stored as unique, not spoiled
        self.watched = 'unique' if self.watched == 'spoiled' else self.watched
        self.unwatched = 'unique' if self.unwatched == 'spoiled' else self.unwatched


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
        return self.SPOIL_TYPE_STYLE_MAP[self.watched
                                         if watch_status else
                                         self.unwatched]