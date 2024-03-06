from datetime import datetime
from json import dumps, JSONEncoder
from logging import Logger
from pathlib import Path
from typing import Any

from num2words import num2words
from titlecase import titlecase

from modules.CleanPath import CleanPath
from modules.Debug import InvalidFormatString, log


# Patch JSON dumps to work with CleanPath objects
def wrapped_default(self, obj):
    if isinstance(obj, (CleanPath, Path)):
        return str(obj.resolve())
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%dT%H:%M:%S%z') # ISO-8601
    return getattr(obj.__class__, '__json__', wrapped_default.default)(obj)
wrapped_default.default = JSONEncoder().default
JSONEncoder.original_default = JSONEncoder.default
JSONEncoder.default = wrapped_default


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
        raise InvalidFormatString(f'Number {number} cannot be converted to a '
                                  f'roman numeral')

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


def to_cardinal(number: int, /, lang: str = 'en') -> str:
    """
    Convert the given number to its cardinal spelling in the given
    language.

    Args:
        number: Number to convert.
        lang: Language code of the conversion.

    Returns:
        Cardinal spelling of the give number.

    Raises:
        NotImplementedError: The given number cannot be converted in the
            specified language.
    """

    return num2words(number, to='cardinal', lang=lang)


def to_ordinal(number: int, /, lang: str = 'en') -> str:
    """
    Convert the given number to its ordinal spelling in the given
    language.

    Args:
        number: Number to convert.
        lang: Language code of the conversion.

    Returns:
        Cardinal spelling of the give number.

    Raises:
        NotImplementedError: The given number cannot be converted in the
            specified language.
    """

    return num2words(number, to='ordinal', lang=lang)


def to_short_ordinal(number: int, /, lang: str = 'en') -> str:
    """
    Convert the given number to a shorthand ordinal spelling in the
    given language.

    Args:
        number: Number to convert.
        lang: Language code of the conversion.

    Returns:
        Shorthand ordinal - e.g. `2nd`, `12th`, etc.

    Raises:
        NotImplementedError: The given number cannot be converted in the
            specified language.
    """

    return num2words(number, lang=lang, to='ordinal_num')


def format_date(date: datetime, fmt: str, /) -> str:
    """
    Format the given date with the given format string. This is just a
    wrapper for `date.strftime(fmt)`.

    Args:
        date: Datetime being formatted.
        fmt: Format string to format the date with. See strftime.org for
            more.

    Returns:
        Formatted string of the given date.
    """

    return date.strftime(fmt)


_BUILTINS = {
    'NEWLINE': '\n',
    'titlecase': titlecase,
    'to_roman_numeral': to_roman_numeral,
    'to_cardinal': to_cardinal,
    'to_ordinal': to_ordinal,
    'to_short_ordinal': to_short_ordinal,
    'format_date': format_date,
}


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


    def __init__(self,
            fstring: str,
            /,
            *,
            data: dict,
            catch: bool = True,
        ) -> None:
        """
        Initialize this objet with the given string and data. This
        evaluates the compiled fstring, and only stores the result.

        Args:
            fstring: String to interpret as an fstring.
            data: Data to make available in the fstring evalaution.
            catch: Whether to catch any Exceptions.

        Raises:
            InvalidFormatString: The fstring is invalid and `catch` is
                true.
            NameError, NotImplementedError, SyntaxError: There is some
                invalid syntax in the fstring and `catch` is false.
        """

        # pylint: disable=eval-used
        try:
            self.result: str = eval(
                compile(f'f"""{fstring}"""', '', 'eval'),
                {'__builtins__': _BUILTINS},
                data,
            )
        except (NameError, SyntaxError, NotImplementedError, KeyError) as exc:
            log.debug(f'Error evaluating ({fstring}) with ({dumps(data, indent=2)})')
            raise (InvalidFormatString if catch else exc) from exc


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
            return FormatString(fstring, data=data, catch=False).result
        except NameError as exc:
            log.error(f'{series} {episode} Cannot format {name} - missing data '
                      f'"{exc}"')
            raise InvalidFormatString from exc
        except (SyntaxError, NotImplementedError) as exc:
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
                log=log,
            )
        )
