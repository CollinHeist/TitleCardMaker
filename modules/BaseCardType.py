from abc import abstractmethod
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Literal,
    Optional,
    Union
)

from titlecase import titlecase

from app.schemas.card import CardTypeDescription, Extra
from modules.Debug import log
from modules.ImageMaker import Dimensions, ImageMagickCommands, ImageMaker
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from modules.Font import Font
    from app.models.preferences import Preferences

CardDescription = CardTypeDescription

__all__ = [
    'BaseCardType',
    'CardDescription',
    'CardTypeDescription',
    'Coordinate',
    'Dimensions',
    'Extra',
    'ImageMagickCommands',
    'ImageMaker',
    'Rectangle',
    'TextCase',
]


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


    def __repr__(self) -> str:
        """
        Detailed object representation.
        
        >>> repr(Coordinate(2, 3))
        'Coordinate(2, 3)'
        """
        return f'Coordinate({self.x}, {self.y})'


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


    def __repr__(self) -> str:
        """Unambiguous representation of this object."""

        return f'Rectangle({self.start!r}, {self.end!r})'


    def __str__(self) -> str:
        """
        Represent this Rectangle as a string. This is the joined string
        representation of the start and end coordinate.
        """

        return f'{str(self.start)},{str(self.end)}'


    @property
    def width(self) -> float:
        """Width of this Rectangle."""

        return abs(self.start.x - self.end.x)

    @property
    def height(self) -> float:
        """Height of this Rectangle."""

        return abs(self.start.y - self.end.y)


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

