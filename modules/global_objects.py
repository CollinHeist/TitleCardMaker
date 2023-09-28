from pathlib import Path


class TemporaryPreferenceParser:
    """
    Pseudo PreferenceParser object for providing when TCM is not fully
    initialized.
    """

    DEFAULT_TEMP_DIR = Path(__file__).parent / '.objects'

    def __init__(self, database_directory):
        """Fake initialize this object"""

        self.card_dimensions = '3200x1800'
        self.database_directory = Path(database_directory)
        self.imagemagick_container = None

# pylint: disable=global-statement
pp = TemporaryPreferenceParser(Path(__file__).parent / '.objects')
def set_preference_parser(to: 'PreferenceParser') -> None: # type: ignore
    """Update the global PreferenceParser `pp` object"""

    global pp
    pp = to

fv = None
def set_font_validator(to: 'FontValidator') -> None: # type: ignore
    """Update the global FontValidator `fv` object."""

    global fv
    fv = to

info_set = None
def set_media_info_set(to: 'MediaInfoSet') -> None: # type: ignore
    """Update the global MediaInfoSet `info_set` object."""

    global info_set
    info_set = to

show_record_keeper = None
def set_show_record_keeper(to: 'ShowRecordKeeper') -> None: # type: ignore
    """Update the global ShowRecordKeeper `show_record_keeper` object."""

    global show_record_keeper
    show_record_keeper = to
