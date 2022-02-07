from abc import abstractmethod

from modules.ImageMaker import ImageMaker

class CardType(ImageMaker):
    """
    This class describes a card type.
    """

    DEFAULT_FONT_CASE = 'upper'
    CASE_FUNCTION_MAP = {
        'upper': str.upper,
        'lower': str.lower,
        'title': str.title,
    }

    @property
    @abstractmethod
    def ARCHIVE_NAME(self) -> str:
        pass

    @property
    @abstractmethod
    def TITLE_FONT(self) -> str:
        pass

    @property
    @abstractmethod
    def TITLE_COLOR(self) -> str:
        pass

    @property
    @abstractmethod
    def FONT_REPLACEMENTS(self) -> dict:
        pass


    @abstractmethod
    def __init__(self) -> None:
        """
        Constructs a new instance.
        """
        
        super().__init__()


    @staticmethod
    @abstractmethod
    def split_title() -> (str, str):
        """

        """
        pass


    def _split_at_width(title: str, width: int) -> (str, str):
        """
        Splits an at width.
        
        :param      width:  The width
        :type       width:  int
        
        :returns:   { description_of_the_return_value }
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
        Determines if custom font.
        
        :returns:   True if custom font, False otherwise.
        """
        pass


    @abstractmethod
    def create(self) -> None:
        """
        { function_description }
        
        :returns:   { description_of_the_return_value }
        """
        
        pass

