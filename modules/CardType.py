from abc import abstractmethod

from titlecase import titlecase

from modules.ImageMaker import ImageMaker

class CardType(ImageMaker):
    """
    This class describes an abstract card type. A CardType is a subclass of
    ImageMaker, because all CardTypes are designed to create title cards. This
    class outlines the requirements for creating a custom type of title card.

    All subclasses of CardType must implement this classe's abstract properties
    and methods in order to work with the TitleCardMaker. However, not all
    CardTypes need to use every argument of these methods. For example, the
    StandardTitleCard utilizes most all customizations for a title card (i.e.
    custom fonts, colors, sizing, season titles, etc.), while a
    StarWarsTitleCard doesn't use anything except the episode title and number.
    """

    """Default case for all episode text"""
    DEFAULT_FONT_CASE = 'upper'

    """Mapping of 'case' strings to format functions"""
    CASE_FUNCTION_MAP = {
        'upper': str.upper,
        'lower': str.lower,
        'title': titlecase,
    }

    """Standard size for a title card"""
    TITLE_CARD_SIZE: str = '3200x1800'

    @property
    @abstractmethod
    def ARCHIVE_NAME(self) -> str:
        """How to name archive directories for this type of card"""
        raise NotImplementedError(f'All CardType objects must implement this')

    @property
    @abstractmethod
    def TITLE_FONT(self) -> str:
        """
        Standard font (full path or ImageMagick recognized font name) to use for
        the episode title text
        """
        raise NotImplementedError(f'All CardType objects must implement this')

    @property
    @abstractmethod
    def TITLE_COLOR(self) -> str:
        """Standard color to use for the episode title text"""
        raise NotImplementedError(f'All CardType objects must implement this')

    @property
    @abstractmethod
    def FONT_REPLACEMENTS(self) -> dict:
        """Standard font replacements for the episode title font"""
        raise NotImplementedError(f'All CardType objects must implement this')

    @property
    @abstractmethod
    def USES_SEASON_TITLE(self) -> bool:
        """Whether this class uses season titles for the purpose of archives"""
        raise NotImplementedError(f'All CardType objects must implement this')


    @abstractmethod
    def __init__(self) -> None:
        """
        Construct a new CardType. Must call super().__init__() to initialize the
        parent ImageMaker class (for PreferenceParser and ImageMagickInterface
        objects).
        """
        
        super().__init__()


    @staticmethod
    @abstractmethod
    def split_title() -> (str, str):
        """
        Abstract method to split an episode title into two lines of text.
        """
        raise NotImplementedError(f'All CardType objects must implement this')


    def _split_at_width(title: str, width: int) -> (str, str):
        """
        Split a given title after a given width. This method prioritizes
        splitting on colons, commas, and parentheses in addition to spaces.

        :param      title:  The episode title to split.

        :param      width:  After how many characters to begin splitting.

        :returns:   Tuple of the two lines of title text as "top" and "bottom".
        """

        top, bottom = '', title
        if len(title) >= width:
            # Only look for colon/comma in the first half of the text to avoid
            # long top lines for titles with these in the last part of the title
            if ': ' in bottom[:len(bottom)//2]:
                top, bottom = title.split(': ', 1)
                top += ':'
            elif ', ' in bottom[:len(bottom)//2]:
                top, bottom = title.split(', ', 1)
                top += ','
            elif '( ' in bottom[:len(bottom)//2]:
                top, bottom = title.split('( ', 1)
                top += '('
            else:
                top, bottom = title.split(' ', 1)

            while len(bottom) >= width:
                top2, bottom = bottom.split(' ', 1)
                top += f' {top2}'

        return top, bottom


    @staticmethod
    @abstractmethod
    def is_custom_font() -> bool:
        """
        Abstract method to determine whether the given font characteristics
        indicate the use of a custom font or not.
        
        :returns:   True if a custom font is indicated, False otherwise.
        """
        raise NotImplementedError(f'All CardType objects must implement this')


    @abstractmethod
    def create(self) -> None:
        """
        Abstract method to create the title card outlined by the CardType. All
        implementations of this method should delete any intermediate files.
        """
        raise NotImplementedError(f'All CardType objects must implement this')

