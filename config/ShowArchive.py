from pathlib import Path

from Show import Show

class ShowArchive:

    PROFILE_DIRECTORY_MAP: dict = {
        'custom-custom':   'Custom Season Titles, Custom Font',
        'custom-generic':  'Custom Season Titles, Generic Font',
        'generic-custom':  'Generic Season Titles, Custom Font',
        'generic-generic': 'Generic Season Titles, Generic Font',
        'none-custom':     'No Season Titles, Custom Font',
        'none-generic':    'No Season Titles, Generic Font',
    }

    def __init__(self, archive_directory: Path, *args: tuple,
                 **kwargs: dict) -> None:

        """
        Constructs a new instance.
        
        :param      show:  The show
        """
        
        base_show = Show(*args, **kwargs)

        self.shows = []
        for profile_string in base_show.profile._get_valid_profile_strings():
            # Create show object for this profile
            show = Show(*args, **kwargs)

            # Update media directory, update profile and parse source
            show.media_directory = (
                archive_directory / show.full_name / self.PROFILE_DIRECTORY_MAP[profile_string]
            )
            show.profile.convert_profile_string(profile_string)
            show.read_source()

            self.shows.append(show)


    def update_archive(self, *args: tuple, **kwargs: dict) -> int:
        for show in self.shows:
            show.create_missing_title_cards(*args, **kwargs)

