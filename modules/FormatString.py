from logging import Logger
from typing import Any

from modules.CleanPath import CleanPath
from modules.Debug import InvalidFormatString, log


_MAX_ROMAN_NUMERAL = 3999
def to_roman_numeral(number: int, /) -> str:
    """
    Convert the given number to a roman numeral string.

    Args:
        number: Number to convert to a roman numeral.

    Returns:
        Roman numeral string representation of the given number.

    Raises:
        `InvalidFormatString` if the given number is not between 1 and
            3999.
    """

    # Verify number can be converted
    if not 1 <= number <= _MAX_ROMAN_NUMERAL:
        raise InvalidFormatString

    m_text = ['', 'M', 'MM', 'MMM']
    c_text = ['', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM']
    x_text = ['', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC']
    i_text = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX']

    # Get each places' roman numeral
    thousands = m_text[number // 1000]
    hundreds = c_text[(number % 1000) // 100]
    tens = x_text[(number % 100) // 10]
    ones = i_text[number % 10]

    return f'{thousands}{hundreds}{tens}{ones}'


class FormatString:
    """
    This class describes an arbitrary input fstring parser. Objects can
    be constructed with fstrings - e.g. "Test {variable}" - and
    data - e.g. {'variable': 123} - and will be evaluated as if a
    Python-typed `f''` string.

    ### NOTE This object makes uses of `eval()`.

    >>> FormatString.new('Example {name}', data={'name': 123})
    'Example 123'
    >>> FormatString.new('Example {name.upper()}', data={'name': 'test'})
    'Example TEST'
    """


    __slots__ = ('result', )


    def __init__(self, fstring: str, /, *, data: dict) -> None:
        """
        Initialize this objet with the given string and data. This
        evaluates the compiled fstring, and only stores the result.

        Args:
            fstring: String to interpret as an fstring.
            data: Data to make available in the fstring evalaution.
        """

        # pylint: disable=eval-used
        self.result = eval(
            compile('f"' + fstring.replace('"', '\\"') + '"', '', 'eval'),
            {
                '__builtins__': {
                    'NEWLINE': '\n',
                    'to_roman_numeral': to_roman_numeral
                }
            },
            data,
        )


    @staticmethod
    def new(
            fstring: str,
            /,
            *,
            data: dict,
            name: str,
            series: Any,
            episode: Any,
            log: Logger = log,
        ) -> str:
        """
        Construct a new FormatString with the given string and data,
        returning the evaluated result.

        Args:
            fstring: String to interpret as an fstring.
            data: Data to make available in the fstring evalaution.

        Returns:
            Evalauted fstring.

        Raises:
            InvalidFormatString: The compiled fstring cannot be
                evaluated.
        """

        try:
            return FormatString(fstring, data=data).result
        except NameError as exc:
            log.error(f'{series} {episode} Cannot format {name} - missing data '
                      f'"{exc}"')
            raise InvalidFormatString from exc
        except SyntaxError as exc:
            log.error(f'{series} {episode} Cannot format {name} - invalid '
                      f'format "{exc}"')
            raise InvalidFormatString from exc


    @staticmethod
    def new_path(
            fstring: str,
            /,
            *,
            data: dict,
            name: str,
            series: Any,
            episode: Any,
            log: Logger = log,
        ) -> str:
        """
        Construct a new path-safe format string with the given string
        and data. See `FormatString.new()`.
        """

        return CleanPath.sanitize_name(
            FormatString.new(
                fstring, data=data, name=name, series=series, episode=episode,
                log=log
            )
        )
