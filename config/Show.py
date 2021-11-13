from pathlib import Path

from DataFileInterface import DataFileInterface
from Debug import *
from Episode import Episode
from Profile import Profile
from TitleCard import TitleCard

class Show:
    """
    This class describes a show.
    """

    HAS_NO_NEW_EPISODES: int = 0
    HAS_NEW_EPISODES: int = 1

    NO_NEW_TITLE_CARDS: int = 0
    CREATED_NEW_TITLE_CARDS: int = 1


    def __init__(self, show_element: 'Element', source: Path, media: Path) -> None:
        """
        Constructs a new instance.
        
        :param      show_element:   The show element

        :param      source:         The source

        :param      media:          The media
        """

        # Parse <show name="..."> attribute
        self.name = show_element.attrib['name']

        # Parse <show year="..."> attribute
        self.year = int(show_element.attrib['year'])

        # Full name is name (year)
        self.full_name = f'{self.name} ({self.year})'

        # Parse <show season_count="..."> attribute
        self.season_count = int(show_element.attrib['seasons'])

        # Parse <show/season_map> element (if present)
        # Parse <season_map> tag (if present) - default is 1:Season 1, 2:Season 2, etc.
        self.season_map = {n: f'Season {n}' for n in range(1, self.season_count+1)}
        self.season_map.update({0: 'Specials'})

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

        self.library = media.name
        self.source_directory = source / self.full_name
        self.media_directory = media / self.full_name

        # Create this show's interface to it's data file
        self.file_interface = DataFileInterface(
            self.source_directory / DataFileInterface.GENERIC_DATA_FILE_NAME
        )

        # Create empty set of Episode objects
        self.episodes = {}


    def __repr__(self) -> str:
        """
        Returns a unambiguous string representation of the object (for debug...).
        
        :returns:   String representation of the object.
        """

        return (
            f'<Show full_name={self.full_name}, season_map={self.season_map}'
            f', profile={self.profile}, episodes={self.episodes}>'
        )


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
            f'{self.full_name} - S{season_number:02}E{episode_number:02}{TitleCard.OUTPUT_CARD_EXTENSION}'
        )

        return self.media_directory / season_folder / filename


    def read_source(self) -> None:
        """
        { function_description }
        """

        for data_row in self.file_interface.read():
            key = f'{data_row["season_number"]}-{data_row["episode_number"]}'
            if key in self.episodes and self.episodes[key].matches(data_row):
                continue

            # Construct the file destination for Episode object building
            self.episodes[key] = Episode(
                base_source=self.source_directory,
                destination=self._get_destination(data_row),
                **data_row
            )


    def check_sonarr_for_new_episodes(self, sonarr_interface: 'SonarrInterface') -> int:
        """
        Query the provided SonarrInterface object, checking if the returned episodes
        exist in this show's associated source. All new entries are added to this 
        object's DataFileInterface.
        
        :param  sonarr_interface:   The sonarr interface to query.
        """

        # Refresh data from file interface
        self.read_source()

        # Get dict of episode data from Sonarr
        try:
            all_episodes = sonarr_interface.get_all_episodes_for_series(self.name, self.year)
        except ValueError:
            error(f'Cannot find series "{self.full_name}" in Sonarr')
            return self.HAS_NO_NEW_EPISODES

        # For each episode, check if the data matches any contained Episode objects
        has_new = False
        for new_episode in all_episodes:
            # Compare against every Episode in this Show
            key = f'{new_episode["season_number"]}-{new_episode["episode_number"]}'
            if key in self.episodes and self.episodes[key].matches(new_episode):
                continue

            # Construct data for new row
            has_new = True
            top, bottom = Episode.split_episode_title(new_episode.pop('title'))
            new_episode.update({'title_top': top, 'title_bottom': bottom})

            info(f'Sonarr indicates new episode ({new_episode})')

            # Add entry to data file through interface
            self.file_interface.add_entry(**new_episode)

        # If new entries were added, re-parse source file
        if has_new:
            self.read_source()
            return self.HAS_NEW_EPISODES
        else:
            return self.HAS_NO_NEW_EPISODES


    def create_missing_title_cards(self,
                                   database_interface: 'DatabaseInterface'=None) -> int:
        """
        Creates missing title cards.
        """

        info(f'Processing Show "{self.full_name}"')
        created_new_cards = TitleCard.NO_TITLE_CARD_CREATED

        # Go through each episode for this show
        for _, episode in self.episodes.items():
            title_card = TitleCard(episode, self.profile)

            # If the title card doesn't exist...
            if not episode.source.exists():
                # Already queried the database, skip
                if not episode.in_database:
                    continue

                # If a DatabaseInterface is provided, query for this episode's source image
                if database_interface is not None:
                    image_url = database_interface.get_title_card_source_image(
                        self.name,
                        self.year,
                        episode.season_number,
                        episode.episode_number,
                    )

                    if image_url is None:
                        episode.in_database = False
                        continue
                    else:
                        database_interface.download_image(image_url, episode.source)

            # Source exists, create the title card
            created_new_cards |= title_card.create()

        if created_new_cards == TitleCard.NO_TITLE_CARD_CREATED:
            return self.NO_NEW_TITLE_CARDS

        return self.CREATED_NEW_TITLE_CARDS



