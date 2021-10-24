from pathlib import Path

from TitleCardMaker import TitleCardMaker

class TitleCardProfile:
    """
    This class describes a title card profile.
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

    def __init__(self, profile_attribute: 'Element', archive_directory: Path,
                 font: str, color: str, season_map: dict) -> None:

        if profile_attribute is None:
            self.active_profile = self.DEFAULT_PROFILE
        else:
            profile = profile_attribute.text.lower()
            if profile not in self.PROFILE_MAP:
                raise ValueError(f'Profile "{profile} is not valid.')

            self.active_profile = profile

        # If the active profile specifies a custom font, use input font/color
        if self.__use_custom_font():
            self.active_font = font
            self.active_color = color
        else:
            self.active_font = TitleCardMaker.TITLE_DEFAULT_FONT
            self.active_color = TitleCardMaker.TITLE_DEFAULT_COLOR

        self.__season_map = season_map

        # Determine whether custom font/season names are used
        self.has_custom_season_titles = not all(
            title.lower() in [f'season {number}', 'specials'] for number, title in season_map.items()
        )

        self.has_custom_font = (
            font is not TitleCardMaker.TITLE_DEFAULT_FONT
        ) or (color is not TitleCardMaker.TITLE_DEFAULT_COLOR)

        # Construct list of profiles to add to archive
        self.archive_profiles = []
        if self.has_custom_season_titles:
            self.archive_profiles += ['custom-generic', 'generic-generic']
            if self.has_custom_font:
                self.archive_profiles += ['custom-custom', 'generic-custom']

        if self.__hide_season_title():
            self.archive_profiles += ['none-generic']
            if self.has_custom_font:
                self.archive_profiles += ['none-custom']


    def get_season_text(self, season_number: int) -> str:
        """
        Gets the season text.
        
        :param      season_number:  The season number
        :type       season_number:  int
        
        :returns:   The season text.
        :rtype:     str
        """

        return '' if self.__hide_season_title() else self.__season_map[season_number]


    def get_title_card_maker_args(self, season_number: int,
                                  episode_number: int) -> dict:
        """
        Gets the title card maker arguments.
        
        :returns:   The title card maker arguments.
        :rtype:     dict
        """

        return {
            'font':         self.active_font,
            'season_text':  self.get_season_text(season_number),
            'episode_text': f'Episode {episode_number}',
            'title_color':  self.active_color,
            'hide_season':  self.__hide_season_title(),
        }


    def __use_custom_season_title(self) -> bool:
        """
        Determines if custom season title.
        
        :returns:   True if custom season title, False otherwise.
        """

        return self.active_profile.split('-')[0] == 'custom'


    def __hide_season_title(self) -> bool:
        """
        Hides the season title.
        
        :returns:   { description_of_the_return_value }
        :rtype:     bool
        """

        return self.active_profile.split('-')[0] == 'none'


    def __use_custom_font(self) -> bool:
        """
        { function_description }
        
        :returns:   { description_of_the_return_value }
        :rtype:     bool
        """

        return self.active_profile.split('-')[1] == 'custom'
