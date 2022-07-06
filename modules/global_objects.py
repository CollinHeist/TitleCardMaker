# Global PreferenceParser object
pp = None
def set_preference_parser(to: 'PreferenceParser') -> None:
    global pp
    pp = to

fv = None
def set_font_validator(to: 'FontValidator') -> None:
    global fv
    fv = to

info_set = None
def set_media_info_set(to: 'MediaInfoSet') -> None:
    global info_set
    info_set = to