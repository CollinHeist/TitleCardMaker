from modules.TitleCardMaker import TitleCardMaker

class Profile:
    """
    This class describes a profile. A profile defines whether to use
    specific aspects of a card - i.e. custom/generic font, custom/generic
    season titles.
    """

    """Default profile for unspecified <profile> tag"""
    DEFAULT_PROFILE: str = 'custom-custom'

    def __init__(self, profile_element: 'Element', font_element: 'Element',
                 season_map: dict) -> None:
        """
        Constructs a new instance of a Profile object. Initializing the
        profile's font, and color.
        
        :param      profile_element:    The XML Element <profile> object
                                        from a config. Or None if absent.

        :param      font_element:       The XML Element <font> object from
                                        a config. Or None if absent.

        :param      season_map:         Dictionary mapping season numbers
                                        to season titles.
        """

        # Parse <profile> element if given
        if profile_element is None:
            self._profile = self.DEFAULT_PROFILE
        else:
            self._profile = profile_element.text.lower()

        self.__use_custom_season_title = self._profile.split('-')[0] == 'custom'
        self.hide_season_title = self._profile.split('-')[0] == 'none'
        self.__use_custom_font = self._profile.split('-')[1] == 'custom'

        ## Parse <font> element if given
        # Parse <font></font> text
        self.__custom_font = getattr(font_element, 'text', TitleCardMaker.TITLE_DEFAULT_FONT.resolve())

        # Parse <show size=""> attribute
        try:
            self.__custom_size = float(font_element.attrib['size'][:-1]) / 100.0
        except:
            self.__custom_size = 1.0

        # Parse <show color=""> attribute
        try:
            self.__custom_color = font_element.attrib['color']
        except:
            self.__custom_color = TitleCardMaker.TITLE_DEFAULT_COLOR

        # Parse <show case=""> attribute
        try:
            self.__custom_case = font_element.attrib['case'].lower()
        except:
            self.__custom_case = TitleCardMaker.DEFAULT_CASE_VALUE

        # Set object attributes
        if not self.__use_custom_font:
            self.font = TitleCardMaker.TITLE_DEFAULT_FONT.resolve()
            self.font_size = 1.0
            self.color = TitleCardMaker.TITLE_DEFAULT_COLOR
            self.case = TitleCardMaker.CASE_FUNCTION_MAP[TitleCardMaker.DEFAULT_CASE_VALUE]
        else:
            self.font = self.__custom_font
            self.font_size = self.__custom_size
            self.color = self.__custom_color
            self.case = TitleCardMaker.CASE_FUNCTION_MAP[self.__custom_case]

        self.__season_map = season_map


    def __repr__(self) -> str:
        """
        Returns a unambiguous string representation of the object (for debug...).
        
        :returns:   String representation of the object.
        """

        return (
            f'<Profile font={self.font}, font_size={self.font_size}, '
            f'color={self.color}, case={self.case}>'
        )


    def _get_valid_profile_strings(self) -> list:
        """
        Gets the valid applicable profiles for this profile. For example,
        for a profile with only generic attributes, it's invalid to
        apply a custom font profile from there.
        
        :returns:   The profile strings that can be created as subprofiles
                    from this object.
        """

        # Determine whether this profile uses custom season titles
        has_custom_season_titles = False
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
            (self.font != TitleCardMaker.TITLE_DEFAULT_FONT) or \
            (self.font_size != 1.0) or \
            (self.color != TitleCardMaker.TITLE_DEFAULT_COLOR) or \
            (self.case != TitleCardMaker.CASE_FUNCTION_MAP[TitleCardMaker.DEFAULT_CASE_VALUE])

        # Get list of profile strings applicable to this object
        valid_profiles = ['generic-generic'] + (['generic-custom'] if has_custom_font else [])
        if has_custom_season_titles:
            valid_profiles += ['custom-generic']
            if has_custom_font:
                valid_profiles += ['custom-custom']

        if self.hide_season_title:
            valid_profiles += ['none-generic']
            if has_custom_font:
                valid_profiles += ['none-custom']

        return valid_profiles


    def convert_profile_string(self, profile_string: str) -> None:
        """
        Convert this profile to the provided profile string. This modifies
        what characteristics are presented by the object.
        
        :param      profile_string:  The profile string to update to.
        """

        # Update this object's data
        self.__use_custom_season_title = profile_string.split('-')[0] == 'custom'
        self.hide_season_title = profile_string.split('-')[0] == 'none'
        self.__use_custom_font = profile_string.split('-')[1] == 'custom'

        if self.__use_custom_font:
            self.font = self.__custom_font
            self.font_size = self.__custom_size
            self.color = self.__custom_color
            self.case = TitleCardMaker.CASE_FUNCTION_MAP[self.__custom_case]
        else:
            self.font = TitleCardMaker.TITLE_DEFAULT_FONT
            self.font_size = 1.0
            self.color = TitleCardMaker.TITLE_DEFAULT_COLOR
            self.case = TitleCardMaker.CASE_FUNCTION_MAP[TitleCardMaker.DEFAULT_CASE_VALUE]


    def get_season_text(self, season_number: int) -> str:
        """
        Gets the season text for the given season number, after applying this
        profile's 'rules' about season text.
        
        :param      season_number:  The season number.
        
        :returns:   The season text. '' if season text is hidden in this profile.
        """

        if self.hide_season_title:
            return ''

        if self.__use_custom_season_title:
            return self.__season_map[season_number]

        return 'Specials' if season_number == 0 else f'Season {season_number}'


    def get_episode_text(self, episde_number: int) -> str:
        """
        Gets the episode text.
        
        :param      episde_number:  The episde number.
        
        :returns:   The episode text.
        """

        return f'Episode {episde_number}'


    def convert_title(self, episode_text: str) -> str:
        """
        Wrap the given episode text through this profile's case setting.
        This is any abitrary function for text processing. Typically
        `str.upper()` or `str.lower()`.
        
        :param      episode_text:   The episode text to convert.
        
        :returns:   The processed text
        """

        # The default font has swapped the () and [] characters - unswap them
        if self.font == TitleCardMaker.TITLE_DEFAULT_FONT:
            episode_text = episode_text.translate(
                str.maketrans({'(': '[', ')': ']', '[': '(', ']': ')'})
            )

        return self.case(episode_text)

