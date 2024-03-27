from argparse import ArgumentParser
from pathlib import Path
from re import compile as re_compile
from typing import Union

try:
    from modules.Debug import log
except ImportError:
    from Debug import log


class Version:
    """
    A class describing some semantic version number. This class parses
    version strings particular to TCM and stores the parsed branch and
    version number(s) as attributes. Allows for comparison of Versions.

    For example:
    >>> v1 = Version('v1.14.1')
    >>> v2 = Version('v1.14.2')
    >>> v1 < v2, v1 == v2, v1 > v2
    (True, False, False)

    This also works for development-branch tagged versions, such as:
    >>> v3 = Version('v2.0-alpha3.0-webui10')
    >>> v4 = Version('v2.0-alpha3.0-webui3')
    >>> v3 < v4, v3 == v4, v3 > v4
    (False, False, True)
    """

    PRIMARY_REGEX = re_compile(
        r'^v(?P<version>\d+)\.(?P<sub_version>\d+)\.(?P<sub_sub_version>\d+)'
        r'(?:-(?P<branch>\D+)(?P<branch_iteration>\d+))?$'
    )
    PRIMARY_DEFAULTS = {'branch': 'master', 'branch_iteration': 0}

    WEB_UI_REGEX = re_compile(
        r'^.*-alpha\.(?P<version>\d+)\.(?P<sub_version>\d+)'
        r'(\.(?P<sub_sub_version>\d+))?(?:-(?P<branch>\D+)'
        r'(?P<branch_iteration>\d+))?$'
    )
    WEB_UI_DEFAULTS = {
        'branch': 'master', 'sub_sub_version': 0, 'branch_iteration': 0
    }


    def __init__(self, /, version_str: str) -> None:
        """
        Initialize a Version object with the given version string.

        Args:
            version_str: Version string to parse for Version info.

        Raises:
            ValueError: If the given `version_str` cannot be parsed.
        """

        # Store raw version string
        self.version_str = version_str

        # Extract version data from regex, merging defaults
        if (data_match := self.PRIMARY_REGEX.match(version_str)) is not None:
            version_data = self.PRIMARY_DEFAULTS | data_match.groupdict()
        elif (data_match := self.WEB_UI_REGEX.match(version_str)) is not None:
            version_data = self.WEB_UI_DEFAULTS | data_match.groupdict()
            if version_data['sub_sub_version'] is None:
                version_data['sub_sub_version'] = 0
        else:
            raise ValueError(f'Cannot identify version from {version_str}')

        # Initialize unparsed attributes
        version_data['branch'] = version_data['branch'] or 'master'
        if version_data['branch_iteration'] is None:
            version_data['branch_iteration'] = 0

        # Store branch and version(s)
        self.branch: str = version_data['branch']
        self.version: tuple[int] = (
            int(version_data['version']),
            int(version_data['sub_version']),
            int(version_data['sub_sub_version']),
            int(version_data['branch_iteration']),
        )


    def __repr__(self) -> str:
        """Get an unambigious string representation of the object."""

        return f'<Version {self.version} on {self.branch} branch>'


    def __str__(self) -> str:
        """Get a printable string representation of this object."""

        # Master branch, omit branch and iteration
        if self.branch == 'master':
            return (
                f'v{self.version[0]}.{self.sub_version}.{self.sub_sub_version}'
            )

        return (
            f'v{self.version[0]}.{self.sub_version}.{self.sub_sub_version}'
            f'-{self.branch}{self.branch_iteration}'
        )


    def __eq__(self, other: 'Version') -> bool:
        """
        Determine whether two Version objects are identical.

        Args:
            other: Version object to compare against.

        Returns:
            True if the two objects have the same branch and version
            data.
        """

        if not isinstance(other, Version):
            raise TypeError(f'Can only compare Version objects')

        return self.version == other.version and self.branch == other.branch


    def __gt__(self, other: 'Version') -> bool:
        """
        Determine whether this object is a newer version than the other.

        Args:
            other: Version object to compare against.

        Returns:
            True if this object represents a newer version than the
            other object. Otherwise False.
        """

        if not isinstance(other, Version):
            raise TypeError(f'Can only compare Version objects')

        # Compare each like-version
        for this_v, other_v in zip(self.version, other.version):
            # Equal, skip
            if this_v == other_v:
                continue

            # This version is higher than other, always gt
            if this_v > other_v:
                return True

            # This version is lower than other, always lt
            if this_v < other_v:
                return False

        # Equal, not gt
        return False


    def __lt__(self, other: 'Version') -> bool:
        """
        Determine whether this object is an older version than the
        other.

        Args:
            other: Version object to compare against.

        Returns:
            True if this object represents an older version than the
            other object. Otherwise False.

        Raises:
            TypeError if `other` is not a `Version` object.
        """

        if not isinstance(other, Version):
            raise TypeError(f'Can only compare Version objects')

        # Compare each like-version
        for this_v, other_v in zip(self.version, other.version):
            # Equal, skip
            if this_v == other_v:
                continue

            # This version is lower than other, always lt
            if this_v < other_v:
                return True

            # This version is higher than other, always gt
            if this_v > other_v:
                return False

        # Equal, not lt
        return False


    @property
    def sub_version(self) -> int:
        """Subversion of this object - i.e. 1.{x}.3"""

        return self.version[1]


    @property
    def sub_sub_version(self) -> int:
        """Subversion of this object - i.e. 1.2.{x}"""

        return self.version[2]


    @property
    def branch_iteration(self) -> int:
        """Subversion of this object - i.e. 1.2.3-branch{x}"""

        return self.version[3]