TextCase = Literal['blank', 'lower', 'source', 'title', 'upper']

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
    DEFAULT_FONT_CASE: TextCase = 'upper'

    """Default font replacements"""
    FONT_REPLACEMENTS: dict[str, str] = {}

    """Mapping of 'case' strings to format functions"""
    CASE_FUNCTIONS: dict[TextCase, Callable[[Any], str]] = {
        'blank': lambda _: '',
        'lower': str.lower,
        'source': str,
        'title': titlecase,
        'upper': str.upper,
    }

    """Default episode text format string, can be overwritten by each class"""
    EPISODE_TEXT_FORMAT: str = 'Episode {episode_number}'

    """Whether this class uses unique source images for card creation"""
    USES_UNIQUE_SOURCES: bool = True

    """Whether this class uses Source Images at all"""
    USES_SOURCE_IMAGES: bool = True

    """Standard size for all title cards"""
    WIDTH: int = 3200
    HEIGHT: int = 1800
    TITLE_CARD_SIZE: str = f'{WIDTH}x{HEIGHT}'

    """Standard blur effect to apply to spoiler-free images"""
    BLUR_PROFILE: str = '0x60'

    @property
    @abstractmethod
    def API_DETAILS(self) -> CardTypeDescription: # pylint: disable=missing-function-docstring
        raise NotImplementedError


    @property
    @abstractmethod
    def TITLE_CHARACTERISTICS(self) -> SplitCharacteristics:
        """Characteristics of title splitting for this card type."""
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
            preferences: Optional['Preferences'] = None,
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


    def __init_subclass__(cls, **kwargs) -> None:
        """
        Initialize the subclass CardType. After initialization, this
        performs basic validations on the class for required
        implementations. This is done on the class itself, not an
        instance of the class.
        """

        super().__init_subclass__(**kwargs)

        if not isinstance(cls.API_DETAILS, CardTypeDescription):
            raise TypeError(
                f'{cls.__name__}.API_DETAILS must be a CardTypeDescription '
                f'object'
            )

        try:
            SplitCharacteristics(**cls.TITLE_CHARACTERISTICS) # type: ignore
        except Exception:
            raise TypeError(
                f'{cls.__name__}.TITLE_CHARACTERISTICS must be a '
                f'SplitCharacteristics dictionary.'
            )

        if not isinstance(cls.ARCHIVE_NAME, str):
            raise TypeError(f'{cls.__name__}.ARCHIVE_NAME must be a string')
        if len(cls.ARCHIVE_NAME) == 0:
            raise ValueError(
                f'{cls.__name__}.ARCHIVE_NAME must be at least 1 character long'
            )

        if not isinstance(cls.DEFAULT_FONT_CASE, str):
            raise TypeError(f'{cls.__name__}.DEFAULT_FONT_CASE must be a string')
        if cls.DEFAULT_FONT_CASE not in ('blank', 'lower', 'source', 'title',
                                         'upper'):
            raise TypeError(
                f'{cls.__name__}.DEFAULT_FONT_CASE must be "blank", "lower", '
                f'"source", "title", or "upper"'
            )

        if not isinstance(cls.TITLE_COLOR, str):
            raise TypeError(f'{cls.__name__}.TITLE_COLOR must be a string')

        if not isinstance(cls.FONT_REPLACEMENTS, dict):
            raise TypeError(
                f'{cls.__name__}.FONT_REPLACEMENTS must be a dictionary'
            )

        if not all(isinstance(k, str) and isinstance(v, str)
                   for k, v in cls.FONT_REPLACEMENTS.items()):
            raise TypeError(
                f'All keys and values of {cls.__name__}.FONT_REPLACEMENTS must '
                f'strings'
            )


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        attributes = ', '.join(
            f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__
            if not attr.startswith('__')
        )

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


    @classmethod
    def _is_custom_font(
            cls: type['BaseCardType'],
            font: 'Font',
        ) -> bool:
        """
        Whether the given font is custom based on all the standard
        font definitions of this class.

        Args:
            font: Font being evaluated.

        Returns:
            True if the given Font is customized, False otherwise.
        """

        return ((font.color != cls.TITLE_COLOR)
            or (font.file != cls.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
            or (font.stroke_width != 1.0)
            or (font.vertical_shift != 0)
        )


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


    @staticmethod
    def resolve_format_strings(**data) -> dict:
        """
        Resolve any class-specific format strings. If a subclass does
        not implement this, the data is returned unmodified.
        """

        return data


    @staticmethod
    def get_title_split_characteristics(
            characteristics: SplitCharacteristics,
            default_font_file: str,
            data: dict,
        ) -> SplitCharacteristics:
        """
        Get the title split characteristics for the card defined by the
        given card data. By default this modifies the max line width
        by the `font_size` (if the default Font is used), and adds the
        `font_line_split_modifier` (if specified).

        Args:
            characteristics: Base split characteristics being modified
                for this card.
            default_font_file: Default font file for size evaluation.
            data: Card data to evaluate for any changes to the split
                characteristics.

        Returns:
            SplitCharacteristics object which defines how to split
            titles.
        """

        if ('font_size' in data and 'font_file' in data
            and data['font_file'] == default_font_file):
            characteristics['max_line_width'] = int(
                characteristics['max_line_width'] / float(data['font_size'])
            )
        if 'font_line_split_modifier' in data:
            characteristics['max_line_width'] += int(
                data['font_line_split_modifier']
            )

        return characteristics


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
        # Prioritize episode-specific mask, then general mask
        if (mask := list(file.parent.glob(f'{file.stem}-mask.*'))):
            mask = mask[0]
        elif (mask := list(file.parent.glob(f'{file.stem}_mask.*'))):
            mask = mask[0]
        elif (mask := list(file.parent.glob(f'mask.*'))):
            mask = mask[0]
        else:
            return []

        log.debug(f'Identified mask image "{mask.resolve()}"')
        if pre_processing is None:
            pre_processing = self.resize_and_style

        return [
            f'\( "{mask.resolve()}"',
            *self.resize,
            *pre_processing,
            f'\) -geometry {x:+}{y:+}',
            f'-composite',
        ]


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
            f'-resize "{self.card_dimensions}"',
            f'-extent "{self.card_dimensions}"',
            f'-quality {self.quality}',
        ]


    def add_drop_shadow(self,
            commands: ImageMagickCommands,
            shadow: Union[str, Shadow],
            x: Union[int, float] = 0,
            y: Union[int, float] = 0,
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
