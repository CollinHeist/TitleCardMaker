# Global PreferenceParser object
pp = None
def set_preference_parser(to: 'PreferenceParser') -> None:
    global pp
    pp = to