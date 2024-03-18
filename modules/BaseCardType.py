from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable, Optional, Union

from titlecase import titlecase

from modules.Debug import log
from modules.ImageMaker import ImageMaker, Dimensions

if TYPE_CHECKING:
    from modules.Font import Font
    from modules.PreferenceParser import PreferenceParser

ImageMagickCommands = list[str]


class Coordinate:
    """Class that defines a single Coordinate on an x/y plane."""

    __slots__ = ('x', 'y')

    def __init__(self, x: float, y: float) -> None:
        """Initialize this Coordinate with the given x/y coordinates."""

        self.x = x
        self.y = y


    def __iter__(self) -> Iterable[tuple[float, float]]:
        """
        Iterate through this object. This can be used to unpack the
        Coordinate, for example:

        >>> x, y = Coordinate(1, 2) # x=1, y=2
        """

        return iter((self.x, self.y))


    def __add__(self,
            other: Union['Coordinate', tuple[float, float]],
        ) -> 'Coordinate':
        """
        Add the given coordinates to this object, returning a new
        combination of the two.

        Args:
            other: The Coordinate to add.

        Returns:
            Newly constructed Coordinate object of these coordinates.
        """

        if isinstance(other, Coordinate):
            return Coordinate(self.x + other.x, self.y + other.y)

        return Coordinate(self.x + other[0], self.y + other[1])


    def __iadd__(self,
            other: Union['Coordinate', tuple[float, float]],
        ) -> 'Coordinate':
        """
        Add the given Coordinate to this one. This adds the x/y
        positions individually.

        Args:
            other: The Coordinate to add.

        Returns:
            This object.
        """

        if isinstance(other, Coordinate):
            self.x += other.x
            self.y += other.y
        else:
            self.x += other[0]
            self.y += other[1]

        return self


    def __str__(self) -> str:
        """
        Represent this Coordinate as a string.

        >>> str(Coordinate(1.2, 3.4))
        '1,2'
        """

        return f'{self.x:.0f},{self.y:.0f}'

    @property
    def as_svg(self) -> str:
        """SVG representation of this Coordinate."""

        return f'{self.x:.1f} {self.y:.1f}'


class Line:
    """Class that defines a drawable SVG line."""

    __slots__ = ('start', 'end')

    def __init__(self, start: Coordinate, end: Coordinate) -> None:
        """
        Initialize a Line which spans between the given start and end
        Coordinates.

        Args:
            start: Coordinate which defines one end of this line.
            end: Coordinate which defines the other end of this line.
        """

        self.start = start
        self.end = end


    def __str__(self) -> str:
        """Represent this Line as a string. This is a SVG-command."""

        return f'M {str(self.start)} L {str(self.end)}'


    def draw(self) -> str:
        """Draw this line."""

        return f'-draw "path \'{str(self)}\'"'


class Rectangle:
    """Class that defines movable SVG rectangle."""

    __slots__ = ('start', 'end')

    def __init__(self, start: Coordinate, end: Coordinate) -> None:
        """
        Initialize this Rectangle that encompasses the given start and
        end Coordinates. These Coordinates are the opposite corners of
        the rectangle.

        Args:
            start: Coordinate which defines one starting corner of the
                rectangle.
            end: Coordinate which opposites the `start` coordinate of
                this rectangle.
        """

        self.start = start
        self.end = end


    def __str__(self) -> str:
        """
        Represent this Rectangle as a string. This is the joined string
        representation of the start and end coordinate.
        """

        return f'{str(self.start)},{str(self.end)}'


    def draw(self) -> str:
        """Draw this Rectangle."""

        return f'-draw "rectangle {str(self)}"'


class Shadow:
    """Class which defines a shadow string."""

    __slots__ = ('opacity', 'sigma', 'x', 'y')

    def __init__(self,
            *,
            opacity: int = 95,
            sigma: int = 2,
            x: int = 10,
            y: int = 10,
        ) -> None:
        """Construct a shadow with the given parameters."""

        self.opacity = opacity
        self.sigma = sigma
        self.x = x
        self.y = y


    def __str__(self) -> str:
        """String representation of this shadow effect."""

        return f'{self.opacity}x{self.sigma}{self.x:+}{self.y:+}'


    @property
    def as_command(self) -> str:
        """Wrapper for `__str__`."""

        return str(self)


