from re import match

from modules.Debug import info, warn, error

class Title:
    """
    This class describes a title. A Title can either be initialized with a full
    title without any formatting done to it, and then split by this class into
    multiple lines with `split()`; or it can be initialized with those lines
    directly. For example:

    >>> t = Title("The One Where Rachel's Sister Babysits")
    >>> t.split(25, 2, False)
    ["The One Where",
     "Rachel's Sister Babysits"]
    >>> t.split(25, 2, True)
    ["The One Where Rachel's",
     "Sister Babysits"]
    """

    def __init__(self, title) -> None:
        """
        Constructs a new instance of a Title from either a full, unsplit title,
        or a list of title lines.
        
        :param      title:  Title for this object.
        :type       title:  str if the full title (from any source), or a list
                            if parsed from YAML
        """
        
        # If given as str, then title is not manually specified
        if isinstance(title, str):
            self.full_title = title
            self.__title_lines = []
            self.__manually_specified = False
        elif isinstance(title, list):
            # If title was given line-by-line, join with spaces
            self.full_title = ' '.join(title)
            self.__title_lines = title
            self.__manually_specified = True
        else:
            error(f'Title can only be created by str or list')
            return

        # This title as represented in YAML
        self.title_yaml = title

        # Generate title to use for matching purposes
        match_func = lambda c: match('[a-zA-Z0-9]', c)
        self.match_title = ''.join(filter(match_func, title)).lower()


    def split(self, max_line_width: int, max_line_count: int,
              top_heavy: bool) -> list:
        """
        Split this title's text into multiple lines. If the title cannot fit
        into the given parameters, line width might not be respected, but the
        maximum number of lines will be.
        
        :param      max_line_width: Maximum line width to base splitting on. 
        :param      max_line_count: The maximum line count to split the title
                                    into.
        :param      top_heavy:      Whether to split the title in a top-heavy
                                    style. This means the top lines will likely
                                    be longer than the bottom ones. False for
                                    bottom-heavy splitting.
        
        :returns:   List of split title text to be read top to bottom.
        """

        # If the object was initialized with lines, return those
        if self.__manually_specified:
            return self.__title_lines

        # If the title can fit on one line, or a single line is requested
        if len(self.full_title) <= max_line_width or max_line_count <= 1:
            return [self.full_title]

        # Misformat ahead..
        if len(self.full_title) > max_line_count * max_line_width:
            #print('WARN: Title too long, potential misformat')
            pass

        # Start splitting on the base full title
        all_lines = [self.full_title]

        # For top heavy splitting, start on top and move text DOWN
        if top_heavy:
            for _ in range(max_line_count+2-1):
                # Start splitting from the last line added
                top, bottom = all_lines.pop(), ''
                while ((len(top) > max_line_width and ' ' in top) or
                    len(bottom) in range(1, max_line_width//3)):
                    # Look to split on special characters
                    special_split = False
                    for char in (':', ',', '(', ')', '[', ']'):
                        if f'{char} ' in top[:max_line_width]:
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
            all_lines = list(filter(lambda l: len(l), map(str.strip,all_lines)))

            # If misformatted, combine overflow lines
            if len(all_lines) > max_line_count:
                all_lines[-2] = f'{all_lines[-2]} {all_lines[-1]}'
                del all_lines[-1]

            warn(f'Top split "{self.full_title}" into {"|".join(all_lines)}')
            return all_lines

        # For bottom heavy splitting, start on bottom and move text UP
        for _ in range(max_line_count+2-1):
            top, bottom = '', all_lines.pop()
            while ((len(bottom) > max_line_width and ' ' in bottom) or
                len(top) in range(1, max_line_width//3)):
                # Look to split on special characters
                special_split = False
                for char in (':', ',', '(', ')', '[', ']'):
                    if f'{char} ' in bottom[:max_line_width]:
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
        all_lines = list(filter(lambda l:len(l),map(str.strip,all_lines[::-1])))

        # If misformatted, combine overflow lines
        if len(all_lines) > max_line_count:
            all_lines[-2] = f'{all_lines[-2]} {all_lines[-1]}'
            del all_lines[-1]
        warn(f'Bottom split "{self.full_title}" into {"|".join(all_lines)}')
        return all_lines


    def apply_profile(self, profile: 'Profile',
                      **title_characteristics: dict) -> str:
        """
        Apply the given profile to this title. If this object was created with
        manually specified title lines, then the profile is applied to each
        line, otherwise it's applied to the full title. Then newlines ('\n') are
        used to join each line
        
        :param      profile:    Profile object to call `convert_title()`.
        
        :returns:   This title with the given profile and splitting details
                    applied.
        """

        # If manually specified, apply the profile to each line, skip splitting
        if self.__manually_specified:
            return '\n'.join(list(map(
                lambda line: profile.convert_title(line),
                self.__title_lines
            )))

        # Title lines weren't manually specified - apply profile, make new Title
        new_title = Title(profile.convert_title(self.full_title))

        # Call split on the new title, join those lines
        return '\n'.join(new_title.split(**title_characteristics))
        