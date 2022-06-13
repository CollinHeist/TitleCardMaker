from regex import match, IGNORECASE

from modules.CardType import CardType
from modules.Debug import log
from modules.MultiEpisode import MultiEpisode
import modules.global_objects as global_objects

class Profile:
    """
    This class describes a profile. A profile defines whether to use
    specific aspects of a card - i.e. custom/generic font, custom/generic
    season titles.
    """

    def __init__(self, font: 'Font', hide_seasons: bool,
                 episode_map: 'EpisodeMap', episode_text_format: str) -> None:
        """
        Constructs a new instance of a Profile. All given arguments will be
        applied through this Profile (and whether it's generic/custom).
        
        :param      font:                   The Font for this profile.
        :param      hide_seasons:           Whether to hide/show seasons.
        :param      episode_map:            EpisodeMap for the series.
        :param      episode_text_format:    The episode text format string.
        """

        # Store this profiles arguments as attributes
        self.font = font
        self.hide_season_title = hide_seasons
        self.__episode_map = episode_map
        self.episode_text_format = episode_text_format

        # These flags are only modified when the profile is converted
        self.__use_custom_seasons = True
        self.__use_custom_font = True


    def get_valid_profiles(self, card_class: CardType) -> [dict]:
        """
        Gets the valid applicable profiles for this profile. For example,
        for a profile with only generic attributes, it's invalid to
        apply a custom font profile from there.

        :param      card_class: Implementation of CardType whose valid 
                                subprofiles are requested. 
        
        :returns:   The profiles that can be created as subprofiles from this
                    object.
        """

        # Determine whether this profile uses custom season titles
        has_custom_season_titles = card_class.is_custom_season_titles(
            custom_episode_map=self.__episode_map.is_custom,
            episode_text_format=self.episode_text_format,
        )
        
        # Determine whether this profile uses a custom font
        has_custom_font = card_class.is_custom_font(self.font)

        # If not archiving all variations, return only indicated profile
        if not global_objects.pp.archive_all_variations:
            seasons = 'generic'
            if self.hide_season_title and card_class.USES_SEASON_TITLE:
                seasons = 'hidden'
            elif has_custom_season_titles:
                seasons = 'custom'

            return [{
                'seasons': seasons,
                'font': 'custom' if has_custom_font else 'generic'
            }]

        # Get list of profile strings applicable to this object
        valid_profiles = [{'seasons': 'generic', 'font': 'generic'}]
        if has_custom_font:
            valid_profiles.append({'seasons': 'generic', 'font': 'custom'})
            
        if has_custom_season_titles:
            valid_profiles.append({'seasons': 'custom', 'font': 'generic'})
            if has_custom_font:
                valid_profiles.append({'seasons': 'custom', 'font': 'custom'})

        if self.hide_season_title and card_class.USES_SEASON_TITLE:
            valid_profiles.append({'seasons': 'hidden', 'font': 'generic'})
            if has_custom_font:
                valid_profiles.append({'seasons': 'hidden', 'font': 'custom'})

        return valid_profiles


    def convert_profile(self, card_class: CardType, seasons: str,
                        font: str) -> None:
        """
        Convert this profile to the provided profile attributes. This modifies
        what characteristics are presented by the object.
        
        :param      card_class: CardType whose default characteristics should
                                be used if converting to default values.
        :param      seasons:    String of how to modify seasons. Must be one of
                                'custom', 'generic', or 'hidden'.
        :param      font:       String of how to modify fonts. Must be 'custom'
                                or 'generic'.
        """

        # Update this object's data
        self.__use_custom_seasons = (seasons == 'custom')
        self.hide_season_title = (seasons == 'hidden')
        self.__use_custom_font = (font == 'custom')

        # If the new profile has a generic font, reset font attributes
        if not self.__use_custom_font:
            self.font.set_default()


    def get_season_text(self, episode_info: 'EpisodeInfo') -> str:
        """
        Gets the season text for the given season number, after applying this
        profile's 'rules' about season text.
        
        :param      episode_info:   Episode info to get the season text of.
        
        :returns:   The season text for the given entry as defined by this
                    profile.
        """

        # If this profile has hidden season titles, return blank string
        if self.hide_season_title:
            return ''

        # Generic season titles are Specials and Season {n}
        if not self.__use_custom_seasons:
            return self.__episode_map.get_generic_season_title(
                episode_info=episode_info
            )

        # Custom season title, query EpisodeMap for title
        return self.__episode_map.get_season_title(episode_info)


    def get_episode_text(self, episode: 'Episode') -> str:
        """
        Gets the episode text for the given episode info, as defined by this
        profile.
        
        :param      episode_info:   Episode info to get the episode text of.
        
        :returns:   The episode text defined by this profile.
        """

        # Warn if absolute number is requested but not present
        if (self.__use_custom_seasons and '{abs_' in self.episode_text_format
            and episode.episode_info.abs_number is None):
                log.warning(f'Episode text formatting uses absolute episode '
                            f'number, but {episode} has no absolute number')

        # Format MultiEpisode episode text
        if isinstance(episode, MultiEpisode):
            # If no custom season/episode text, use card class standard
            new_etf = episode.modify_format_string(
                self.episode_text_format
                if self.__use_custom_seasons else
                episode.card_class.EPISODE_TEXT_FORMAT
            )

            return new_etf.format(
                season_number=episode.season_number,
                episode_start=episode.episode_start,
                episode_end=episode.episode_end,
                abs_start=episode.abs_start,
                abs_end=episode.abs_end,
                **episode.extra_characteristics,
            )

        # Standard Episode class
        if self.__use_custom_seasons:
            format_string = self.episode_text_format
        else:
            format_string = episode.card_class.EPISODE_TEXT_FORMAT

        try:
            return format_string.format(
                season_number=episode.episode_info.season_number,
                episode_number=episode.episode_info.episode_number,
                abs_number=episode.episode_info.abs_number,
                **episode.extra_characteristics,
            )
        except Exception:
            log.error(f'Cannot format episode text "{format_string}" for '
                      f'{episode}')
            return f'EPISODE {episode.episode_info.episode_number}'


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
        one_to_9_group = rf'(?<one_to_9>(?:{one_to_9}))'

        # Regex group for matching 10-19 called "ten_to_19"
        ten_to_19 = (
            'ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|'
            'eighteen|nineteen'
        )
        ten_to_19_group = rf'(?<ten_to_19>(?:{ten_to_19}))'

        # Regex group for two digit prefix (20, 30..) called "two_digit_prefix"
        two_digit_prefix='twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety'
        two_digit_prefix_group = rf'(?<two_digit_prefix>(?:{two_digit_prefix}))'

        # Regex group for 1-99 called "one_to_99"
        one_to_99_group = (
            r'(?<one_to_99>(?&two_digit_prefix)(?:[- ](?&one_to_9))?|'
            r'(?&ten_to_19)|(?&one_to_9)|\d+)'
        )

        # Define all the groups used in the regex
        define_all = (
            f'(?(DEFINE){one_to_9_group}{ten_to_19_group}'
            f'{two_digit_prefix_group}{one_to_99_group})'
        )

        # Full regex for any number followed by colon, comma, or dash (+spaces)
        full_regex = rf'{define_all}(?&one_to_99)\s*[:,-]?\s*'

        # Look for number indicator to replace with above regex
        format_string = self.episode_text_format
        if '{abs_number}' in format_string:
            remove_regex = format_string.replace('{abs_number}', full_regex)
        elif '{episode_number}' in format_string:
            remove_regex = format_string.replace('{episode_number}', full_regex)
        else:
            return title_text

        # Find match of above regex, if exists, delete that text
        # Perform match on the case-ified episode text
        try:
            text_to_remove = match(remove_regex, title_text, IGNORECASE)
        except Exception:
            # Regex match error, return title text
            return title_text

        # If there's no match, return the original title
        if not text_to_remove:
            return title_text

        # Replace removal text, return original if all text was removed
        finalized_title = title_text.replace(text_to_remove.group(), '')
        return title_text if len(finalized_title) == 0 else finalized_title


    def convert_title(self, title_text: str,
                      manually_specified: bool=False) -> str:
        """
        Convert the given title text through this profile's settings. This is
        any combination of text substitutions, case functions, and optionally
        removing text that matches the format of this profile's episode text
        format.

        For example, if the episode format string was 'Chapter {episode_number}'
        and the given `title_text` was 'Chapter 1: Pilot', then the returned
        text (excluding any replacements or case mappings) would be 'Pilot'.
        
        :param      title_text:         The title text to convert.
        :param      manually_specified: Whether the given title text has been
                                        manually specified.
        
        :returns:   The processed text.
        """

        # Modify the title if it contains the episode text format
        if self.__use_custom_seasons:
            # Attempt to remove text that matches the episode text format string
            title_text = self.__remove_episode_text_format(title_text)

        # Create translation table for this profile's replacements
        translation = str.maketrans(self.font.replacements)

        # Apply translation table to this text
        translated_text = title_text.translate(translation)

        # Apply this profile's font function to the translated text, unless
        # this is a manually specified title and we're apply title casing
        if manually_specified and self.font.case_name in ('title', 'source'):
            return translated_text

        return self.font.case(translated_text)