class BaseCardType(ImageMaker):
    """
    This class describes an abstract card type. A BaseCardType is a
    subclass of ImageMaker, because all CardTypes are designed to create
    title cards. This class outlines the requirements for creating a
    custom type of title card.

    All implementations of BaseCardType must implement this class's
    abstract properties and methods in order to work with TCM.
    """

    """Default case string for all title text"""
    DEFAULT_FONT_CASE = 'upper'

    """Default font replacements"""
    FONT_REPLACEMENTS = {}

    """Mapping of 'case' strings to format functions"""
    CASE_FUNCTIONS: dict[str, Callable[[Any], str]] = {
        'blank': lambda _: '',
        'lower': str.lower,
        'source': str,
        'title': titlecase,
        'upper': str.upper,
    }

    """Default episode text format string, can be overwritten by each class"""
    EPISODE_TEXT_FORMAT = 'EPISODE {episode_number}'

    """Whether this class uses unique source images for card creation"""
    USES_UNIQUE_SOURCES = True

    """Standard size for all title cards"""
    WIDTH = 3200
    HEIGHT = 1800
    TITLE_CARD_SIZE = f'{WIDTH}x{HEIGHT}'

    """Standard blur effect to apply to spoiler-free images"""
    BLUR_PROFILE = '0x60'

    @property
    @abstractmethod
    def TITLE_CHARACTERISTICS(self) -> dict[str, Union[int, bool]]:
        """
        Characteristics of title splitting for this card type. Must have
        keys for max_line_width, max_line_count, and top_heavy. See
        `Title` class for details.
        """
        raise NotImplementedError


    @property
    @abstractmethod
    def ARCHIVE_NAME(self) -> str:
        """How to name archive directories for this type of card"""
        raise NotImplementedError


    @property
    @abstractmethod
    def TITLE_FONT(self) -> str:
        """
        Standard font (full path or ImageMagick recognized font name) to
        use for the episode title text.
        """
        raise NotImplementedError


    @property
    @abstractmethod
    def TITLE_COLOR(self) -> str:
        """Standard color to use for the episode title text"""
        raise NotImplementedError


    @property
    @abstractmethod
    def USES_SEASON_TITLE(self) -> bool:
        """Whether this class uses season titles for archives"""
        raise NotImplementedError


    """Slots for standard style attributes"""
    __slots__ = ('valid', 'blur', 'grayscale')


    @abstractmethod
    def __init__(self,
            blur: bool = False,
            grayscale: bool = False,
            *,
            preferences: Optional['PreferenceParser'] = None,
            **unused,
        ) -> None:
        """
        Construct a new CardType. Must call super().__init__() to
        initialize the parent ImageMaker class (for PreferenceParser and
        ImageMagickInterface objects).

        Args:
            blur: Whether to blur the source image. Defaults to False.
            grayscale: Whether to convert the source image to grayscale.
                Defaults to False.
        """

        # Initialize parent ImageMaker
        super().__init__(preferences=preferences)

        # Object starts as valid
        self.valid = True

        # Store style attributes
        self.blur = blur
        self.grayscale = grayscale


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        attributes = ', '.join(f'{attr}={getattr(self, attr)!r}'
                               for attr in self.__slots__
                               if not attr.startswith('__'))

        return f'<{self.__class__.__name__} {attributes}>'


    @staticmethod
    def modify_extras( # pylint: disable=unused-argument
            extras: dict,
            custom_font: bool,
            custom_season_titles: bool,
        ) -> None:
        """
        Modify the given extras base on whether font or season titles
        are custom. The default behavior is to not modify the extras at
        all.

        Args:
            extras: Dictionary to modify.
            custom_font: Whether the font are custom.
            custom_season_titles: Whether the season titles are custom.
        """

        return None


    @staticmethod
    @abstractmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Abstract method to determine whether the given font
        characteristics indicate the use of a custom font or not.

        Returns:
            True if a custom font is indicated, False otherwise.
        """
        raise NotImplementedError


    @staticmethod
    @abstractmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> bool:
        """
        Abstract method to determine whether the given season
        characteristics indicate the use of a custom season title or not.

        Returns:
            True if a custom season title is indicated, False otherwise.
        """
        raise NotImplementedError


    @property
    def resize(self) -> ImageMagickCommands:
        """
        ImageMagick commands to only resize an image to the output title
        card size.
        """

        return [
            # Use 4:4:4 sampling by default
            f'-sampling-factor 4:4:4',
            # Full sRGB colorspace on source image
            f'-set colorspace sRGB',
            # Ignore profile conversion warnings
            f'+profile "*"',
            # Background resize shouldn't fill with any color
            f'-background transparent',
            f'-gravity center',
            # Fit to title card size
            f'-resize "{self.TITLE_CARD_SIZE}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
        ]


    @property
    def style(self) -> ImageMagickCommands:
        """
        ImageMagick commands to apply any style modifiers to an image.
        """

        return [
            # Use 4:4:4 sampling by default
            f'-sampling-factor 4:4:4',
            # Full sRGB colorspace on source image
            f'-set colorspace sRGB',
            # Ignore profile conversion warnings
            f'+profile "*"',
            # Optionally blur
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            # Optionally set gray colorspace
            f'-colorspace gray' if self.grayscale else '',
            # Reset to full colorspace
            f'-set colorspace sRGB' if self.grayscale else '',
        ]


    @property
    def resize_and_style(self) -> ImageMagickCommands:
        """
        ImageMagick commands to resize and apply any style modifiers to
        an image.
        """

        return [
            # Use 4:4:4 sampling by default
            f'-sampling-factor 4:4:4',
            # Full sRGB colorspace on source image
            f'-set colorspace sRGB',
            # Ignore profile conversion warnings
            f'+profile "*"',
            # Background resize shouldn't fill with any color
            f'-background transparent',
            f'-gravity center',
            # Fit to title card size
            f'-resize "{self.TITLE_CARD_SIZE}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            # Optionally blur
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            # Optionally set gray colorspace
            f'-colorspace gray' if self.grayscale else '',
            # Reset to full colorspace
            f'-set colorspace sRGB',
        ]


    def add_overlay_mask(self,
            file: Path,
            /,
            *,
            pre_processing: Optional[ImageMagickCommands] = None,
            x: int = 0,
            y: int = 0,
        ) -> ImageMagickCommands:
        """
        ImageMagick commands to add a top-level mask to the image.
        
        Args:
            file: Path to the file to search for the mask image
                alongside.
            pre_processing: Any ImageMagick commands to apply to the
                mask before it is overlaid.
            x: Offset X-coordinate to use when compositing the mask.
            y: Offset Y-coordinate to use when compositing the mask.

        Returns:
            List of ImageMagick commands.
        """

        # Do not apply any masks for stylized cards
        if self.blur or self.grayscale:
            return []

        # Look for mask file corresponding to this source image
        mask = file.parent / f'{file.stem}-mask.png'

        # If source mask does not exist, query for global mask
        mask = mask if mask.exists() else file.parent / 'mask.png'

        # Mask exists, return commands to compose atop image
        if mask.exists():
            log.debug(f'Identified mask image "{mask.resolve()}"')
            if pre_processing is None:
                pre_processing = self.resize_and_style

            return [
                f'\( "{mask.resolve()}"',
                *pre_processing,
                f'\) -geometry {x:+}{y:+}',
                f'-composite',
            ]

        return []


    @property
    def resize_output(self) -> ImageMagickCommands:
        """
        ImageMagick commands to resize the card to the global card
        dimensions.
        """

        return [
            f'-sampling-factor 4:4:4',
            f'-set colorspace sRGB',
            f'+profile "*"',
            f'-background transparent',
            f'-gravity center',
            f'-resize "{self.preferences.card_dimensions}"',
            f'-extent "{self.preferences.card_dimensions}"',
        ]


    def add_drop_shadow(self,
            commands: ImageMagickCommands,
            shadow: Union[str, Shadow],
            x: int = 0,
            y: int = 0,
            *,
            shadow_color: str = 'black',
        ) -> ImageMagickCommands:
        """
        Amend the given commands to apply a drop shadow effect.

        Args:
            commands: List of commands being modified. Must contain some
                image definition that can be cloned.
            shadow: IM Shadow string - i.e. `85x10+10+10`.
            x: X-position of the offset to apply when compositing.
            y: Y-position of the offset to apply when compositing.
            shadow_color: Color of the shadow to add.

        Returns:
            List of ImageMagick commands.
        """

        return [
            f'\(',
            *commands,
            f'\( +clone',
            f'-background "{shadow_color}"',
            f'-shadow {shadow} \)',
            f'+swap',
            f'-background None',
            f'-layers merge',
            f'+repage \)',
            f'-geometry {x:+.0f}{y:+.0f}',
            f'-composite',
        ]


    @abstractmethod
    def create(self) -> None:
        """
        Abstract method to create the title card outlined by the
        CardType. All implementations of this method should delete any
        intermediate files.
        """
        raise NotImplementedError
