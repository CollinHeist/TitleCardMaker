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

    def __init__(self, full_title: str=None, *title_lines: tuple) -> None:
        """
        Constructs a new instance of a Title.
        
        :param      full_title:     Complete, unsplit title.
        :param      title_lines:    A title that is pre-split into any number
                                    of lines.
        """
        

        if full_title != None:
            # If the full title was given
            self.full_title = full_title
            self.__manually_specified = False
        else:
            # If title was given line-by-line, join with spaces
            self.full_title = ' '.join(title_lines)
            self.__manually_specified = True

        # If title lines were specified
        self.__title_lines = [] if self.__skip_split else list(title_lines)

        # Generate title to use for matching purposes
        match_func = lambda c: match('[a-zA-Z0-9]', c)
        self.match_title = ''.join(filter(match_func, text)).lower()


    def split(self, line_width: int, max_line_count: int=2,
              top_heavy: bool=False) -> list:
        """
        Split this title's text into multiple lines. If the title cannot fit
        into the given parameters, line width might not be respected, but the
        maximum number of lines will be.
        
        :param      line_width:     Maximum ine width to base splitting on. 
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
        if len(self.full_title) <= line_width or max_line_count <= 1:
            return [self.full_title]

        # Misformat ahead..
        if len(self.full_title) > max_line_count * character_count:
            #print('WARN: Title too long, potential misformat')
            pass

        all_lines = [self.title]

        # For top heavy splitting, start on top and move text DOWN
        if top_heavy:
            for _ in range(max_line_count+2-1):
                # Start splitting from the last line added
                top, bottom = all_lines.pop(), ''
                while ((len(top) > line_width and ' ' in top) or
                    len(bottom) in range(1, line_width//3)):
                    # Look to split on special characters
                    special_split = False
                    for char in (':', ',', '(', ')', '[', ']'):
                        if f'{char} ' in top[:line_width]:
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

            return all_lines

        # For bottom heavy splitting, start on bottom and move text UP
        for _ in range(max_line_count+2-1):
            top, bottom = '', all_lines.pop()
            while ((len(bottom) > line_width and ' ' in bottom) or
                len(top) in range(1, line_width//3)):
                # Look to split on special characters
                special_split = False
                for char in (':', ',', '(', ')', '[', ']'):
                    if f'{char} ' in bottom[:line_width]:
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

        return all_lines


    def apply_profile(self, profile: 'Profile', line_width: int,
                      max_line_count: int) -> list:
        """
        Apply the given profile to this title. If this object was created with
        manually specified title lines, then the profile is applied to each
        line, otherwise it's applied to the full title.
        
        :param      profile:    Profile object to call `convert_title()`.
        
        :returns:   List of modified title lines.
        """

        # If manually specified, apply the profile to each line, skip splitting
        if self.__manually_specified:
            return list(map(
                lambda line: profile.convert_title(line),
                self.__title_lines
            ))

        # Title lines weren't manually specified, apply profile then split
        return self.split(
            profile.convert_title(self.full_title),
            line_width,
            max_line_count
        )
        