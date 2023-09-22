from re import compile as re_compile, IGNORECASE
from typing import Literal, Optional, Union

from modules.Debug import log


class Title:
    """
    This class describes a title. A Title can either be initialized with
    a full title without any formatting done to it, and then split by
    this class into multiple lines with `split()`; or it can be
    initialized with those lines directly. For example:

    >>> t = Title("The One Where Rachel's Sister Babysits")
    >>> t.split(25, 2, False)
    ["The One Where",
     "Rachel's Sister Babysits"]
    >>> t.split(25, 2, True)
    ["The One Where Rachel's",
     "Sister Babysits"]
    """

    """Characters that should be used for priority line splitting"""
    SPLIT_CHARACTERS = (':', ',', ')', ']', '?', '!', '-', '.', '/', '|')

    """Regex for identifying partless titles for MultiEpisodes"""
    PARTLESS_REGEX = (
        # Match for "title" ((digit)) or "title" (Part (digit))
        re_compile(r'^(.*?)\s*\((?:Part\s*)?(?:\d|[IVXLCDM])+\)', IGNORECASE),
        # Match for "title" (optional separator) Part (word)
        re_compile(r'^(.*?)(?::|\s*-|,)?\s+Part\s+[a-zA-Z0-9]+', IGNORECASE),
        # Match for "title" (Part (word))
        re_compile(r'^(.*?)\s*\(Part\s*[a-zA-Z0-9]+\)', IGNORECASE),
        # Match for "title" (roman numeral)
        re_compile(r'^(.*?)\s+[IVXLCDM]+\s*$', IGNORECASE),
    )

    __slots__ = (
        'full_title', '__title_lines', '__manually_specified', 'title_yaml',
        'match_title', '__original_title'
    )


    def __init__(self,
            title: Union[str, list[str]], *,
            original_title: Optional[str] = None
        ) -> None:
        """
        Constructs a new instance of a Title from either a full, unsplit
        title, or a list of title lines.

        Args:
            title: Title for this object.
            title: str if the full title (from any source), or a list if
                parsed from YAML.
            original_title: Original title for matching.
        """

        # If given as str, then title is not manually specified
        if isinstance(title, list):
            # If title was given line-by-line, join with spaces
            self.full_title = ' '.join(title)
            self.__title_lines = title
            self.__manually_specified = True
        else:
            try:
                self.full_title = str(title)
                self.__title_lines = []
                self.__manually_specified = False
            except Exception as e:
                raise TypeError(f'Cannot create Title with {title!r}') from e

        # This title as represented in YAML
        self.title_yaml = title

        # Generate title to use for matching purposes
        self.match_title = self.get_matching_title(self.full_title)
        if original_title != title and original_title:
            # Combine if manually specified
            if isinstance(original_title, list):
                original_title = ' '.join(original_title)
            self.__original_title = self.get_matching_title(original_title)
        else:
            self.__original_title = None


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return self.full_title


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'<Title title="{self.full_title}", lines={self.__title_lines}>'


    def get_partless_title(self) -> str:
        """
        Gets the partless title for this object. This removes
        parenthesized digits, and title with "part" in them.

        Returns:
            The partless title for this object.
        """

        # Attempt to match any compiled partless regex
        for regex in self.PARTLESS_REGEX:
            if (partless := regex.match(self.full_title)):
                # If this regex matched, return partless group
                return partless.group(1)

        # No match, return full title
        return self.full_title


    def __evenly_split(self) -> list[str]:
        """
        Attempt to evenly split this Title between two lines of text.

        Returns:
            List of strings that is this split title.
        """

        lines = [[], []]
        len_l1 = lambda: sum(map(len, lines[0]))
        len_l2 = lambda: sum(map(len, lines[1]))
        diff = lambda: abs(len_l2() - len_l1())

        # Add each word to the shortest line
        words = self.full_title.split()
        for word in words:
            # Always add word to end of last line
            lines[1].append(word)

            # While there is a last line, the first line is shorter than
            # the last, and the current line length difference is at
            # least twice the length of the next-popped word, move the
            # first word of the last line to last position on first line
            while (lines[1]
                   and len_l1() < len_l2()
                   and diff() >= 2 * len(lines[1][0])):
                lines[0].append(lines[1].pop(0))

        return list(map(' '.join,  lines))


    def __top_split(self,
            max_line_width: int,
            max_line_count: int,
        ) -> list[str]:
        """
        Args:
            max_line_width: Maximum line width to base splitting on.
            max_line_count: The maximum line count to split the title
                into.

        Returns:
            List of strings that is this split title.
        """

        all_lines = [self.full_title]
        for _ in range(max_line_count+2-1):
            # Start splitting from the last line added
            top, bottom = all_lines.pop(), ''
            while ((len(top) > max_line_width
                    or len(bottom) in range(1, 6))
                    and ' ' in top):
                # Look to split on special characters
                special_split = False
                for char in self.SPLIT_CHARACTERS:
                    # Split only if present after first third of next line
                    if f'{char} ' in top[max_line_width//2:max_line_width]:
                        top, bottom_add = top.rsplit(f'{char} ', 1)
                        top += char
                        bottom = f'{bottom_add} {bottom}'
                        special_split = True
                        break

                # If no special character splitting was done, split on space
                if not special_split:
                    try:
                        top, bottom_add = top.rsplit(' ', 1)
                        bottom = f'{bottom_add} {bottom}'.strip()
                    except ValueError:
                        break

            all_lines += [top, bottom]

        # Strip every line, delete blank entries
        all_lines = list(filter(len, map(str.strip, all_lines)))

        # If misformatted, combine overflow lines
        if len(all_lines) > max_line_count:
            all_lines[-2] = f'{all_lines[-2]} {all_lines[-1]}'
            del all_lines[-1]

        return all_lines


    def split(self,
            max_line_width: int,
            max_line_count: int,
            top_heavy: Union[bool, Literal['even']],
        ) -> list[str]:
        """
        Split this title's text into multiple lines. If the title cannot
        fit into the given parameters, line width might not be
        respected, but the maximum number of lines will be.

        Args:
            max_line_width: Maximum line width to base splitting on.
            max_line_count: The maximum line count to split the title
                into.
            top_heavy: Whether to split the title in a top-heavy style.
                This means the top lines will likely be longer than the
                bottom ones. False for bottom-heavy splitting.

        Returns:
            List of split title text to be read top to bottom.
        """

        # If the object was initialized with lines, return those
        if self.__manually_specified:
            return self.__title_lines

        # If the title can fit on one line, is one line or one word, return
        if (len(self.full_title) <= max_line_width
            or max_line_count <= 1
            or ' ' not in self.full_title):
            return [self.full_title]

        # Split title into two "even" width lines
        if top_heavy == 'even':
            return self.__evenly_split()

        # Misformat ahead..
        if len(self.full_title) > max_line_count * max_line_width:
            log.debug(f'Title {self} too long, potential misformat')

        if top_heavy:
            return self.__top_split(max_line_width, max_line_count)

        all_lines = [self.full_title]
        # For bottom heavy splitting, start on bottom and move text UP
        for _ in range(max_line_count+2-1):
            top, bottom = '', all_lines.pop()
            while ((len(bottom) > max_line_width
                    or len(top) in range(1, 6))
                    and ' ' in bottom):
                # Look to split on special characters
                special_split = False
                for char in self.SPLIT_CHARACTERS:
                    if f'{char} ' in bottom[:min(max_line_width,len(bottom)//2)]:
                        top_add, bottom = bottom.split(f'{char} ', 1)
                        top = f'{top} {top_add}{char}'
                        special_split = True
                        break

                # If no special character splitting was done, split on space
                if not special_split:
                    top_add, bottom = bottom.split(' ', 1)
                    top = f'{top} {top_add}'.strip()

            all_lines += [bottom, top]

        # Reverse order, strip every line, delete blank entries
        all_lines = list(filter(len, map(str.strip,all_lines[::-1])))

        # If misformatted, combine overflow lines
        if len(all_lines) > max_line_count:
            all_lines[-2] = f'{all_lines[-2]} {all_lines[-1]}'
            del all_lines[-1]

        return all_lines


    def apply_profile(self,
            profile: 'Profile', # type: ignore
            **title_characteristics: dict
        ) -> str:
        """
        Apply the given profile to this title. If this object was
        created with manually specified title lines, then the profile is
        applied to each line, otherwise it's applied to the full title.
        Then newlines are used to join each line

        Args:
            profile: Profile object to convert title with.

        Returns:
            This title with the given profile and splitting details
            applied.
        """

        # If manually specified, apply the profile to each line, skip splitting
        if self.__manually_specified:
            return '\n'.join(list(map(
                lambda line: profile.convert_title(line, True),
                self.__title_lines
            )))

        # Title lines weren't manually specified - apply profile, make new Title
        new_title = Title(profile.convert_title(self.full_title, False))

        # Call split on the new title, join those lines
        return '\n'.join(new_title.split(**title_characteristics))


    @staticmethod
    def get_matching_title(text: str) -> str:
        """
        Remove all non A-Z characters from the given title.

        Args:
            text: The title to strip of special characters.

        Returns:
            The input text with all non A-Z characters removed.
        """

        return ''.join(filter(str.isalnum, text)).lower()


    def matches(self, *titles: tuple[Union[str, 'Title']]) -> bool:
        """
        Get whether any of the given titles match this object.

        Args:
            titles: The titles to check.

        Returns:
            True if any of the given titles match this series, False
            otherwise.
        """

        def _get_title(title):
            if isinstance(title, Title):
                return self.get_matching_title(title.match_title)
            return self.get_matching_title(title)

        matching_titles = map(_get_title, titles)

        if self.__original_title is not None:
            return any(title in (self.__original_title, self.match_title)
                       for title in matching_titles)

        return any(title == self.match_title for title in matching_titles)