class Changelog:
    """Helper class for converting Markdown changelog files to HTML."""

    """How many spaces corresponds to a single indent"""
    INDENT_SPACES = 2

    """Regex for matching types of content"""
    BOLD_REGEX = re_compile(r'__([^_]+)__')
    CODE_REGEX = re_compile(r'`([^`]+)`')
    ITALIC_REGEX = re_compile(r'\s+_([^_]+)_\s+')
    LINK_REGEX = re_compile(r'\[(.+)]\((.+)\)')
    HEADER_REGEX = re_compile(r'^#\s+(.+)$')
    OUTER_BULLET_REGEX = re_compile(r'^-\s+(.+)$')
    INNER_BULLET_REGEX = re_compile(r'^(\s+)-\s+(.+)$')
    IMAGE_REGEX = re_compile(r'^\s+<img.*src="(.+)".*\/?>$')


    def __init__(self, file: Union[Path, str], /) -> None:
        """
        Parse the Changelog (Markdown) in the given file.
        
        Args:
            file: Path to the file to parse.
        """

        i_1, i_2, i_3 = self._indent(1), self._indent(2), self._indent(3)
        html: list[str] = []
        _prev_indent = 0

        for line in Path(file).read_text().splitlines():
            # Header -> <h2>
            if (match := self.HEADER_REGEX.match(line)):
                # Close previous indented list
                if _prev_indent:
                    html.append(f'{i_2}</div>')
                    html.append(f'{i_1}</div>')
                # Close previous section list
                if html:
                    html.append(f'</div>')
                # Start new list
                html.append(f'<h2>{match.group(1)}</h2>')
                html.append(f'<div class="ui ordered list">')
                _prev_indent = 0
            # Outer-level bullet
            elif (match := self.OUTER_BULLET_REGEX.match(line)):
                # Was in prior sublist, close list
                if _prev_indent:
                    html.append(f'{i_2}</div>') # Close list
                    html.append(f'{i_1}</div>') # Close item

                html.append(f'{i_1}<div class="item">{self._format(match.group(1))}</div>')
                _prev_indent = 0
            # Inner bullet
            elif (match := self.INNER_BULLET_REGEX.match(line)):
                curr_indent = len(match.group(1))
                # This line is below last line, turn last line into list
                if _prev_indent < curr_indent:
                    html[-1] = html[-1][:-len('</div>')] # Remove item closing tag
                    html.append(f'{i_2}<div class="list">')
                    html.append(f'{i_3}<div class="item">{self._format(match.group(2))}</div>')
                    _prev_indent = curr_indent
                # Line is same indent as previous, add as item
                elif _prev_indent == curr_indent:
                    html.append(f'{i_3}<div class="item">{self._format(match.group(2))}</div>')
                # Line is less indented, add as item
                else:
                    html.append(f'{i_2}</div>')
                    html.append(f'{i_2}<div class="item">{self._format(match.group(2))}</div>')
                    _prev_indent = curr_indent
            # Image
            elif (match := self.IMAGE_REGEX.match(line)):
                html[-1] = html[-1][:-len('</div>')]
                html.append(f'{i_2}<div class="list">')
                html.append(f'{i_3}<img width="50%" src="{match.group(1)}">')
                html.append(f'{i_2}</div>')
                html.append(f'{i_1}</div>')

        # Close final list
        html.append(f'</div>')

        # Store resulting HTML string
        self.html = '\n'.join(html)
        log.debug(f'Parsed {file}')


    def _indent(self, amount: int, /) -> str:
        """
        Get the string corresponding to the given level of indentation.

        Args:
            amount: How much indentation to return.

        Returns:
            Indentation string.
        """

        return ' ' * amount * Changelog.INDENT_SPACES


    def _format(self, text: str, /) -> str:
        """
        Format the given text for HTML. This replaces markdown elements
        like italics, code highlights, and links with their HTML
        equivalents.

        >>> print(self._format('This `code` _example_ with [links!](test.com)'))
        'This <b>code</b> <i>example</i> with <a href="test.com" target="_blank">links!</a>

        Args:
            text: Text to format.

        Returns:
            Formatted text.
        """

        return self.LINK_REGEX.sub(
            r'<a href="\2" target="_blank">\1</a>',
            self.BOLD_REGEX.sub(
                r'<b>\1</b>',
                self.CODE_REGEX.sub(
                    r'<b>\1</b>',
                    self.ITALIC_REGEX.sub(
                        r'<i>\1</i>',
                        text,
                    )
                )
            )
        )

    def write(self, file: Union[Path, str], /) -> None:
        """Write this Changelog (HTML) to the given file."""

        Path(file).write_text(self.html)
        log.info(f'Wrote converted HTML changelog to {file}')


if __name__ == '__main__':
    ap = ArgumentParser()
    ap.add_argument('changelog', type=Path, help='Markdown file to parse')
    ap.add_argument('output', type=Path, help='HTML file to write')
    args = ap.parse_args()

    Changelog(args.changelog).write(args.output)
