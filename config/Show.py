from pathlib import Path

from DataFileInterface import DataFileInterface
from Debug import *
from Episode import Episode
from Profile import Profile
from TitleCard import TitleCard

class Show:
    def __init__(self, show_element: 'Element', source: Path, media: Path) -> None:
        """
        Constructs a new instance.
        
        :param      show_element:   The show element

        :param      source:         The source

        :param      media:          The media
        """

        # show_element will have name, year, season_count, season_map, profile

        # Parse <show name="..."> attribute
        self.name = show_element.attrib['name']

        # Parse <show year="..."> attribute
        self.year = int(show_element.attrib['year'])

        # Parse <show season_count="..."> attribute
        self.season_count = int(show_element.attrib['seasons'])

        # Parse <show/season_map> element (if present)
        # Parse <season_map> tag (if present) - default is 1:Season 1, 2:Season 2, etc.
        self.season_map = {n: f'Season {n}' for n in range(1, self.season_count+1)}
        self.season_map.update({0: 'SPECIALS'})

        for season in show_element.findall('season_map/'):
            self.season_map.update({
                int(season.attrib['number']): season.attrib['name']
            })

        # Parse <profile> tag (if present) into a Profile object
        self.profile = Profile(
            show_element.find('profile'),
            show_element.find('font'),
            self.season_map,
        )

        self.source_directory = source / f'{self.name} ({self.year})'
        self.media_directory = media / f'{self.name} ({self.year})'

        # Create this show's interface to it's data file
        self.file_interface = DataFileInterface(
            self.source_directory / DataFileInterface.GENERIC_DATA_FILE_NAME
        )

        # Create empty set of Episode objects
        self.episodes = []


    def _get_destination(self, data_row: dict) -> Path:
        """
        Get the destination filename for the given data row. The row's
        'season_number', and 'episode_number' keys are used.
        
        :param      data_row:   The data row returned from the file interface.
        
        :returns:   Path for the full title card destination
        """

        # Read from data row
        season_number = int(data_row['season_number'])
        episode_number = int(data_row['episode_number'])

        # Get the season folder corresponding to this episode's season
        season_folder = 'Specials' if season_number == 0 else f'Season {season_number}'

        # The standard plex filename for this episode
        filename = (
            f'{self.name} ({self.year}) - '
            f'S{season_number:02}E{episode_number:02}{TitleCard.OUTPUT_CARD_EXTENSION}'
        )

        return self.media_directory / season_folder / filename


    def check_sonarr_for_new_episodes(self, sonarr_interface: 'SonarrInterface') -> None:
        """
        { function_description }
        
        :param      sonarr_interface:  The sonarr interface
        """

        # Refresh data from file interface
        self.parse_episodes()

        # Get dict of episode data from Sonarr
        all_episodes = sonarr_interface.get_all_episodes_for_series(self.name)

        # For each episode, check if the data matches any contained Episode objects
        for new_episode in all_episodes:
            # Compare against every Episode in this Show
            has_match = False
            for current_episode in self.episodes:
                if current_episode.matches(new_episode):
                    has_match = True
                    break

            # If no match is found, add to source file
            if not has_match:
                # Construct data for new row
                top, bottom = Episode.split_episode_title(new_episode.pop('title'))
                new_episode.update({'title_top': top, 'title_bottom': bottom})

                info(f'Sonarr indicates new episode ({new_episode})')

                # Add entry to data file through interface
                self.file_interface.add_entry(**new_episode)

        # After adding new entries, re-parse source file
        self.parse_episodes()


    def parse_episodes(self) -> None:
        """
        { function_description }
        """

        self.episodes = []
        for data_row in self.file_interface.read():
            # Construct the file destination for Episode object building
            self.episodes.append(
                Episode(
                    base_source=self.source_directory,
                    destination=self._get_destination(data_row),
                    **data_row
                )
            )


    def create_missing_title_cards(self,
                                   database_interface: 'DatabaseInterface'=None) -> None:
        """
        Creates missing title cards.
        
        :returns:   { description_of_the_return_value }
        :rtype:     None
        """

        for episode in self.episodes:
            title_card = TitleCard(episode, self.profile)

            if not episode.source.exists() and database_interface is not None:
                # Get the image URL for this episode's image
                image_url = database_interface.get_title_card_source_image(
                    self.name,
                    episode.season_number,
                    episode.episode_number,
                    self.year,
                )

                if image_url is not None:
                    info(f'Downloading source image ({episode.destination}).')
                    database_interface.download_image(image_url, episode.destination)

            title_card.create()




