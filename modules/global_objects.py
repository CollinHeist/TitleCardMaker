from pathlib import Path


class TemporaryPreferenceParser:
    DEFAULT_TEMP_DIR = Path(__file__).parent / '.objects'
    def __init__(self, database_directory):
        self.database_directory = Path(database_directory)


pp = TemporaryPreferenceParser(Path(__file__).parent / '.objects')
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

show_record_keeper = None
def set_show_record_keeper(to: 'ShowRecordKeeper') -> None:
    global show_record_keeper
    show_record_keeper = to