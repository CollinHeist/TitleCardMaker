from TitleCardMaker import TitleCardMaker

class Profile:
    """
    This class describes a profile. A profile determines whether to use
    custom or generic font and season titles.
    """

    DEFAULT_PROFILE = 'custom-custom'

    PROFILE_MAP: dict = {
        'custom-custom':   'Custom Season Titles, Custom Font',
        'custom-generic':  'Custom Season Titles, Generic Font',
        'generic-custom':  'Generic Season Titles, Custom Font',
        'generic-generic': 'Generic Season Titles, Generic Font',
        'none-custom':     'No Season Titles, Custom Font',
        'none-generic':    'No Season Titles, Generic Font',
    }

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

        # If a profile wasn't specified, use the default
        if profile_element is None:
            self._profile = self.DEFAULT_PROFILE
        else:
            self._profile = profile_element.text.lower()

        # Booleans for custom/hidden font/titles
        self.__use_custom_season_title = self._profile.split('-')[0] == 'custom'
        self.hide_season_title = self._profile.split('-')[0] == 'none'
        self.__use_custom_font = self._profile.split('-')[1] == 'custom'

        # If a font wasn't specified (or profile is generic), use the default font+color
        if font_element is None or not self.__use_custom_font:
            self.font = TitleCardMaker.TITLE_DEFAULT_FONT
            self.color = TitleCardMaker.TITLE_DEFAULT_COLOR
        else:
            self.font = font_element.text
            try:
                self.color = font_element.attrib['color']
            except KeyError:
                self.color = TitleCardMaker.TITLE_DEFAULT_COLOR

        self.__season_map = season_map


    def get_season_text(self, season_number: int) -> str:
        """
        Gets the season text for the given season number, after applying this
        profile's 'rules' about season text.
        
        :param      season_number:  The season number.
        
        :returns:   The season text. '' if season text is hidden
        """

        return '' if self.hide_season_title else self.__season_map[season_number]


    def get_episode_text(self, episde_number: int) -> str:
        """
        Gets the episode text.
        
        :param      episde_number:  The episde number.
        
        :returns:   The episode text.
        """

        return f'Episode {episde_number}'

