from regex import match, IGNORECASE

from modules.Debug import *
from modules.StandardTitleCard import StandardTitleCard

class Profile:
    """
    This class describes a profile. A profile defines whether to use
    specific aspects of a card - i.e. custom/generic font, custom/generic
    season titles.
    """

    def __init__(self, font_color: str, font_size: float, font: str,
                 font_case: str, font_replacements: dict, hide_seasons: bool,
                 season_map: dict, episode_range: dict, map_or_range: bool,
                 episode_text_format: str) -> None:
        """
        Constructs a new instance of a Profile object. Initializing the
        profile's font, and color.
        """

        # Store this profiles arguments as attributes
        self.font_color = font_color
        self.font_size = font_size
        self.font = font
        self.font_case = StandardTitleCard.CASE_FUNCTION_MAP[font_case]
        self.font_replacements = font_replacements
        self.hide_season_title = hide_seasons
        self.__season_map = season_map
        self.__episode_range = episode_range
        self.__map_or_range = map_or_range
        self.episode_text_format = episode_text_format

        # These flags are only modified when the profile is converted
        self.__use_custom_seasons = True
        self.__use_custom_font = True


    def _get_valid_profiles(self) -> list:
        """
        Gets the valid applicable profiles for this profile. For example,
        for a profile with only generic attributes, it's invalid to
        apply a custom font profile from there.
        
        :returns:   The profiles that can be created as subprofiles
                    from this object.
        """

        # Determine whether this profile uses custom season titles
        has_custom_season_titles = False
        if self.episode_text_format != 'EPISODE {episode_number}':
            has_custom_season_titles = True
        elif self.__episode_range != {}:
            has_custom_season_titles = True
        else:
            for number, title in self.__season_map.items():
                if number == 0:
                    if title.lower() != 'specials':
                        has_custom_season_titles = True
                        break
                else:
                    if title.lower() != f'season {number}':
                        has_custom_season_titles = True
                        break

        # Determine whether this profile uses a custom font
        has_custom_font = \
            (self.font != StandardTitleCard.TITLE_DEFAULT_FONT) or \
            (self.font_size != 1.0) or \
            (self.font_color != StandardTitleCard.TITLE_DEFAULT_COLOR) or \
            (self.font_replacements != StandardTitleCard.DEFAULT_FONT_REPLACEMENTS) or \
            (self.font_case != StandardTitleCard.CASE_FUNCTION_MAP[StandardTitleCard.DEFAULT_CASE_VALUE])

        # Get list of profile strings applicable to this object
        valid_profiles = [{'seasons': 'generic', 'font': 'generic'}]
        if has_custom_font:
            valid_profiles.append({'seasons': 'generic', 'font': 'custom'})
            
        if has_custom_season_titles:
            valid_profiles.append({'seasons': 'custom', 'font': 'generic'})
            if has_custom_font:
                valid_profiles.append({'seasons': 'custom', 'font': 'custom'})

        if self.hide_season_title:
            valid_profiles.append({'seasons': 'hidden', 'font': 'generic'})
            if has_custom_font:
                valid_profiles.append({'seasons': 'hidden', 'font': 'custom'})

        return valid_profiles


    def convert_profile_string(self, seasons: str, font: str) -> None:
        """
        Convert this profile to the provided profile attributes. This modifies
        what characteristics are presented by the object.
        
        
        """

        # Update this object's data
        self.__use_custom_seasons = (seasons == 'custom')
        self.hide_season_title = (seasons == 'hidden')
        self.__use_custom_font = (font == 'custom')

        # If the new profile has a generic font, reset font attributes
        if not self.__use_custom_font:
            self.font = StandardTitleCard.TITLE_DEFAULT_FONT
            self.font_size = 1.0
            self.font_color = StandardTitleCard.TITLE_DEFAULT_COLOR
            self.font_replacements = StandardTitleCard.DEFAULT_FONT_REPLACEMENTS
            self.font_case = StandardTitleCard.CASE_FUNCTION_MAP[
                StandardTitleCard.DEFAULT_CASE_VALUE
            ]


    def get_season_text(self, season_number: int, abs_number: int=None) -> str:
        """
        Gets the season text for the given season number, after applying this
        profile's 'rules' about season text.
        
        :param      season_number:  The season number.
        
        :returns:   The season text for the given entry as defined by this
                    profile.
        """

        # If this profile has hidden season titles, return blank string
        if self.hide_season_title:
            return ''

        # Generic season titles
        if not self.__use_custom_seasons:
            return 'Specials' if season_number == 0 else f'Season {season_number}'

        # Custom season titles and method is season map
        if self.__map_or_range == 'map':
            return self.__season_map[season_number]
        
        # Custom season titles using episode range, check for absolute number
        if abs_number == None:
            # Episode range, but episode has no absolute number
            if season_number != 0: # Don't warn on specials, rarely have range
                warn(f'Episode range preferred, but episode has no absolute '
                     f'number', 1)
            return self.__season_map[season_number]
        elif abs_number not in self.__episode_range:
            # Absolute number doesn't have episode range, fallback on season map
            warn(f'Episode {abs_number} does not fall into specified range', 1)
            return self.__season_map[season_number]

        # Absolute number is provided and falls into mapped episode ranges
        return self.__episode_range[abs_number]


    def get_episode_text(self, episode_number: int, abs_number: int=None)-> str:
        """
        Gets the episode text for the given episode number, as defined by this
        profile.
        
        :param      episode_number: The episode number.

        :param      abs_number:     The absolute episode number. 
        
        :returns:   The episode text defined by this profile.
        """

        # Custom season tag can also indicate custom episode text format
        if self.__use_custom_seasons:
            # Warn if absolute isn't given, but is requested
            if '{abs_number}' in self.episode_text_format and abs_number ==None:
                warn(f'Episode text formatting uses absolute episode number, '
                     f'but episode {episode_number} has no absolute number.')

            return self.episode_text_format.format(
                episode_number=episode_number,
                abs_number=abs_number if abs_number != None else '',
            )

        return f'EPISODE {episode_number}'


    def __remove_episode_text_format(self, title_text: str) -> str:
        """
        Removes text that matches this profile's episode text format. This
        replaces the {episode_number} and {abs_number} format placeholders
        with a regex for any number. Currently, any number expressed as a digit
        (i.e. 1, 2, ... 99999), and all numbers between 1-99 expressed as
        ENGLISH TEXT (i.e. "one", "twenty", "ninety-nine") are removed. For
        example, if self.episode_text_format = 'Chapter {abs_number}':

        >>> self.__remove_episode_text_format('Chapter 1: Title')
        'Title'
        >>> self.__remove_episode_text_format('Chapter Thirty-Three, Example')
        'Example'
        >>> self.__remove_episode_text_format('Chapter 919491 - Longer Title')
        'Longer Title'
        >>> self.__remove_episode_text_format('Chapter Eighty Eight Example 2')
        'Example 2'
        
        :param      episode_text:  The episode text to process.
        
        :returns:   The episode text with all text that matches the format
                    specified in this profile's episode text format REMOVED. If
                    there is no matching text, the title is returned unaltered.
        """

        # Regex group for matching 1-9 called "one_to_9"
        one_to_9 = 'one|two|three|four|five|six|seven|eight|nine'
        one_to_9_group = f'(?<one_to_9>(?:{one_to_9}))'

        # Regex group for matching 10-19 called "ten_to_19"
        ten_to_19 = (
            'ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|'
            'eighteen|nineteen'
        )
        ten_to_19_group = f'(?<ten_to_19>(?:{ten_to_19}))'

        # Regex group for two digit prefix (20, 30..) called "two_digit_prefix"
        two_digit_prefix='twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety'
        two_digit_prefix_group = f'(?<two_digit_prefix>(?:{two_digit_prefix}))'

        # Regex group for 1-99 called "one_to_99"
        one_to_99_group = (
            '(?<one_to_99>(?&two_digit_prefix)(?:[- ](?&one_to_9))?|'
            '(?&ten_to_19)|(?&one_to_9)|\d+)'
        )

        # Define all the groups used in the regex
        define_all = (
            f'(?(DEFINE){one_to_9_group}{ten_to_19_group}'
            f'{two_digit_prefix_group}{one_to_99_group})'
        )

        # Full regex for any number followed by colon, comma, or dash (+spaces)
        full_regex = f'{define_all}(?&one_to_99)\s*[:,-]?\s*'

        # Look for number indicator to replace with above regex
        format_string = self.episode_text_format
        if '{abs_number}' in format_string:
            remove_regex = format_string.replace('{abs_number}', full_regex)
        elif '{episode_number}' in format_string:
            remove_regex = format_string.replace('{episode_number}', full_regex)

        # Find match of above regex, if exists, delete that text
        # Perform match on the case-ified episode text
        text_to_remove = match(remove_regex, title_text, IGNORECASE)

        if text_to_remove:
            info(f'Removed episode number format text "'
                 f'{text_to_remove.group()}" from episode title', 1)
            return title_text.replace(text_to_remove.group(), '')

        return title_text


    def convert_title(self, title_text: str) -> str:
        """
        Convert the given title text through this profile's settings. This is
        any combination of text substitutions, case functions such as
        `str.upper()` or `str.lower()`, and optionally removing text that
        matches the format of this profile's episode text format.

        For example, if the episode format string was
        'Chapter {episode_number}', and the given `title_text` was 'Chapter 1:
        Pilot', then the returned text (excluding any replacements or case
        mappings) would be 'Pilot'.
        
        :param      title_text: The title text to convert.
        
        :returns:   The processed text.
        """

        # Modify the title if it contains the episode text format
        if self.__use_custom_seasons:
            # Attempt to remove case that matches the episode text format string
            title_text = self.__remove_episode_text_format(title_text)

        # Create translation table for this profile's replacements
        translation = str.maketrans(self.font_replacements)

        # Apply translation table to this text
        translated_text = title_text.translate(translation)

        # Apply this profile's font function to the translated text
        return self.font_case(translated_text)


